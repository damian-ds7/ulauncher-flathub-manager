import logging
import subprocess

from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from .constants import SCRIPT_PATH
from .models import FlathubApp

logger = logging.getLogger(__name__)


def is_installed(app_id: str) -> bool:
    result = subprocess.run(
        ["flatpak", "info", app_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return not result.returncode


def get_installed_actions(name: str, app_id: str) -> list[ExtensionResultItem]:
    return [
        ExtensionResultItem(
            icon="images/update.jpg",
            name="Update",
            on_enter=RunScriptAction(f"{SCRIPT_PATH} update {app_id} {name}"),
        ),
        ExtensionResultItem(
            icon="images/remove.png",
            name="Uninstall",
            on_enter=RunScriptAction(f"{SCRIPT_PATH} uninstall {app_id} {name}"),
        ),
    ]


def get_not_installed_actions(name: str, app_id: str) -> list[ExtensionResultItem]:
    return [
        ExtensionResultItem(
            icon="images/download.jpg",
            name="Install",
            on_enter=RunScriptAction(f"{SCRIPT_PATH} install {app_id} {name}"),
        ),
        ExtensionResultItem(
            icon="images/icon.png",
            name="Open in browser",
            on_enter=OpenUrlAction(f"https://flathub.org/apps/{app_id}"),
        ),
    ]


def get_result_actions(app: FlathubApp) -> list[ExtensionResultItem]:
    if is_installed(app.flatpak_app_id):
        logger.info(f"Generating actions for installed app - {app.name}")
        return get_installed_actions(app.name, app.flatpak_app_id)
    else:
        logger.info(f"Generating actions for non-installed app - {app.name}")
        return get_not_installed_actions(app.name, app.flatpak_app_id)


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
