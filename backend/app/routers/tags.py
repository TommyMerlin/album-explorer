from __future__ import annotations

import json
import logging
from collections import Counter

from fastapi import APIRouter, Query

from app.database import get_db
from app.models import TagEdge, TagGraph, TagNode

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("")
async def get_tags(top_n: int = Query(100, ge=1, le=500)) -> list[TagNode]:
    """获取标签频率统计。"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT result_json FROM assets WHERE status = 'done' AND result_json IS NOT NULL"
    )
    rows = await cursor.fetchall()

    tag_counter: Counter[str] = Counter()
    for r in rows:
        result = json.loads(r["result_json"])
        tags = result.get("tags", [])
        tag_counter.update(tags)

    return [TagNode(tag=t, count=c) for t, c in tag_counter.most_common(top_n)]


@router.get("/graph")
async def get_tag_graph(
    min_weight: int = Query(10, ge=1),
    top_nodes: int = Query(80, ge=10, le=200),
) -> TagGraph:
    """获取标签共现图数据。优先从 tag_cooccurrence 表读取，否则实时计算。"""
    db = await get_db()

    # 尝试从预计算表读取
    try:
        cursor = await db.execute(
            "SELECT tag_a, tag_b, weight FROM tag_cooccurrence WHERE weight >= ? ORDER BY weight DESC LIMIT 500",
            [min_weight],
        )
        rows = await cursor.fetchall()
        if rows:
            node_set: set[str] = set()
            edges = []
            for r in rows:
                node_set.add(r["tag_a"])
                node_set.add(r["tag_b"])
                edges.append(TagEdge(source=r["tag_a"], target=r["tag_b"], weight=r["weight"]))

            # 获取节点计数
            tag_counts = await _get_tag_counts(db)
            nodes = [TagNode(tag=t, count=tag_counts.get(t, 0)) for t in node_set]
            return TagGraph(nodes=nodes, edges=edges)
    except Exception:
        logging.getLogger(__name__).warning("tag_graph 表查询失败，退化为实时计算", exc_info=True)

    # 实时计算（首次使用或表不存在时）
    cursor = await db.execute(
        "SELECT result_json FROM assets WHERE status = 'done' AND result_json IS NOT NULL"
    )
    rows = await cursor.fetchall()

    tag_counter: Counter[str] = Counter()
    cooccurrence: Counter[tuple[str, str]] = Counter()

    for r in rows:
        result = json.loads(r["result_json"])
        tags = result.get("tags", [])
        tag_counter.update(tags)
        # 计算共现（取 top tags 避免组合爆炸）
        top_tags = tags[:8]
        for i in range(len(top_tags)):
            for j in range(i + 1, len(top_tags)):
                pair = tuple(sorted([top_tags[i], top_tags[j]]))
                cooccurrence[pair] += 1

    # 取 top_nodes 个高频标签
    top_tag_set = {t for t, _ in tag_counter.most_common(top_nodes)}

    edges = []
    for (a, b), w in cooccurrence.most_common(500):
        if w >= min_weight and a in top_tag_set and b in top_tag_set:
            edges.append(TagEdge(source=a, target=b, weight=w))

    node_set_final = set()
    for e in edges:
        node_set_final.add(e.source)
        node_set_final.add(e.target)

    nodes = [TagNode(tag=t, count=tag_counter[t]) for t in node_set_final]
    return TagGraph(nodes=nodes, edges=edges)


async def _get_tag_counts(db) -> dict[str, int]:
    cursor = await db.execute(
        "SELECT result_json FROM assets WHERE status = 'done' AND result_json IS NOT NULL"
    )
    rows = await cursor.fetchall()
    counter: Counter[str] = Counter()
    for r in rows:
        result = json.loads(r["result_json"])
        counter.update(result.get("tags", []))
    return dict(counter)
