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
    if not await cursor.fetchone():
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

    await _ensure_fts_triggers(db)
    await db.commit()


async def _ensure_fts_triggers(db: aiosqlite.Connection) -> None:
    """保持 assets_fts 与 assets 表同步的触发器。"""
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS assets_fts_insert
        AFTER INSERT ON assets WHEN NEW.status = 'done'
        BEGIN
            INSERT INTO assets_fts(rowid, caption_short, scene, tags_text, city_name)
            VALUES(NEW.asset_id, COALESCE(NEW.caption_short,''),
                   COALESCE(NEW.scene,''), COALESCE(NEW.tags_text,''),
                   COALESCE(NEW.city_name,''));
        END
    """)
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS assets_fts_update
        AFTER UPDATE ON assets WHEN NEW.status = 'done'
        BEGIN
            INSERT INTO assets_fts(assets_fts, rowid, caption_short, scene, tags_text, city_name)
            VALUES('delete', OLD.asset_id, COALESCE(OLD.caption_short,''),
                   COALESCE(OLD.scene,''), COALESCE(OLD.tags_text,''),
                   COALESCE(OLD.city_name,''));
            INSERT INTO assets_fts(rowid, caption_short, scene, tags_text, city_name)
            VALUES(NEW.asset_id, COALESCE(NEW.caption_short,''),
                   COALESCE(NEW.scene,''), COALESCE(NEW.tags_text,''),
                   COALESCE(NEW.city_name,''));
        END
    """)
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS assets_fts_delete
        AFTER UPDATE ON assets WHEN OLD.status = 'done' AND NEW.status != 'done'
        BEGIN
            INSERT INTO assets_fts(assets_fts, rowid, caption_short, scene, tags_text, city_name)
            VALUES('delete', OLD.asset_id, COALESCE(OLD.caption_short,''),
                   COALESCE(OLD.scene,''), COALESCE(OLD.tags_text,''),
                   COALESCE(OLD.city_name,''));
        END
    """)


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
