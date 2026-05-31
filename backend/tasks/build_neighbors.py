"""预计算每张图片的 Top-K 近邻，写入 asset_neighbors 表。

用法：
    python -m tasks.build_neighbors [--top-k 20]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="预计算 Top-K 近邻")
    parser.add_argument("--top-k", type=int, default=20, help="每张图保留的邻居数")
    parser.add_argument("--batch-size", type=int, default=500, help="批量计算大小")
    args = parser.parse_args()

    embeddings = np.load(str(settings.vectors_dir / "embeddings.npy"))
    asset_ids = np.load(str(settings.vectors_dir / "asset_ids.npy"))

    print(f"加载 embeddings: {embeddings.shape}, top_k={args.top_k}")

    # L2 归一化后用点积计算余弦相似度
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embeddings_norm = embeddings / norms

    conn = sqlite3.connect(str(settings.db_source))
    conn.row_factory = sqlite3.Row

    conn.execute("DROP TABLE IF EXISTS asset_neighbors")
    conn.execute("""
        CREATE TABLE asset_neighbors (
            asset_id INTEGER NOT NULL,
            neighbor_id INTEGER NOT NULL,
            score REAL NOT NULL,
            rank INTEGER NOT NULL,
            PRIMARY KEY (asset_id, rank)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_neighbors_asset ON asset_neighbors(asset_id)")

    n = len(asset_ids)
    total_inserted = 0

    for start in range(0, n, args.batch_size):
        end = min(start + args.batch_size, n)
        batch = embeddings_norm[start:end]

        # 计算 batch 与全部的相似度
        sims = batch @ embeddings_norm.T  # (batch_size, n)

        rows = []
        for i in range(end - start):
            global_idx = start + i
            sim_row = sims[i]
            # 排除自身
            sim_row[global_idx] = -1
            top_indices = np.argpartition(sim_row, -args.top_k)[-args.top_k:]
            top_indices = top_indices[np.argsort(sim_row[top_indices])[::-1]]

            aid = int(asset_ids[global_idx])
            for rank, idx in enumerate(top_indices, 1):
                rows.append((aid, int(asset_ids[idx]), float(sim_row[idx]), rank))

        conn.executemany(
            "INSERT INTO asset_neighbors (asset_id, neighbor_id, score, rank) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        total_inserted += len(rows)
        print(f"  进度: {end}/{n} ({total_inserted} 条记录)")

    conn.close()
    print(f"完成！共写入 {total_inserted} 条邻居记录")


if __name__ == "__main__":
    main()
