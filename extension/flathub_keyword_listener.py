import threading
from typing import Optional

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.Response import Response

from .api import search_flathub
from .constants import RESULTS_LIMIT_DEFAULT, RESULTS_LIMIT_MAX, RESULTS_LIMIT_MIN
from .models import FlathubApp, ShortQueryException
from .utils import flathub_app_2_result_item


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
