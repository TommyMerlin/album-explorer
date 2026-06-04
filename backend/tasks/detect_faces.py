"""检测人脸、提取 embedding 并生成人脸缩略图。

用法：
    python -m tasks.detect_faces [--det-size 640] [--preload-workers 8]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

MIN_FACE_SIZE = 80
FACE_THUMB_SIZE = 112


def detect_path_prefix(sample_path: str, image_root: Path) -> str | None:
    """检测数据库路径与实际 image_root 之间需要替换的前缀。"""
    p = Path(sample_path)
    if p.exists():
        return None  # 不需要重映射
    for i in range(1, len(p.parts)):
        candidate = image_root / Path(*p.parts[i:])
        if candidate.exists():
            return str(Path(*p.parts[:i]))
    return None


def remap_path(abs_path: str, prefix: str | None, image_root: Path) -> str:
    """替换路径前缀。"""
    if prefix is None:
        return abs_path
    return str(image_root / abs_path[len(prefix):].lstrip("/"))


def load_image(abs_path: str, source_format: str | None) -> np.ndarray | None:
    path = Path(abs_path)
    if not path.exists():
        return None
    img = cv2.imread(str(path))
    if img is None:
        if source_format and source_format.lower() in ("heic", "heif"):
            try:
                pil_img = Image.open(path).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception:
                return None
        else:
            return None
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="检测人脸并提取 embedding")
    parser.add_argument("--det-size", type=int, default=640, help="检测输入尺寸")
    parser.add_argument("--preload-workers", type=int, default=2, help="图片预加载线程数")
    parser.add_argument("--threads", type=int, default=4, help="onnxruntime 推理线程数")
    args = parser.parse_args()

    from insightface.app import FaceAnalysis

    face_thumbs_dir = settings.vectors_dir / "face_thumbs"
    face_thumbs_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    print("加载 insightface 模型...")
    import onnxruntime
    onnxruntime.set_default_logger_severity(3)
    sess_options = onnxruntime.SessionOptions()
    sess_options.intra_op_num_threads = args.threads
    sess_options.inter_op_num_threads = 1

    available = onnxruntime.get_available_providers()
    if "CUDAExecutionProvider" in available:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        print("使用 GPU 推理")
    else:
        providers = ["CPUExecutionProvider"]
        print("使用 CPU 推理")

    app = FaceAnalysis(name="buffalo_l", providers=providers)
    app.prepare(ctx_id=0, det_size=(args.det_size, args.det_size))

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            face_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            bbox TEXT NOT NULL,
            confidence REAL NOT NULL,
            embedding_idx INTEGER,
            person_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_faces_asset ON faces(asset_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_faces_person ON faces(person_id)")
    conn.commit()

    existing_asset_ids = set(
        r[0] for r in conn.execute("SELECT DISTINCT asset_id FROM faces").fetchall()
    )
    rows = conn.execute(
        "SELECT asset_id, abs_path, source_format FROM assets WHERE status = 'done'"
    ).fetchall()
    tasks = [r for r in rows if r["asset_id"] not in existing_asset_ids]
    print(f"总计 {len(rows)} 张图片，待检测 {len(tasks)} 张")

    if not tasks:
        print("无需处理")
        conn.close()
        return

    # 检测路径前缀映射
    path_prefix = detect_path_prefix(tasks[0]["abs_path"], settings.image_root)
    if path_prefix:
        print(f"路径重映射: {path_prefix} -> {settings.image_root}")

    BATCH_SIZE = 200

    emb_path = settings.vectors_dir / "face_embeddings.npy"
    ids_path = settings.vectors_dir / "face_ids.npy"

    if emb_path.exists() and ids_path.exists():
        existing_embs = np.load(str(emb_path))
        existing_ids = np.load(str(ids_path)).tolist()
    else:
        existing_embs = np.zeros((0, 512), dtype=np.float32)
        existing_ids = []

    total_new_faces = 0
    processed = 0

    for batch_start in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[batch_start:batch_start + BATCH_SIZE]
        batch_embeddings: list[np.ndarray] = []
        batch_records: list[dict] = []

        img_queue: Queue = Queue(maxsize=args.preload_workers * 4)

        def producer(batch_tasks=batch):
            with ThreadPoolExecutor(max_workers=args.preload_workers) as pool:
                for row in batch_tasks:
                    mapped = remap_path(row["abs_path"], path_prefix, settings.image_root)
                    future = pool.submit(load_image, mapped, row["source_format"])
                    img_queue.put((row["asset_id"], future))
            img_queue.put(None)

        producer_thread = Thread(target=producer, daemon=True)
        producer_thread.start()

        while True:
            item = img_queue.get()
            if item is None:
                break
            asset_id, future = item
            img = future.result()

            if img is None:
                processed += 1
                continue

            try:
                faces = app.get(img)
                for face in faces:
                    bbox = face.bbox.astype(int).tolist()
                    x1, y1, x2, y2 = bbox
                    w, h = x2 - x1, y2 - y1
                    if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                        continue

                    ih, iw = img.shape[:2]
                    cx1, cy1 = max(0, x1), max(0, y1)
                    cx2, cy2 = min(iw, x2), min(ih, y2)
                    face_crop = img[cy1:cy2, cx1:cx2]
                    face_crop_resized = cv2.resize(face_crop, (FACE_THUMB_SIZE, FACE_THUMB_SIZE))

                    batch_records.append({
                        "asset_id": asset_id,
                        "bbox": json.dumps(bbox),
                        "confidence": float(face.det_score),
                        "crop": face_crop_resized,
                    })
                    batch_embeddings.append(face.normed_embedding.copy())
            except Exception as e:
                print(f"  [错误] asset_id={asset_id}: {e}")

            del img
            processed += 1
            if processed % 50 == 0:
                print(f"  已处理 {processed}/{len(tasks)}, 本批检测到 {len(batch_records)} 张人脸")

        producer_thread.join()

        if not batch_records:
            continue

        now = datetime.now().isoformat()
        cursor = conn.cursor()
        batch_ids: list[int] = []

        for rec in batch_records:
            cursor.execute(
                "INSERT INTO faces (asset_id, bbox, confidence, created_at) VALUES (?, ?, ?, ?)",
                [rec["asset_id"], rec["bbox"], rec["confidence"], now],
            )
            batch_ids.append(cursor.lastrowid)

        for i, face_id in enumerate(batch_ids):
            emb_idx = len(existing_ids) + i
            conn.execute("UPDATE faces SET embedding_idx = ? WHERE face_id = ?", [emb_idx, face_id])
            thumb_path = face_thumbs_dir / f"{face_id}.webp"
            cv2.imwrite(str(thumb_path), batch_records[i]["crop"], [cv2.IMWRITE_WEBP_QUALITY, 85])

        conn.commit()

        new_embs = np.array(batch_embeddings, dtype=np.float32)
        if len(existing_embs) > 0:
            existing_embs = np.vstack([existing_embs, new_embs])
        else:
            existing_embs = new_embs
        existing_ids.extend(batch_ids)

        np.save(str(emb_path), existing_embs)
        np.save(str(ids_path), np.array(existing_ids, dtype=np.int64))

        total_new_faces += len(batch_ids)
        print(f"  批次 {batch_start // BATCH_SIZE + 1} 完成，新增 {len(batch_ids)} 张人脸")

        del batch_records, batch_embeddings, new_embs

    conn.close()
    print(f"全部完成！新增 {total_new_faces} 张人脸，总计 {len(existing_ids)} 张")


if __name__ == "__main__":
    main()
