"""
Models for the data parsed by this module

Each top-level dataclass here has a 'key' property
which determines unique events while merging
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Tuple, Any, Union, Iterator, TYPE_CHECKING, Dict
from dataclasses import dataclass

from .common import Res
from .log import logger


Details = str


# because of https://github.com/karlicoss/cachew/issues/28, need
# to do these as tuples instead of NamedTuples
MetaData = Optional[str]
# name, url, source, sourceUrl
LocationInfo = Tuple[MetaData, MetaData, MetaData, MetaData]

# name, url
Subtitles = Tuple[str, MetaData]

if TYPE_CHECKING:
    try:
        from typing import Protocol
    except ImportError:
        from typing_extensions import Protocol  # type: ignore
else:
    Protocol = object


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
    titleUrl: Optional[str]
    # note: in HTML exports, there is no way to tell the difference between
    # a description and a subtitle, so they end up as subtitles
    # more lines of text describing this
    subtitles: List[Subtitles]
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
        return self.header, self.title, int(self.time.timestamp())


@dataclass
class YoutubeComment(BaseEvent):
    content: str
    dt: datetime
    urls: List[str]

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
    accuracy: Optional[int]
    dt: datetime

    @property
    def key(self) -> Tuple[float, float, Optional[int], int]:
        return self.lat, self.lng, self.accuracy, int(self.dt.timestamp())


# this is not cached as a model, its saved as JSON -- its a helper class that placevisit uses
@dataclass
class CandidateLocation:
    lat: float
    lng: float
    address: Optional[str]
    name: Optional[str]
    placeId: str
    locationConfidence: float
    sourceInfoDeviceTag: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandidateLocation:
        return cls(
            address=data.get("address"),
            name=data.get("name"),
            placeId=data["placeId"],
            locationConfidence=data["locationConfidence"],
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
    locationConfidence: float
    placeId: str
    startTime: datetime
    endTime: datetime
    sourceInfoDeviceTag: Optional[int]
    otherCandidateLocationsJSON: str
    # TODO: parse these into an enum of some kind? may be prone to breaking due to new values from google though...
    placeConfidence: str
    placeVisitType: Optional[str]
    visitConfidence: float
    editConfirmationStatus: str
    placeVisitImportance: Optional[str] = None

    @property
    def dt(self) -> datetime:  # type: ignore[override]
        return self.startTime

    @property
    def key(self) -> Tuple[float, float, int, Optional[float]]:
        return self.lat, self.lng, int(self.startTime.timestamp()), self.visitConfidence

    @property
    def otherCandidateLocations(self) -> List[CandidateLocation]:
        import json

        loaded = json.loads(self.otherCandidateLocationsJSON)
        if not isinstance(loaded, list):
            logger.warning(
                f"loading candidate locations: expected list, got {type(loaded)}, {loaded}"
            )
            return []

        return [CandidateLocation.from_dict(x) for x in loaded]


@dataclass
class ChromeHistory(BaseEvent):
    title: str
    url: str
    dt: datetime

    @property
    def key(self) -> Tuple[str, int]:
        return self.url, int(self.dt.timestamp())


# cant compute this dynamically -- have to write it out
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
