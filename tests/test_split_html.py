import os
import tempfile
import subprocess
from typing import Generator
from pathlib import Path

import pytest

from .common import this_dir
from google_takeout_parser.parse_html.activity import _parse_html_activity


activity_html_file = str(
    Path("~/.cache/gt/Takeout-Old/My Activity/YouTube/MyActivity.html")
    .expanduser()
    .absolute()
)

golang_dir = this_dir / ".." / "split_html"


@pytest.fixture
def in_golang_dir() -> Generator[None, None, None]:
    current_dir = os.getcwd()
    try:
        os.chdir(golang_dir)
        yield
    finally:
        os.chdir(current_dir)


@pytest.mark.skipif(
    "TEST_GOLANG_SPLIT" not in os.environ,
    reason="TEST_GOLANG_SPLIT not set, skipping test",
)
def test_split_html(in_golang_dir: None) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [
                "go",
                "run",
                golang_dir / "split_html_activity.go",
                "-output",
                temp_dir,
                activity_html_file,
            ],
            check=True,
        )

        assert Path(temp_dir).is_dir()

        from_merged = []

        files = sorted(Path(temp_dir).iterdir())
        assert len(files) > 1
        for file in files:
            assert file.is_file()
            assert file.stat().st_size > 0

            for x in _parse_html_activity(file):
                if isinstance(x, Exception):
                    raise x
                from_merged.append(x)

        from_original = [
            a
            for a in _parse_html_activity(Path(activity_html_file))
            if not isinstance(a, Exception)
        ]

        assert len(from_merged) == len(from_original)

        from_merged.sort(key=lambda x: x.time)
        from_original.sort(key=lambda x: x.time)

        for a, b in zip(from_merged, from_original):
            assert a == b
