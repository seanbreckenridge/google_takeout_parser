"""
Lots of functions to transform the JSON from the Takeout to useful information
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterator, Any, Dict, Iterable, Optional

from .time_utils import parse_datetime_millis
from .models import (
    Activity,
    LikedYoutubeVideo,
    ChromeHistory,
    PlayStoreAppInstall,
    Location,
    PlaceVisit,
    CandidateLocation,
)
from .common import Res
from .time_utils import parse_json_utc_date


# "YouTube and YouTube Music/history/search-history.json"
# "YouTube and YouTube Music/history/watch-history.json"
# This is also the 'My Activity' JSON format
def _parse_json_activity(p: Path) -> Iterator[Res[Activity]]:
    json_data = json.loads(p.read_text())
    if not isinstance(json_data, list):
        yield RuntimeError(f"Activity: Top level item in '{p}' isn't a list")
    for blob in json_data:
        try:
            subtitles = []
            for s in blob.get("subtitles", []):
                if s == {}:
                    # sometimes it's just empty ("My Activity/Assistant" data circa 2018)
                    continue
                subtitles.append((s["name"], s.get("url")))

            # till at least 2017
            old_format = "snippet" in blob
            if old_format:
                blob = blob["snippet"]
                header = "YouTube"  # didn't have header
                time_str = blob["publishedAt"]
            else:
                header = blob["header"]
                time_str = blob["time"]

            yield Activity(
                header=header,
                title=blob["title"],
                titleUrl=blob.get("titleUrl"),
                description=blob.get("description"),
                time=parse_json_utc_date(time_str),
                subtitles=subtitles,
                details=[d["name"] for d in blob.get("details", [])],
                locationInfos=[
                    (
                        locinfo.get("name"),
                        locinfo.get("url"),
                        locinfo.get("source"),
                        locinfo.get("sourceUrl"),
                    )
                    for locinfo in blob.get("locationInfos", [])
                ],
                products=blob.get("products", []),
            )
        except Exception as e:
            yield e


def _parse_likes(p: Path) -> Iterator[Res[LikedYoutubeVideo]]:
    json_data = json.loads(p.read_text())
    if not isinstance(json_data, list):
        yield RuntimeError(f"Likes: Top level item in '{p}' isn't a list")
    for jlike in json_data:
        try:
            yield LikedYoutubeVideo(
                title=jlike["snippet"]["title"],
                desc=jlike["snippet"]["description"],
                link="https://youtube.com/watch?v={}".format(
                    jlike["contentDetails"]["videoId"]
                ),
                dt=parse_json_utc_date(jlike["snippet"]["publishedAt"]),
            )
        except Exception as e:
            yield e


def _parse_app_installs(p: Path) -> Iterator[Res[PlayStoreAppInstall]]:
    json_data = json.loads(p.read_text())
    if not isinstance(json_data, list):
        yield RuntimeError(f"App installs: Top level item in '{p}' isn't a list")
    for japp in json_data:
        try:
            yield PlayStoreAppInstall(
                title=japp["install"]["doc"]["title"],
                device_name=japp["install"]["deviceAttribute"].get("deviceDisplayName"),
                dt=parse_json_utc_date(japp["install"]["firstInstallationTime"]),
            )
        except Exception as e:
            yield e


def _parse_timestamp_key(d: Dict[str, Any], key: str) -> datetime:
    if f"{key}Ms" in d:
        return parse_datetime_millis(d[f"{key}Ms"])
    else:
        # else should be the isoformat
        return parse_json_utc_date(d[key])


def _parse_location_timestamp(d: Dict[str, Any]) -> datetime:
    return _parse_timestamp_key(d, "timestamp")


def _parse_location_history(p: Path) -> Iterator[Res[Location]]:
    ### HMMM, seems that all the locations are right after one another. broken? May just be all the location history that google has on me
    ### see numpy.diff(list(map(lambda yy: y.at, filter(lambda y: isinstance(Location), events()))))
    json_data = json.loads(p.read_text())
    if "locations" not in json_data:
        yield RuntimeError(f"Locations: no 'locations' key in '{p}'")
    for loc in json_data.get("locations", []):
        accuracy = loc.get("accuracy")
        try:
            yield Location(
                lng=float(loc["longitudeE7"]) / 1e7,
                lat=float(loc["latitudeE7"]) / 1e7,
                dt=_parse_location_timestamp(loc),
                accuracy=None if accuracy is None else float(accuracy),
            )
        except Exception as e:
            yield e


_sem_required_keys = ["location", "duration"]


def _check_required_keys(
    d: Dict[str, Any], required_keys: Iterable[str]
) -> Optional[str]:
    for k in required_keys:
        if k not in d:
            return k
    return None


def _parse_semantic_location_history(p: Path) -> Iterator[Res[PlaceVisit]]:
    json_data = json.loads(p.read_text())
    if not isinstance(json_data, dict):
        yield RuntimeError(f"Locations: Top level item in '{p}' isn't a dict")
    if "timelineObjects" not in json_data:
        yield RuntimeError(f"Locations: no 'timelineObjects' key in '{p}'")
    timelineObjects = json_data.get("timelineObjects", [])
    for timelineObject in timelineObjects:
        if "placeVisit" not in timelineObject:
            # yield RuntimeError(f"PlaceVisit: no 'placeVisit' key in '{p}'")
            continue
        placeVisit = timelineObject["placeVisit"]
        missing_key = _check_required_keys(placeVisit, _sem_required_keys)
        if missing_key is not None:
            yield RuntimeError(f"PlaceVisit: no '{missing_key}' key in '{p}'")
            continue
        try:
            location = CandidateLocation.from_dict(placeVisit["location"])
            duration = placeVisit["duration"]
            yield PlaceVisit(
                name=location.name,
                address=location.address,
                # separators=(",", ":") removes whitespace from json.dumps
                otherCandidateLocationsJSON=json.dumps(
                    placeVisit.get("otherCandidateLocations", []), separators=(",", ":")
                ),
                sourceInfoDeviceTag=location.sourceInfoDeviceTag,
                placeConfidence=placeVisit["placeConfidence"],
                placeVisitImportance=placeVisit.get("placeVisitImportance"),
                placeVisitType=placeVisit.get("placeVisitType"),
                visitConfidence=placeVisit["visitConfidence"],
                editConfirmationStatus=placeVisit["editConfirmationStatus"],
                placeId=location.placeId,
                lng=location.lng,
                lat=location.lat,
                centerLat=float(placeVisit["centerLatE7"]) / 1e7
                if "centerLatE7" in placeVisit
                else None,
                centerLng=float(placeVisit["centerLngE7"]) / 1e7
                if "centerLngE7" in placeVisit
                else None,
                startTime=_parse_timestamp_key(duration, "startTimestamp"),
                endTime=_parse_timestamp_key(duration, "endTimestamp"),
                locationConfidence=location.locationConfidence,
            )
        except Exception as e:
            if isinstance(e, KeyError):
                yield RuntimeError(f"PlaceVisit: {p}, no key '{e}' in {placeVisit}")
            else:
                yield e


def _parse_chrome_history(p: Path) -> Iterator[Res[ChromeHistory]]:
    json_data = json.loads(p.read_text())
    if "Browser History" not in json_data:
        yield RuntimeError(f"Chrome/BrowserHistory: no 'Browser History' key in '{p}'")
    for item in json_data.get("Browser History", []):
        try:
            time_naive = datetime.utcfromtimestamp(item["time_usec"] / 10**6)
            yield ChromeHistory(
                title=item["title"],
                url=item["url"],
                dt=time_naive.replace(tzinfo=timezone.utc),
            )
        except Exception as e:
            yield e
