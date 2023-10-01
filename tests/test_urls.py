import logging
from google_takeout_parser.http_allowlist import _convert_to_https


def test__convert_to_https(caplog) -> None:
    url = "http://www.google.com"
    assert _convert_to_https(url) == "https://www.google.com"

    url = "http://youtube.com"
    assert _convert_to_https(url) == "https://youtube.com"

    url = "https://youtube.com"
    assert _convert_to_https(url) == "https://youtube.com"

    url = "http://maps.google.com/something+else"
    assert _convert_to_https(url) == "https://maps.google.com/something+else"

    from logzero import logger

    logger.propagate = True

    # catpure logs
    url = "http://www.otherurl.com"

    caplog.clear()

    with caplog.at_level(logging.DEBUG):
        assert _convert_to_https(url, logger) == "http://www.otherurl.com"

    assert len(caplog.records) == 1
    assert (
        "HTTP URL did not match allowlist: http://www.otherurl.com\nIf you think this should be auto-converted to HTTPS, make an issue here:"
        in caplog.records[0].message
    )
