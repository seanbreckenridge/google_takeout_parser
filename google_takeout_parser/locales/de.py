from .common import (
    HandlerMap,
    _parse_html_activity,
    _parse_json_activity,
    _parse_html_comment_file,
    _parse_chrome_history,
    _parse_app_installs,
    _parse_semantic_location_history,
    _parse_location_history,
    _parse_likes,
)

HANDLER_MAP: HandlerMap = {
    # Chrome
    r"Chrome/BrowserHistory.json": _parse_chrome_history,
    r"Chrome": None,  # Ignore rest of Chrome stuff
    r"Google Play Store/Installs.json": _parse_app_installs,
    r"Google Play Store/": None,  # ignore anything else in Play Store
    r"Location History \(Timeline\)/Semantic Location History/.*/.*.json": _parse_semantic_location_history,
    r"Location History \(Timeline\)/Records.json": _parse_location_history,
    r"Location History \(Timeline\)/": None,  # ignore anything else in Location History
    # Youtube
    r"YouTube( und YouTube Music)?/Verlauf/.*?.html": _parse_html_activity,
    r"YouTube( und YouTube Music)?/Verlauf/.*?.json": _parse_json_activity,
    r"YouTube( und YouTube Music)?/Meine Kommentare/.*?.html": _parse_html_comment_file,
    r"YouTube( und YouTube Music)?/meine-live-chat-nachrichten/.*?.html": _parse_html_comment_file,
    r"YouTube( und YouTube Music)?/Playlists/Liked videos.json": _parse_likes,
    r"YouTube( und Youtube Music)?/*": None,  # ignore anything else in Youtube
    # Activities
    # parse html activity is intentionally not used here, its deprecated and for languages other
    # than english would require restructuring the html parsing significantly
    r"Meine Aktivitäten/.*?Meine\s*Aktivitäten.html": None,
    r"Meine Aktivitäten/.*?Meine\s*Aktivitäten.json": _parse_json_activity,
    # Ignored Google Services
    r"Google Fit": None,
    r"Google Play-Spieldienste/": None,
    r"Google Developers/": None,
    r"Google Play/": None,
    r"Google Pay": None,
    r"Google Finanzen/": None,  # stock watchlist
    r"Home App/": None,
    r"Google Shopping": None,
    r"Google Workspace Marketplace": None,
    r"Google Play Filme _ Serien/": None,
    r"Google Play Bücher/": None,  # books
    r"Google News/": None,
    r"Discover/": None,
    r"Google Kontakte/": None,
    r"Gmail/": None,
    r"Google Shopping": None,
    r"Google Unternehmensprofil/": None,
    r"Google Fotos/": None,
    r"Gespeichert/": None,
    r"Google Chat/": None,
    r"Business Messages/": None,
    r"Classroom/": None,
    r"Google-Konto/": None,
    r"Google-Hilfe-Communities/": None,
    r"Kalender/": None,
    r"Aufgaben/": None,
    r"Maps \(Meine Orte\)/": None,
    r"Maps/": None,
    r"Profil/": None,
    r"Groups/": None,
    r"Drive/": None,
    r"Zugriffsprotokollaktivitäten/": None,
    r"Search Contributions/": None,
    r"Android-Gerätekonfigurationsdienst/": None,
    r"Archiv_Übersicht.html": None,  # description of takeout, not that useful
}
