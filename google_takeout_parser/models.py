"""
Models for the data parsed by this module

Each top-level NamedTuple here has a 'key' property
which determines unique events while merging
"""

from datetime import datetime
from typing import NamedTuple, Optional, List, Tuple, Union


Details = str


# beacuse of https://github.com/karlicoss/cachew/issues/28, need
# to do these as tuples instead of NamedTuples
MetaData = Optional[str]
# name, url, source, sourceUrl
LocationInfo = Tuple[MetaData, MetaData, MetaData, MetaData]

# name, url
Subtitles = Tuple[str, MetaData]


class Activity(NamedTuple):
    header: str
    title: str
    description: Optional[str]
    titleUrl: Optional[str]
    time: datetime
    # note: in HTML exports, there is no way to tell the difference between
    # a description and a subtitle, so they end up as subtitles
    subtitles: List[Subtitles]  # more lines of text describing this
    details: List[Details]
    locationInfos: List[LocationInfo]
    products: List[str]

    @property
    def dt(self) -> datetime:
        return self.time

    @property
    def products_desc(self) -> str:
        return ", ".join(sorted(self.products))

    @property
    def key(self) -> Tuple[str, str, int]:
        return (self.header, self.title, int(self.time.timestamp()))


class YoutubeComment(NamedTuple):
    content: str
    dt: datetime
    urls: List[str]

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


class LikedYoutubeVideo(NamedTuple):
    title: str
    desc: str
    link: str
    dt: datetime

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


class PlayStoreAppInstall(NamedTuple):
    title: str
    device_name: Optional[str]
    dt: datetime

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


class Location(NamedTuple):
    lng: float
    lat: float
    dt: datetime

    @property
    def key(self) -> Tuple[float, float, int]:
        return (self.lng, self.lat, int(self.dt.timestamp()))


class ChromeHistory(NamedTuple):
    title: str
    url: str
    dt: datetime

    @property
    def key(self) -> Tuple[str, int]:
        return (self.url, int(self.dt.timestamp()))


Event = Union[
    Activity,
    YoutubeComment,
    LikedYoutubeVideo,
    PlayStoreAppInstall,
    Location,
    ChromeHistory,
]
