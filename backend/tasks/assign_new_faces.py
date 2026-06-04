"""将未分类人脸增量分配到已有人物。

用法：
    python -m tasks.assign_new_faces [--threshold 0.5]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="将新人脸分配到已有人物")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="cosine similarity 阈值，高于此值归入已有人物")
    args = parser.parse_args()

    emb_path = settings.vectors_dir / "face_embeddings.npy"
    ids_path = settings.vectors_dir / "face_ids.npy"

    if not emb_path.exists() or not ids_path.exists():
        print("未找到人脸 embedding 文件，请先运行 detect_faces")
        return

    embeddings = np.load(str(emb_path))
    face_ids = np.load(str(ids_path)).tolist()
    face_id_to_idx = {fid: i for i, fid in enumerate(face_ids)}

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    # 找出未分类的人脸
    unassigned = conn.execute(
        "SELECT face_id FROM faces WHERE person_id IS NULL"
    ).fetchall()
    unassigned_ids = [r["face_id"] for r in unassigned]

    if not unassigned_ids:
        print("没有未分类的人脸")
        conn.close()
        return

    print(f"未分类人脸: {len(unassigned_ids)} 张")

    # 计算每个已有人物的 embedding 中心
    persons = conn.execute(
        "SELECT person_id FROM persons WHERE hidden = 0"
    ).fetchall()

    if not persons:
        print("没有已有人物，请先运行 cluster_faces")
        conn.close()
        return

    person_centers = {}
    for p in persons:
        pid = p["person_id"]
        face_rows = conn.execute(
            "SELECT face_id FROM faces WHERE person_id = ?", [pid]
        ).fetchall()
        indices = [face_id_to_idx[r["face_id"]] for r in face_rows if r["face_id"] in face_id_to_idx]
        if not indices:
            continue
        center = embeddings[indices].mean(axis=0)
        center = center / np.linalg.norm(center)
        person_centers[pid] = center

    if not person_centers:
        print("没有有效的人物中心")
        conn.close()
        return

    print(f"已有人物: {len(person_centers)} 个")

    # 构建中心矩阵用于批量计算
    pids = list(person_centers.keys())
    center_matrix = np.array([person_centers[pid] for pid in pids], dtype=np.float32)

    assigned = 0
    now = datetime.now().isoformat()

    for fid in unassigned_ids:
        if fid not in face_id_to_idx:
            continue
        emb = embeddings[face_id_to_idx[fid]]
        emb_norm = emb / np.linalg.norm(emb)

        similarities = center_matrix @ emb_norm
        best_idx = similarities.argmax()
        best_sim = similarities[best_idx]

        if best_sim >= args.threshold:
            best_pid = pids[best_idx]
            conn.execute(
                "UPDATE faces SET person_id = ? WHERE face_id = ?",
                [best_pid, fid],
            )
            assigned += 1

    # 更新 face_count
    for pid in pids:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT asset_id) FROM faces WHERE person_id = ?", [pid]
        )
        count = cursor.fetchone()[0]
        conn.execute(
            "UPDATE persons SET face_count = ?, updated_at = ? WHERE person_id = ?",
            [count, now, pid],
        )

    conn.commit()
    conn.close()
    print(f"完成！分配 {assigned} 张人脸到已有人物，{len(unassigned_ids) - assigned} 张仍未分类")


if __name__ == "__main__":
    main()
