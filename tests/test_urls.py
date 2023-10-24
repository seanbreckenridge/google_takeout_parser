import logging
from pytest import LogCaptureFixture
from google_takeout_parser.http_allowlist import _convert_to_https


def test_convert_to_https(caplog: LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        url = "http://www.google.com"
        assert _convert_to_https(url) == "https://www.google.com"

        url = "http://youtube.com"
        assert _convert_to_https(url) == "https://youtube.com"

        url = "http://www.youtube.com"
        assert _convert_to_https(url) == "https://www.youtube.com"

        url = "https://youtube.com"
        assert _convert_to_https(url) == "https://youtube.com"

        url = "http://maps.google.com/something+else"
        assert _convert_to_https(url) == "https://maps.google.com/something+else"

        url = "http://m.youtube.com/watch?v=123"
        assert _convert_to_https(url) == "https://m.youtube.com/watch?v=123"

        from logzero import logger  # type: ignore[import]

        logger.propagate = True

        # capture logs
        url = "http://www.otherurl.com"

    assert len(caplog.records) == 0

    caplog.clear()

    with caplog.at_level(logging.DEBUG):
        assert _convert_to_https(url, logger) == "http://www.otherurl.com"

    assert len(caplog.records) == 1
    assert (
        "HTTP URL did not match allowlist: http://www.otherurl.com\nIf you think this should be auto-converted to HTTPS, make an issue here:"
        in caplog.records[0].message
    )
