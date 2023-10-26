from google_takeout_parser.locales.main import get_json_activity_paths, LOCALES


def test_locale_paths() -> None:
    jpths = get_json_activity_paths()
    assert len(jpths) > len(LOCALES)

    assert "My Activity" in jpths
    assert "Meine Aktivitäten" in jpths
