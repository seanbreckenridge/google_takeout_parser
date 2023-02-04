from google_takeout_parser.path_dispatch import TakeoutParser

from .common import testdata


def test_structure() -> None:
    recent_takeout = testdata / "RecentTakeout"
    assert recent_takeout.exists()
    files = [f for f in recent_takeout.rglob("*") if f.is_file()]
    tk = TakeoutParser(recent_takeout)
    m = tk.dispatch_map()
    assert len(files) == 53
    assert len(m) == 35
