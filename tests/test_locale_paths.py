from google_takeout_parser.locales.main import get_paths_for_functions


def test_locale_paths() -> None:
    jpths = get_paths_for_functions()
    assert jpths == {
        "Chrome",
        "Location History",
        "Meine Aktivitäten",
        "My Activity",
        "Standortverlauf",
        "YouTube( and YouTube Music)?",
        "YouTube( und YouTube Music)?",
    }
