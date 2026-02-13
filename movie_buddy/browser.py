from __future__ import annotations

import subprocess
import sys


def open_in_chrome(url: str) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-a", "Google Chrome", url], check=True)
        else:
            subprocess.run(["google-chrome", url], check=True)
    except FileNotFoundError as e:
        msg = "Chrome not found. Please install Google Chrome."
        raise RuntimeError(msg) from e
