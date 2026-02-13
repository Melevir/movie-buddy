import time
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from movie_buddy.auth import KinoPubAuth
from movie_buddy.config import config
from movie_buddy.models import AuthError, AuthTimeoutError, DeviceCode, Token


@pytest.fixture
def tmp_token_path(tmp_path: Path) -> Path:
    return tmp_path / "token.bin"


@pytest.fixture
def auth(tmp_token_path: Path) -> KinoPubAuth:
    return KinoPubAuth(token_path=tmp_token_path)


class TestTokenEncryption:
    def test_encrypt_decrypt_roundtrip(self, auth: KinoPubAuth) -> None:
        token = Token(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=time.time() + 3600,
        )
        auth.save_token(token)
        loaded = auth.load_token()
        assert loaded is not None
        assert loaded.access_token == "test_access"
        assert loaded.refresh_token == "test_refresh"

    def test_load_nonexistent_returns_none(self, auth: KinoPubAuth) -> None:
        result = auth.load_token()
        assert result is None

    def test_decrypt_with_corrupted_data_returns_none(
        self, auth: KinoPubAuth, tmp_token_path: Path
    ) -> None:
        tmp_token_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_token_path.write_bytes(b"garbage data that is not valid fernet")
        result = auth.load_token()
        assert result is None


class TestDeviceFlow:
    def test_start_device_flow(self, auth: KinoPubAuth, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=config.oauth_url,
            method="POST",
            json={
                "code": "device_code_123",
                "user_code": "ABC12",
                "verification_uri": "https://kino.pub/device",
                "interval": 5,
                "expires_in": 300,
            },
        )
        device_code = auth.start_device_flow()
        assert device_code.user_code == "ABC12"
        assert device_code.verification_uri == "https://kino.pub/device"
        assert device_code.code == "device_code_123"

    def test_poll_for_token_success(
        self, auth: KinoPubAuth, httpx_mock: HTTPXMock
    ) -> None:
        device_code = DeviceCode(
            code="dc123",
            user_code="X",
            verification_uri="https://kino.pub/device",
            interval=0,
            expires_in=300,
        )
        httpx_mock.add_response(
            url=config.oauth_url,
            method="POST",
            status_code=400,
            json={"error": "authorization_pending"},
        )
        httpx_mock.add_response(
            url=config.oauth_url,
            method="POST",
            json={
                "access_token": "at_123",
                "refresh_token": "rt_456",
                "expires_in": 86400,
            },
        )
        token = auth.poll_for_token(device_code)
        assert token.access_token == "at_123"
        assert token.refresh_token == "rt_456"

    def test_poll_for_token_timeout(self, auth: KinoPubAuth) -> None:
        device_code = DeviceCode(
            code="dc123",
            user_code="X",
            verification_uri="https://kino.pub/device",
            interval=0,
            expires_in=0,
        )
        with pytest.raises(AuthTimeoutError):
            auth.poll_for_token(device_code)


class TestTokenRefresh:
    def test_refresh_token_success(
        self, auth: KinoPubAuth, httpx_mock: HTTPXMock
    ) -> None:
        old_token = Token(
            access_token="old_at",
            refresh_token="old_rt",
            expires_at=time.time() - 10,
        )
        httpx_mock.add_response(
            url=config.token_refresh_url,
            method="POST",
            json={
                "access_token": "new_at",
                "refresh_token": "new_rt",
                "expires_in": 86400,
            },
        )
        new_token = auth.refresh_token(old_token)
        assert new_token.access_token == "new_at"
        assert new_token.refresh_token == "new_rt"

    def test_ensure_valid_token_refreshes_expired(
        self, auth: KinoPubAuth, httpx_mock: HTTPXMock
    ) -> None:
        expired_token = Token(
            access_token="old",
            refresh_token="rt",
            expires_at=time.time() - 10,
        )
        auth.save_token(expired_token)
        httpx_mock.add_response(
            url=config.token_refresh_url,
            method="POST",
            json={
                "access_token": "refreshed",
                "refresh_token": "new_rt",
                "expires_in": 86400,
            },
        )
        token = auth.ensure_valid_token()
        assert token.access_token == "refreshed"

    def test_ensure_valid_token_raises_when_no_token(self, auth: KinoPubAuth) -> None:
        with pytest.raises(AuthError):
            auth.ensure_valid_token()
