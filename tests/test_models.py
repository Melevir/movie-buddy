import time

from movie_buddy.config import config
from movie_buddy.models import Content, Episode, Season, Token


class TestToken:
    def test_construction(self) -> None:
        token = Token(
            access_token="abc123",
            refresh_token="def456",
            expires_at=time.time() + 3600,
        )
        assert token.access_token == "abc123"
        assert token.refresh_token == "def456"

    def test_is_expired_false_when_valid(self) -> None:
        token = Token(
            access_token="abc",
            refresh_token="def",
            expires_at=time.time() + 3600,
        )
        assert not token.is_expired

    def test_is_expired_true_when_past(self) -> None:
        token = Token(
            access_token="abc",
            refresh_token="def",
            expires_at=time.time() - 10,
        )
        assert token.is_expired

    def test_to_dict(self) -> None:
        expires = time.time() + 3600
        token = Token(
            access_token="abc",
            refresh_token="def",
            expires_at=expires,
        )
        d = token.to_dict()
        assert d == {
            "access_token": "abc",
            "refresh_token": "def",
            "expires_at": expires,
        }

    def test_from_dict(self) -> None:
        expires = time.time() + 3600
        d = {
            "access_token": "abc",
            "refresh_token": "def",
            "expires_at": expires,
        }
        token = Token.from_dict(d)
        assert token.access_token == "abc"
        assert token.refresh_token == "def"
        assert token.expires_at == expires


class TestEpisode:
    def test_construction(self) -> None:
        ep = Episode(id=104311, number=1, title="Pilot", season_number=1)
        assert ep.id == 104311
        assert ep.number == 1
        assert ep.title == "Pilot"
        assert ep.season_number == 1


class TestSeason:
    def test_construction(self) -> None:
        ep = Episode(id=1, number=1, title="Ep1", season_number=1)
        season = Season(number=1, episodes=[ep])
        assert season.number == 1
        assert len(season.episodes) == 1


class TestContent:
    def _make_serial(self) -> Content:
        episodes_s1 = [
            Episode(id=100, number=1, title="S1E1", season_number=1),
            Episode(id=101, number=2, title="S1E2", season_number=1),
        ]
        episodes_s2 = [
            Episode(id=200, number=1, title="S2E1", season_number=2),
        ]
        return Content(
            id=8894,
            title="Friends",
            content_type="serial",
            year=1994,
            seasons=[
                Season(number=1, episodes=episodes_s1),
                Season(number=2, episodes=episodes_s2),
            ],
        )

    def test_construction(self) -> None:
        content = self._make_serial()
        assert content.id == 8894
        assert content.title == "Friends"
        assert content.content_type == "serial"
        assert len(content.seasons) == 2

    def test_build_watch_url_series_episode(self) -> None:
        content = self._make_serial()
        ep = content.seasons[0].episodes[0]
        url = content.build_watch_url(ep)
        assert url == f"{config.web_base_url}/8894/s1e1"

    def test_build_watch_url_series_season2(self) -> None:
        content = self._make_serial()
        ep = content.seasons[1].episodes[0]
        url = content.build_watch_url(ep)
        assert url == f"{config.web_base_url}/8894/s2e1"

    def test_build_watch_url_movie(self) -> None:
        content = Content(
            id=113,
            title="The Matrix",
            content_type="movie",
            year=1999,
            seasons=[],
        )
        url = content.build_watch_url()
        assert url == f"{config.web_base_url}/113"

    def test_all_episodes(self) -> None:
        content = self._make_serial()
        all_eps = content.all_episodes
        assert len(all_eps) == 3
        assert all_eps[0].season_number == 1
        assert all_eps[2].season_number == 2
