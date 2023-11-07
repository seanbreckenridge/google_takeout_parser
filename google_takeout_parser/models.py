"""
Models for the data parsed by this module

Each top-level dataclass here has a 'key' property
which determines unique events while merging
"""

from __future__ import annotations
from datetime import datetime
from typing import (
    Optional,
    Type,
    List,
    Tuple,
    Any,
    Union,
    Iterator,
    Dict,
    Protocol,
    NamedTuple,
)
from dataclasses import dataclass

from .common import Res

Url = str


def get_union_args(cls: Any) -> Optional[Tuple[Type]]:  # type: ignore[type-arg]
    if getattr(cls, "__origin__", None) != Union:
        return None

    args = cls.__args__
    args = [e for e in args if e != type(None)]  # noqa: E721
    assert len(args) > 0
    return args  # type: ignore


class Subtitles(NamedTuple):
    name: str
    url: Optional[Url]


class LocationInfo(NamedTuple):
    name: Optional[str]
    url: Optional[Url]
    source: Optional[str]
    sourceUrl: Optional[Url]


class BaseEvent(Protocol):
    @property
    def key(self) -> Any:
        ...


@dataclass
class Activity(BaseEvent):
    header: str
    title: str
    time: datetime
    description: Optional[str]
    titleUrl: Optional[Url]
    # note: in HTML exports, there is no way to tell the difference between
    # a description and a subtitle, so they end up as subtitles
    # more lines of text describing this
    subtitles: List[Subtitles]
    details: List[str]
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
        return self.header, self.title, int(self.time.timestamp())


@dataclass
class YoutubeComment(BaseEvent):
    content: str
    dt: datetime
    urls: List[Url]

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
    device_name: Optional[str]

    @property
    def key(self) -> int:
        return int(self.dt.timestamp())


@dataclass
class Location(BaseEvent):
    lat: float
    lng: float
    accuracy: Optional[float]
    dt: datetime

    @property
    def key(self) -> Tuple[float, float, Optional[float], int]:
        return self.lat, self.lng, self.accuracy, int(self.dt.timestamp())


# this is not cached as a model, its saved as JSON -- its a helper class that placevisit uses
@dataclass
class CandidateLocation:
    lat: float
    lng: float
    address: Optional[str]
    name: Optional[str]
    placeId: str
    locationConfidence: Optional[float]  # missing in older (around 2014/15) history
    sourceInfoDeviceTag: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandidateLocation:
        return cls(
            address=data.get("address"),
            name=data.get("name"),
            placeId=data["placeId"],
            locationConfidence=data.get("locationConfidence"),
            lat=data["latitudeE7"] / 1e7,
            lng=data["longitudeE7"] / 1e7,
            sourceInfoDeviceTag=data.get("sourceInfo", {}).get("deviceTag"),
        )


@dataclass
class PlaceVisit(BaseEvent):
    # these are part of the 'location' key
    lat: float
    lng: float
    centerLat: Optional[float]
    centerLng: Optional[float]
    address: Optional[str]
    name: Optional[str]
    locationConfidence: Optional[float]  # missing in older (around 2014/15) history
    placeId: str
    startTime: datetime
    endTime: datetime
    sourceInfoDeviceTag: Optional[int]
    otherCandidateLocations: List[CandidateLocation]
    # TODO: parse these into an enum of some kind? may be prone to breaking due to new values from google though...
    placeConfidence: Optional[str]  # older semantic history (pre-2018 didn't have it)
    placeVisitType: Optional[str]
    visitConfidence: Optional[float]  # missing in older (around 2014/15) history
    editConfirmationStatus: Optional[str]  # missing in older (around 2014/15) history
    placeVisitImportance: Optional[str] = None

    @property
    def dt(self) -> datetime:  # type: ignore[override]
        return self.startTime

    @property
    def key(self) -> Tuple[float, float, int, Optional[float]]:
        return self.lat, self.lng, int(self.startTime.timestamp()), self.visitConfidence


@dataclass
class ChromeHistory(BaseEvent):
    title: str
    url: Url
    dt: datetime

    @property
    def key(self) -> Tuple[str, int]:
        return self.url, int(self.dt.timestamp())


# can't compute this dynamically -- have to write it out
# if you want to override, override both global variable types with new types
DEFAULT_MODEL_TYPE = Union[
    Activity,
    LikedYoutubeVideo,
    PlayStoreAppInstall,
    Location,
    ChromeHistory,
    YoutubeComment,
    PlaceVisit,
]

CacheResults = Iterator[Res[DEFAULT_MODEL_TYPE]]
