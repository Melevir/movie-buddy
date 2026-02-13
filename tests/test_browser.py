from unittest.mock import patch

import pytest

from movie_buddy.browser import open_in_chrome


class TestOpenInChrome:
    @patch("movie_buddy.browser.subprocess.run")
    def test_calls_open_on_macos(self, mock_run: object) -> None:
        with patch("movie_buddy.browser.sys.platform", "darwin"):
            open_in_chrome("https://kino.pub/item/view/8894/s1e1")
        from unittest.mock import call

        assert mock_run.call_args == call(  # type: ignore[union-attr]
            ["open", "-a", "Google Chrome", "https://kino.pub/item/view/8894/s1e1"],
            check=True,
        )

    @patch("movie_buddy.browser.subprocess.run")
    def test_calls_google_chrome_on_linux(self, mock_run: object) -> None:
        with patch("movie_buddy.browser.sys.platform", "linux"):
            open_in_chrome("https://kino.pub/item/view/8894/s1e1")
        from unittest.mock import call

        assert mock_run.call_args == call(  # type: ignore[union-attr]
            ["google-chrome", "https://kino.pub/item/view/8894/s1e1"],
            check=True,
        )

    @patch("movie_buddy.browser.subprocess.run", side_effect=FileNotFoundError)
    def test_raises_on_chrome_not_found(self, mock_run: object) -> None:
        with (
            patch("movie_buddy.browser.sys.platform", "darwin"),
            pytest.raises(RuntimeError, match="Chrome"),
        ):
            open_in_chrome("https://kino.pub/item/view/123")
