import bs4

from .activity import _parse_subtitles, _parse_caption, _is_location_api_link

# bring into scope
from .comment import test_parse_html_comment_file  # noqa: F401
from .html_time_utils import test_parse_dt  # noqa: F401


def bs4_div(html: str) -> bs4.element.Tag:
    tag = bs4.BeautifulSoup(html, "lxml").select_one("div")
    assert tag is not None
    return tag


def test_parse_subtitles() -> None:
    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">Visited&nbsp;<a href="https://support.google.com/youtube/answer/7071292?hl=en">Get support with Premium memberships &amp; purchases - YouTube Help</a><br>Aug 25, 2020, 5:06:44 PM PDT</div>"""
    )
    res = _parse_subtitles(content, file_dt=None)
    assert not isinstance(res, Exception)
    subs, dt = res
    assert subs == [
        (
            "Visited Get support with Premium memberships & purchases - YouTube Help",
            "https://support.google.com/youtube/answer/7071292?hl=en",
        )
    ]
    assert dt is not None

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">6 cards in your feed<br/>Sep 4, 2020, 11:01:46 AM PDT</div>"""
    )
    res = _parse_subtitles(content, file_dt=None)
    assert not isinstance(res, Exception)
    subs, dt = res
    assert subs == [("6 cards in your feed", None)]
    # parses into a DstTzInfo timezone, so just testing that it parsed
    assert int(dt.timestamp()) == 1599242506

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">1 notification<br>Including topics:<br><a href="https://www.google.com/maps/place/?q=place_id:XX">Emergency resources and information</a><br>Sep 1, 2020, 9:27:07 PM PDT</div>""",
    )
    res = _parse_subtitles(content, file_dt=None)
    assert not isinstance(res, Exception)
    subs, dt = res

    # how multiple lines of body look in subtitles
    assert subs == [
        ("1 notification", None),
        ("Including topics:", None),
        (
            "Emergency resources and information",
            "https://www.google.com/maps/place/?q=place_id:XX",
        ),
    ]
    assert dt is not None


def test_parse_captions() -> None:
    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Drive<br><b>Details:</b><br> From IP 8.8.8.8<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == ["From IP 8.8.8.8"]
    assert products == ["Drive"]
    assert locationInfos == []


def test_parse_locations() -> None:

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Discover<br><b>Locations:</b><br> At <a href="https://www.google.com/maps/@?something">this general area</a> - From <a href="https://support.google.com/maps/answer/1">your places</a> (Home)<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == []
    assert products == ["Discover"]

    assert locationInfos == [
        (
            "At this general area",
            "https://www.google.com/maps/@?something",
            "From your places (Home)",
            "https://support.google.com/maps/answer/1",
        )
    ]

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Maps<br><b>Locations:</b><br> At <a href="https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11">this general area</a> - Based on your past activity<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == []
    assert products == ["Maps"]

    assert locationInfos == [
        (
            "At this general area",
            "https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11",
            "Based on your past activity",
            None,
        )
    ]


def test_parse_is_google_url() -> None:
    assert _is_location_api_link(
        "https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11"
    )
    assert not _is_location_api_link("https://www.google.com/")
