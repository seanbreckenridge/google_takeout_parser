# google_takeout_parser

- parses both the Historical HTML and new JSON format for Google Takeouts
- caches individual takeout results behind [`cachew`](https://github.com/karlicoss/cachew)
- merge multiple takeouts into unique events

Parses data out of your [Google Takeout](https://takeout.google.com/) (History, Activity, Youtube, Locations, etc...)

This doesn't handle all cases, but I have yet to find a parser that does, so here is my attempt at parsing what I see as the most useful info from it. The Google Takeout is pretty particular, and the contents of the directory depend on what you select while exporting. Unhandled files will warn, though feel free to [PR a parser](#contributing) or [create an issue](https://github.com/seanbreckenridge/google_takeout_parser/issues/new?title=add+parser+for) if this doesn't parse some part you want.

This can take a few minutes to parse depending on what you have in your Takeout (especially while using the old HTML format), so this uses [cachew](https://github.com/karlicoss/cachew) to cache the function result for each Takeout you may have. That means this'll take a few minutes the first time parsing a takeout, but then only a few seconds every subsequent time.

Since the Takeout slowly removes old events over time, I would recommend periodically (personally I do it once every few months) backing up your data, to not lose any old events and get data from new ones. To use, go to [takeout.google.com](https://takeout.google.com/); For Reference, once on that page, I hit `Deselect All`, then select:

- Chrome
- Google Play Store
- Location History
  - Select JSON as format
- My Activity
  - Select JSON as format
- Youtube and Youtube Music
  - Select JSON as format
  - In options, deselect `music-library-songs`, `music-uploads` and `videos`

The process for getting these isn't that great -- you have to manually go to [takeout.google.com](https://takeout.google.com) every few months, select what you want to export info for, and then it puts the zipped file into your google drive. You can tell it to run it at specific intervals, but I personally haven't found that to be that reliable.

This was extracted out of [my HPI](https://github.com/seanbreckenridge/HPI/tree/4bb1f174bdbd693ab29e744413424d18b8667b1f/my/google) modules, which was in turn modified from the google files in [karlicoss/HPI](https://github.com/karlicoss/HPI/blob/4a04c09f314e10a4db8f35bf1ecc10e4d0203223/my/google/takeout/html.py)

## Installation

Requires `python3.7+`

To install with pip, run:

    pip install google_takeout_parser

## Usage

### CLI Usage

Can be access by either `google_takeout_parser` or `python -m google_takeout_parser`. Offers a basic interface to list/clear the cache directory, and/or parse/merge a takeout and interact with it in a REPL:

To clear the `cachew` cache: `google_takeout_parser cache_dir clear`

A few examples of parsing takeouts:

```
$ google_takeout_parser --quiet parse ~/data/Unpacked_Takout --cache
Interact with the export using res

In [1]: res[-2]
Out[1]: PlayStoreAppInstall(title='Hangouts', device_name='motorola moto g(7) play', dt=datetime.datetime(2020, 8, 2, 15, 51, 50, 180000, tzinfo=datetime.timezone.utc))

In [2]: len(res)
Out[2]: 236654
```

`$ google_takeout_parser --quiet merge ./Takeout-Old ./Takeout-New --action summary --no-cache`

```python
Counter({'Activity': 366292,
         'Location': 147581,
         'YoutubeComment': 131,
         'PlayStoreAppInstall': 122,
         'LikedYoutubeVideo': 100,
         'ChromeHistory': 4})
```

Can also dump the info to JSON; e.g. to filter YouTube links from your Activity:

```bash
google_takeout_parser parse -a json --no-cache ./Takeout-New \
  | jq '.[] | select(.type == "Activity") | select(.header == "YouTube") | .titleUrl'
```

Also contains a small utility command to help move/extract the google takeout:

```bash
$ google_takeout_parser move --from ~/Downloads/takeout*.zip --to-dir ~/data/google_takeout --extract
Extracting /home/sean/Downloads/takeout-20211023T070558Z-001.zip to /tmp/tmp07ua_0id
Moving /tmp/tmp07ua_0id/Takeout to /home/sean/data/google_takeout/Takeout-1634993897
$ ls -1 ~/data/google_takeout/Takeout-1634993897
archive_browser.html
Chrome
'Google Play Store'
'Location History'
'My Activity'
'YouTube and YouTube Music'
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
from google_takeout.path_dispatch import TakeoutParser
tp = TakeoutParser("/full/path/to/Takeout-1599315526")
# to check if files are all handled
tp.dispatch_map()
# to parse without caching the results in ~/.cache/google_takeout_parser
uncached = list(tp.parse())
# to parse with cachew cache https://github.com/karlicoss/cachew
cached = list(tp.parse(cache=True))
```

To cache and merge takeouts (maintains a single dependency on the paths you pass -- so if you change the input paths, it does a full recompute)

```python
from google_takeout.merge import cached_merge_takeouts
results = list(cached_merge_takeouts(["/full/path/to/Takeout-1599315526", "/full/path/to/Takeout-1634971143"]))
```

If you don't want to cache the results but want to merge results from multiple takeouts, can do something custom by directly using the `merge_events` function:

```python
from google_takeout_parser.merge import merge_events, TakeoutParser
itrs = []  # list of iterators of google events
for path in ['path/to/Takeout-1599315526' 'path/to/Takeout-1616796262']:
    # ignore errors
    tk = TakeoutParser(path, error_policy="drop")
    itrs.append(tk.parse(cache=False))
res = list(merge_events(*itrs))
```

The events this returns is a combination of all types in the [`models.py`](google_takeout_parser/models.py), to filter to a particular type you can provide that to skip parsing other files:

```python
from google_takeout_parser.models import Location
from google_takeout_parser.path_dispatch import TakeoutParser
locations = list(TakeoutParser("path/to/Takeout").parse(filter_type=Location))
len(locations)
99913
```

I personally exclusively use this through the [HPI google takeout](https://github.com/karlicoss/HPI/blob/master/my/google/takeout/parser.py) file, as a configuration layer to locate where my takeouts are on disk, and since that 'automatically' unzips the takeouts (I store them as the zips), i.e., doesn't require me to maintain an unpacked view

### Contributing

Just to give a brief overview, to add new functionality (parsing some new folder that this doesn't currently support), you'd need to:

- Add a `model` for it in [`models.py`](google_takeout_parser/models.py) subclassing `BaseEvent` and adding it to the Union at the bottom of the file. That should have a `key` property function which describes each event uniquely (used to merge takeout events)
- Write a function which takes the `Path` to the file you're trying to parse and converts it to the model you created (See examples in [`parse_json.py`](google_takeout_parser/parse_json.py)). Ideally extract a single raw item from the takeout file add a test for it so its obvious when/if the format changes.
- Set [the `return_type`](https://github.com/seanbreckenridge/google_takeout_parser/blob/7b1ee8ec3c3f36e6f279f20a9a214b6a3e8775f5/google_takeout_parser/parse_json.py#L71) property on the function, to use for caching/filtering
- Add a regex match for the file path to the [`DEFAULT_HANDLER_MAP`](https://github.com/seanbreckenridge/google_takeout_parser/blob/2bd64b7373e4a2ac2ace32e03b25ca3b7e901034/google_takeout_parser/path_dispatch.py#L48)

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/google_takeout_parser'
cd ./google_takeout_parser
pip install '.[testing]'
mypy ./google_takeout_parser
flake8 ./google_takeout_parser
pytest
```
