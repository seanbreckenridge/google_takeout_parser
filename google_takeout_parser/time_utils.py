from typing import Union
from datetime import datetime, timezone


def parse_datetime_sec(d: Union[str, float, int]) -> datetime:
    return datetime.fromtimestamp(int(d), tz=timezone.utc)


def parse_datetime_millis(d: Union[str, float, int]) -> datetime:
    return parse_datetime_sec(int(d) / 1000)


def parse_json_utc_date(ds: str) -> datetime:
    utc_naive = datetime.fromisoformat(ds.rstrip("Z"))
    return utc_naive.replace(tzinfo=timezone.utc)


def test_parse_utc_date() -> None:
    expected = datetime(2021, 9, 30, 1, 44, 33, tzinfo=timezone.utc)
    assert parse_json_utc_date("2021-09-30T01:44:33.000Z") == expected
