import re
from pathlib import Path
from typing import Iterator
from datetime import datetime, timezone

import bs4  # type: ignore[import]

from ..models import YoutubeComment
from ..common import Res
from .activity import _group_by_brs, clean_latin1_chars

# seems to always be in UTC?
COMMENT_DATE_REGEX = re.compile(
    r"([0-9]{4})\-([0-9]{2})\-([0-9]{2})\s*([0-9]{2})\:([0-9]{2})\:([0-9]{2})"
)

# for YoutubeComment
# can be in lots of formats
# sent at '...'
# on '....'
# probably just need to use regex
def _extract_html_li_date(comment: str) -> datetime:
    matches = re.search(COMMENT_DATE_REGEX, comment)
    if matches:
        g = matches.groups()
        year, month, day, hour, minute, second = tuple(map(int, g))
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    else:
        raise RuntimeError(f"Couldn't parse date from {comment}")


def _parse_html_li(li: bs4.element.Tag) -> YoutubeComment:
    parsed_date: datetime = _extract_html_li_date(li.text)
    groups = _group_by_brs(li.children)
    assert len(groups) == 2, f"Expected 2 parts separated by a <br /> {groups}"
    desc = ""
    for tag in groups[1]:
        if isinstance(tag, bs4.element.NavigableString):
            desc += str(tag)
        elif isinstance(tag, bs4.element.Tag):
            desc += str(tag.text)
    urls = list({l.attrs["href"] for l in li.select("a") if "href" in l.attrs})
    return YoutubeComment(
        content=clean_latin1_chars(desc).strip(), urls=urls, dt=parsed_date
    )


def _parse_html_comment_file(p: Path) -> Iterator[Res[YoutubeComment]]:
    soup = bs4.BeautifulSoup(p.read_text(), "lxml")
    for li in soup.select("li"):
        try:
            yield _parse_html_li(li)
        # catch expected errors are yield them as part of the union type
        except (AssertionError, RuntimeError) as e:
            yield e


def test_parse_html_comment_file() -> None:
    li_obj = bs4.BeautifulSoup(
        """<ul><li>Sent at 2020-04-27 23:18:23 UTC while watching <a href="http://www.youtube.com/watch?v=mM">a video</a>.<br/>content here</li></ul>""",
        "lxml",
    ).select_one("li")
    parsed_li = _parse_html_li(li_obj)
    assert parsed_li == YoutubeComment(
        content="content here",
        dt=datetime(2020, 4, 27, 23, 18, 23, tzinfo=timezone.utc),
        urls=["http://www.youtube.com/watch?v=mM"],
    )
