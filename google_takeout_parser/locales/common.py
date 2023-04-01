"""
This file defines general takout-files.
locale HandlerMaps should match strings against these files to allow auto-parser selection.
Parsers are mapped in google_takeout_parser/path_handler.py
"""

from enum import Enum, auto
from typing import (
    Dict,
    Optional
)

class TakeoutFile(Enum):
    CHROME_HISTORY = auto(),
    GPLAYSTORE_INSTALLS = auto(),
    LOCATION_HISTORY = auto(),
    LOCATION_HISTORY_SEMANTIC = auto(),
    YOUTUBE_HISTORY_HTML = auto(),
    YOUTUBE_HISTORY_JSON = auto(),
    YOUTUBE_COMMENT = auto(),
    YOUTUBE_COMMENT_LIVECHAT = auto(),
    YOUTUBE_LIKES = auto(),
    # Parent Folder "My Activity"
    ACTIVITY_HTML = auto(),
    ACTIVITY_JSON = auto()

HandlerMap = Dict[str, Optional[TakeoutFile]]