import hashlib
import json
import logging
import os
import subprocess
import tempfile
import threading
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.Response import Response

ICON_CACHE_DIR = os.path.join(tempfile.gettempdir(), "ulauncher-flathub-icons")
RESULTS_LIMIT_MIN = 2
RESULTS_LIMIT_DEFAULT = 6
RESULTS_LIMIT_MAX = 20
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(SCRIPT_DIR, "flatpak-helper.sh")
DEBOUNCE_DELAY = 0.3  # 300ms debounce delay

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=6)


class ShortQueryException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class FlathubApp:
    flatpak_app_id: str
    name: str
    icon_desktop_url: str
    icon_future: Optional[Future] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional["FlathubApp"]:
        try:
            return cls(
                flatpak_app_id=data["flatpakAppId"],
                name=data["name"],
                icon_desktop_url=data["iconDesktopUrl"],
            )
        except KeyError:
            return None

    @classmethod
    def from_list(cls, data_list: list[dict[str, str]]) -> list["FlathubApp"]:
        return [app for item in data_list if (app := cls.from_dict(item)) is not None]


def icon_path(url: str) -> str:
    os.makedirs(ICON_CACHE_DIR, exist_ok=True)
    fname = hashlib.sha256(url.encode()).hexdigest() + ".png"
    return os.path.join(ICON_CACHE_DIR, fname)


def download_icon(url: str, timeout: int = 5) -> str:
    path = icon_path(url)
    if not os.path.exists(path):
        try:
            r = requests.get(url, timeout=timeout)
            if r.ok:
                with open(path, "wb") as f:
                    f.write(r.content)
        except Exception:
            return "images/icon.png"  # fallback if request fails
    return path


def search_flathub(
    query: str, results_limit: int, timeout: int = 5
) -> list[FlathubApp]:
    if len(query) < 2:
        raise ShortQueryException

    url: str = f"https://flathub.org/api/v2/compat/apps/search/{query}"

    logger.info(f"Fetching results with params {query=}, {results_limit=}")

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                data: list[dict[str, str]] = json.loads(response.read())
                apps = FlathubApp.from_list(data[:results_limit])
                for app in apps:
                    app.icon_future = executor.submit(
                        download_icon, app.icon_desktop_url
                    )
                return apps

            return []
    except Exception as e:
        logger.error(f"Something went wrong {e}")
        return []


def is_installed(app_id: str) -> bool:
    result = subprocess.run(
        ["flatpak", "info", app_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return not result.returncode


def get_result_actions(app: FlathubApp) -> list[ExtensionResultItem]:
    if is_installed(app.flatpak_app_id):
        logger.info(f"Generating actions for installed app - {app.name}")
        return [
            ExtensionResultItem(
                icon="images/update.jpg",
                name="Update",
                on_enter=RunScriptAction(
                    f"{SCRIPT_PATH} update {app.flatpak_app_id} {app.name}"
                ),
            ),
            ExtensionResultItem(
                icon="images/remove.png",
                name="Uninstall",
                on_enter=RunScriptAction(
                    f"{SCRIPT_PATH} uninstall {app.flatpak_app_id} {app.name}"
                ),
            ),
        ]
    else:
        logger.info(f"Generating actions for non-installed app - {app.name}")
        return [
            ExtensionResultItem(
                icon="images/download.jpg",
                name="Install",
                on_enter=RunScriptAction(
                    f"{SCRIPT_PATH} install {app.flatpak_app_id} {app.name}"
                ),
            ),
            ExtensionResultItem(
                icon="images/icon.png",
                name="Open in browser",
                on_enter=OpenUrlAction(
                    f"https://flathub.org/apps/{app.flatpak_app_id}"
                ),
            ),
        ]


def flathub_app_2_result_item(apps: list[FlathubApp]) -> list[ExtensionResultItem]:
    items: list[ExtensionResultItem] = []
    for app in apps:
        icon = "images/icon.png"
        if app.icon_future:
            try:
                icon = app.icon_future.result(timeout=0.1)
            except Exception:
                pass
        items.append(
            ExtensionResultItem(
                icon=icon,
                name=app.name,
                on_enter=RenderResultListAction(get_result_actions(app)),
            )
        )
    return items


class FlathubSearchExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, FlathubSearchKeywordListener())


class FlathubSearchKeywordListener(EventListener):
    def __init__(self):
        super().__init__()
        self._debounce_timer: Optional[threading.Timer] = None
        self._debounce_delay: float = 1

    def _run_search(self, extension, event, query: str, results_limit: int):
        items: list[ExtensionResultItem] = []
        try:
            search_results: list[FlathubApp] = search_flathub(query, results_limit)
            items = flathub_app_2_result_item(search_results)
        except ShortQueryException:
            items.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Enter at least 2 characters to search",
                    on_enter=HideWindowAction(),
                )
            )
        extension._client.send(Response(event, RenderResultListAction(items)))

    def on_event(self, event, extension):
        query: str = (
            event.get_argument().replace("%", "") if event.get_argument() else ""
        )

        results_limit_str: str = extension.preferences["results_limit"]
        try:
            results_limit = int(results_limit_str.strip())
            results_limit = max(
                min(results_limit, RESULTS_LIMIT_MAX), RESULTS_LIMIT_MIN
            )
        except Exception:
            results_limit = RESULTS_LIMIT_DEFAULT

        if self._debounce_timer and self._debounce_timer.is_alive():
            self._debounce_timer.cancel()

        self._debounce_timer = threading.Timer(
            self._debounce_delay,
            self._run_search,
            args=(extension, event, query, results_limit),
        )
        self._debounce_timer.start()

        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Searching...",
                    on_enter=HideWindowAction(),
                )
            ]
        )


if __name__ == "__main__":
    FlathubSearchExtension().run()
