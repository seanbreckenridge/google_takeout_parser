## This is for splitting the old HTML format, you shouldn't use this for new exports

This dir contains a go script to split an HTML file into smaller chunks, so its possible to parse on machines with limited memory.

In particular, I had issues using this with [termux](https://termux.dev/en/) on my phone, as the ~100MB takeout HTML files when parsed by loading the whole file into memory cause my terminal to just crash since it runs out of memory

So, this script splits the HTML files into lots of smaller chunks, like:

```
MyActivity-001.html
MyActivity-002.html
MyActivity-003.html
MyActivity-004.html
MyActivity-005.html
MyActivity-006.html
```

To build: `go build -o split_html`

```
Usage: ./split_html [options] input
  -count int
    	how many cells to split into each file (default 1000)
  -output string
    	output directory. if not specified, will use the directory of the input file
```

Then, use it against any large files that you have problems parsing:

```bash
./split_html ~/data/takeout/something/MyActivity/YouTube/MyActivity.html
# move other file somewhere else
mv ~/data/takeout/something/MyActivity/Youtube/MyActivity.html /tmp
# test parsing to make sure they still work
google_takeout_parser merge -a summary ~/data/takeout/something
```

This splits the `100MB+` HTML files into dozens of small files sized about `~700K`.

I personally **created copies** of all of my HTML exports, and did:

```
find ~/Downloads/takeout/ -name 'MyActivity.html' -exec ./split_html "{}" \;
find ~/Downloads/takeout/ -name 'MyActivity.html' -delete
```

And then used `google_takeout_parser merge -a summary` to compare the new and old outputs before removing the old files
