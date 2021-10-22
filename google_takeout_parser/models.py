from datetime import datetime
from typing import NamedTuple, Optional, List


class Subtitles(NamedTuple):
    name: str
    url: Optional[str]


class Details(NamedTuple):
    name: str


class LocationInfo(NamedTuple):
    name: Optional[str]
    url: Optional[str]
    source: Optional[str]
    sourceUrl: Optional[str]


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


class YoutubeComment(NamedTuple):
    content: str
    dt: datetime
    urls: List[str]


class LikedYoutubeVideo(NamedTuple):
    title: str
    desc: str
    link: str
    dt: datetime


class PlayStoreAppInstall(NamedTuple):
    title: str
    device_name: Optional[str]
    dt: datetime


class Location(NamedTuple):
    lng: float
    lat: float
    dt: datetime


class ChromeHistory(NamedTuple):
    title: str
    url: str
    dt: datetime


class HangoutsMessage(NamedTuple):
    text: Optional[str]
    link: Optional[str]
    dt: datetime
