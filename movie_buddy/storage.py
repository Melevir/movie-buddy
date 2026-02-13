from __future__ import annotations

import json
from typing import TYPE_CHECKING

import libsql_client  # type: ignore[import-untyped]

from movie_buddy.config import config as default_config
from movie_buddy.models import CatalogEntry, KinoPubError, Rating

if TYPE_CHECKING:
    from movie_buddy.config import Config

_SCHEMA_CATALOG = """
CREATE TABLE IF NOT EXISTS catalog (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    genres TEXT NOT NULL DEFAULT '[]',
    countries TEXT NOT NULL DEFAULT '[]',
    imdb_rating REAL,
    kinopoisk_rating REAL,
    plot TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
)
"""

_SCHEMA_RATINGS = """
CREATE TABLE IF NOT EXISTS ratings (
    content_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10),
    rated_at TEXT NOT NULL
)
"""


class TursoStorage:
    def __init__(self, cfg: Config | None = None) -> None:
        c = cfg or default_config
        if not c.turso_database_url:
            msg = "TURSO_DATABASE_URL not set. See quickstart guide for setup."
            raise KinoPubError(msg)
        self._client = libsql_client.create_client_sync(
            url=c.turso_database_url,
            auth_token=c.turso_auth_token or "",
        )

    def close(self) -> None:
        self._client.close()

    def init_schema(self) -> None:
        self._client.execute(_SCHEMA_CATALOG)
        self._client.execute(_SCHEMA_RATINGS)

    # ── Ratings ──────────────────────────────────────────────

    def insert_ratings(self, ratings: list[Rating]) -> None:
        for r in ratings:
            self._client.execute(
                "INSERT OR IGNORE INTO ratings "
                "(content_id, title, content_type, score, rated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                [r.content_id, r.title, r.content_type, r.score, r.rated_at],
            )

    def get_all_ratings(self) -> list[Rating]:
        result = self._client.execute(
            "SELECT content_id, title, content_type, score, rated_at FROM ratings"
        )
        return [
            Rating(
                content_id=row[0],
                title=row[1],
                content_type=row[2],
                score=row[3],
                rated_at=row[4],
            )
            for row in result.rows
        ]

    def get_rated_content_ids(self) -> set[int]:
        result = self._client.execute("SELECT content_id FROM ratings")
        return {row[0] for row in result.rows}

    def delete_all_ratings(self) -> None:
        self._client.execute("DELETE FROM ratings")

    # ── Catalog ──────────────────────────────────────────────

    def insert_catalog_entries(self, entries: list[CatalogEntry]) -> None:
        for e in entries:
            self._client.execute(
                "INSERT OR IGNORE INTO catalog "
                "(id, title, year, content_type, genres, countries, "
                "imdb_rating, kinopoisk_rating, plot, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    e.id,
                    e.title,
                    e.year,
                    e.content_type,
                    json.dumps(e.genres, ensure_ascii=False),
                    json.dumps(e.countries, ensure_ascii=False),
                    e.imdb_rating,
                    e.kinopoisk_rating,
                    e.plot,
                    e.created_at,
                ],
            )

    def get_catalog_entries(self) -> list[CatalogEntry]:
        result = self._client.execute(
            "SELECT id, title, year, content_type, genres, countries, "
            "imdb_rating, kinopoisk_rating, plot, created_at FROM catalog"
        )
        return [
            CatalogEntry(
                id=row[0],
                title=row[1],
                year=row[2],
                content_type=row[3],
                genres=json.loads(row[4]),
                countries=json.loads(row[5]),
                imdb_rating=row[6],
                kinopoisk_rating=row[7],
                plot=row[8],
                created_at=row[9],
            )
            for row in result.rows
        ]

    def get_catalog_count(self) -> int:
        result = self._client.execute("SELECT COUNT(*) FROM catalog")
        count: int = result.rows[0][0]
        return count

    def get_existing_catalog_ids(self) -> set[int]:
        result = self._client.execute("SELECT id FROM catalog")
        return {row[0] for row in result.rows}
