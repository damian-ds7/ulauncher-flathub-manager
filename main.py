import hashlib
import json
import logging
import os
import tempfile
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

ICON_CACHE_DIR = os.path.join(tempfile.gettempdir(), "ulauncher-flathub-icons")
RESULTS_LIMIT_MIN = 2
RESULTS_LIMIT_DEFAULT = 6
RESULTS_LIMIT_MAX = 20

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


def fetch_icons_parallel(apps: list[FlathubApp]) -> dict[str, str]:
    with ThreadPoolExecutor(max_workers=6) as executor:
        return {
            app.icon_desktop_url: path
            for app, path in zip(
                apps, executor.map(lambda a: download_icon(a.icon_desktop_url), apps)
            )
        }


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


def flathub_app_2_result_item(apps: list[FlathubApp]) -> list[ExtensionResultItem]:
    items: list[ExtensionResultItem] = []
    for app in apps:
        local_icon = "images/icon.png"
        if app.icon_future:
            try:
                local_icon = app.icon_future.result(timeout=0.1)  # short wait
            except Exception:
                pass
        items.append(
            ExtensionResultItem(
                icon=local_icon,
                name=app.name,
                on_enter=HideWindowAction(),
            )
        )
    return items


class FlathubSearchExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items: list[ExtensionResultItem] = []
        query: Optional[str] = (
            event.get_argument().replace("%", "") if event.get_argument() else ""
        )

        results_limit_str: str = extension.preferences["results_limit"]
        results_limit: int

        try:
            results_limit_str = results_limit_str.strip()
            results_limit = int(results_limit_str)

            if results_limit < RESULTS_LIMIT_MIN:
                results_limit = RESULTS_LIMIT_MIN
            elif results_limit > RESULTS_LIMIT_MAX:
                results_limit = RESULTS_LIMIT_MAX
        except Exception as e:
            results_limit = RESULTS_LIMIT_DEFAULT

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

        return RenderResultListAction(items)


if __name__ == "__main__":
    FlathubSearchExtension().run()
