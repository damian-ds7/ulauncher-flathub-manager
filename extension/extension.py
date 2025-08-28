from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent

from .flathub_keyword_listener import FlathubSearchKeywordListener
from .local_search_keyword_listener import LocalSearchKeywordListener


class FlathubSearchExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, FlathubSearchKeywordListener())
        self.subscribe(KeywordQueryEvent, LocalSearchKeywordListener())
