"""
Taken from https://github.com/karlicoss/HPI/blob/4a04c09f314e10a4db8f35bf1ecc10e4d0203223/my/core/time.py
For backwards compatability, used to parse HTML datetimes with non-standard timezones
"""

from typing import Dict, Any
from functools import lru_cache
from datetime import tzinfo, datetime

import pytz


@lru_cache(1)
def _abbr_to_timezone_map() -> Dict[str, tzinfo]:
    timezones = pytz.all_timezones + ["UTC"]

    res: Dict[str, tzinfo] = {}
    for tzname in timezones:
        tz = pytz.timezone(tzname)
        infos = getattr(tz, "_tzinfos", [])
        for info in infos:
            abbr = info[-1]
            res[abbr] = tz
        tzn = getattr(tz, "_tzname", None)
        if tzn is not None:
            res[tzn] = tz
    return res


@lru_cache(maxsize=None)
def abbr_to_timezone(abbr: str) -> tzinfo:
    return _abbr_to_timezone_map()[abbr]


# Mar 8, 2018, 5:14:40 PM
_TIME_FORMAT = "%b %d, %Y, %I:%M:%S %p"


def parse_html_dt(s: str) -> datetime:
    fmt = _TIME_FORMAT

    end = s[-3:]
    tz: Any
    if end == " PM" or end == " AM":
        # old takeouts didn't have timezone
        # hopefully it was utc? Legacy, so no that much of an issue anymore..
        tz = pytz.utc
    else:
        s, tzabbr = s.rsplit(maxsplit=1)
        tz = abbr_to_timezone(tzabbr)

    dt = datetime.strptime(s, fmt)
    dt = tz.localize(dt)
    return dt


def test_parse_dt() -> None:
    parse_html_dt("Jun 23, 2015, 2:43:45 PM")
    parse_html_dt("Jan 25, 2019, 8:23:48 AM GMT")
    parse_html_dt("Jan 22, 2020, 8:34:00 PM UTC")
    parse_html_dt("Sep 10, 2019, 8:51:45 PM MSK")
    parse_html_dt("Sep 10, 2019, 8:51:45 PM PST")
    parse_html_dt("Sep 10, 2019, 8:51:45 PM PDT")
