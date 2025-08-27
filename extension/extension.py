from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent

from .flathub_keyword_listener import FlathubSearchKeywordListener


class FlathubSearchExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, FlathubSearchKeywordListener())
