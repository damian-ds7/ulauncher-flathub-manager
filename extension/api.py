import json
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from .icons import download_icon
from .models import FlathubApp, ShortQueryException

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=6)


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
