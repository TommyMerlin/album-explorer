"""构建标签共现数据并写入数据库。

用法：
    python -m tasks.build_tag_graph [--min-weight 5]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="构建标签共现图")
    parser.add_argument("--min-weight", type=int, default=5, help="最小共现次数")
    args = parser.parse_args()

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    # 创建表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tag_cooccurrence (
            tag_a TEXT NOT NULL,
            tag_b TEXT NOT NULL,
            weight INTEGER NOT NULL,
            PRIMARY KEY (tag_a, tag_b)
        )
    """)
    conn.execute("DELETE FROM tag_cooccurrence")

    rows = conn.execute(
        "SELECT result_json FROM assets WHERE status = 'done' AND result_json IS NOT NULL"
    ).fetchall()

    print(f"处理 {len(rows)} 张图片的标签共现...")

    cooccurrence: Counter[tuple[str, str]] = Counter()
    tag_counter: Counter[str] = Counter()

    for r in rows:
        result = json.loads(r["result_json"])
        tags = result.get("tags", [])[:10]
        tag_counter.update(tags)
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                pair = tuple(sorted([tags[i], tags[j]]))
                cooccurrence[pair] += 1

    # 只保留高频标签之间的共现
    top_tags = {t for t, _ in tag_counter.most_common(200)}
    inserts = []
    for (a, b), w in cooccurrence.items():
        if w >= args.min_weight and a in top_tags and b in top_tags:
            inserts.append((a, b, w))

    conn.executemany(
        "INSERT INTO tag_cooccurrence (tag_a, tag_b, weight) VALUES (?, ?, ?)",
        inserts,
    )
    conn.commit()
    conn.close()

    print(f"完成！写入 {len(inserts)} 条共现关系（min_weight={args.min_weight}）。")


if __name__ == "__main__":
    main()
