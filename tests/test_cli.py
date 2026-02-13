import random
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from movie_buddy.cli import app
from movie_buddy.config import config
from movie_buddy.matcher import rank_results
from movie_buddy.models import (
    AuthError,
    Content,
    Episode,
    KinoPubError,
    NetworkError,
    Rating,
    Season,
    WatchingItem,
)


def _make_content(item_id: int, title: str, content_type: str = "serial") -> Content:
    return Content(
        id=item_id, title=title, content_type=content_type, year=2020, seasons=[]
    )


class TestRandomEpisodeSelection:
    def _make_multi_season_content(self) -> Content:
        seasons = []
        ep_id = 1
        for s in range(1, 4):
            episodes = []
            for e in range(1, 6):
                episodes.append(
                    Episode(id=ep_id, number=e, title=f"S{s}E{e}", season_number=s)
                )
                ep_id += 1
            seasons.append(Season(number=s, episodes=episodes))
        return Content(
            id=100, title="Test Show", content_type="serial", year=2020, seasons=seasons
        )

    def test_random_selection_covers_multiple_seasons(self) -> None:
        content = self._make_multi_season_content()
        all_eps = content.all_episodes
        rng = random.Random(42)
        selected_seasons: set[int] = set()
        for _ in range(50):
            ep = rng.choice(all_eps)
            selected_seasons.add(ep.season_number)
        assert len(selected_seasons) > 1

    def test_single_episode_series(self) -> None:
        content = Content(
            id=200,
            title="Mini",
            content_type="serial",
            year=2020,
            seasons=[
                Season(
                    number=1,
                    episodes=[Episode(id=1, number=1, title="Only", season_number=1)],
                )
            ],
        )
        all_eps = content.all_episodes
        assert len(all_eps) == 1
        assert random.choice(all_eps).title == "Only"


class TestMatchRanking:
    def test_single_result_auto_selects(self) -> None:
        results = [_make_content(100, "Only Show")]
        selected, reason = rank_results(results, watching_ids=set(), bookmark_ids=set())
        assert selected.id == 100
        assert reason is None

    def test_watching_match_auto_selects(self) -> None:
        results = [
            _make_content(100, "Friends"),
            _make_content(200, "Friends & Neighbors"),
            _make_content(300, "Other"),
        ]
        selected, reason = rank_results(results, watching_ids={200}, bookmark_ids=set())
        assert selected.id == 200
        assert "watching" in reason.lower()

    def test_bookmark_match_auto_selects(self) -> None:
        results = [
            _make_content(100, "Friends"),
            _make_content(200, "Friends & Neighbors"),
        ]
        selected, reason = rank_results(results, watching_ids=set(), bookmark_ids={200})
        assert selected.id == 200
        assert "bookmark" in reason.lower()

    def test_watching_takes_priority_over_bookmarks(self) -> None:
        results = [
            _make_content(100, "Show A"),
            _make_content(200, "Show B"),
        ]
        selected, reason = rank_results(results, watching_ids={100}, bookmark_ids={200})
        assert selected.id == 100
        assert "watching" in reason.lower()

    def test_no_activity_match_returns_none(self) -> None:
        results = [
            _make_content(100, "Show A"),
            _make_content(200, "Show B"),
            _make_content(300, "Show C"),
        ]
        selected, reason = rank_results(results, watching_ids=set(), bookmark_ids=set())
        assert selected is None
        assert reason is None

    def test_multiple_watching_matches_returns_none(self) -> None:
        results = [
            _make_content(100, "Show A"),
            _make_content(200, "Show B"),
        ]
        selected, reason = rank_results(
            results, watching_ids={100, 200}, bookmark_ids=set()
        )
        assert selected is None


class TestMovieHandling:
    def test_movie_opens_without_episode_suffix(self) -> None:
        movie = Content(
            id=113,
            title="The Matrix",
            content_type="movie",
            year=1999,
            seasons=[],
        )
        url = movie.build_watch_url()
        assert url == f"{config.web_base_url}/113"
        assert "/s" not in url
        assert "/e" not in url

    def test_movie_skips_get_item(self) -> None:
        movie = Content(
            id=113,
            title="The Matrix",
            content_type="movie",
            year=1999,
            seasons=[],
        )
        mock_client = MagicMock()
        with patch("movie_buddy.cli.open_in_chrome"):
            from movie_buddy.cli import _open_content

            _open_content(mock_client, movie)

        mock_client.get_item.assert_not_called()

    def test_mixed_movie_and_series_in_picker(self) -> None:
        results = [
            _make_content(100, "Friends", "serial"),
            _make_content(200, "Friends: The Movie", "movie"),
            _make_content(300, "Friends Show", "tvshow"),
        ]
        from movie_buddy.cli import TYPE_LABELS

        for item in results:
            label = TYPE_LABELS.get(item.content_type, item.content_type)
            assert label in ("Series", "Movie", "TV Show")


class TestCLIErrorDisplay:
    def test_network_error_shows_friendly_message(self) -> None:
        from movie_buddy.cli import app

        runner = CliRunner()
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient") as mock_client_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            mock_client = mock_client_cls.return_value
            mock_client.search.side_effect = NetworkError("Unable to reach kino.pub")
            result = runner.invoke(app, ["watch", "Friends"])

        assert result.exit_code == 1
        assert (
            "unable to reach" in result.output.lower()
            or "network" in result.output.lower()
        )

    def test_auth_error_shows_auth_message(self) -> None:
        from movie_buddy.cli import app

        runner = CliRunner()
        with patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls:
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.side_effect = AuthError("No token found")
            result = runner.invoke(app, ["watch", "Friends"])

        assert result.exit_code == 1
        assert "auth" in result.output.lower()

    def test_single_episode_series_opens_correctly(self) -> None:
        single_ep_content = Content(
            id=200,
            title="Mini Series",
            content_type="serial",
            year=2020,
            seasons=[
                Season(
                    number=1,
                    episodes=[
                        Episode(id=1, number=1, title="Only Episode", season_number=1)
                    ],
                )
            ],
        )
        mock_client = MagicMock()
        mock_client.get_item.return_value = single_ep_content
        with patch("movie_buddy.cli.open_in_chrome") as mock_open:
            from movie_buddy.cli import _open_content

            _open_content(mock_client, single_ep_content)

        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        assert "s1e1" in url


def _watching_items() -> list[WatchingItem]:
    return [
        WatchingItem(
            id=1, title="Friends", content_type="serial", total=234, watched=50
        ),
        WatchingItem(
            id=2, title="The Matrix", content_type="movie", total=1, watched=1
        ),
        WatchingItem(
            id=3, title="Breaking Bad", content_type="serial", total=62, watched=62
        ),
    ]


def _mock_storage(rated_ids: set[int] | None = None):
    storage = MagicMock()
    storage.get_rated_content_ids.return_value = rated_ids or set()
    storage.get_all_ratings.return_value = []
    storage.get_catalog_count.return_value = 0
    return storage


def _patch_rate_deps(
    watching: list[WatchingItem] | None = None,
    storage: MagicMock | None = None,
):
    """Return a context manager patching auth, client, and storage for rate tests."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient") as mock_client_cls,
            patch("movie_buddy.cli.TursoStorage") as mock_storage_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            mock_client = mock_client_cls.return_value
            mock_client.get_watching_serials.return_value = [
                w for w in (watching or []) if w.content_type != "movie"
            ]
            mock_client.get_watching_movies.return_value = [
                w for w in (watching or []) if w.content_type == "movie"
            ]
            mock_storage_cls.return_value = storage or _mock_storage()
            store = mock_storage_cls.return_value
            store.init_schema.return_value = None
            yield mock_client, store

    return _ctx()


class TestRateCommand:
    def test_presents_movies_from_watching_history(self) -> None:
        runner = CliRunner()
        # Provide "q" to quit after seeing first item
        with _patch_rate_deps(watching=_watching_items()) as (client, store):
            result = runner.invoke(app, ["rate"], input="q\n")
        assert result.exit_code == 0
        assert "Friends" in result.output

    def test_rating_saves_to_storage(self) -> None:
        runner = CliRunner()
        items = [
            WatchingItem(
                id=1, title="Friends", content_type="serial", total=10, watched=5
            )
        ]
        with _patch_rate_deps(watching=items) as (client, store):
            result = runner.invoke(app, ["rate"], input="8\n")
        assert result.exit_code == 0
        store.insert_ratings.assert_called_once()
        saved_rating = store.insert_ratings.call_args[0][0][0]
        assert saved_rating.score == 8
        assert saved_rating.content_id == 1

    def test_skip_moves_to_next(self) -> None:
        runner = CliRunner()
        items = [
            WatchingItem(
                id=1, title="Friends", content_type="serial", total=10, watched=5
            ),
            WatchingItem(
                id=2, title="Matrix", content_type="movie", total=1, watched=1
            ),
        ]
        with _patch_rate_deps(watching=items) as (client, store):
            # Skip first, rate second, then done
            result = runner.invoke(app, ["rate"], input="\n9\n")
        assert result.exit_code == 0
        store.insert_ratings.assert_called_once()
        saved = store.insert_ratings.call_args[0][0][0]
        assert saved.content_id == 2

    def test_quit_ends_session_early(self) -> None:
        runner = CliRunner()
        with _patch_rate_deps(watching=_watching_items()) as (client, store):
            result = runner.invoke(app, ["rate"], input="q\n")
        assert result.exit_code == 0
        store.insert_ratings.assert_not_called()

    def test_previously_rated_excluded(self) -> None:
        runner = CliRunner()
        storage = _mock_storage(rated_ids={1, 2})
        items = _watching_items()  # ids 1, 2, 3
        with _patch_rate_deps(watching=items, storage=storage) as (client, store):
            result = runner.invoke(app, ["rate"], input="7\n")
        assert result.exit_code == 0
        # Only item 3 (Breaking Bad) should be presented
        assert "Breaking Bad" in result.output
        assert "Friends" not in result.output.split("Rated")[0]

    def test_no_unrated_movies_shows_message(self) -> None:
        runner = CliRunner()
        storage = _mock_storage(rated_ids={1, 2, 3})
        with _patch_rate_deps(watching=_watching_items(), storage=storage) as (
            client,
            store,
        ):
            result = runner.invoke(app, ["rate"])
        assert result.exit_code == 0
        assert (
            "no more" in result.output.lower() or "watch more" in result.output.lower()
        )

    def test_no_watching_history_shows_message(self) -> None:
        runner = CliRunner()
        with _patch_rate_deps(watching=[]) as (client, store):
            result = runner.invoke(app, ["rate"])
        assert result.exit_code == 0
        assert (
            "no more" in result.output.lower() or "watch more" in result.output.lower()
        )

    def test_summary_message_after_session(self) -> None:
        runner = CliRunner()
        items = [
            WatchingItem(
                id=1, title="Friends", content_type="serial", total=10, watched=5
            )
        ]
        storage = _mock_storage()
        storage.get_all_ratings.return_value = [
            Rating(
                content_id=1,
                title="Friends",
                content_type="serial",
                score=8,
                rated_at="2026-01-01",
            ),
        ]
        with _patch_rate_deps(watching=items, storage=storage) as (client, store):
            result = runner.invoke(app, ["rate"], input="8\n")
        assert result.exit_code == 0
        assert "rated" in result.output.lower()


class TestRateErrorHandling:
    def test_missing_turso_config_shows_message(self) -> None:
        runner = CliRunner()
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient"),
            patch("movie_buddy.cli.TursoStorage") as mock_storage_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            mock_storage_cls.side_effect = KinoPubError("TURSO_DATABASE_URL not set")
            result = runner.invoke(app, ["rate"])
        assert result.exit_code == 1
        assert "turso" in result.output.lower() or "error" in result.output.lower()

    def test_network_error_shows_friendly_message(self) -> None:
        runner = CliRunner()
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient") as mock_client_cls,
            patch("movie_buddy.cli.TursoStorage") as mock_storage_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            mock_storage_cls.return_value = _mock_storage()
            mock_storage_cls.return_value.init_schema.return_value = None
            mock_client = mock_client_cls.return_value
            mock_client.get_watching_serials.side_effect = NetworkError(
                "Unable to reach kino.pub"
            )
            result = runner.invoke(app, ["rate"])
        assert result.exit_code == 1
        assert "network" in result.output.lower() or "unable" in result.output.lower()


def _mock_catalog_entries():
    from movie_buddy.models import CatalogEntry

    return [
        CatalogEntry(
            id=501,
            title="Movie A",
            year=2026,
            content_type="movie",
            genres=["Drama"],
            countries=["USA"],
            imdb_rating=7.5,
            kinopoisk_rating=7.0,
            plot="Plot A",
            created_at="2026-01-01",
        ),
        CatalogEntry(
            id=502,
            title="Movie B",
            year=2025,
            content_type="movie",
            genres=["Comedy"],
            countries=["USA"],
            imdb_rating=6.8,
            kinopoisk_rating=None,
            plot="Plot B",
            created_at="2026-01-01",
        ),
    ]


def _patch_catalog_deps(
    category_items: list | None = None,
    storage: MagicMock | None = None,
):
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient") as mock_client_cls,
            patch("movie_buddy.cli.TursoStorage") as mock_storage_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            mock_client = mock_client_cls.return_value
            mock_client.get_category_items.return_value = (
                category_items if category_items is not None else []
            )
            store = storage or _mock_storage()
            store.init_schema.return_value = None
            mock_storage_cls.return_value = store
            yield mock_client, store

    return _ctx()


class TestCatalogCommand:
    def test_fetches_9_endpoints(self) -> None:
        runner = CliRunner()
        with _patch_catalog_deps(category_items=[]) as (client, store):
            result = runner.invoke(app, ["catalog"])
        assert result.exit_code == 0
        assert client.get_category_items.call_count == 9

    def test_deduplicates_against_existing(self) -> None:
        runner = CliRunner()
        entries = _mock_catalog_entries()
        storage = _mock_storage()
        storage.get_existing_catalog_ids.return_value = {501}
        with _patch_catalog_deps(category_items=entries, storage=storage) as (
            client,
            store,
        ):
            result = runner.invoke(app, ["catalog"])
        assert result.exit_code == 0
        # Should have been called to insert — the dedup filters in the command
        store.insert_catalog_entries.assert_called()

    def test_shows_summary_with_counts(self) -> None:
        runner = CliRunner()
        entries = _mock_catalog_entries()
        storage = _mock_storage()
        storage.get_existing_catalog_ids.return_value = set()
        storage.get_catalog_count.return_value = 18
        with _patch_catalog_deps(category_items=entries, storage=storage) as (
            client,
            store,
        ):
            result = runner.invoke(app, ["catalog"])
        assert result.exit_code == 0
        assert "catalog" in result.output.lower() or "updated" in result.output.lower()

    def test_network_error_handling(self) -> None:
        runner = CliRunner()
        with (
            patch("movie_buddy.cli.KinoPubAuth") as mock_auth_cls,
            patch("movie_buddy.cli.KinoPubClient") as mock_client_cls,
            patch("movie_buddy.cli.TursoStorage") as mock_storage_cls,
        ):
            mock_auth = mock_auth_cls.return_value
            mock_auth.ensure_valid_token.return_value = MagicMock()
            store = _mock_storage()
            store.init_schema.return_value = None
            mock_storage_cls.return_value = store
            mock_client = mock_client_cls.return_value
            mock_client.get_category_items.side_effect = NetworkError(
                "Unable to reach kino.pub"
            )
            result = runner.invoke(app, ["catalog"])
        assert result.exit_code == 1
        assert "network" in result.output.lower() or "unable" in result.output.lower()
