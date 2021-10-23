"""
This handles mapping the filenames in the export
to the corresponding functions
"""

import os
import re
from pathlib import Path
from typing import Iterator, Dict, Callable, Optional, List

from cachew import cachew

from .common import Res
from .cache import takeout_cache_path
from .log import logger

from .models import Event

from .parse_html.activity import _parse_html_activity
from .parse_html.comment import _parse_html_comment_file
from .parse_json import (
    _parse_likes,
    _parse_app_installs,
    _parse_json_activity,
    _parse_location_history,
    _parse_chrome_history,
)


Results = Iterator[Res[Event]]

HandlerFunction = Callable[[Path], Results]
HandlerMap = Dict[str, Optional[HandlerFunction]]


# Note: when I say 'no info here' or 'not useful', is just how the
# data appears in my export. It might be useful for you -- if so
# feel free to make a PR or an issue to parse it
#
# Can also extend or overwrite these functions by passing
# 'None' if you don't want a certain part to be parsed,
# or by passing your own function which parses the file into Results

# Setting 'None' in the handler map specifies that we should ignore this file
DEFAULT_HANDLER_MAP: HandlerMap = {
    "Chrome/BrowserHistory\.json": _parse_chrome_history,
    "Chrome": None,  # Ignore rest of Chrome stuff
    "Google Photos": None,  # has images/some metadata on each of them
    "archive_browser.html": None,  # description of takeout, not that useful
    "Google Play Store/Installs.json": _parse_app_installs,
    "Google Play Store/": None,  # ignore anything else in Play Store
    "YouTube and YouTube Music/subscriptions": None,  # TODO: parse
    "YouTube and YouTube Music/videos": None,
    "Location History/Semantic Location History": None,  # not that much data here. maybe parse it?
    "Location History/Location History.json": _parse_location_history,
    # HTML/JSON activity-like files which aren't in 'My Activity'
    "YouTube and YouTube Music/history/.*?.html": _parse_html_activity,
    "YouTube and YouTube Music/history/.*?.json": _parse_json_activity,
    # basic list item files which have chat messages/comments
    "YouTube and YouTube Music/my-comments/.*?\.html": _parse_html_comment_file,
    "YouTube and YouTube Music/my-live-chat-messages/.*?\.html": _parse_html_comment_file,
    "YouTube and YouTube Music/playlists/likes.json": _parse_likes,
    "YouTube and YouTube Music/playlists/": None,  # dicts are ordered, so the rest of the stuff is ignored
    "My Activity/Takeout": None,  # activity for when you made takeouts, dont need
    # HTML 'My Activity' Files
    r"My Activity/.*?My\s*Activity.html": _parse_html_activity,
    r"My Activity/.*?My\s*Activity.json": _parse_json_activity,
}

HandlerMatch = Res[Optional[HandlerFunction]]


class TakeoutParser:
    def __init__(
        self,
        takeout_dir: Path,
        cachew_identifier: Optional[str] = None,
        warn_exceptions: bool = True,
        raise_exceptions: bool = False,
        drop_exceptions: bool = False,
        additional_handlers: Optional[HandlerMap] = None,
    ) -> None:
        """
        takeout_dir: Path to the google takeout directory
        cachew_identifier: some unique string that identifies this takeout
            If not given, approximates using the full path. Useful if you're
            temporarily extracting the zipfile to extract events or if the
            Takeout dir path isn't at its regular location
        """
        self.takeout_dir = takeout_dir.absolute()
        self.cachew_identifier: Optional[str] = cachew_identifier
        self.additional_handlers = (
            {} if additional_handlers is None else additional_handlers
        )
        self.raise_exceptions = raise_exceptions
        self.warn_exceptions = warn_exceptions
        self.drop_exceptions = drop_exceptions

    def _warn_if_no_activity(self) -> None:
        # most common is probably 'My Activity'?
        # can be used as a check to see if the user passed a wrong directory
        expected = self.takeout_dir / "My Activity"
        if not expected.exists():
            logger.warning(
                f"Warning: given {self.takeout_dir}, expected a directory at {expected}"
            )

    @staticmethod
    def _match_handler(p: Path, handler: HandlerMap) -> HandlerMatch:
        """
        Match one of the handler regexes to a function which parses the file
        """
        sf = str(p)
        for prefix, h in handler.items():
            # regex match the map (e.g. above)
            if bool(re.search(prefix, sf)):
                return h  # could be None, if chosen to ignore
        else:
            return RuntimeError(f"No function to handle parsing {sf}")

    def dispatch_map(self) -> Dict[Path, HandlerFunction]:
        res: Dict[Path, HandlerFunction] = {}
        for f in self.takeout_dir.rglob("*"):
            if f.name.startswith("."):
                continue
            if not f.is_file():
                continue

            # if user overrode some function, use that
            user_handler: HandlerMatch = self.__class__._match_handler(
                f, self.additional_handlers
            )
            # user handler matched something
            if not isinstance(user_handler, Exception):
                # if not explicitly ignored by the handler map
                if user_handler is not None:
                    res[f] = user_handler
                continue

            # try the default matchers
            def_handler: HandlerMatch = self.__class__._match_handler(
                f, DEFAULT_HANDLER_MAP
            )
            # default handler
            if not isinstance(def_handler, Exception):
                # if not explicitly ignored by the handler map
                if def_handler is not None:
                    res[f] = def_handler
                continue
            else:
                # is an exception
                if self.raise_exceptions:
                    raise def_handler
                elif self.warn_exceptions:
                    logger.warning(str(def_handler))

        return res

    def parse_raw(self) -> Results:
        """
        Parse the entire Takeout -- no cache
        """

        for f, handler in self.dispatch_map().items():
            yield from handler(f)

    def parse(self) -> Results:
        """
        Wrap the raw parse and check if we should warn or raise exceptions
        """
        for r in self.parse_raw():
            if isinstance(r, Exception):
                if self.raise_exceptions:
                    raise r
                else:
                    if self.warn_exceptions:
                        logger.warning(str(r))
                    if self.drop_exceptions:
                        continue
                    # use didn't specify to raise or drop, so return
                    # exceptions as part of the result
                    yield r
            else:
                # some NT/result, return as normal
                yield r

    @staticmethod
    def _depends_on(instance: "TakeoutParser") -> List[str]:
        return list(sorted([str(p.name) for p in instance.takeout_dir.rglob("*")]))

    @staticmethod
    def _determine_cache_path(instance: "TakeoutParser") -> str:
        """
        Create the unique cachew database path for this TakeoutParser instance
        """
        base = takeout_cache_path
        part: str
        if instance.cachew_identifier is not None:
            part = instance.cachew_identifier
        else:
            # use a full-ish path of the takeout dir to create a unique identifier
            part = os.path.join(*instance.takeout_dir.parts[1:])
        return str(base / part)

    # passes self to the cachew depends_on/cache_path functions
    @cachew(
        depends_on=lambda s: TakeoutParser._depends_on(s),
        cache_path=lambda s: TakeoutParser._determine_cache_path(s),
        logger=logger,
    )
    def cached_parse(self) -> Results:
        yield from self.parse()
