from __future__ import annotations

import base64
import getpass
import hashlib
import json
import platform
import time
from typing import TYPE_CHECKING

import httpx
from cryptography.fernet import Fernet, InvalidToken

from movie_buddy.config import config as default_config
from movie_buddy.models import AuthError, AuthTimeoutError, DeviceCode, Token

if TYPE_CHECKING:
    from pathlib import Path

    from movie_buddy.config import Config


class KinoPubAuth:
    def __init__(
        self,
        token_path: Path | None = None,
        cfg: Config | None = None,
    ) -> None:
        self._config = cfg or default_config
        self._token_path = token_path or self._config.token_file
        self._fernet = Fernet(self._derive_key())

    @staticmethod
    def _derive_key() -> bytes:
        raw = f"{platform.node()}:{getpass.getuser()}:movie_buddy_salt"
        digest = hashlib.sha256(raw.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def save_token(self, token: Token) -> None:
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(token.to_dict()).encode()
        encrypted = self._fernet.encrypt(data)
        self._token_path.write_bytes(encrypted)

    def load_token(self) -> Token | None:
        if not self._token_path.exists():
            return None
        try:
            encrypted = self._token_path.read_bytes()
            data = self._fernet.decrypt(encrypted)
            return Token.from_dict(json.loads(data))
        except (InvalidToken, json.JSONDecodeError, KeyError):
            return None

    def start_device_flow(self) -> DeviceCode:
        response = httpx.post(
            self._config.oauth_url,
            data={
                "grant_type": "device_code",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
            },
        )
        response.raise_for_status()
        body = response.json()
        return DeviceCode(
            code=body["code"],
            user_code=body["user_code"],
            verification_uri=body["verification_uri"],
            interval=body["interval"],
            expires_in=body["expires_in"],
        )

    def poll_for_token(self, device_code: DeviceCode) -> Token:
        deadline = time.time() + device_code.expires_in
        while time.time() < deadline:
            response = httpx.post(
                self._config.oauth_url,
                data={
                    "grant_type": "device_token",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "code": device_code.code,
                },
            )
            if response.status_code == 200:
                body = response.json()
                return Token(
                    access_token=body["access_token"],
                    refresh_token=body["refresh_token"],
                    expires_at=time.time() + body["expires_in"],
                )
            body = response.json()
            if body.get("error") != "authorization_pending":
                raise AuthError(f"Unexpected auth error: {body.get('error')}")
            time.sleep(device_code.interval)
        raise AuthTimeoutError("Device authorization timed out")

    def refresh_token(self, token: Token) -> Token:
        response = httpx.post(
            self._config.token_refresh_url,
            data={
                "grant_type": "refresh_token",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "refresh_token": token.refresh_token,
            },
        )
        if response.status_code != 200:
            raise AuthError("Token refresh failed")
        body = response.json()
        return Token(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=time.time() + body["expires_in"],
        )

    def ensure_valid_token(self) -> Token:
        token = self.load_token()
        if token is None:
            raise AuthError("Not authenticated. Run 'movie-buddy auth' first.")
        if token.is_expired:
            token = self.refresh_token(token)
            self.save_token(token)
        return token
