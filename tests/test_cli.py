import random
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from movie_buddy.config import config
from movie_buddy.matcher import rank_results
from movie_buddy.models import AuthError, Content, Episode, NetworkError, Season


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
