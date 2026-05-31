"""HDBSCAN 聚类并写回数据库。

用法：
    python -m tasks.run_clustering [--min-cluster-size 30]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def name_cluster(asset_ids: list[int], conn: sqlite3.Connection) -> str:
    """根据聚类内图片的 tags 和 scene 自动命名。"""
    scene_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()

    placeholders = ",".join("?" * len(asset_ids))
    rows = conn.execute(
        f"SELECT result_json FROM assets WHERE asset_id IN ({placeholders})",
        asset_ids,
    ).fetchall()

    for r in rows:
        result = json.loads(r["result_json"])
        scene = result.get("scene", "")
        if scene:
            scene_counter[scene] += 1
        tag_counter.update(result.get("tags", [])[:5])

    top_scene = scene_counter.most_common(1)[0][0] if scene_counter else "未知"
    # 补充标签（排除与 scene 重复的）
    extra_tags = [t for t, _ in tag_counter.most_common(5) if t != top_scene][:2]

    if extra_tags:
        return f"{top_scene}（{'·'.join(extra_tags)}）"
    return top_scene


def main() -> None:
    parser = argparse.ArgumentParser(description="HDBSCAN 聚类")
    parser.add_argument("--min-cluster-size", type=int, default=30, help="最小聚类大小")
    parser.add_argument("--min-samples", type=int, default=10, help="核心点邻域")
    args = parser.parse_args()

    embeddings = np.load(str(settings.vectors_dir / "embeddings.npy"))
    asset_ids = np.load(str(settings.vectors_dir / "asset_ids.npy"))

    print(f"加载 embeddings: {embeddings.shape}")
    print(f"参数: min_cluster_size={args.min_cluster_size}, min_samples={args.min_samples}")

    import hdbscan
    # 向量已 L2 归一化，欧氏距离等价于余弦距离
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = (labels == -1).sum()
    print(f"聚类结果: {n_clusters} 个簇, {noise_count} 个噪声点")

    # 写回数据库
    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    # 确保列存在
    try:
        conn.execute("ALTER TABLE assets ADD COLUMN cluster_id INTEGER")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE assets ADD COLUMN cluster_name TEXT")
    except Exception:
        pass
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_cluster_id ON assets(cluster_id)")
    except Exception:
        pass

    # 创建 clusters 表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            cluster_id INTEGER PRIMARY KEY,
            cluster_name TEXT NOT NULL,
            representative_asset_id INTEGER,
            asset_count INTEGER,
            top_tags TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("DELETE FROM clusters")

    # 按聚类分组
    cluster_groups: dict[int, list[int]] = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue
        cluster_groups.setdefault(int(label), []).append(int(asset_ids[i]))

    # 为每个聚类命名并写入
    for cluster_id, members in cluster_groups.items():
        cluster_name = name_cluster(members, conn)
        representative_id = members[0]

        # 获取 top tags
        tag_counter: Counter[str] = Counter()
        placeholders = ",".join("?" * min(len(members), 50))
        sample = members[:50]
        rows = conn.execute(
            f"SELECT result_json FROM assets WHERE asset_id IN ({placeholders})", sample
        ).fetchall()
        for r in rows:
            result = json.loads(r["result_json"])
            tag_counter.update(result.get("tags", [])[:5])
        top_tags = [t for t, _ in tag_counter.most_common(10)]

        conn.execute(
            "INSERT INTO clusters (cluster_id, cluster_name, representative_asset_id, asset_count, top_tags) VALUES (?, ?, ?, ?, ?)",
            [cluster_id, cluster_name, representative_id, len(members), json.dumps(top_tags, ensure_ascii=False)],
        )

        # 更新 assets 表
        placeholders = ",".join("?" * len(members))
        conn.execute(
            f"UPDATE assets SET cluster_id = ?, cluster_name = ? WHERE asset_id IN ({placeholders})",
            [cluster_id, cluster_name] + members,
        )

    # 噪声点标记为 cluster_id = -1
    noise_ids = [int(asset_ids[i]) for i, l in enumerate(labels) if l == -1]
    if noise_ids:
        batch_size = 500
        for i in range(0, len(noise_ids), batch_size):
            batch = noise_ids[i:i + batch_size]
            placeholders = ",".join("?" * len(batch))
            conn.execute(
                f"UPDATE assets SET cluster_id = -1, cluster_name = '未分类' WHERE asset_id IN ({placeholders})",
                batch,
            )

    conn.commit()
    conn.close()
    print("聚类结果已写入数据库。")


if __name__ == "__main__":
    main()
