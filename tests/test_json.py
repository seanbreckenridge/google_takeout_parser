import datetime
from pathlib import Path
from typing import Iterator
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
import google_takeout_parser.parse_json as prj


@contextmanager
def temp_path(contents: str) -> Iterator[Path]:
    tf = NamedTemporaryFile(prefix="gtp-", delete=False)
    p = Path(tf.name)
    p.write_text(contents)
    yield p
    p.unlink()
    assert not p.exists()


def test_parse_activity_json() -> None:
    contents = '[{"header": "Discover", "title": "7 cards in your feed", "time": "2021-12-13T03:04:05.007Z", "products": ["Discover"], "locationInfos": [{"name": "At this general area", "url": "https://www.google.com/maps/@?api=1&map_action=map&center=lat,lon&zoom=12", "source": "From your Location History", "sourceUrl": "https://www.google.com/maps/timeline"}], "subtitles": [{"name": "Computer programming"}, {"name": "Computer Science"}, {"name": "PostgreSQL"}, {"name": "Technology"}]}]'
    with temp_path(contents) as p:
        res = list(prj._parse_json_activity(p))
    assert res[0] == prj.Activity(
        header="Discover",
        title="7 cards in your feed",
        time=datetime.datetime(
            2021, 12, 13, 3, 4, 5, 7000, tzinfo=datetime.timezone.utc
        ),
        description=None,
        titleUrl=None,
        subtitles=[
            ("Computer programming", None),
            ("Computer Science", None),
            ("PostgreSQL", None),
            ("Technology", None),
        ],
        locationInfos=[
            (
                "At this general area",
                "https://www.google.com/maps/@?api=1&map_action=map&center=lat,lon&zoom=12",
                "From your Location History",
                "https://www.google.com/maps/timeline",
            ),
        ],
        details=[],
        products=["Discover"],
    )


def test_parse_likes_json() -> None:
    contents = """[{"contentDetails": {"videoId": "J1tF-DKKt7k", "videoPublishedAt": "2015-10-05T17:23:15.000Z"}, "etag": "GbLczUV2gsP6j0YQgTcYropUbdY", "id": "TExBNkR0bmJaMktKY2t5VFlmWE93UU5BLkoxdEYtREtLdDdr", "kind": "youtube#playlistItem", "snippet": {"channelId": "UCA6DtnbZ2KJckyTYfXOwQNA", "channelTitle": "Sean B", "description": "\\u30b7\\u30e5\\u30ac\\u30fc\\u30bd\\u30f3\\u30b0\\u3068\\u30d3\\u30bf\\u30fc\\u30b9\\u30c6\\u30c3\\u30d7 \\nSugar Song and Bitter Step\\n\\u7cd6\\u6b4c\\u548c\\u82e6\\u5473\\u6b65\\u9a5f\\nUNISON SQUARE GARDEN\\n\\u7530\\u6df5\\u667a\\u4e5f\\n\\u8840\\u754c\\u6226\\u7dda\\n\\u5e7b\\u754c\\u6230\\u7dda\\nBlood Blockade Battlefront ED\\nArranged by Maybe\\nScore:https://drive.google.com/open?id=0B9Jb1ks6rtrWSk1hX1U0MXlDSUE\\nThx~~", "playlistId": "LLA6DtnbZ2KJckyTYfXOwQNA", "position": 4, "publishedAt": "2020-07-05T18:27:32.000Z", "resourceId": {"kind": "youtube#video", "videoId": "J1tF-DKKt7k"}, "thumbnails": {"default": {"height": 90, "url": "https://i.ytimg.com/vi/J1tF-DKKt7k/default.jpg", "width": 120}, "high": {"height": 360, "url": "https://i.ytimg.com/vi/J1tF-DKKt7k/hqdefault.jpg", "width": 480}, "medium": {"height": 180, "url": "https://i.ytimg.com/vi/J1tF-DKKt7k/mqdefault.jpg", "width": 320}, "standard": {"height": 480, "url": "https://i.ytimg.com/vi/J1tF-DKKt7k/sddefault.jpg", "width": 640}}, "title": "[Maybe]Blood Blockade Battlefront ED \\u30b7\\u30e5\\u30ac\\u30fc\\u30bd\\u30f3\\u30b0\\u3068\\u30d3\\u30bf\\u30fc\\u30b9\\u30c6\\u30c3\\u30d7 Sugar Song and Bitter Step"}, "status": {"privacyStatus": "public"}}]"""
    with temp_path(contents) as p:
        res = list(prj._parse_likes(p))
    assert res == [
        prj.LikedYoutubeVideo(
            title="[Maybe]Blood Blockade Battlefront ED シュガーソングとビターステップ "
            "Sugar Song and Bitter Step",
            desc="シュガーソングとビターステップ \n"
            "Sugar Song and Bitter Step\n"
            "糖歌和苦味步驟\n"
            "UNISON SQUARE GARDEN\n"
            "田淵智也\n"
            "血界戦線\n"
            "幻界戰線\n"
            "Blood Blockade Battlefront ED\n"
            "Arranged by Maybe\n"
            "Score:https://drive.google.com/open?id=0B9Jb1ks6rtrWSk1hX1U0MXlDSUE\n"
            "Thx~~",
            link="https://youtube.com/watch?v=J1tF-DKKt7k",
            dt=datetime.datetime(2020, 7, 5, 18, 27, 32, tzinfo=datetime.timezone.utc),
        )
    ]


def test_parse_app_installs() -> None:
    contents = """[{"install": {"doc": {"documentType": "Android Apps", "title": "Discord - Talk, Video Chat & Hang Out with Friends"}, "firstInstallationTime": "2020-05-25T03:11:53.055Z", "deviceAttribute": {"manufacturer": "motorola", "deviceDisplayName": "motorola moto g(7) play"}, "lastUpdateTime": "2020-08-27T02:55:33.259Z"}}]"""
    with temp_path(contents) as p:
        res = list(prj._parse_app_installs(p))
    assert res == [
        prj.PlayStoreAppInstall(
            title="Discord - Talk, Video Chat & Hang Out with Friends",
            dt=datetime.datetime(
                2020, 5, 25, 3, 11, 53, 55000, tzinfo=datetime.timezone.utc
            ),
            device_name="motorola moto g(7) play",
        )
    ]


def test_location_old() -> None:
    contents = '{"locations": [{"timestampMs": "1512947698030", "latitudeE7": 351324213, "longitudeE7": -1122434441, "accuracy": 10}]}'
    with temp_path(contents) as p:
        res = list(prj._parse_location_history(p))
    assert res == [
        prj.Location(
            lng=-112.2434441,
            lat=35.1324213,
            dt=datetime.datetime(
                2017, 12, 10, 23, 14, 58, tzinfo=datetime.timezone.utc
            ),
            accuracy=10,
        ),
    ]


def test_location_new() -> None:
    contents = '{"locations": [{"latitudeE7": 351324213, "longitudeE7": -1122434441, "accuracy": 10, "deviceTag": -80241446968629135069, "deviceDesignation": "PRIMARY", "timestamp": "2017-12-10T23:14:58.030Z"}]}'
    with temp_path(contents) as p:
        res = list(prj._parse_location_history(p))
    assert res == [
        prj.Location(
            lng=-112.2434441,
            lat=35.1324213,
            dt=datetime.datetime(
                2017, 12, 10, 23, 14, 58, 30000, tzinfo=datetime.timezone.utc
            ),
            accuracy=10,
        ),
    ]


def test_chrome_history() -> None:
    contents = '{"Browser History": [{"page_transition": "LINK", "title": "sean", "url": "https://sean.fish", "client_id": "W1vSb98l403jhPeK==", "time_usec": 1617404690134513}]}'
    with temp_path(contents) as p:
        res = list(prj._parse_chrome_history(p))
    assert res == [
        prj.ChromeHistory(
            title="sean",
            url="https://sean.fish",
            dt=datetime.datetime(
                2021, 4, 2, 23, 4, 50, 134513, tzinfo=datetime.timezone.utc
            ),
        ),
    ]
