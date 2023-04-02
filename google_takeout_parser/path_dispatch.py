"""
This file loads and parses files according to a localized HandlerMap
"""

import os
import re
from pathlib import Path
from typing import (
    Iterator,
    Dict,
    Callable,
    Any,
    Optional,
    List,
    Type,
    Tuple,
    cast,
    Union
)

from collections import defaultdict

from cachew import cachew

from . import __version__ as _google_takeout_version
from .compat import Literal
from .common import Res, PathIsh

from .locales.common import HandlerMap
from .path_handler import (
    BaseResults,
    HandlerFunction,
    TakeoutFile,
    TAKEOUT_PARSER, # maps localized files to parser functions
    LocalizedHandler 
)



from .cache import takeout_cache_path
from .log import logger
from .models import BaseEvent


_CacheKeySingle = Type[BaseEvent]
CacheKey = _CacheKeySingle


def _cache_key_to_str(c: CacheKey) -> str:
    return str(c.__name__).casefold()


def _parse_handler_return_type(handler: HandlerFunction) -> CacheKey:
    assert hasattr(
        handler, "return_type"
    ), f"Handler functions should have an 'return_type' property which specifies what types this produces. See parse_json.py for an example. No 'return_type' on {handler}"
    val: Any = getattr(handler, "return_type")
    assert isinstance(val, type), f"{val} is not  a type"
    assert BaseEvent in val.__mro__, f"{val} not a subclass of BaseEvent"
    return cast(_CacheKeySingle, val)


HandlerMatch = Res[Optional[HandlerFunction]]

ErrorPolicy = Literal["yield", "raise", "drop"]

class TakeoutParser:
    def __init__(
        self,
        takeout_dir: PathIsh,
        cachew_identifier: Optional[str] = None,
        handlers: Union[HandlerMap, List[HandlerMap], None] = None,
        warn_exceptions: bool = True,
        error_policy: ErrorPolicy = "yield",
    ) -> None:
        """
        takeout_dir: Path to the google takeout directory
        cachew_identifier: some unique string that identifies this takeout
            If not given, approximates using the full path. Useful if you're
            temporarily extracting the zipfile to extract events or if the
            Takeout dir path isn't at its regular location
        handlers: 0-n handlers resolving Paths to a parser-functions.
            A handler can either resolve a string to a TakeoutFile or a callable.
            See path_handler/LocalizedHandler for predefined handlers.
            Default to LocalizedHandler.EN()
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
        
        # copy handler objects or set default handler
        self.handlers: List[HandlerMap] = []
        if isinstance(handlers, list):
            self.handlers: List[HandlerMap] = handlers
        elif isinstance(handlers, dict):
            self.handlers: List[HandlerMap] = [handlers]
        
        # triggers also at handlers == None 
        if(len(self.handlers) == 0):
            logger.warning(f"No handler specified. Fallback to EN handler.")
            self.handlers = [LocalizedHandler.EN()]

        self.error_policy: ErrorPolicy = error_policy
        self.warn_exceptions = warn_exceptions
        self._warn_if_no_activity()

    def _warn_if_no_activity(self) -> None:
        # most common is probably 'My Activity'?
        # can be used as a check to see if the user passed a wrong directory

        # TODO: extract activity_dir from selected DEFAULT_HANDLER_MAP
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
                # could be None, if chosen to ignore
                if h is None:
                    return None
                elif type(h) is TakeoutFile:
                    return TAKEOUT_PARSER[h] # resolve TakeoutFile to a parser function
                elif callable(h):
                    return h
                else:
                    RuntimeError(f"Parser for {sf} could not be resolved. You should map either to 'None', a callable or a TakeoutFile")
        else:
            return RuntimeError(f"No function to handle parsing {sf}")

    # TODO: cache? may run into issues though
    def dispatch_map(self) -> Dict[Path, HandlerFunction]:
        res: Dict[Path, HandlerFunction] = {}
        for f in self.takeout_dir.rglob("*"):
            if f.name.startswith("."):
                continue
            if not f.is_file():
                continue
            rf = f.relative_to(self.takeout_dir)

            # try to resolve file to parser-function by checking all supplied handlers
            
            # cache handler information for warning if we can't resolve the file
            file_resolved: bool = False
            last_handler: Exception = None

            for handler in self.handlers:
                file_handler: HandlerMatch = self.__class__._match_handler(
                    rf, handler
                )
                # file_handler matched something
                if not isinstance(file_handler, Exception):
                    # if not explicitly ignored by the handler map
                    if file_handler is not None:
                        res[f] = file_handler
                    file_resolved = True
                    continue

                last_handler = file_handler

            if not file_resolved:
                # this is an exception specifying an unhandled file
                # this shouldn't cause a fatal error, so don't check
                # error_policy here, just warn the user
                if self.warn_exceptions:
                    logger.warning(str(last_handler))

        return res

    def _log_handler(self, path: Path, handler: Any) -> None:
        """Log the path/function parsing it"""
        rel_path = str(path)[len(str(self.takeout_dir)) + 1 :]
        func_name: str = getattr(handler, "__name__", str(handler))
        logger.info(f"Parsing '{rel_path}' using '{func_name}'")

    def _parse_raw(self, filter_type: Optional[Type[BaseEvent]] = None) -> BaseResults:
        """Parse the takeout with no cache. If a filter is specified, only parses those files"""
        handlers = self._group_by_return_type(filter_type=filter_type)
        for cache_key, result_tuples in handlers.items():
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
            ckey: CacheKey = _parse_handler_return_type(handler)
            # don't include in the result if we're filtering to a specific type
            if filter_type is not None and ckey != filter_type:
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
            # Hmm -- I think this should work with CacheKeys that have multiple
            # types but it may fail -- need to check if one is added
            #
            # create a function which groups the iterators for this return type
            # that all gets stored in one database
            #
            # the return type here is purely for cachew, so it can infer the type
            def _func() -> Iterator[Res[cache_key]]:  # type: ignore[valid-type]
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
