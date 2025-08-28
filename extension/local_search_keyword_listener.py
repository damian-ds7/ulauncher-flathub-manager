from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from .constants import RESULTS_LIMIT_DEFAULT, RESULTS_LIMIT_MAX, RESULTS_LIMIT_MIN
from .local_search import search_installed


class LocalSearchKeywordListener(EventListener):
    def __init__(self) -> None:
        super().__init__()

    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences["local_kw"]:
            return

        query: str = (
            event.get_argument().replace("%", "") if event.get_argument() else ""
        )

        if query == "":
            return []

        results_limit_str: str = extension.preferences["results_limit"]
        try:
            results_limit = int(results_limit_str.strip())
            results_limit = max(
                min(results_limit, RESULTS_LIMIT_MAX), RESULTS_LIMIT_MIN
            )
        except Exception:
            results_limit = RESULTS_LIMIT_DEFAULT

        return RenderResultListAction(search_installed(query, results_limit))
