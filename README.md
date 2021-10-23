# google_takeout_parser

WIP

- [x] parse both the Historical HTML and new JSON format for Google Takeouts
- [x] cache individual takeout results behind [cachew](https://github.com/karlicoss/cachew)
- [x] merge takeouts into unique events
- [ ] CLI interface/Usage examples
- [ ] push to pypi?

Parses data out of your Google Takeout (History, Activity, Youtube, Locations, etc...)

This doesn't handle all cases, but I have yet to find a parser that does, so here is my attempt. The Google Takeout is pretty particular, and the contents of the directory depend. Unhandled files will warn, though feel free to PR a parser or create an issue if this doesn't parse some part you want.

This can take a few minutes to parse depending on what you have in your Takeout (especially while using the old HTML format), so this uses [cachew](https://github.com/karlicoss/cachew) to cache the function result for each Takeout you may have.

To use, go to [takeout.google.com](https://takeout.google.com/); For Reference, I select:

- Chrome
- Google Play Store
- Location History
  - Select JSON as format
- My Activity
  - Select JSON as format
- Youtube and Youtube Music
  - go to options and select JSON instead of HTML
  - deselect music-library-songs, music-uploads and videos)

The process for getting these isn't that great -- you have to manually go to takeout.google.com every few months, select what you want to export manually info, and then it puts the zipped file into your google drive. You can tell it to run it at specific intervals, but I personally haven't found that to be that reliable.

This was extracted out of [my HPI](https://github.com/seanbreckenridge/HPI/tree/4bb1f174bdbd693ab29e744413424d18b8667b1f/my/google) modules, which was in turn modified from the google files in [karlicoss/HPI](https://github.com/karlicoss/HPI/blob/4a04c09f314e10a4db8f35bf1ecc10e4d0203223/my/google/takeout/html.py)

## Installation

Requires `python3.7+`

To install with pip, run:

    pip install git+https://github.com/seanbreckenridge/google_takeout_parser

---

## Usage

TODO: add

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/google_takeout_parser'
cd ./google_takeout_parser
pip install '.[testing]'
mypy ./google_takeout_parser
pytest
```
