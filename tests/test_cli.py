import random

from movie_buddy.matcher import rank_results
from movie_buddy.models import Content, Episode, Season


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
