# API Client Contracts

Internal Python API for interacting with kino.pub.

## KinoPubAuth

```python
class KinoPubAuth:
    """Manages OAuth2 Device Flow and token persistence."""

    def start_device_flow(self) -> DeviceCode:
        """Request a new device code. Returns user_code + verification_uri."""

    def poll_for_token(self, device_code: DeviceCode) -> Token:
        """Poll until user authorizes. Raises AuthTimeout after 300s."""

    def load_token(self) -> Token | None:
        """Load and decrypt stored token. Returns None if not found."""

    def save_token(self, token: Token) -> None:
        """Encrypt and save token to disk."""

    def refresh_token(self, token: Token) -> Token:
        """Refresh an expired token. Raises AuthError on failure."""

    def ensure_valid_token(self) -> Token:
        """Load token, refresh if expired, raise if no token."""
```

## KinoPubClient

```python
class KinoPubClient:
    """HTTP client for kino.pub API v1."""

    def __init__(self, token: Token) -> None: ...

    def search(self, query: str) -> list[Content]:
        """Search for content. Filters to movie/serial/tvshow.
        Returns empty list if no results."""

    def get_item(self, item_id: int) -> Content:
        """Get full item details including seasons/episodes.
        Uses nolinks=1 to minimize payload."""

    def get_watching_serials(self) -> list[WatchingItem]:
        """Get user's currently watching series list."""

    def get_watching_movies(self) -> list[WatchingItem]:
        """Get user's currently watching movies list."""

    def get_bookmark_folders(self) -> list[BookmarkFolder]:
        """Get user's bookmark folders."""

    def get_bookmark_items(self, folder_id: int) -> list[int]:
        """Get item IDs in a bookmark folder."""
```

## Error Types

```python
class KinoPubError(Exception): ...
class AuthError(KinoPubError): ...
class AuthTimeout(AuthError): ...
class NetworkError(KinoPubError): ...
class NotFoundError(KinoPubError): ...
class RateLimitError(KinoPubError): ...
```

## API Endpoint Mapping

| Method | Endpoint | HTTP |
|--------|----------|------|
| search | GET /v1/items/search?q=&type= | 200: items[], 401: refresh |
| get_item | GET /v1/items/{id}?nolinks=1 | 200: item, 404: not found |
| get_watching_serials | GET /v1/watching/serials | 200: items[] |
| get_watching_movies | GET /v1/watching/movies | 200: items[] |
| get_bookmark_folders | GET /v1/bookmarks | 200: items[] |
| get_bookmark_items | GET /v1/bookmarks/{id} | 200: items[] |
| start_device_flow | POST /oauth2/device | 200: code |
| poll_for_token | POST /oauth2/device | 200: token, 400: pending |
| refresh_token | POST /oauth2/token | 200: token |
