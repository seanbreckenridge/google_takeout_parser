"""
Related to locating the default cache directory for this module
"""

from pathlib import Path
from platformdirs import user_cache_dir

cache_dir = user_cache_dir()  # handle portability issues/$HOME not being set
takeout_cache_path = Path(cache_dir) / "google_takeout_parser"
