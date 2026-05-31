from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """应用配置，所有路径通过环境变量覆盖，方便后期桌面打包。"""

    def __init__(self) -> None:
        base = Path(os.environ.get("ALBUM_EXPLORER_BASE", "/mnt/d/数据备份"))

        self.db_path = Path(
            os.environ.get(
                "ALBUM_EXPLORER_DB",
                str(base / ".album-assetizer" / "state" / "album_assetizer.db"),
            )
        )
        self.image_root = Path(
            os.environ.get("ALBUM_EXPLORER_IMAGE_ROOT", str(base))
        )
        self.thumbnail_dir = Path(
            os.environ.get(
                "ALBUM_EXPLORER_THUMBS",
                str(base / "album-explorer" / "data" / "thumbnails"),
            )
        )
        self.vectors_dir = Path(
            os.environ.get(
                "ALBUM_EXPLORER_VECTORS",
                str(base / "album-explorer" / "data" / "vectors"),
            )
        )
        self.port = int(os.environ.get("ALBUM_EXPLORER_PORT", "8000"))
        self.thumb_sm_size = 200
        self.thumb_md_size = 600
        self.thumb_quality_sm = 75
        self.thumb_quality_md = 80


settings = Settings()
