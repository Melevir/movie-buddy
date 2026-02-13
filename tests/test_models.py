import time

from movie_buddy.models import Token


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
