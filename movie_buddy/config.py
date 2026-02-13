from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    client_id: str = field(default_factory=lambda: os.environ["KINOPUB_CLIENT_ID"])
    client_secret: str = field(
        default_factory=lambda: os.environ["KINOPUB_CLIENT_SECRET"]
    )
    api_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "KINOPUB_API_BASE_URL", "https://api.srvkp.com/v1"
        ),
    )
    oauth_url: str = field(
        default_factory=lambda: os.environ.get(
            "KINOPUB_OAUTH_URL", "https://api.srvkp.com/oauth2/device"
        ),
    )
    token_refresh_url: str = field(
        default_factory=lambda: os.environ.get(
            "KINOPUB_TOKEN_REFRESH_URL", "https://api.srvkp.com/oauth2/token"
        ),
    )
    web_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "KINOPUB_WEB_BASE", "https://kino.pub/item/view"
        ),
    )
    config_dir: Path = field(
        default_factory=lambda: Path.home() / ".config" / "movie_buddy"
    )
    supported_types: tuple[str, ...] = ("movie", "serial", "tvshow")
    turso_database_url: str | None = field(
        default_factory=lambda: os.environ.get("TURSO_DATABASE_URL"),
    )
    turso_auth_token: str | None = field(
        default_factory=lambda: os.environ.get("TURSO_AUTH_TOKEN"),
    )
    openai_api_key: str | None = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY"),
    )

    @property
    def token_file(self) -> Path:
        return self.config_dir / "token.bin"


config = Config()
