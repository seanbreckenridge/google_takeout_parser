"""
This handles mapping the filenames in the export
to the corresponding functions and caching the results
"""

import os
import re
from pathlib import Path
from typing import (
    Iterator,
    Dict,
    Union,
    Callable,
    Any,
    Optional,
    List,
    Type,
    Tuple,
    Literal,
)

from collections import defaultdict

from cachew import cachew

from . import __version__ as _google_takeout_version
from .common import Res, PathIsh
from .cache import takeout_cache_path
from .log import logger
from .models import BaseEvent, get_union_args

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


# anything that subclasses BaseEvent
BaseResults = Iterator[Res[BaseEvent]]

HandlerFunction = Callable[[Path], BaseResults]
HandlerMap = Dict[str, Optional[HandlerFunction]]

CacheKey = Tuple[Type[BaseEvent], ...]


def _cache_key_to_str(c: CacheKey) -> str:
    """Convert a cache key to a string"""
    return "_".join(sorted(p.__name__ for p in c)).casefold()


def _handler_type_cache_key(handler: HandlerFunction) -> CacheKey:
    # Take a function like Iterator[Union[Item, Exception]] and return Item

    import inspect

    sig = inspect.signature(handler)

    # get the return type of the function
    # e.g. Iterator[Union[Item, Exception]]
    return_type = sig.return_annotation

    # this must have a return type
    if return_type == inspect.Signature.empty:
        raise TypeError(f"Could not get return type for {handler.__name__}")

    # remove top-level iterator if it has it
    if return_type._name == "Iterator":
        return_type = return_type.__args__[0]

    args: Optional[Tuple[Type]] = get_union_args(return_type)  # type: ignore[type-arg]
    if args is None:
        raise TypeError(
            f"Could not get union args for {return_type} in {handler.__name__}"
        )

    # remove exceptions
    t_args = tuple(t for t in args if t != Exception)

    for t in t_args:
        if BaseEvent not in t.__mro__:
            raise TypeError(
                f"Return type {t} from {return_type} of {handler.__name__} does not contain BaseEvent"
            )
        if t == BaseEvent:
            raise TypeError(
                f"Return type {t} from {return_type} of {handler.__name__} is BaseEvent, which is not allowed"
            )

    return tuple(t_args)


def _cache_key_to_type(c: CacheKey) -> Any:
    """
    If there's one item in the cache key, return that
    If there's multiple, return a Union of them
    """
    assert len(c) > 0
    if len(c) == 1:
        return c[0]
    else:
        assert isinstance(c, tuple)

        return Union[c]  # type: ignore[valid-type]


# If parsed, should mention:
# Google Help Communities
#   - Select JSON as Output
# Google Play Books
#   - Select JSON as Output
# Google Play Games Services
#   - Select JSON as Output
# Google Play Movies & TV options
#   - Select JSON as Output
# Profile
#   - Select JSON as Output


# Note: when I say 'no info here' or 'not useful', is just how the
# data appears in my export. It might be useful for you -- if so
# feel free to make a PR or an issue to parse it
#
# Can also extend or overwrite these functions by passing
# 'None' if you don't want a certain part to be parsed,
# or by passing your own function which parses the file something from models.py

# Reminder that dicts are ordered, so order here can matter
# If you want to parse one file from a folder with lot of files, can
# specify that file, and then on the next line specify 'None'
# for the folder, ignoring the rest of files

# Setting 'None' in the handler map specifies that we should ignore this file
DEFAULT_HANDLER_MAP: HandlerMap = {
    r"Chrome/BrowserHistory.json": _parse_chrome_history,
    r"Chrome": None,  # Ignore rest of Chrome stuff
    r"Google Play Store/Installs.json": _parse_app_installs,
    r"Google Play Store/": None,  # ignore anything else in Play Store
    r"Location History/Semantic Location History/.*/.*.json": _parse_semantic_location_history,
    # optional space to handle pre-2017 data
    r"Location History/Location( )?History.json": _parse_location_history,  # old path to Location History
    r"Location History/Records.json": _parse_location_history,  # new path to Location History
    r"Location History/Settings.json": None,
    # HTML/JSON activity-like files which aren't in 'My Activity'
    # optional " and Youtube Music" to handle pre-2017 data
    r"YouTube( and YouTube Music)?/history/.*?.html": _parse_html_activity,
    r"YouTube( and YouTube Music)?/history/.*?.json": _parse_json_activity,
    # basic list item files which have chat messages/comments
    r"YouTube( and YouTube Music)?/my-comments/.*?.html": _parse_html_comment_file,
    r"YouTube( and YouTube Music)?/my-live-chat-messages/.*?.html": _parse_html_comment_file,
    r"YouTube( and YouTube Music)?/playlists/likes.json": _parse_likes,
    r"YouTube( and YouTube Music)?/playlists/": None,
    r"YouTube( and YouTube Music)?/subscriptions": None,
    r"YouTube( and YouTube Music)?/videos": None,
    r"YouTube( and YouTube Music)?/music-uploads": None,
    r"My Activity/Assistant/.*.mp3": None,  # might be interesting to extract timestamps
    r"My Activity/Voice and Audio/.*.mp3": None,
    r"My Activity/Takeout": None,  # activity for when you made takeouts, dont need
    # HTML 'My Activity' Files
    # the \d+ is for split html files, see the ./split_html directory
    r"My Activity/.*?My\s*Activity(-\d+)?.html": _parse_html_activity,
    r"My Activity/.*?My\s*Activity.json": _parse_json_activity,
    # Maybe parse these?
    r"Access Log Activity": None,
    r"Assistant Notes and Lists/.*.csv": None,
    r"Blogger/Comments/.*?feed.atom": None,
    r"Blogger/Blogs/": None,
    # Fit has possibly interesting data
    # Fit/Daily activity metrics/2015-07-27.csv
    # Fit/Activities/2017-10-29T23_08_59Z_PT2M5.699S_Other.tcx
    # Fit/All Data/derived_com.google.calories.bmr_com.google.and.json
    r"Fit/": None,
    r"Groups": None,
    r"Google Play Games Services/Games/.*/(Achievements|Activity|Experience|Scores).html": None,
    r"Hangouts": None,
    r"Keep": None,
    r"Maps (your places)": None,
    r"My Maps/.*.kmz": None,  # custom KML maps
    r"Saved/.*.csv": None,  # lists with saved places from Google Maps
    r"Shopping Lists/.*.csv": None,
    r"Tasks": None,
    # Files to ignore
    r"Android Device Configuration Service/": None,
    r"Blogger/Albums/": None,
    r"Blogger/Profile/": None,
    r"Calendar/": None,
    r"Cloud Print/": None,
    r"Contacts/": None,
    r"Drive/": None,
    r"Google Account/": None,
    r"Google Business Profile/": None,
    r"Google My Business/": None,
    r"Google Pay/": None,
    r"Google Photos/": None,  # has images/some metadata on each of them
    r"Google Play Books/.*.pdf": None,
    r"Google Play Games Services/Games/.*/(Data.bin|Metadata.html)": None,
    r"Google Play Movies.*?/": None,
    r"Google Shopping/": None,
    r"Google Store/": None,
    r"Google Translator Toolkit/": None,
    r"Google Workspace Marketplace/": None,
    r"Home App/": None,
    r"Mail/": None,
    r"Maps/": None,
    r"News/": None,
    r"Profile/Profile.json": None,
    r"Saved/Favorite places.csv": None,
    r"Search Contributions/": None,
    r"archive_browser.html": None,  # description of takeout, not that useful
}

HandlerMatch = Res[Optional[HandlerFunction]]

ErrorPolicy = Literal["yield", "raise", "drop"]


class TakeoutParser:
    def __init__(
        self,
        takeout_dir: PathIsh,
        cachew_identifier: Optional[str] = None,
        warn_exceptions: bool = True,
        error_policy: ErrorPolicy = "yield",
        additional_handlers: Optional[HandlerMap] = None,
    ) -> None:
        """
        takeout_dir: Path to the google takeout directory
        cachew_identifier: some unique string that identifies this takeout
            If not given, approximates using the full path. Useful if you're
            temporarily extracting the zipfile to extract events or if the
            Takeout dir path isn't at its regular location
        error_policy: How to handle exceptions while parsing:
            "yield": return as part of the results (default)
            "raise": raise exceptions
            "drop": drop/ignore exceptions
        """
        # isinstance check to avoid messing up objects which mimic Path (e.g. zip wrappers)
        takeout_dir = (
            takeout_dir if isinstance(takeout_dir, Path) else Path(takeout_dir)
        )
        self.takeout_dir = takeout_dir.absolute()
        if not self.takeout_dir.exists():
            raise FileNotFoundError(f"{self.takeout_dir} does not exist!")
        self.cachew_identifier: Optional[str] = cachew_identifier
        self.additional_handlers = (
            {} if additional_handlers is None else additional_handlers
        )
        self.error_policy: ErrorPolicy = error_policy
        self.warn_exceptions = warn_exceptions
        self._warn_if_no_activity()

    def _warn_if_no_activity(self) -> None:
        # most common is probably 'My Activity'?
        # can be used as a check to see if the user passed a wrong directory
        activity_dir = "My Activity"
        expected = self.takeout_dir / activity_dir
        if not expected.exists():
            logger.warning(
                f"Warning: given '{self.takeout_dir}', expected the '{activity_dir}' directory at '{expected}'. Perhaps you passed the wrong location?"
            )

    @staticmethod
    def _match_handler(p: Path, handler: HandlerMap) -> HandlerMatch:
        """
        Match one of the handler regexes to a function which parses the file
        """
        assert not p.is_absolute(), p  # should be relative to Takeout dir
        # replace OS-specific (e.g. windows) path separator to match the handler
        sf = str(p).replace(os.sep, "/")
        for prefix, h in handler.items():
            # regex match the map (e.g. above)
            if bool(re.match(prefix, sf)):
                return h  # could be None, if chosen to ignore
        else:
            return RuntimeError(f"No function to handle parsing {sf}")

    # TODO: cache? may run into issues though
    def dispatch_map(self) -> Dict[Path, HandlerFunction]:
        res: Dict[Path, HandlerFunction] = {}
        for f in sorted(self.takeout_dir.rglob("*")):
            if f.name.startswith("."):
                continue
            if not f.is_file():
                continue
            rf = f.relative_to(self.takeout_dir)

            # if user overrode some function, use that
            user_handler: HandlerMatch = self.__class__._match_handler(
                rf, self.additional_handlers
            )
            # user handler matched something
            if not isinstance(user_handler, Exception):
                # if not explicitly ignored by the handler map
                if user_handler is not None:
                    res[f] = user_handler
                continue

            # don't raise errors here since the DEFAULT_HANDLER_MAP may handle parsing it

            # try the default matchers
            def_handler: HandlerMatch = self.__class__._match_handler(
                rf, DEFAULT_HANDLER_MAP
            )
            # default handler
            if not isinstance(def_handler, Exception):
                # if not explicitly ignored by the handler map
                if def_handler is not None:
                    res[f] = def_handler
                continue
            else:
                # this is an exception specifying an unhandled file
                # this shouldn't cause a fatal error, so don't check
                # error_policy here, just warn the user
                if self.warn_exceptions:
                    logger.warning(str(def_handler))

        return res

    def _log_handler(self, path: Path, handler: Any) -> None:
        """Log the path/function parsing it"""
        rel_path = str(path)[len(str(self.takeout_dir)) + 1 :]
        func_name: str = getattr(handler, "__name__", str(handler))
        logger.info(f"Parsing '{rel_path}' using '{func_name}'")

    def _parse_raw(self, filter_type: Optional[Type[BaseEvent]] = None) -> BaseResults:
        """Parse the takeout with no cache. If a filter is specified, only parses those files"""
        handlers = self._group_by_return_type(filter_type=filter_type)
        for _, result_tuples in handlers.items():
            for path, itr in result_tuples:
                self._log_handler(path, itr)
                yield from itr

    def _handle_errors(self, results: BaseResults) -> BaseResults:
        """Wrap the results and handle any errors according to the policy"""
        for e in results:
            if not isinstance(e, Exception):
                yield e
            else:
                if self.warn_exceptions:
                    logger.warning(str(e))
                # return errors as part of the result, default
                if self.error_policy == "yield":
                    yield e
                # raise errors; crash
                elif self.error_policy == "raise":
                    raise e
                # ignore errors
                elif self.error_policy == "drop":
                    continue

    def parse(
        self, cache: bool = False, filter_type: Optional[Type[BaseEvent]] = None
    ) -> BaseResults:
        """
        Parses the Takeout

        if cache is True, using cachew to cache the results
        if filter_type is given, only parses the files which have that type
        """
        if not cache:
            yield from self._handle_errors(self._parse_raw(filter_type=filter_type))
        else:
            yield from self._handle_errors(self._cached_parse(filter_type=filter_type))

    def _group_by_return_type(
        self, filter_type: Optional[Type[BaseEvent]] = None
    ) -> Dict[CacheKey, List[Tuple[Path, BaseResults]]]:
        """
        Groups the dispatch_map by output model type
        If filter_type is provided, only returns that Model

        e.g.:

        Activity -> [
            (filepath, iterator that produces activity)
            (filepath, iterator that produces activity),
            (filepath, iterator that produces activity),
        ]
        """
        handlers: Dict[CacheKey, List[Tuple[Path, BaseResults]]] = defaultdict(list)
        for path, handler in self.dispatch_map().items():
            ckey: CacheKey = _handler_type_cache_key(handler)
            # don't include in the result if we're filtering to a specific type
            if filter_type is not None and filter_type not in ckey:
                logger.debug(
                    f"Provided '{filter_type}' as filter, '{ckey}' doesn't match, ignoring '{path}'..."
                )
                continue
            # call the function -- since the parsers are all generators,
            # this doesn't run here, it just waits till its consumed
            handlers[ckey].append((path, handler(path)))
        return dict(handlers)

    def _depends_on(self) -> str:
        """
        basename of all files in the takeout directory + google_takeout_version version
        """
        file_index: List[str] = list(
            sorted([str(p.name) for p in self.takeout_dir.rglob("*")])
        )
        # store version at the beginning of hash
        # if pip version changes, invalidates old results and re-computes
        file_index.insert(0, f"google_takeout_version: {_google_takeout_version}")
        return str(file_index)

    def _determine_cache_path(self, cache_key: CacheKey) -> str:
        """
        Create the unique cachew database path for this TakeoutParser instance
        """
        base = takeout_cache_path
        part: str
        if self.cachew_identifier is not None:
            part = self.cachew_identifier
        else:
            # use a full-ish path of the takeout dir to create a unique identifier
            part = os.path.join(*self.takeout_dir.parts[1:])
        return str(base / part / _cache_key_to_str(cache_key))

    def _cached_parse(
        self, filter_type: Optional[Type[BaseEvent]] = None
    ) -> BaseResults:
        handlers = self._group_by_return_type(filter_type=filter_type)
        for cache_key, result_tuples in handlers.items():
            _ret_type: Any = _cache_key_to_type(cache_key)

            def _func() -> Iterator[Res[_ret_type]]:  # type: ignore[valid-type]
                for path, itr in result_tuples:
                    self._log_handler(path, itr)
                    yield from itr

            cached_itr: Callable[[], BaseResults] = cachew(
                depends_on=lambda: self._depends_on(),
                cache_path=lambda: self._determine_cache_path(cache_key),
                force_file=True,
                logger=logger,
            )(_func)

            yield from cached_itr()
