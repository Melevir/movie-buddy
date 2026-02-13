import random

from movie_buddy.models import Content, Episode, Season


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
