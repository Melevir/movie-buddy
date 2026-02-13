from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Any

import httpx

from movie_buddy.config import config as default_config
from movie_buddy.models import (
    AuthError,
    BookmarkFolder,
    CatalogEntry,
    Content,
    Episode,
    NetworkError,
    RateLimitError,
    Season,
    WatchingItem,
)

if TYPE_CHECKING:
    from movie_buddy.config import Config
    from movie_buddy.models import Token

_MAX_RETRIES = 2
_RETRY_DELAY = 5


class KinoPubClient:
    def __init__(self, token: Token, cfg: Config | None = None) -> None:
        self._config = cfg or default_config
        self._client = httpx.Client(
            base_url=self._config.api_base_url,
            headers={"Authorization": f"Bearer {token.access_token}"},
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        retries = 0
        while True:
            try:
                response = self._client.request(method, url, params=params)
            except httpx.ConnectError as e:
                msg = "Unable to reach kino.pub. Check your internet connection."
                raise NetworkError(msg) from e
            except httpx.TimeoutException as e:
                msg = "Request to kino.pub timed out. Please try again."
                raise NetworkError(msg) from e

            if response.status_code == 429:
                retries += 1
                if retries >= _MAX_RETRIES:
                    msg = "Rate limited by kino.pub. Please wait and try again."
                    raise RateLimitError(msg)
                time.sleep(_RETRY_DELAY)
                continue

            if response.status_code == 401:
                msg = "Token expired or invalid. Please run `movie-buddy auth`."
                raise AuthError(msg)

            response.raise_for_status()
            return response

    def search(self, query: str) -> list[Content]:
        types = ",".join(self._config.supported_types)
        response = self._request(
            "GET",
            "/items/search",
            params={"q": query, "type": types},
        )
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
        response = self._request(
            "GET",
            f"/items/{item_id}",
            params={"nolinks": "1"},
        )
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

    def _parse_watching(self, endpoint: str) -> list[WatchingItem]:
        response = self._request("GET", endpoint)
        return [
            WatchingItem(
                id=item["id"],
                title=item["title"],
                content_type=item["type"],
                total=item.get("total", 0),
                watched=item.get("watched", 0),
            )
            for item in response.json().get("items", [])
        ]

    def get_watching_serials(self) -> list[WatchingItem]:
        return self._parse_watching("/watching/serials")

    def get_watching_movies(self) -> list[WatchingItem]:
        return self._parse_watching("/watching/movies")

    def get_bookmark_folders(self) -> list[BookmarkFolder]:
        response = self._request("GET", "/bookmarks")
        return [
            BookmarkFolder(id=item["id"], title=item["title"])
            for item in response.json().get("items", [])
        ]

    def get_bookmark_items(self, folder_id: int) -> list[int]:
        response = self._request("GET", f"/bookmarks/{folder_id}")
        return [item["id"] for item in response.json().get("items", [])]

    def get_category_items(
        self,
        category: str,
        content_type: str,
        per_page: int = 50,
    ) -> list[CatalogEntry]:
        response = self._request(
            "GET",
            f"/items/{category}",
            params={"type": content_type, "perpage": str(per_page)},
        )
        now = datetime.datetime.now(tz=datetime.UTC).isoformat()
        return [
            CatalogEntry(
                id=item["id"],
                title=item["title"],
                year=item.get("year", 0),
                content_type=item["type"],
                genres=[g["title"] for g in item.get("genres", [])],
                countries=[c["title"] for c in item.get("countries", [])],
                imdb_rating=item.get("imdb_rating"),
                kinopoisk_rating=item.get("kinopoisk_rating"),
                plot=item.get("plot", ""),
                created_at=now,
            )
            for item in response.json().get("items", [])
        ]
