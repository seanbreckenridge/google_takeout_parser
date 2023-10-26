from typing import List
from pathlib import Path

from .en import HANDLER_MAP as EN_DEFAULT_HANDLER_MAP
from .de import HANDLER_MAP as DE_DEFAULT_HANDLER_MAP

LOCALES = {
    "EN": EN_DEFAULT_HANDLER_MAP,
    "DE": DE_DEFAULT_HANDLER_MAP,
}


def get_json_activity_paths() -> List[str]:
    """
    returns the base directory name for which the json activity parses for every locale

    for example, the EN path is:
    My Activity/Ads/MyActivity.json

    in german its
    Meine Aktivität/Werbung/MeineAktivität.json

    this will return ['My Activity', 'Meine Aktivität']

    this is used in HPI to find the correct directory to parse

    note: should probably remove whitespace as well, so like:

    ['My Activity', 'MyActivity', 'Meine Aktivität', 'MeineAktivität'] when testing against filepaths
    """
    from ..parse_json import _parse_json_activity

    paths = []
    for handler_map in LOCALES.values():
        for path, function in handler_map.items():
            if function == _parse_json_activity:
                paths.append(Path(path.strip("/")).parts[0])

    return paths
