"""
This file maps implemented parser to takout-files.
It also supplies the LocalizedHandler which allows localized takout-file mapping 
"""

from pathlib import Path
from typing import (
    Iterator,
    Callable,
    Optional,
    Dict
)
from .common import Res
from .models import BaseEvent
from .locales.common import TakeoutFile, HandlerMap

# anything that subclasses BaseEvent
BaseResults = Iterator[Res[BaseEvent]]

HandlerFunction = Callable[[Path], BaseResults]
ParserMap = Dict[str, Optional[HandlerFunction]]

# Link TakeoutFiles to a parser
from .parse_html.activity import _parse_html_activity
from .parse_html.comment import _parse_html_comment_file
from .parse_json import (
    _parse_likes,
    _parse_app_installs,
    _parse_json_activity,
    _parse_location_history,
    _parse_semantic_location_history,
    _parse_chrome_history,
)

TAKEOUT_PARSER : ParserMap = {
    TakeoutFile.CHROME_HISTORY: _parse_chrome_history,
    TakeoutFile.GPLAYSTORE_INSTALLS: _parse_app_installs,
    TakeoutFile.LOCATION_HISTORY_SEMANTIC: _parse_semantic_location_history,
    TakeoutFile.LOCATION_HISTORY: _parse_location_history,
    TakeoutFile.YOUTUBE_HISTORY_HTML: _parse_html_activity,
    TakeoutFile.YOUTUBE_HISTORY_JSON: _parse_json_activity,
    TakeoutFile.YOUTUBE_COMMENT: _parse_html_comment_file,
    TakeoutFile.YOUTUBE_COMMENT_LIVECHAT: _parse_html_comment_file,
    TakeoutFile.YOUTUBE_LIKES: _parse_likes,
    TakeoutFile.ACTIVITY_HTML: _parse_html_activity,
    TakeoutFile.ACTIVITY_JSON: _parse_json_activity
}


# collect all localized handlers into one object
from .locales.en import HANDLER_MAP as hmap_en
from .locales.de import HANDLER_MAP as hmap_de

class LocalizedHandler:
    
    # static methods resolving to a localized HandlerMap
    def EN() -> HandlerMap:
        return hmap_en
    

    def DE() -> HandlerMap:
        return hmap_de
    