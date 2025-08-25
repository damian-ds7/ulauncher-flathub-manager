import json
import logging
import urllib.request
from dataclasses import dataclass
from typing import Optional

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

RESULTS_LIMIT_MIN = 2
RESULTS_LIMIT_DEFAULT = 6
RESULTS_LIMIT_MAX = 20


class ShortQueryException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


logger = logging.getLogger(__name__)


@dataclass
class FlathubApp:
    flatpak_app_id: str
    name: str
    icon_desktop_url: str

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
                return FlathubApp.from_list(data[:results_limit])
            return []
    except Exception as e:
        logger.error(f"Something went wrong {e}")
        return []


def flathub_app_2_result_item(apps: list[FlathubApp]) -> list[ExtensionResultItem]:
    items: list[ExtensionResultItem] = []
    logger.info("Creating entry list")
    for app in apps:
        logger.info(f"Adding {app.name} entry")
        items.append(
            ExtensionResultItem(
                icon="images/icon.png",
                name=app.name,
                on_enter=HideWindowAction(),
            )
        )
    logger.info("Extension result items created")
    logger.info(items)
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
