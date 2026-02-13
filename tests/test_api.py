import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from movie_buddy.api import KinoPubClient
from movie_buddy.config import config
from movie_buddy.models import Token

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
