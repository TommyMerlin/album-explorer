"""对人脸 embedding 进行聚类，生成 persons 记录。

用法：
    python -m tasks.cluster_faces [--min-cluster-size 5] [--min-samples 3]
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
    parser = argparse.ArgumentParser(description="聚类人脸 embedding")
    parser.add_argument("--min-cluster-size", type=int, default=5)
    parser.add_argument("--min-samples", type=int, default=3)
    args = parser.parse_args()

    emb_path = settings.vectors_dir / "face_embeddings.npy"
    ids_path = settings.vectors_dir / "face_ids.npy"

    if not emb_path.exists() or not ids_path.exists():
        print("未找到人脸 embedding 文件，请先运行 detect_faces")
        return

    embeddings = np.load(str(emb_path))
    face_ids = np.load(str(ids_path)).tolist()
    print(f"加载 {len(face_ids)} 张人脸 embedding")

    if len(face_ids) < args.min_cluster_size:
        print(f"人脸数量不足 {args.min_cluster_size}，无法聚类")
        return

    import hdbscan

    print(f"HDBSCAN 聚类 (min_cluster_size={args.min_cluster_size}, min_samples={args.min_samples})...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embeddings)

    n_clusters = labels.max() + 1
    noise_count = (labels == -1).sum()
    print(f"聚类结果：{n_clusters} 个人物，{noise_count} 张未分类")

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            representative_face_id INTEGER,
            face_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # 保留已命名的人物信息用于恢复
    old_persons = {}
    try:
        rows = conn.execute(
            "SELECT person_id, name, representative_face_id FROM persons WHERE name != ''"
        ).fetchall()
        for r in rows:
            old_persons[r["representative_face_id"]] = r["name"]
    except Exception:
        pass

    # 清空旧数据
    conn.execute("DELETE FROM persons")
    conn.execute("UPDATE faces SET person_id = NULL")
    conn.commit()

    now = datetime.now().isoformat()

    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_indices = np.where(mask)[0]
        cluster_face_ids = [face_ids[i] for i in cluster_indices]
        cluster_embs = embeddings[mask]

        # 找到离聚类中心最近的人脸作为代表
        center = cluster_embs.mean(axis=0)
        center = center / np.linalg.norm(center)
        similarities = cluster_embs @ center
        best_idx = similarities.argmax()
        representative_face_id = cluster_face_ids[best_idx]

        # 尝试恢复旧名称
        name = old_persons.get(representative_face_id, "")
        if not name:
            for fid in cluster_face_ids:
                if fid in old_persons:
                    name = old_persons[fid]
                    break

        # 计算不同图片数
        cluster_asset_ids = set()
        for fid in cluster_face_ids:
            row = conn.execute("SELECT asset_id FROM faces WHERE face_id = ?", [fid]).fetchone()
            if row:
                cluster_asset_ids.add(row[0])

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO persons (name, representative_face_id, face_count, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [name, representative_face_id, len(cluster_asset_ids), now, now],
        )
        person_id = cursor.lastrowid

        # 更新 faces 表
        for fid in cluster_face_ids:
            conn.execute("UPDATE faces SET person_id = ? WHERE face_id = ?", [person_id, fid])

    conn.commit()
    conn.close()

    print(f"完成！创建 {n_clusters} 个人物，恢复 {sum(1 for v in old_persons.values() if v)} 个已命名人物")


if __name__ == "__main__":
    main()
