import tempfile
from pathlib import Path

ICON_CACHE_DIR = Path(tempfile.gettempdir()) / "ulauncher-flathub-icons"
SCRIPT_DIR = Path(__file__).resolve().parent / "scripts"
SCRIPT_PATH = SCRIPT_DIR / "flatpak-helper.sh"
RESULTS_LIMIT_MIN = 2
RESULTS_LIMIT_DEFAULT = 6
RESULTS_LIMIT_MAX = 20
