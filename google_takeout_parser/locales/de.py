from .common import TakeoutFile, HandlerMap

HANDLER_MAP: HandlerMap = {
    # Chrome
    r"Chrome/BrowserHistory.json": TakeoutFile.CHROME_HISTORY,
    r"Chrome": None,  # Ignore rest of Chrome stuff

    r"Google Play Store/Installs.json": TakeoutFile.GPLAYSTORE_INSTALLS,
    r"Google Play Store/": None,  # ignore anything else in Play Store
    r"Standortverlauf/Semantic Location History/.*/.*.json": TakeoutFile.LOCATION_HISTORY_SEMANTIC,  
    r"Standortverlauf/Records.json": TakeoutFile.LOCATION_HISTORY,
    # Youtube
    r"YouTube( und YouTube Music)?/Verlauf/.*?.html":  TakeoutFile.YOUTUBE_HISTORY_HTML,
    r"YouTube( und YouTube Music)?/Verlauf/.*?.json": TakeoutFile.YOUTUBE_HISTORY_JSON,
    r"YouTube( und YouTube Music)?/Meine Kommentare/.*?.html": TakeoutFile.YOUTUBE_COMMENT,
    r"YouTube( und YouTube Music)?/meine-live-chat-nachrichten/.*?.html": TakeoutFile.YOUTUBE_COMMENT,
    r"YouTube( und YouTube Music)?/Playlists/Liked videos.json": TakeoutFile.YOUTUBE_LIKES,
    r"YouTube( und Youtube Music)?/*": None, # ignore anything else in Youtube
    # Activities
    r"Meine Aktivitäten/.*?Meine\s*Aktivitäten.html": TakeoutFile.ACTIVITY_HTML,
    r"Meine Aktivitäten/.*?Meine\s*Aktivitäten.json": TakeoutFile.ACTIVITY_JSON,
    # Ignored Google Services
    r"Google Play-Spieldienste/": None,
    r"Google Developers/": None,
    r"Google Play/": None,
    r"Google Pay": None,
    r"Home App/": None,
    r"Google Shopping": None,
    r"Google Play Filme _ Serien/": None,
    r"Google News/": None,
    r"Google Kontakte/": None,
    r"Gmail/": None,
    r"Google Shopping": None,
    r"Google Unternehmensprofil/": None,
    r"Google Fotos/": None,
    r"Gespeichert/": None,
    r"Business Messages/": None,
    r"Classroom/":None,
    r"Google-Konto/": None,
    r"Google-Hilfe-Communities/": None,
    r"Kalender/": None,
    r"Maps (Meine Orte)/": None,
    r"Maps/": None,
    r"Profil/": None,
    r"Drive/": None,

    r"Zugriffsprotokollaktivitäten/": None,
    r"Android-Gerätekonfigurationsdienst/": None,
    r"Archiv_Übersicht.html": None # description of takeout, not that useful
}