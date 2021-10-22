"""
Related to locating the default cache directory for this module
"""

import os
from pathlib import Path

cache_dir = os.environ.get("XDG_CACHE_HOME", os.path.join(os.environ["HOME"], ".cache"))
takeout_cache_path = Path(cache_dir) / "google_takeout_parser"
