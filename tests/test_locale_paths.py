import os

import pytest
from google_takeout_parser.locales.main import get_paths_for_functions


@pytest.mark.skipif(
    os.environ.get("RUNNER_OS", "Linux") == "Windows",
    reason="skipping locale test on windows, some quoting issue",
)
def test_locale_paths() -> None:
    jpths = get_paths_for_functions()
    assert jpths == [
        "Chrome",
        "Location History",
        r"Location History \(Timeline\)",  # using "Location History \\(Timeline\\)" fails on windows.
        "Meine Aktivitäten",
        "My Activity",
        "YouTube( and YouTube Music)?",
        "YouTube( und YouTube Music)?",
    ]
