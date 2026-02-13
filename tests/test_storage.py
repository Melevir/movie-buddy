from __future__ import annotations

from typing import TYPE_CHECKING

import libsql_client
import pytest

from movie_buddy.models import CatalogEntry, KinoPubError, Rating

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    return f"file://{tmp_path}/test.db"


@pytest.fixture
def storage(tmp_db: str):
    from movie_buddy.storage import TursoStorage

    store = TursoStorage.__new__(TursoStorage)
    store._client = libsql_client.create_client_sync(url=tmp_db)
    store.init_schema()
    yield store
    store.close()


class TestConfigValidation:
    def test_missing_turso_url_raises_error(self) -> None:
        from movie_buddy.config import Config
        from movie_buddy.storage import TursoStorage

        cfg = Config.__new__(Config)
        object.__setattr__(cfg, "turso_database_url", None)
        object.__setattr__(cfg, "turso_auth_token", None)
        with pytest.raises(KinoPubError, match="TURSO_DATABASE_URL not set"):
            TursoStorage(cfg=cfg)


class TestSchemaInit:
    def test_init_schema_creates_tables(self, storage) -> None:
        result = storage._client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in result.rows]
        assert "catalog" in tables
        assert "ratings" in tables


class TestRatingsCRUD:
    def test_insert_and_get_ratings(self, storage) -> None:
        rating = Rating(
            content_id=1,
            title="The Matrix",
            content_type="movie",
            score=9,
            rated_at="2026-02-13T12:00:00",
        )
        storage.insert_ratings([rating])
        ratings = storage.get_all_ratings()
        assert len(ratings) == 1
        assert ratings[0].content_id == 1
        assert ratings[0].title == "The Matrix"
        assert ratings[0].score == 9

    def test_get_rated_content_ids(self, storage) -> None:
        ratings = [
            Rating(
                content_id=1,
                title="A",
                content_type="movie",
                score=5,
                rated_at="2026-01-01",
            ),
            Rating(
                content_id=2,
                title="B",
                content_type="serial",
                score=8,
                rated_at="2026-01-02",
            ),
        ]
        storage.insert_ratings(ratings)
        ids = storage.get_rated_content_ids()
        assert ids == {1, 2}

    def test_delete_all_ratings(self, storage) -> None:
        rating = Rating(
            content_id=1,
            title="The Matrix",
            content_type="movie",
            score=9,
            rated_at="2026-02-13T12:00:00",
        )
        storage.insert_ratings([rating])
        assert len(storage.get_all_ratings()) == 1
        storage.delete_all_ratings()
        assert len(storage.get_all_ratings()) == 0

    def test_rating_deduplication_by_content_id(self, storage) -> None:
        rating1 = Rating(
            content_id=1,
            title="A",
            content_type="movie",
            score=5,
            rated_at="2026-01-01",
        )
        rating2 = Rating(
            content_id=1,
            title="A Updated",
            content_type="movie",
            score=8,
            rated_at="2026-01-02",
        )
        storage.insert_ratings([rating1])
        storage.insert_ratings([rating2])
        ratings = storage.get_all_ratings()
        assert len(ratings) == 1


class TestCatalogCRUD:
    def _make_entry(
        self, entry_id: int = 100, title: str = "Test Movie"
    ) -> CatalogEntry:
        return CatalogEntry(
            id=entry_id,
            title=title,
            year=2024,
            content_type="movie",
            genres=["Drama"],
            countries=["USA"],
            imdb_rating=7.5,
            kinopoisk_rating=7.0,
            plot="A test movie",
            created_at="2026-02-13T12:00:00",
        )

    def test_insert_and_get_catalog_entries(self, storage) -> None:
        entry = self._make_entry()
        storage.insert_catalog_entries([entry])
        entries = storage.get_catalog_entries()
        assert len(entries) == 1
        assert entries[0].id == 100
        assert entries[0].title == "Test Movie"
        assert entries[0].genres == ["Drama"]
        assert entries[0].imdb_rating == 7.5

    def test_catalog_deduplication_by_id(self, storage) -> None:
        entry1 = self._make_entry(entry_id=100, title="Original")
        entry2 = self._make_entry(entry_id=100, title="Duplicate")
        storage.insert_catalog_entries([entry1])
        storage.insert_catalog_entries([entry2])
        entries = storage.get_catalog_entries()
        assert len(entries) == 1

    def test_get_catalog_count(self, storage) -> None:
        assert storage.get_catalog_count() == 0
        storage.insert_catalog_entries(
            [self._make_entry(entry_id=1), self._make_entry(entry_id=2)]
        )
        assert storage.get_catalog_count() == 2

    def test_get_existing_catalog_ids(self, storage) -> None:
        storage.insert_catalog_entries(
            [self._make_entry(entry_id=10), self._make_entry(entry_id=20)]
        )
        ids = storage.get_existing_catalog_ids()
        assert ids == {10, 20}
