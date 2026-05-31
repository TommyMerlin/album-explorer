from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.services.query_builder import BRIEF_COLS
from app.routers.assets import _row_to_brief

router = APIRouter(prefix="/api/albums", tags=["albums"])


class AlbumCreate(BaseModel):
    name: str
    description: str = ""


class AlbumUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    cover_asset_id: int | None = None


class AlbumAssetAdd(BaseModel):
    asset_id: int


async def _ensure_tables():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            cover_asset_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS album_assets (
            album_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            PRIMARY KEY (album_id, asset_id)
        )
    """)
    await db.commit()


@router.get("")
async def list_albums():
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute("""
        SELECT a.*, COUNT(aa.asset_id) AS asset_count
        FROM albums a
        LEFT JOIN album_assets aa ON aa.album_id = a.id
        GROUP BY a.id
        ORDER BY a.updated_at DESC
    """)
    rows = await cursor.fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "cover_asset_id": r["cover_asset_id"],
            "asset_count": r["asset_count"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@router.post("", status_code=201)
async def create_album(body: AlbumCreate):
    await _ensure_tables()
    db = await get_db()
    now = datetime.now().isoformat()
    cursor = await db.execute(
        "INSERT INTO albums (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
        [body.name, body.description, now, now],
    )
    await db.commit()
    return {"id": cursor.lastrowid, "name": body.name, "description": body.description, "created_at": now}


@router.get("/{album_id}")
async def get_album(album_id: int):
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute("SELECT * FROM albums WHERE id = ?", [album_id])
    album = await cursor.fetchone()
    if album is None:
        raise HTTPException(status_code=404, detail="相册不存在")

    cols = BRIEF_COLS.replace("a.", "assets.")
    cursor = await db.execute(
        f"SELECT {cols} FROM album_assets aa "
        f"JOIN assets ON assets.asset_id = aa.asset_id "
        f"WHERE aa.album_id = ? AND assets.status = 'done' "
        f"ORDER BY aa.sort_order, aa.added_at DESC",
        [album_id],
    )
    items = [_row_to_brief(r) for r in await cursor.fetchall()]

    return {
        "id": album["id"],
        "name": album["name"],
        "description": album["description"],
        "cover_asset_id": album["cover_asset_id"],
        "asset_count": len(items),
        "items": items,
        "created_at": album["created_at"],
        "updated_at": album["updated_at"],
    }


@router.patch("/{album_id}")
async def update_album(album_id: int, body: AlbumUpdate):
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute("SELECT * FROM albums WHERE id = ?", [album_id])
    album = await cursor.fetchone()
    if album is None:
        raise HTTPException(status_code=404, detail="相册不存在")

    name = body.name if body.name is not None else album["name"]
    description = body.description if body.description is not None else album["description"]
    cover = body.cover_asset_id if body.cover_asset_id is not None else album["cover_asset_id"]
    now = datetime.now().isoformat()

    await db.execute(
        "UPDATE albums SET name=?, description=?, cover_asset_id=?, updated_at=? WHERE id=?",
        [name, description, cover, now, album_id],
    )
    await db.commit()
    return {"id": album_id, "name": name, "description": description, "cover_asset_id": cover}


@router.delete("/{album_id}", status_code=204)
async def delete_album(album_id: int):
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute("SELECT id FROM albums WHERE id = ?", [album_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="相册不存在")
    await db.execute("DELETE FROM album_assets WHERE album_id = ?", [album_id])
    await db.execute("DELETE FROM albums WHERE id = ?", [album_id])
    await db.commit()


@router.post("/{album_id}/assets", status_code=201)
async def add_asset_to_album(album_id: int, body: AlbumAssetAdd):
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute("SELECT id FROM albums WHERE id = ?", [album_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="相册不存在")

    now = datetime.now().isoformat()
    try:
        await db.execute(
            "INSERT INTO album_assets (album_id, asset_id, added_at) VALUES (?, ?, ?)",
            [album_id, body.asset_id, now],
        )
    except Exception:
        raise HTTPException(status_code=409, detail="图片已在相册中")

    # 如果相册没有封面，自动设置
    cursor = await db.execute("SELECT cover_asset_id FROM albums WHERE id = ?", [album_id])
    row = await cursor.fetchone()
    if row and row["cover_asset_id"] is None:
        await db.execute("UPDATE albums SET cover_asset_id=?, updated_at=? WHERE id=?", [body.asset_id, now, album_id])

    await db.commit()
    return {"album_id": album_id, "asset_id": body.asset_id}


@router.delete("/{album_id}/assets/{asset_id}", status_code=204)
async def remove_asset_from_album(album_id: int, asset_id: int):
    await _ensure_tables()
    db = await get_db()
    cursor = await db.execute(
        "SELECT rowid FROM album_assets WHERE album_id = ? AND asset_id = ?",
        [album_id, asset_id],
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="图片不在相册中")
    await db.execute(
        "DELETE FROM album_assets WHERE album_id = ? AND asset_id = ?",
        [album_id, asset_id],
    )
    await db.commit()

