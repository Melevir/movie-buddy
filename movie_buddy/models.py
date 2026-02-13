from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


class KinoPubError(Exception): ...


class AuthError(KinoPubError): ...


class AuthTimeoutError(AuthError): ...


class NetworkError(KinoPubError): ...


class NotFoundError(KinoPubError): ...


class RateLimitError(KinoPubError): ...


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Token:
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
        )


@dataclass
class DeviceCode:
    code: str
    user_code: str
    verification_uri: str
    interval: int
    expires_in: int


@dataclass
class Episode:
    id: int
    number: int
    title: str
    season_number: int


@dataclass
class Season:
    number: int
    episodes: list[Episode]


@dataclass
class Content:
    id: int
    title: str
    content_type: str
    year: int
    seasons: list[Season]

    @property
    def all_episodes(self) -> list[Episode]:
        return [ep for season in self.seasons for ep in season.episodes]

    def build_watch_url(self, episode: Episode | None = None) -> str:
        from movie_buddy.config import config

        if self.content_type == "movie" or episode is None:
            return f"{config.web_base_url}/{self.id}"
        return (
            f"{config.web_base_url}/{self.id}/s{episode.season_number}e{episode.number}"
        )


@dataclass
class WatchingItem:
    id: int
    title: str
    content_type: str
    total: int
    watched: int


@dataclass
class BookmarkFolder:
    id: int
    title: str


@dataclass
class CatalogEntry:
    id: int
    title: str
    year: int
    content_type: str
    genres: list[str]
    countries: list[str]
    imdb_rating: float | None
    kinopoisk_rating: float | None
    plot: str
    created_at: str


@dataclass
class Rating:
    content_id: int
    title: str
    content_type: str
    score: int
    rated_at: str


@dataclass
class Recommendation:
    content_id: int
    title: str
    year: int
    content_type: str
    explanation: str
