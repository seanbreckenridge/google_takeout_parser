"""
Helper module to remove duplicate events when combining takeouts
"""

from pathlib import Path
from itertools import chain
from typing import Set, Tuple, List, Any

from cachew import cachew

from .path_dispatch import Results, TakeoutParser
from .log import logger
from .cache import takeout_cache_path
from .models import Event

# hmm -- feel there are too many usecases to support
# everything here, so just need to document this a bit
# so is obvious how to use
#
# else Im just duplicating code that would exist in HPI anyways


# Note: only used for this module, HPI caches elsewhere
@cachew(
    cache_path=lambda _p: str(takeout_cache_path / "_merged_takeouts"),
    depends_on=lambda pths: list(sorted([str(p) for p in pths])),
    force_file=True,
    logger=logger,
)
def cached_merge_takeouts(takeout_paths: List[Path]) -> Results:
    """
    Cached version of merge events, merges each of these into one cachew database

    Additional arguments are passed to TakeoutParser constructor

    If your takeout directory was something like:

    $ /bin/ls ~/data/google_takeout -1
    Takeout-1599315526
    Takeout-1599728222
    Takeout-1616796262

    takeout_paths would be:
    [PosixPath('Takeout-1599315526'), PosixPath('Takeout-1616796262'), PosixPath('Takeout-1599728222')]
    """
    itrs: List[Results] = []
    for pth in takeout_paths:
        itrs.append(TakeoutParser(pth).cached_parse())
    yield from merge_events(*itrs)


# TODO: need to make sure that differences in format don't result in duplicate events
def merge_events(*sources: Results) -> Results:
    """
    Given a bunch of iterators, merges takeout events together
    """
    emitted: GoogleEventSet = GoogleEventSet()
    for event in chain(*sources):
        if isinstance(event, Exception):
            yield event
            continue
        if event in emitted:
            continue
        emitted.add(event)
        yield event


def _create_key(e: Event) -> Tuple[str, Any]:
    return (type(e).__name__, e.key)


# This is so that its easier to use this logic in other
# places, e.g. in github.com/seanbreckenridge/HPI
class GoogleEventSet:
    """
    Class to help manage keys for the models
    """

    def __init__(self) -> None:
        self.keys: Set[Tuple[str, Any]] = set()

    def __contains__(self, other: Event) -> bool:
        return _create_key(other) in self.keys

    def add(self, other: Event) -> None:
        self.keys.add(_create_key(other))
