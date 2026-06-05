from __future__ import annotations

from typing import Any


BRIEF_COLS = (
    "a.asset_id, a.rel_path, a.asset_type, a.source_format, a.taken_at, "
    "a.city_name, a.province_name, a.cluster_id, a.cluster_name, "
    "a.caption_short, a.scene, a.tags_text, a.gps_lat, a.gps_lng"
)


class QueryBuilder:
    """统一查询构造器，所有列表查询共用。"""

    def __init__(self) -> None:
        self.conditions: list[str] = ["a.status = 'done'"]
        self.params: list[Any] = []

    def filter_cluster(self, cluster_id: int | None) -> "QueryBuilder":
        if cluster_id is not None:
            self.conditions.append("a.cluster_id = ?")
            self.params.append(cluster_id)
        return self

    def filter_city(self, city: str | None) -> "QueryBuilder":
        if city:
            self.conditions.append("a.city_name = ?")
            self.params.append(city)
        return self

    def filter_province(self, province: str | None) -> "QueryBuilder":
        if province:
            self.conditions.append("a.province_name = ?")
            self.params.append(province)
        return self

    def filter_month(self, month: str | None) -> "QueryBuilder":
        if month:
            self.conditions.append("a.taken_at LIKE ?")
            self.params.append(f"{month}%")
        return self

    def filter_tag(self, tag: str | None) -> "QueryBuilder":
        if tag:
            self.conditions.append(
                "(a.tags_text = ? OR a.tags_text LIKE ? OR a.tags_text LIKE ? OR a.tags_text LIKE ?)"
            )
            self.params.extend([tag, f"{tag}|%", f"%|{tag}|%", f"%|{tag}"])
        return self

    def filter_date_range(self, date_from: str | None, date_to: str | None) -> "QueryBuilder":
        if date_from:
            self.conditions.append("a.taken_at >= ?")
            self.params.append(date_from)
        if date_to:
            self.conditions.append("a.taken_at <= ?")
            self.params.append(date_to + "T23:59:59")
        return self

    def filter_has_gps(self, has_gps: bool | None) -> "QueryBuilder":
        if has_gps is True:
            self.conditions.append("a.gps_lat IS NOT NULL AND a.gps_lng IS NOT NULL")
        elif has_gps is False:
            self.conditions.append("a.gps_lat IS NULL")
        return self

    def filter_favorite(self, is_favorite: bool | None) -> "QueryBuilder":
        if is_favorite is True:
            self.conditions.append("a.asset_id IN (SELECT asset_id FROM favorites)")
        return self

    def filter_media_type(self, media_type: str | None) -> "QueryBuilder":
        if media_type:
            self.conditions.append(
                "a.asset_id IN (SELECT asset_id FROM asset_media_types WHERE media_type = ?)"
            )
            self.params.append(media_type)
        return self

    _SEARCH_COLS = ("a.caption_short", "a.scene", "a.tags_text", "a.city_name")

    def filter_text(self, q: str | None) -> "QueryBuilder":
        if not q:
            return self
        terms = q.split()
        for term in terms:
            clause = " OR ".join(f"{col} LIKE ?" for col in self._SEARCH_COLS)
            self.conditions.append(f"({clause})")
            self.params.extend([f"%{term}%"] * len(self._SEARCH_COLS))
        return self

    def build_count(self) -> tuple[str, list[Any]]:
        where = " AND ".join(self.conditions)
        return f"SELECT COUNT(*) FROM assets a WHERE {where}", list(self.params)

    def build_select(
        self, sort_by: str = "taken_at", order: str = "desc",
        page: int = 1, page_size: int = 50,
    ) -> tuple[str, list[Any]]:
        offset = (page - 1) * page_size
        where = " AND ".join(self.conditions)
        sql = (
            f"SELECT {BRIEF_COLS} FROM assets a WHERE {where} "
            f"ORDER BY a.{sort_by} IS NULL, a.{sort_by} {order} "
            f"LIMIT ? OFFSET ?"
        )
        return sql, self.params + [page_size, offset]
