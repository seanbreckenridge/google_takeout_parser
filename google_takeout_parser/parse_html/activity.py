"""
Parses the HTML MyActivity.html files that used to be the standard
"""

import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Iterator, Optional, Tuple, Union, Dict
from urllib.parse import urlparse, parse_qs

import bs4  # type: ignore[import]
from bs4.element import Tag  # type: ignore[import]

from ..models import Activity, Subtitles, Details, LocationInfo
from ..common import Res
from .html_time_utils import parse_html_dt


def clean_latin1_chars(s: str) -> str:
    # these are latin1 encoded space characters, replace them with spaces
    return s.replace("\xa0", " ").replace("\u2003", " ")


TextOrEl = Union[bs4.element.Tag, bs4.element.NavigableString]
ListOfTags = List[List[TextOrEl]]


def _group_by_brs(els: TextOrEl) -> ListOfTags:
    """
    splits elements (children of some top-level div)
    into groups of elements, separated by 'br' elements

    we want to split by lines which have '<br/>' elements, since
    it can contain URLs whose link text contains both text and
    a URL we want
    """
    res: ListOfTags = []
    cur: List[TextOrEl] = []
    for tag in els:
        if isinstance(tag, bs4.element.NavigableString):
            cur.append(tag)
        else:
            # is a bs4.element.Tag
            if tag.name == "br":
                res.append(cur)
                cur = []
            else:
                cur.append(tag)
    if cur:
        res.append(cur)
    return res


def _parse_subtitles(
    subtitle_cell: bs4.element.Tag,
    *,
    file_dt: Optional[datetime],
) -> Tuple[List[Subtitles], datetime]:

    parsed_subs: List[Subtitles] = []

    # iterate over direct children, and remove the last
    # one (the date)
    sub_children = list(subtitle_cell.children)
    dt_raw = sub_children.pop(-1).strip()

    for group in _group_by_brs(sub_children):

        # loop vars
        buf: str = ""  # current text, till we hit a br (next group)
        url: Optional[str] = None  # a URL, if this subtitle contains one

        for tag in group:
            if isinstance(tag, bs4.element.NavigableString):
                buf += str(tag)
            elif isinstance(tag, bs4.element.Tag):
                if tag.name == "a":
                    buf += str(tag.text)
                    if "href" in tag.attrs:
                        url = tag.attrs["href"]
                else:
                    warnings.warn(f"Unexpected tag! {tag}")
            else:
                raise RuntimeError(f"Unexpected Type {tag} {type(tag)}")

        parsed_subs.append((clean_latin1_chars(buf), url))

    return parsed_subs, parse_html_dt(dt_raw, file_dt=file_dt)


def _split_by_caption_headers(groups: List[ListOfTags]) -> Dict[str, List[ListOfTags]]:
    """
    Captions are structured like:

    head1:
        value1
    head2:
        value2
        value3
    {
        "head1": [value1],
        "head2": [value2, value]
    }
    """

    k = ""
    res: Dict[str, List[ListOfTags]] = {}
    vals: ListOfTags = []

    for g in groups:
        possible_key = g[0]
        # keys look like [<b>Products:</b>]
        if (
            isinstance(possible_key, bs4.element.Tag)
            and possible_key.name == "b"
            and possible_key.text.endswith(":")
        ):
            # if we already have data, add that to the result
            if k:
                res[k] = vals
                vals = []
            k = possible_key.text.strip()
        else:
            assert (
                k
            ), f"While parsing caption; Found value while key has no value {groups}"
            # add non-header key to values
            vals.append(g)

    # add last key/val pair
    if vals:
        res[k] = vals

    return res


COMMON_GMAPS_QUERY_PARAMS = set(
    [
        "api",
        "map_action",
        "center",
        "zoom",
    ]
)


def _is_location_api_link(url: str) -> bool:
    query_params = parse_qs(urlparse(url).query)
    query_match_count = [
        param in query_params for param in COMMON_GMAPS_QUERY_PARAMS
    ].count(True)
    return query_match_count > 2


def _parse_caption(
    cap_cell: bs4.element.Tag,
) -> Tuple[List[Details], List[LocationInfo], List[str]]:
    details: List[Details] = []
    locationInfos: List[LocationInfo] = []
    products: List[str] = []

    groups = _group_by_brs(list(cap_cell.children))

    split_groups = _split_by_caption_headers(groups)

    for header, values in split_groups.items():
        for value in values:
            if header == "Products:":
                products.append(clean_latin1_chars(str(value[0])).strip())
            elif header == "Locations:":
                # man...
                # so it seems that the name/url
                # and the source/sourceUrl come in pairs
                # because of how html works, there can be anywhere
                # from 2 to 5 elements here, so it seems its best to
                # convert the entire buffer of elements to text and URLs
                # and then use some logic to figure out what it is

                # if we have two, we can use the order and split by the hyphen
                # if we have one, check the url to see if its a specific sort
                # of google maps URL (e.g. https://www.google.com/maps/search/?api=1&query=...)
                # and if it is, use it as the name/url pair, else use the text
                # as the source

                name: Optional[str] = None
                url: Optional[str] = None
                source: Optional[str] = None
                sourceUrl: Optional[str] = None

                textbuf = ""
                links: List[str] = []

                for tag in value:
                    if isinstance(tag, bs4.element.NavigableString):
                        textbuf += str(tag)
                    elif isinstance(tag, bs4.element.Tag):
                        textbuf += str(tag.text)
                        if tag.name == "a" and "href" in tag.attrs:
                            links.append(tag.attrs["href"])

                textbuf = clean_latin1_chars(textbuf).strip()

                if "-" in textbuf:
                    f, _, s = textbuf.partition("-")
                    name = f.strip()
                    source = s.strip()

                if len(links) == 2:
                    url = links[0]
                    sourceUrl = links[1]

                elif len(links) == 1:
                    if _is_location_api_link(links[0]):
                        url = links[0]
                        # wasnt set in partition above, was only one
                        # phrase of text
                        if name is None:
                            name = textbuf
                    else:
                        sourceUrl = links[0]
                        if source is None:
                            source = textbuf
                else:
                    # no links, just a description of the source
                    # (since theres no URL, cant be name)
                    source = textbuf

                locationInfos.append(
                    (
                        name,
                        url,
                        source,
                        sourceUrl,
                    )
                )
            elif header == "Details:":
                details.append(Details(clean_latin1_chars(str(value[0])).strip()))

            else:
                warnings.warn(f"Unexpected header in caption {header} {value}")

    return details, locationInfos, products


def _parse_activity_div(
    div: bs4.element.Tag,
    *,
    file_dt: Optional[datetime],
) -> Activity:
    header = div.select_one("p.mdl-typography--title").text.strip()

    # all possible data that this div could parse
    dtime: datetime
    subtitles: List[Subtitles] = []  # more lines of text describing this
    details: List[Details] = []
    locationInfos: List[LocationInfo] = []
    products: List[str] = []

    # cells in the div which contain the above information

    # has the main description/content and the datetime
    subtitle_cells: List[Tag] = []
    # has what product/extra info which this is related to
    caption_cells: List[Tag] = []

    # iterate over content-cells (contain all the info in this cell)
    # and categorize the cells. Pretty sure there should only be one
    # of each, but doing this to be safe
    for d in div.select(".content-cell"):
        div_classes = d.attrs["class"]
        # these are used for spacing on the right
        if "mdl-typography--text-right" in div_classes:
            continue
        # the main content cell -- the first item contains the title, and possible titleUrl
        # then after that, is the subtitles, which can contain text and possibly links
        elif "mdl-typography--body-1" in div_classes:
            subtitle_cells.append(d)
        # caption cells, optionally contains Products and Details, which contain lots of info
        # depending on the activity type
        elif "mdl-typography--caption" in div_classes:
            caption_cells.append(d)

    assert (
        len(subtitle_cells) == 1
    ), f"Expected one body cell in {div}, found {len(subtitle_cells)}"
    sub_cell = subtitle_cells[0]

    subtitles, dtime = _parse_subtitles(sub_cell, file_dt=file_dt)

    assert (
        len(caption_cells) == 1
    ), f"Expected one body cell in {div}, found {len(subtitle_cells)}"
    cap_cell = caption_cells[0]

    details, locationInfos, products = _parse_caption(cap_cell)

    # the first subtitle is the title/titleUrl
    assert len(subtitles) >= 0, f"Could not extract a title from {div}"

    title_info = subtitles.pop(0)

    return Activity(
        header=header,
        title=title_info[0],
        titleUrl=title_info[1],  # could be None, matched by model
        description=None,  # always none since we can't differentiate in HTML parsing
        time=dtime,
        locationInfos=locationInfos,
        subtitles=subtitles,
        details=details,
        products=products,
    )


def _parse_html_activity(p: Path) -> Iterator[Res[Activity]]:
    file_dt = datetime.fromtimestamp(p.stat().st_mtime)
    soup = bs4.BeautifulSoup(p.read_text(), "lxml")
    for outer_div in soup.select("div.outer-cell"):
        try:
            yield _parse_activity_div(outer_div, file_dt=file_dt)
        except Exception as ae:
            yield ae


_parse_html_activity.return_type = Activity  # type: ignore[attr-defined]
