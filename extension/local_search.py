import os
import subprocess

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from .utils import get_installed_actions


def find_icon(app_id, base_dir="/var/lib/flatpak/exports/share/icons"):
    if not os.path.exists(base_dir):
        return None

    extensions = ["svg", "png", "jpg"]

    for ext in extensions:
        try:
            result = subprocess.run(
                ["find", base_dir, "-name", f"{app_id}.{ext}", "-print", "-quit"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    return output

        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            continue

    return "images/icon.png"


def search_installed(query: str, result_limit: int) -> list[ExtensionResultItem]:
    result = subprocess.run(
        f"flatpak list --app --columns=name,application | fzf --with-nth=1 --delimiter='\t' --filter {query}",
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.stdout == "":
        return []

    lines: list[str] = result.stdout.strip().split("\n")[:result_limit]
    return [
        ExtensionResultItem(
            icon=find_icon(app_id),
            name=name,
            on_enter=RenderResultListAction(get_installed_actions(name, app_id)),
        )
        for name, app_id in map(lambda line: line.split("\t"), lines)
    ]
