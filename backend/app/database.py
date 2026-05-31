from __future__ import annotations

import aiosqlite

from app.config import settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(str(settings.db_path), uri=False)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await _ensure_indexes(_db)
        await _ensure_fts(_db)
    return _db


async def _ensure_indexes(db: aiosqlite.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_assets_status_taken ON assets(status, taken_at)",
        "CREATE INDEX IF NOT EXISTS idx_assets_status_city ON assets(status, city_name)",
        "CREATE INDEX IF NOT EXISTS idx_assets_status_cluster ON assets(status, cluster_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_gps ON assets(gps_lat, gps_lng)",
    ]
    for sql in indexes:
        await db.execute(sql)
    await db.commit()


async def _ensure_fts(db: aiosqlite.Connection) -> None:
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='assets_fts'"
    )
    if await cursor.fetchone():
        return
    await db.execute(
        "CREATE VIRTUAL TABLE assets_fts USING fts5("
        "caption_short, scene, tags_text, city_name, "
        "content='assets', content_rowid='asset_id')"
    )
    await db.execute(
        "INSERT INTO assets_fts(rowid, caption_short, scene, tags_text, city_name) "
        "SELECT asset_id, COALESCE(caption_short,''), COALESCE(scene,''), "
        "COALESCE(tags_text,''), COALESCE(city_name,'') FROM assets WHERE status='done'"
    )
    await db.commit()


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
