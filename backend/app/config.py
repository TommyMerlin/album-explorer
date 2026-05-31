from __future__ import annotations

import os
import shutil
from pathlib import Path


class Settings:
    """应用配置，所有路径通过环境变量覆盖，方便后期桌面打包。"""

    def __init__(self) -> None:
        base = Path(os.environ.get("ALBUM_EXPLORER_BASE", "/mnt/d/数据备份"))
        project_root = Path(__file__).resolve().parents[2]

        self.db_source = Path(
            os.environ.get(
                "ALBUM_EXPLORER_DB",
                str(base / ".album-assetizer" / "state" / "album_assetizer.db"),
            )
        )
        # WSL2 跨文件系统 IO 极慢，把 DB 复制到 Linux 原生文件系统加速读取
        cache_dir = Path(os.environ.get("ALBUM_EXPLORER_CACHE", "/tmp/album-explorer"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "album_assetizer.db"
        self._sync_db()

        self.image_root = Path(
            os.environ.get("ALBUM_EXPLORER_IMAGE_ROOT", str(base))
        )
        self.thumbnail_dir = Path(
            os.environ.get(
                "ALBUM_EXPLORER_THUMBS",
                str(project_root / "data" / "thumbnails"),
            )
        )
        self.vectors_dir = Path(
            os.environ.get(
                "ALBUM_EXPLORER_VECTORS",
                str(project_root / "data" / "vectors"),
            )
        )
        self.port = int(os.environ.get("ALBUM_EXPLORER_PORT", "8000"))
        self.thumb_sm_size = 200
        self.thumb_md_size = 600
        self.thumb_quality_sm = 75
        self.thumb_quality_md = 80

    def _sync_db(self) -> None:
        """如果源 DB 比缓存新，则复制一份到本地文件系统。
        如果拷贝后校验失败，回退到直接使用源数据库。"""
        if not self.db_source.exists():
            return
        if self.db_path.exists():
            src_mtime = self.db_source.stat().st_mtime
            dst_mtime = self.db_path.stat().st_mtime
            if src_mtime <= dst_mtime:
                # 验证缓存完整性
                import sqlite3
                try:
                    conn = sqlite3.connect(str(self.db_path))
                    result = conn.execute("PRAGMA quick_check").fetchone()
                    conn.close()
                    if result and result[0] == "ok":
                        return
                except Exception:
                    pass
                # 缓存损坏，删除后重新拷贝
        try:
            shutil.copy2(str(self.db_source), str(self.db_path))
            # 验证拷贝结果
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            result = conn.execute("PRAGMA quick_check").fetchone()
            conn.close()
            if not result or result[0] != "ok":
                raise RuntimeError("copy corrupted")
        except Exception:
            # 拷贝失败或损坏，直接使用源数据库
            self.db_path = self.db_source


settings = Settings()
