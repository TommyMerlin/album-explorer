"""检测人脸、提取 embedding 并生成人脸缩略图。

用法：
    python -m tasks.detect_faces [--det-size 640]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

MIN_FACE_SIZE = 80
FACE_THUMB_SIZE = 112


def main() -> None:
    parser = argparse.ArgumentParser(description="检测人脸并提取 embedding")
    parser.add_argument("--det-size", type=int, default=640, help="检测输入尺寸")
    args = parser.parse_args()

    from insightface.app import FaceAnalysis

    face_thumbs_dir = settings.vectors_dir / "face_thumbs"
    face_thumbs_dir.mkdir(parents=True, exist_ok=True)

    print("加载 insightface 模型...")
    app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
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

    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    all_embeddings: list[np.ndarray] = []
    all_records: list[dict] = []
    processed = 0

    for row in tasks:
        asset_id = row["asset_id"]
        abs_path = row["abs_path"]
        source_format = row["source_format"]
        path = Path(abs_path)

        if not path.exists():
            processed += 1
            continue

        try:
            img = cv2.imread(str(path))
            if img is None:
                if source_format and source_format.lower() in ("heic", "heif"):
                    pil_img = Image.open(path).convert("RGB")
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                else:
                    processed += 1
                    continue

            faces = app.get(img)

            for face in faces:
                bbox = face.bbox.astype(int).tolist()
                x1, y1, x2, y2 = bbox
                w, h = x2 - x1, y2 - y1
                if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                    continue

                # 裁剪人脸
                ih, iw = img.shape[:2]
                cx1, cy1 = max(0, x1), max(0, y1)
                cx2, cy2 = min(iw, x2), min(ih, y2)
                face_crop = img[cy1:cy2, cx1:cx2]
                face_crop_resized = cv2.resize(face_crop, (FACE_THUMB_SIZE, FACE_THUMB_SIZE))

                all_records.append({
                    "asset_id": asset_id,
                    "bbox": json.dumps(bbox),
                    "confidence": float(face.det_score),
                    "crop": face_crop_resized,
                })
                all_embeddings.append(face.normed_embedding.copy())

        except Exception as e:
            print(f"  [错误] asset_id={asset_id}: {e}")

        processed += 1
        if processed % 100 == 0:
            print(f"  已处理 {processed}/{len(tasks)}")

    print(f"检测到 {len(all_records)} 张人脸，写入数据库...")

    if not all_records:
        print("没有检测到人脸")
        conn.close()
        return

    # 批量插入 faces 表
    now = datetime.now().isoformat()
    cursor = conn.cursor()
    inserted_ids: list[int] = []

    for rec in all_records:
        cursor.execute(
            "INSERT INTO faces (asset_id, bbox, confidence, created_at) VALUES (?, ?, ?, ?)",
            [rec["asset_id"], rec["bbox"], rec["confidence"], now],
        )
        inserted_ids.append(cursor.lastrowid)

    conn.commit()

    # 保存缩略图并更新 embedding_idx
    # 加载已有 embedding 数据
    emb_path = settings.vectors_dir / "face_embeddings.npy"
    ids_path = settings.vectors_dir / "face_ids.npy"

    if emb_path.exists() and ids_path.exists():
        existing_embs = np.load(str(emb_path))
        existing_ids = np.load(str(ids_path)).tolist()
    else:
        existing_embs = np.zeros((0, 512), dtype=np.float32)
        existing_ids = []

    new_embs = np.array(all_embeddings, dtype=np.float32)
    combined_embs = np.vstack([existing_embs, new_embs]) if len(existing_embs) > 0 else new_embs
    combined_ids = existing_ids + inserted_ids

    for i, face_id in enumerate(inserted_ids):
        emb_idx = len(existing_ids) + i
        conn.execute("UPDATE faces SET embedding_idx = ? WHERE face_id = ?", [emb_idx, face_id])

        # 保存缩略图
        thumb_path = face_thumbs_dir / f"{face_id}.webp"
        cv2.imwrite(str(thumb_path), all_records[i]["crop"], [cv2.IMWRITE_WEBP_QUALITY, 85])

    conn.commit()
    conn.close()

    # 保存 embedding 文件
    np.save(str(emb_path), combined_embs)
    np.save(str(ids_path), np.array(combined_ids, dtype=np.int64))

    print(f"完成！新增 {len(inserted_ids)} 张人脸，总计 {len(combined_ids)} 张")


if __name__ == "__main__":
    main()
