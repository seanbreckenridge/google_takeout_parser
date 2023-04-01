from .common import TakeoutFile, HandlerMap

# Note: when I say 'no info here' or 'not useful', is just how the
# data appears in my export. It might be useful for you -- if so
# feel free to make a PR or an issue to parse it
#
# Can also extend or overwrite these functions by passing
# 'None' if you don't want a certain part to be parsed,
# or by passing your own function which parses the file something from models.py

# Reminder that dicts are ordered, so order here can matter
# If you want to parse one file from a folder with lot of files, can
# specify that file, and then on the next line specify 'None'
# for the folder, ignoring the rest of files

# Setting 'None' in the handler map specifies that we should ignore this file

HANDLER_MAP: HandlerMap = {
    r"Chrome/BrowserHistory.json": TakeoutFile.CHROME_HISTORY,
    r"Chrome": None,  # Ignore rest of Chrome stuff
    r"Google Play Store/Installs.json": TakeoutFile.GPLAYSTORE_INSTALLS,
    r"Google Play Store/": None,  # ignore anything else in Play Store
    r"Location History/Semantic Location History/.*/.*.json": TakeoutFile.LOCATION_HISTORY_SEMANTIC,
    # optional space to handle pre-2017 data
    r"Location History/Location( )?History.json": TakeoutFile.LOCATION_HISTORY,  
    r"Location History/Records.json": TakeoutFile.LOCATION_HISTORY,  
    r"Location History/Settings.json": None,
    # HTML/JSON activity-like files which aren't in 'My Activity'
    # optional " and Youtube Music" to handle pre-2017 data
    r"YouTube( and YouTube Music)?/history/.*?.html": TakeoutFile.YOUTUBE_HISTORY_HTML,
    r"YouTube( and YouTube Music)?/history/.*?.json": TakeoutFile.YOUTUBE_HISTORY_JSON,
    # basic list item files which have chat messages/comments
    r"YouTube( and YouTube Music)?/my-comments/.*?.html": TakeoutFile.YOUTUBE_COMMENT,
    r"YouTube( and YouTube Music)?/my-live-chat-messages/.*?.html": TakeoutFile.YOUTUBE_COMMENT,
    r"YouTube( and YouTube Music)?/playlists/likes.json": TakeoutFile.YOUTUBE_LIKES,
    r"YouTube( and YouTube Music)?/playlists/": None,
    r"YouTube( and YouTube Music)?/subscriptions": None,
    r"YouTube( and YouTube Music)?/videos": None,
    r"YouTube( and YouTube Music)?/music-uploads": None,
    r"My Activity/Assistant/.*.mp3": None,  # might be interesting to extract timestamps
    r"My Activity/Voice and Audio/.*.mp3": None,
    r"My Activity/Takeout": None,  # activity for when you made takeouts, dont need
    # HTML 'My Activity' Files
    r"My Activity/.*?My\s*Activity.html": TakeoutFile.ACTIVITY_HTML,
    r"My Activity/.*?My\s*Activity.json": TakeoutFile.ACTIVITY_JSON,
    # Maybe parse these?
    r"Access Log Activity": None,
    r"Assistant Notes and Lists/.*.csv": None,
    r"Blogger/Comments/.*?feed.atom": None,
    r"Blogger/Blogs/": None,
    # Fit has possibly interesting data
    # Fit/Daily activity metrics/2015-07-27.csv
    # Fit/Activities/2017-10-29T23_08_59Z_PT2M5.699S_Other.tcx
    # Fit/All Data/derived_com.google.calories.bmr_com.google.and.json
    r"Fit/": None,
    r"Groups": None,
    r"Google Play Games Services/Games/.*/(Achievements|Activity|Experience|Scores).html": None,
    r"Hangouts": None,
    r"Keep": None,
    r"Maps (your places)": None,
    r"My Maps/.*.kmz": None,  # custom KML maps
    r"Saved/.*.csv": None,  # lists with saved places from Google Maps
    r"Shopping Lists/.*.csv": None,
    r"Tasks": None,
    # Files to ignore
    r"Android Device Configuration Service/": None,
    r"Blogger/Albums/": None,
    r"Blogger/Profile/": None,
    r"Calendar/": None,
    r"Cloud Print/": None,
    r"Contacts/": None,
    r"Drive/": None,
    r"Google Account/": None,
    r"Google Business Profile/": None,
    r"Google My Business/": None,
    r"Google Pay/": None,
    r"Google Photos/": None,  # has images/some metadata on each of them
    r"Google Play Books/.*.pdf": None,
    r"Google Play Games Services/Games/.*/(Data.bin|Metadata.html)": None,
    r"Google Play Movies.*?/": None,
    r"Google Shopping/": None,
    r"Google Store/": None,
    r"Google Translator Toolkit/": None,
    r"Google Workspace Marketplace/": None,
    r"Home App/": None,
    r"Mail/": None,
    r"Maps/": None,
    r"News/": None,
    r"Profile/Profile.json": None,
    r"Saved/Favorite places.csv": None,
    r"Search Contributions/": None,
    r"archive_browser.html": None # description of takeout, not that useful
}