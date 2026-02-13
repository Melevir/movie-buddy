import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from movie_buddy.api import KinoPubClient
from movie_buddy.config import config
from movie_buddy.models import NetworkError, RateLimitError, Token

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def token() -> Token:
    return Token(
        access_token="test_token", refresh_token="test_rt", expires_at=9999999999.0
    )


@pytest.fixture
def client(token: Token) -> KinoPubClient:
    return KinoPubClient(token)


class TestSearch:
    def test_search_returns_content_list(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "search_friends.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/items/search?q=Friends&type=movie%2Cserial%2Ctvshow",
            json=data,
        )
        results = client.search("Friends")
        assert len(results) == 2
        assert results[0].id == 8894
        assert results[0].title == "Друзья / Friends"
        assert results[0].content_type == "serial"
        assert results[0].year == 1994

    def test_search_empty_results(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "search_empty.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/items/search?q=xyznonexistent&type=movie%2Cserial%2Ctvshow",
            json=data,
        )
        results = client.search("xyznonexistent")
        assert results == []


class TestGetItem:
    def test_get_item_returns_content_with_seasons(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "item_8894.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/items/8894?nolinks=1",
            json=data,
        )
        content = client.get_item(8894)
        assert content.id == 8894
        assert content.title == "Друзья / Friends"
        assert content.content_type == "serial"
        assert len(content.seasons) == 2
        assert content.seasons[0].number == 1
        assert len(content.seasons[0].episodes) == 2
        assert (
            content.seasons[0].episodes[0].title
            == "The One Where Monica Gets a Roommate"
        )
        assert content.seasons[0].episodes[0].season_number == 1
        assert content.seasons[1].number == 2
        assert len(content.seasons[1].episodes) == 1


class TestWatching:
    def test_get_watching_serials(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "watching_serials.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/watching/serials",
            json=data,
        )
        items = client.get_watching_serials()
        assert len(items) == 2
        assert items[0].id == 8894
        assert items[0].title == "Друзья / Friends"
        assert items[0].content_type == "serial"
        assert items[0].total == 234
        assert items[0].watched == 50

    def test_get_watching_movies(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "watching_movies.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/watching/movies",
            json=data,
        )
        items = client.get_watching_movies()
        assert items == []


class TestBookmarks:
    def test_get_bookmark_folders(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "bookmarks.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/bookmarks",
            json=data,
        )
        folders = client.get_bookmark_folders()
        assert len(folders) == 1
        assert folders[0].id == 2576791
        assert folders[0].title == "Буду смотреть"

    def test_get_bookmark_items(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        data = json.loads((FIXTURES / "bookmark_items.json").read_text())
        httpx_mock.add_response(
            url=f"{config.api_base_url}/bookmarks/2576791",
            json=data,
        )
        item_ids = client.get_bookmark_items(2576791)
        assert item_ids == [110440, 555]


class TestNetworkErrorHandling:
    def test_connect_error_raises_network_error(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        with pytest.raises(NetworkError, match="Unable to reach kino.pub"):
            client.search("test")

    def test_timeout_raises_network_error(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))
        with pytest.raises(NetworkError, match="timed out"):
            client.search("test")

    @patch("movie_buddy.api.time.sleep")
    def test_429_raises_rate_limit_error(
        self, mock_sleep: object, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(status_code=429)
        httpx_mock.add_response(status_code=429)
        with pytest.raises(RateLimitError):
            client.search("test")

    @patch("movie_buddy.api.time.sleep")
    def test_429_retries_then_succeeds(
        self, mock_sleep: object, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(status_code=429)
        data = json.loads((FIXTURES / "search_empty.json").read_text())
        httpx_mock.add_response(json=data)
        results = client.search("test")
        assert results == []

    def test_401_raises_auth_error(
        self, client: KinoPubClient, httpx_mock: HTTPXMock
    ) -> None:
        from movie_buddy.models import AuthError

        httpx_mock.add_response(status_code=401)
        with pytest.raises(AuthError, match="expired|auth"):
            client.search("test")
