from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api/saved-searches", tags=["saved-searches"])


class SavedSearchCreate(BaseModel):
    name: str
    query_json: dict


class SavedSearchUpdate(BaseModel):
    name: str | None = None
    query_json: dict | None = None


class SavedSearchResponse(BaseModel):
    id: int
    name: str
    query_json: dict
    created_at: str
    updated_at: str


async def _ensure_table():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await db.commit()


@router.get("")
async def list_saved_searches() -> list[SavedSearchResponse]:
    await _ensure_table()
    db = await get_db()
    cursor = await db.execute("SELECT * FROM saved_searches ORDER BY updated_at DESC")
    rows = await cursor.fetchall()
    return [
        SavedSearchResponse(
            id=r["id"],
            name=r["name"],
            query_json=json.loads(r["query_json"]),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.post("", status_code=201)
async def create_saved_search(body: SavedSearchCreate) -> SavedSearchResponse:
    await _ensure_table()
    db = await get_db()
    now = datetime.now().isoformat()
    cursor = await db.execute(
        "INSERT INTO saved_searches (name, query_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
        [body.name, json.dumps(body.query_json, ensure_ascii=False), now, now],
    )
    await db.commit()
    return SavedSearchResponse(
        id=cursor.lastrowid,
        name=body.name,
        query_json=body.query_json,
        created_at=now,
        updated_at=now,
    )


@router.patch("/{search_id}")
async def update_saved_search(search_id: int, body: SavedSearchUpdate) -> SavedSearchResponse:
    await _ensure_table()
    db = await get_db()
    cursor = await db.execute("SELECT * FROM saved_searches WHERE id = ?", [search_id])
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="保存的搜索不存在")

    name = body.name if body.name is not None else row["name"]
    query_json = body.query_json if body.query_json is not None else json.loads(row["query_json"])
    now = datetime.now().isoformat()

    await db.execute(
        "UPDATE saved_searches SET name=?, query_json=?, updated_at=? WHERE id=?",
        [name, json.dumps(query_json, ensure_ascii=False), now, search_id],
    )
    await db.commit()
    return SavedSearchResponse(
        id=search_id,
        name=name,
        query_json=query_json,
        created_at=row["created_at"],
        updated_at=now,
    )


@router.delete("/{search_id}", status_code=204)
async def delete_saved_search(search_id: int):
    await _ensure_table()
    db = await get_db()
    cursor = await db.execute("SELECT id FROM saved_searches WHERE id = ?", [search_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="保存的搜索不存在")
    await db.execute("DELETE FROM saved_searches WHERE id = ?", [search_id])
    await db.commit()
