"""批量生成缩略图。

用法：
    python -m tasks.generate_thumbnails [--workers 4]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.services.thumbnail import ensure_thumbnail


def process_one(asset_id: int, abs_path: str, source_format: str) -> tuple[int, bool]:
    """生成单张图片的 sm + md 缩略图。"""
    path = Path(abs_path)
    if not path.exists():
        return asset_id, False

    try:
        sm_path = settings.thumbnail_dir / "sm" / f"{asset_id}.webp"
        md_path = settings.thumbnail_dir / "md" / f"{asset_id}.webp"
        ensure_thumbnail(path, source_format, sm_path, settings.thumb_sm_size, settings.thumb_quality_sm)
        ensure_thumbnail(path, source_format, md_path, settings.thumb_md_size, settings.thumb_quality_md)
        return asset_id, True
    except Exception as e:
        print(f"  [错误] asset_id={asset_id}: {e}")
        return asset_id, False


def main() -> None:
    parser = argparse.ArgumentParser(description="批量生成缩略图")
    parser.add_argument("--workers", type=int, default=4, help="并行进程数")
    args = parser.parse_args()

    settings.thumbnail_dir.joinpath("sm").mkdir(parents=True, exist_ok=True)
    settings.thumbnail_dir.joinpath("md").mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT asset_id, abs_path, source_format FROM assets WHERE status = 'done'"
    ).fetchall()
    conn.close()

    # 过滤已生成的
    tasks = []
    for r in rows:
        sm_path = settings.thumbnail_dir / "sm" / f"{r['asset_id']}.webp"
        if not sm_path.exists():
            tasks.append((r["asset_id"], r["abs_path"], r["source_format"]))

    print(f"总计 {len(rows)} 张，待生成 {len(tasks)} 张，使用 {args.workers} 进程")

    if not tasks:
        print("全部缩略图已存在，无需生成。")
        return

    success = 0
    failed = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_one, *t): t[0] for t in tasks}
        for i, future in enumerate(as_completed(futures), 1):
            asset_id, ok = future.result()
            if ok:
                success += 1
            else:
                failed += 1
            if i % 100 == 0:
                print(f"  进度: {i}/{len(tasks)} (成功={success}, 失败={failed})")

    print(f"完成！成功={success}, 失败={failed}")


if __name__ == "__main__":
    main()
