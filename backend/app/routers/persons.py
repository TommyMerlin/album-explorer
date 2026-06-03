from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.models import PaginatedResponse
from app.routers.assets import _row_to_brief
from app.services.query_builder import BRIEF_COLS

router = APIRouter(prefix="/api/persons", tags=["persons"])


class PersonUpdate(BaseModel):
    name: str | None = None
    representative_face_id: int | None = None


class MergeRequest(BaseModel):
    target_id: int
    source_ids: list[int]


class FaceIdsRequest(BaseModel):
    face_ids: list[int]


async def ensure_persons_tables():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            face_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            bbox TEXT NOT NULL,
            confidence REAL NOT NULL,
            embedding_idx INTEGER,
            person_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_faces_asset ON faces(asset_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_faces_person ON faces(person_id)")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            representative_face_id INTEGER,
            face_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await db.commit()


@router.get("")
async def list_persons():
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM persons ORDER BY face_count DESC"
    )
    rows = await cursor.fetchall()
    return [
        {
            "person_id": r["person_id"],
            "name": r["name"],
            "representative_face_id": r["representative_face_id"],
            "face_count": r["face_count"],
        }
        for r in rows
    ]


@router.get("/uncategorized")
async def list_uncategorized_faces(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM faces WHERE person_id IS NULL"
    )
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    cursor = await db.execute(
        "SELECT face_id, asset_id, bbox, person_id FROM faces "
        "WHERE person_id IS NULL ORDER BY face_id DESC LIMIT ? OFFSET ?",
        [page_size, offset],
    )
    items = [
        {"face_id": r["face_id"], "asset_id": r["asset_id"], "bbox": r["bbox"], "person_id": None}
        for r in await cursor.fetchall()
    ]
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=total_pages,
    )


@router.get("/{person_id}")
async def get_person_assets(
    person_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM persons WHERE person_id = ?", [person_id])
    person = await cursor.fetchone()
    if person is None:
        raise HTTPException(status_code=404, detail="人物不存在")

    cursor = await db.execute(
        "SELECT COUNT(DISTINCT f.asset_id) FROM faces f "
        "JOIN assets a ON a.asset_id = f.asset_id "
        "WHERE f.person_id = ? AND a.status = 'done'",
        [person_id],
    )
    total = (await cursor.fetchone())[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    cols = BRIEF_COLS.replace("a.", "assets.")
    cursor = await db.execute(
        f"SELECT DISTINCT {cols} FROM faces f "
        f"JOIN assets ON assets.asset_id = f.asset_id "
        f"WHERE f.person_id = ? AND assets.status = 'done' "
        f"ORDER BY assets.taken_at DESC LIMIT ? OFFSET ?",
        [person_id, page_size, offset],
    )
    items = [_row_to_brief(r) for r in await cursor.fetchall()]

    return {
        "person_id": person["person_id"],
        "name": person["name"],
        "representative_face_id": person["representative_face_id"],
        "face_count": person["face_count"],
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{person_id}/faces")
async def get_person_faces(person_id: int):
    db = await get_db()
    cursor = await db.execute(
        "SELECT face_id, asset_id, bbox, person_id FROM faces WHERE person_id = ? ORDER BY face_id",
        [person_id],
    )
    rows = await cursor.fetchall()
    return [
        {"face_id": r["face_id"], "asset_id": r["asset_id"], "bbox": r["bbox"], "person_id": r["person_id"]}
        for r in rows
    ]


@router.patch("/{person_id}")
async def update_person(person_id: int, body: PersonUpdate):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM persons WHERE person_id = ?", [person_id])
    person = await cursor.fetchone()
    if person is None:
        raise HTTPException(status_code=404, detail="人物不存在")

    name = body.name if body.name is not None else person["name"]
    rep = body.representative_face_id if body.representative_face_id is not None else person["representative_face_id"]
    now = datetime.now().isoformat()

    await db.execute(
        "UPDATE persons SET name = ?, representative_face_id = ?, updated_at = ? WHERE person_id = ?",
        [name, rep, now, person_id],
    )
    await db.commit()
    return {"person_id": person_id, "name": name, "representative_face_id": rep}


@router.post("/merge")
async def merge_persons(body: MergeRequest):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM persons WHERE person_id = ?", [body.target_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="目标人物不存在")

    for sid in body.source_ids:
        if sid == body.target_id:
            continue
        await db.execute(
            "UPDATE faces SET person_id = ? WHERE person_id = ?",
            [body.target_id, sid],
        )
        await db.execute("DELETE FROM persons WHERE person_id = ?", [sid])

    # 更新 face_count
    cursor = await db.execute(
        "SELECT COUNT(*) FROM faces WHERE person_id = ?", [body.target_id]
    )
    count = (await cursor.fetchone())[0]
    now = datetime.now().isoformat()
    await db.execute(
        "UPDATE persons SET face_count = ?, updated_at = ? WHERE person_id = ?",
        [count, now, body.target_id],
    )
    await db.commit()
    return {"person_id": body.target_id, "face_count": count}


@router.post("/{person_id}/remove-faces")
async def remove_faces_from_person(person_id: int, body: FaceIdsRequest):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM persons WHERE person_id = ?", [person_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="人物不存在")

    for fid in body.face_ids:
        await db.execute(
            "UPDATE faces SET person_id = NULL WHERE face_id = ? AND person_id = ?",
            [fid, person_id],
        )

    cursor = await db.execute(
        "SELECT COUNT(*) FROM faces WHERE person_id = ?", [person_id]
    )
    count = (await cursor.fetchone())[0]
    now = datetime.now().isoformat()
    await db.execute(
        "UPDATE persons SET face_count = ?, updated_at = ? WHERE person_id = ?",
        [count, now, person_id],
    )
    await db.commit()
    return {"person_id": person_id, "face_count": count}


@router.post("/{person_id}/add-faces")
async def add_faces_to_person(person_id: int, body: FaceIdsRequest):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM persons WHERE person_id = ?", [person_id])
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="人物不存在")

    for fid in body.face_ids:
        await db.execute(
            "UPDATE faces SET person_id = ? WHERE face_id = ?",
            [person_id, fid],
        )

    cursor = await db.execute(
        "SELECT COUNT(*) FROM faces WHERE person_id = ?", [person_id]
    )
    count = (await cursor.fetchone())[0]
    now = datetime.now().isoformat()
    await db.execute(
        "UPDATE persons SET face_count = ?, updated_at = ? WHERE person_id = ?",
        [count, now, person_id],
    )
    await db.commit()
    return {"person_id": person_id, "face_count": count}
