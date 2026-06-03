"""批量分类图片媒体类型（截图/长图/动图/普通）。

用法：
    python -m tasks.classify_media_type [--workers 4]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

KNOWN_PHONE_WIDTHS = {
    640, 750, 828, 1080, 1125, 1170, 1179, 1206, 1242, 1284, 1290, 1320, 1440,
}

PHONE_RATIOS_MIN = 9 / 16 - 0.02
PHONE_RATIOS_MAX = 9 / 21 - 0.02


def classify_one(asset_id: int, abs_path: str, source_format: str) -> tuple[int, str | None]:
    if source_format and source_format.lower() == "gif":
        return asset_id, "gif"

    path = Path(abs_path)
    if not path.exists():
        return asset_id, None

    try:
        from PIL import Image
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass

        with Image.open(path) as img:
            width, height = img.size

        if width == 0 or height == 0:
            return asset_id, "normal"

        ratio = min(width, height) / max(width, height)

        if height / width >= 3.0 or width / height >= 3.0:
            return asset_id, "long_image"

        portrait_w = min(width, height)
        if portrait_w in KNOWN_PHONE_WIDTHS and PHONE_RATIOS_MAX <= ratio <= PHONE_RATIOS_MIN:
            return asset_id, "screenshot"

        return asset_id, "normal"
    except Exception as e:
        print(f"  [错误] asset_id={asset_id}: {e}")
        return asset_id, None


def main() -> None:
    parser = argparse.ArgumentParser(description="批量分类图片媒体类型")
    parser.add_argument("--workers", type=int, default=4, help="并行进程数")
    args = parser.parse_args()

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_media_types (
            asset_id INTEGER PRIMARY KEY,
            media_type TEXT NOT NULL
        )
    """)
    conn.commit()

    rows = conn.execute(
        "SELECT a.asset_id, a.abs_path, a.source_format FROM assets a "
        "WHERE a.status = 'done' AND a.asset_id NOT IN (SELECT asset_id FROM asset_media_types)"
    ).fetchall()
    conn.close()

    tasks = [(r["asset_id"], r["abs_path"], r["source_format"]) for r in rows]
    print(f"待分类 {len(tasks)} 张，使用 {args.workers} 进程")

    if not tasks:
        print("无需处理")
        return

    results: list[tuple[int, str]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(classify_one, *t): t[0] for t in tasks}
        done_count = 0
        for future in as_completed(futures):
            asset_id, media_type = future.result()
            if media_type:
                results.append((asset_id, media_type))
            done_count += 1
            if done_count % 500 == 0:
                print(f"  已处理 {done_count}/{len(tasks)}")

    conn = sqlite3.connect(str(settings.db_path))
    batch_size = 500
    for i in range(0, len(results), batch_size):
        batch = results[i:i + batch_size]
        conn.executemany(
            "INSERT OR REPLACE INTO asset_media_types (asset_id, media_type) VALUES (?, ?)",
            batch,
        )
        conn.commit()
    conn.close()

    type_counts: dict[str, int] = {}
    for _, mt in results:
        type_counts[mt] = type_counts.get(mt, 0) + 1
    print(f"完成！共分类 {len(results)} 张：")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
