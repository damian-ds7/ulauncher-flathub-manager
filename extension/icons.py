import hashlib
from pathlib import Path

import requests

from .constants import ICON_CACHE_DIR


def icon_path(url: str) -> str:
    ICON_CACHE_DIR.mkdir(exist_ok=True)
    fname = hashlib.sha256(url.encode()).hexdigest() + ".png"
    return str(ICON_CACHE_DIR / fname)


def download_icon(url: str, timeout: int = 5) -> str:
    path = icon_path(url)
    if not Path(path).exists():
        try:
            r = requests.get(url, timeout=timeout)
            if r.ok:
                with open(path, "wb") as f:
                    f.write(r.content)
        except Exception:
            return "images/icon.png"  # fallback if request fails
    return path
