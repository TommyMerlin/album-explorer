"""生成 embedding 向量。

用法：
    python -m tasks.generate_embeddings [--model BAAI/bge-small-zh-v1.5] [--batch-size 256]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 embedding 向量")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="embedding 模型名")
    parser.add_argument("--batch-size", type=int, default=256, help="批次大小")
    args = parser.parse_args()

    print(f"加载模型: {args.model}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT asset_id, result_json FROM assets WHERE status = 'done' AND result_json IS NOT NULL ORDER BY asset_id"
    ).fetchall()
    conn.close()

    asset_ids = []
    texts = []
    for r in rows:
        result = json.loads(r["result_json"])
        embedding_text = result.get("embedding_text", "")
        if not embedding_text:
            # 退化：拼接 caption + tags
            parts = [result.get("caption_short", ""), result.get("scene", "")]
            parts.extend(result.get("tags", []))
            embedding_text = " ".join(parts)
        asset_ids.append(r["asset_id"])
        texts.append(embedding_text)

    print(f"共 {len(texts)} 条文本待编码，batch_size={args.batch_size}")

    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    output_dir = settings.vectors_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(str(output_dir / "embeddings.npy"), embeddings)
    np.save(str(output_dir / "asset_ids.npy"), np.array(asset_ids, dtype=np.int64))

    print(f"保存完成: embeddings.shape={embeddings.shape}")
    print(f"  文件: {output_dir / 'embeddings.npy'}")
    print(f"  文件: {output_dir / 'asset_ids.npy'}")


if __name__ == "__main__":
    main()
