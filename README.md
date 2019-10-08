# py-scrapers

Practice with web scraping in Python: `requests` for fetching and BeautifulSoup for parsing.
It started as a way to learn the tools and grew a few habits I wanted to keep: be polite, be testable, never hit a site while developing a parser.

Three small scrapers share one fetching layer:

* **books**: titles, prices, star ratings and stock status from a catalogue, following the "next" link, with CSV export and a price-change report between two exports.
* **weather**: reads a forecast table into numbers (the "no data" dash becomes empty).
* **rss**: lists the newest items of an RSS 2.0 or Atom feed, optionally since a date.

## Install

```
pip install -r requirements.txt
```

`requests` is only needed when talking to a real site. BeautifulSoup is used when it is installed, otherwise the parsers use `py_scrapers/htmltree.py`, a small standard library tree with the same `find`/`find_all`/`get_text` calls.
Python 3.6 or newer.

## Use

```
python3 -m py_scrapers books http://books.example.com/index.html --pages 3 --csv today.csv
python3 -m py_scrapers price-changes last_week.csv today.csv
python3 -m py_scrapers weather http://weather.example.com/harlow --fahrenheit
python3 -m py_scrapers rss https://gazette.example.com/rss --since 2019-07-01 --limit 5
```

Options before the command apply to every scraper: `--delay SECONDS` (default 1), `--cache-dir DIR` and `--ignore-robots`.

The example hostnames are made up; point the commands at a site you are allowed to scrape.

## Being polite

* `robots.txt` is fetched once per host and respected. `--ignore-robots` exists for pages you own.
* At least `--delay` seconds pass between requests.
* 429 and 5xx responses are retried with exponential backoff and `Retry-After` is honoured (capped at two minutes).
* `--cache-dir` keeps pages for an hour so parser work does not mean repeated requests.
* The User-Agent says what the script is.

## Tests

```
python3 -m unittest discover
```

The tests run against saved pages in `tests/fixtures` and a fake session, so they need no network and no third party packages.