# google_takeout_parser

- parses both the Historical HTML and new JSON format for Google Takeouts
- caches individual takeout results behind [`cachew`](https://github.com/karlicoss/cachew)
- merge multiple takeouts into unique events

Parses data out of your [Google Takeout](https://takeout.google.com/) (History, Activity, Youtube, Locations, etc...)

This doesn't handle all cases, but I have yet to find a parser that does, so here is my attempt at parsing what I see as the most useful info there. The Google Takeout is pretty particular, and the contents of the directory depend on what you select while exporting. Unhandled files will warn, though feel free to PR a parser or create an issue if this doesn't parse some part you want.

This can take a few minutes to parse depending on what you have in your Takeout (especially while using the old HTML format), so this uses [cachew](https://github.com/karlicoss/cachew) to cache the function result for each Takeout you may have. That means this'll take a few minutes the first time parsing a takeout, but then only a few seconds every subsequent time.

Since the Takeout slowly removes old events over time, I would recommend periodically (personally I do it once every few months) backing up your data, to not lose any new events and get data from new ones. To use, go to [takeout.google.com](https://takeout.google.com/); For Reference, once on that page, I hit `Deselect All`, then select:

- Chrome
- Google Play Store
- Location History
  - Select JSON as format
- My Activity
  - Select JSON as format
- Youtube and Youtube Music
  - go to options and select JSON instead of HTML
  - deselect music-library-songs, music-uploads and videos

The process for getting these isn't that great -- you have to manually go to takeout.google.com every few months, select what you want to export info for, and then it puts the zipped file into your google drive. You can tell it to run it at specific intervals, but I personally haven't found that to be that reliable.

This was extracted out of [my HPI](https://github.com/seanbreckenridge/HPI/tree/4bb1f174bdbd693ab29e744413424d18b8667b1f/my/google) modules, which was in turn modified from the google files in [karlicoss/HPI](https://github.com/karlicoss/HPI/blob/4a04c09f314e10a4db8f35bf1ecc10e4d0203223/my/google/takeout/html.py)

## Installation

Requires `python3.7+`

To install with pip, run:

    pip install git+https://github.com/seanbreckenridge/google_takeout_parser

## Usage

### CLI Usage

Can be executing `google_takeout_parser` or `python -m google_takeout_parser`. Offers a basic interface to list/clear the cache directory, and/or parse a takeout and interact with it in a REPL:

To clear the `cachew` cache: `google_takeout_parser cache_dir clear`

To parse a takeout:

```
$ google_takeout_parser parse ~/data/Unpacked_Takout --cache
Parsing...
Interact with the export using res

In [1]: res[-2]
Out[1]: PlayStoreAppInstall(title='Hangouts', device_name='motorola moto g(7) play', dt=datetime.datetime(2020, 8, 2, 15, 51, 50, 180000, tzinfo=datetime.timezone.utc))

In [2]: len(res)
Out[2]: 236654
```

### Library Usage

Assuming you maintain an unpacked view, e.g. like:

```
 $ tree -L 1 ./Takeout-1599315526
./Takeout-1599315526
├── Google Play Store
├── Location History
├── My Activity
└── YouTube and YouTube Music
```

To parse one takeout:

```python
fro pathlib import Path
from google_takeout.path_dispatch import TakeoutParser
tp = TakeoutParser(Path("/full/path/to/Takeout-1599315526"))
# to check if files are all handled
tp.dispatch_map()
# to parse without caching the results in ~/.cache/google_takeout_parser
uncached = list(tp.parse())
# to parse with cachew cache https://github.com/karlicoss/cachew
cached = list(tp.cached_parse())
```

To merge takeouts:

```python
from pathlib import Path
from google_takeout.merge import cached_merge_takeouts
results = list(cached_merge_takeouts(["/full/path/to/Takeout-1599315526", "/full/path/to/Takeout-1634971143"]))
```

The events this returns is a combination of all types in the [`models.py`](google_takeout_parser/models.py) (to support easy serialization with cachew), to filter to a particular just do an `isinstance` check:

```python
from google_takeout_parser.models import Location
takeout_generator = TakeoutParser(Path("/full/path/to/Takeout")).cached_parse()
locations = list(filter(lambda e: isinstance(e, Location), takeout_generator))
>>> len(locations)
99913
```

I personally exclusively use this through my [HPI google takeout](https://github.com/seanbreckenridge/HPI/blob/master/my/google_takeout.py) file, as a configuration layer to locate where my takeouts are on disk, and since that 'automatically' unzips the takeouts (I store them as the zips), i.e., doesn't require me to maintain an unpacked view

### Contributing

Just to give a brief overview, to add new functionality (parsing some new folder that this doesn't currently support), you'd need to:

- Add a `model` for it in [`models.py`](google_takeout_parser/models.py), which a `key` property function which describes each event uniquely (used to merge takeout events); add it to the `Event` Union
- Write a function which takes the `Path` to the file you're trying to parse and converts it to the model you created (See examples in [`parse_json.py`](google_takeout_parser/parse_json.py)). If its relatively complicated (e.g. HTML), ideally extract a `div` from the page and add a test for it so its obvious when/if the format changes.
- Add a regex match for the file path to the [`DEFAULT_HANDLER_MAP`](https://github.com/seanbreckenridge/google_takeout_parser/blob/2bd64b7373e4a2ac2ace32e03b25ca3b7e901034/google_takeout_parser/path_dispatch.py#L48)

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/google_takeout_parser'
cd ./google_takeout_parser
pip install '.[testing]'
mypy ./google_takeout_parser
pytest
```
