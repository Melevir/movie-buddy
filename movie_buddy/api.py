from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from movie_buddy.config import config as default_config
from movie_buddy.models import Content, Episode, Season

if TYPE_CHECKING:
    from movie_buddy.config import Config
    from movie_buddy.models import Token


class KinoPubClient:
    def __init__(self, token: Token, cfg: Config | None = None) -> None:
        self._config = cfg or default_config
        self._client = httpx.Client(
            base_url=self._config.api_base_url,
            headers={"Authorization": f"Bearer {token.access_token}"},
        )

    def search(self, query: str) -> list[Content]:
        types = ",".join(self._config.supported_types)
        response = self._client.get(
            "/items/search",
            params={"q": query, "type": types},
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        return [
            Content(
                id=item["id"],
                title=item["title"],
                content_type=item["type"],
                year=item.get("year", 0),
                seasons=[],
            )
            for item in items
        ]

    def get_item(self, item_id: int) -> Content:
        response = self._client.get(
            f"/items/{item_id}",
            params={"nolinks": "1"},
        )
        response.raise_for_status()
        item = response.json()["item"]
        seasons = []
        for s in item.get("seasons", []):
            episodes = [
                Episode(
                    id=ep["id"],
                    number=ep["number"],
                    title=ep.get("title", ""),
                    season_number=s["number"],
                )
                for ep in s.get("episodes", [])
            ]
            seasons.append(Season(number=s["number"], episodes=episodes))
        return Content(
            id=item["id"],
            title=item["title"],
            content_type=item["type"],
            year=item.get("year", 0),
            seasons=seasons,
        )
