from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


class KinoPubError(Exception): ...


class AuthError(KinoPubError): ...


class AuthTimeoutError(AuthError): ...


class NetworkError(KinoPubError): ...


class NotFoundError(KinoPubError): ...


class RateLimitError(KinoPubError): ...


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Token:
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
        )


@dataclass
class DeviceCode:
    code: str
    user_code: str
    verification_uri: str
    interval: int
    expires_in: int
