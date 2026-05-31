"""聚类增强：生成摘要、多封面、标签画像、相关聚类。

用法：
    python -m tasks.enrich_clusters
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def main() -> None:
    conn = sqlite3.connect(str(settings.db_source))
    conn.row_factory = sqlite3.Row

    # 确保扩展字段存在
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(clusters)").fetchall()}
    new_cols = {
        "summary_text": "TEXT",
        "cover_asset_ids": "TEXT",
        "top_scenes": "TEXT",
        "distinct_tags": "TEXT",
    }
    for col, col_type in new_cols.items():
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE clusters ADD COLUMN {col} {col_type}")
    conn.commit()

    clusters = conn.execute("SELECT cluster_id, cluster_name FROM clusters").fetchall()
    print(f"处理 {len(clusters)} 个聚类")

    # 加载 embeddings 用于计算聚类中心
    embeddings = np.load(str(settings.vectors_dir / "embeddings.npy"))
    asset_ids_arr = np.load(str(settings.vectors_dir / "asset_ids.npy"))
    id_to_idx = {int(aid): i for i, aid in enumerate(asset_ids_arr)}

    cluster_centers = {}

    for cluster in clusters:
        cid = cluster["cluster_id"]
        rows = conn.execute(
            "SELECT asset_id, result_json FROM assets WHERE cluster_id = ? AND status = 'done'",
            [cid],
        ).fetchall()

        if not rows:
            continue

        scene_counter: Counter[str] = Counter()
        tag_counter: Counter[str] = Counter()
        city_counter: Counter[str] = Counter()

        asset_ids_list = []
        for r in rows:
            asset_ids_list.append(r["asset_id"])
            result = json.loads(r["result_json"]) if r["result_json"] else {}
            scene = result.get("scene", "")
            if scene:
                scene_counter[scene] += 1
            tag_counter.update(result.get("tags", [])[:8])

        # 选 4 张封面：按与聚类中心的距离选最近的
        cluster_embs = []
        valid_ids = []
        for aid in asset_ids_list:
            if aid in id_to_idx:
                cluster_embs.append(embeddings[id_to_idx[aid]])
                valid_ids.append(aid)

        cover_ids = valid_ids[:4]
        if cluster_embs:
            cluster_embs_np = np.array(cluster_embs)
            center = cluster_embs_np.mean(axis=0)
            cluster_centers[cid] = center
            dists = np.linalg.norm(cluster_embs_np - center, axis=1)
            closest_indices = np.argsort(dists)[:4]
            cover_ids = [valid_ids[i] for i in closest_indices]

        # 高区分度标签：频率高但不是全局高频的
        top_scenes = [s for s, _ in scene_counter.most_common(5)]
        distinct_tags = [t for t, _ in tag_counter.most_common(15)][:10]

        # 摘要句
        top_scene = top_scenes[0] if top_scenes else cluster["cluster_name"]
        tag_str = "、".join(distinct_tags[:4])
        summary = f"{top_scene}，包含{len(rows)}张图片，主要标签：{tag_str}"

        conn.execute(
            "UPDATE clusters SET summary_text=?, cover_asset_ids=?, top_scenes=?, distinct_tags=? "
            "WHERE cluster_id=?",
            [
                summary,
                json.dumps(cover_ids),
                json.dumps(top_scenes, ensure_ascii=False),
                json.dumps(distinct_tags, ensure_ascii=False),
                cid,
            ],
        )

    conn.commit()
    conn.close()
    print("聚类增强完成")


if __name__ == "__main__":
    main()
