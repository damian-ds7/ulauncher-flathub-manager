from concurrent.futures import Future
from dataclasses import dataclass
from typing import Optional


class ShortQueryException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class FlathubApp:
    app_id: str
    name: str
    icon_url: str
    icon_future: Optional[Future] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional["FlathubApp"]:
        try:
            return cls(
                app_id=data["flatpakAppId"],
                name=data["name"],
                icon_url=data["iconDesktopUrl"],
            )
        except KeyError:
            return None

    @classmethod
    def from_list(cls, data_list: list[dict[str, str]]) -> list["FlathubApp"]:
        return [app for item in data_list if (app := cls.from_dict(item)) is not None]
