from __future__ import annotations

from pathlib import Path

from app.config import settings


def resolve_asset_path(abs_path: str | None, rel_path: str | None) -> Path:
    """Resolve an asset path inside or outside containers.

    The source database may store host absolute paths such as `/mnt/d/...`.
    When the app runs in Docker, those paths do not exist in the container,
    but the asset tree is mounted under `settings.image_root` and `rel_path`
    remains valid. Prefer a real existing path and fall back to the mounted tree.
    """
    candidates: list[Path] = []

    if abs_path:
        candidates.append(Path(abs_path))

    if rel_path:
        candidates.append(settings.image_root / rel_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[-1] if candidates else settings.image_root
