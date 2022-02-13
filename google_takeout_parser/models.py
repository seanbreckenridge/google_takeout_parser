"""
Models for the data parsed by this module

Each top-level NamedTuple here has a 'key' property
which determines unique events while merging
"""

from datetime import datetime
from typing import Optional, List, Tuple, Any, Type, Union, Iterator
from dataclasses import dataclass, field

from .common import Res


Details = str


# because of https://github.com/karlicoss/cachew/issues/28, need
# to do these as tuples instead of NamedTuples
MetaData = Optional[str]
# name, url, source, sourceUrl
LocationInfo = Tuple[MetaData, MetaData, MetaData, MetaData]

# name, url
Subtitles = Tuple[str, MetaData]


class BaseEvent:
    def __init__(self) -> None:
        raise NotImplementedError

    @property
    def key(self) -> Any:
        raise NotImplementedError


@dataclass
class Activity(BaseEvent):
    header: str
    title: str
    time: datetime
    description: Optional[str] = None
    titleUrl: Optional[str] = None
    # note: in HTML exports, there is no way to tell the difference between
    # a description and a subtitle, so they end up as subtitles
    subtitles: List[Subtitles] = field(
        default_factory=list
    )  # more lines of text describing this
    details: List[Details] = field(default_factory=list)
    locationInfos: List[LocationInfo] = field(default_factory=list)
    products: List[str] = field(default_factory=list)

    @property
    def dt(self) -> datetime:
        return self.time

    @property
    def products_desc(self) -> str:
        return ", ".join(sorted(self.products))

    @property
    def key(self) -> Tuple[str, str, int]:
        return (self.header, self.title, int(self.time.timestamp()))


@dataclass
class YoutubeComment(BaseEvent):
    content: str
    dt: datetime
    urls: List[str] = field(default_factory=list)

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


@dataclass
class LikedYoutubeVideo(BaseEvent):
    title: str
    desc: str
    link: str
    dt: datetime

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


@dataclass
class PlayStoreAppInstall(BaseEvent):
    title: str
    dt: datetime
    device_name: Optional[str] = None

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


@dataclass
class Location(BaseEvent):
    lng: float
    lat: float
    dt: datetime

    @property
    def key(self) -> Tuple[float, float, int]:
        return (self.lng, self.lat, int(self.dt.timestamp()))


@dataclass
class ChromeHistory(BaseEvent):
    title: str
    url: str
    dt: datetime

    @property
    def key(self) -> Tuple[str, int]:
        return (self.url, int(self.dt.timestamp()))


# cant compute this dynamically -- have to write it out
# if you want to override, override both global variable types with new types
DEFAULT_MODEL_TYPE = Union[
    Activity, LikedYoutubeVideo, PlayStoreAppInstall, Location, ChromeHistory
]


Results = Iterator[Res[DEFAULT_MODEL_TYPE]]
