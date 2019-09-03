"""Command line entry point: python3 -m py_scrapers <command>."""
import argparse
import sys

from datetime import datetime, timezone

from . import books, rss, weather
from .http import Fetcher


def build_parser():
    parser = argparse.ArgumentParser(prog="py_scrapers", description="Small polite scrapers.")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait between requests (default 1)")
    parser.add_argument("--ignore-robots", action="store_true", help="do not read robots.txt (be careful)")
    parser.add_argument("--cache-dir", metavar="DIR", help="keep fetched pages here for an hour (handy while developing a parser)")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    p_books = sub.add_parser("books", help="list book prices from a catalogue")
    p_books.add_argument("url")
    p_books.add_argument("--pages", type=int, default=1, help="how many pages to follow (default 1)")
    p_books.add_argument("--csv", metavar="PATH", help="write the results to a CSV file")

    p_weather = sub.add_parser("weather", help="show a forecast table")
    p_weather.add_argument("url")
    p_weather.add_argument("--fahrenheit", action="store_true")

    p_rss = sub.add_parser("rss", help="list the newest items of an RSS or Atom feed")
    p_rss.add_argument("url")
    p_rss.add_argument("--since", metavar="YYYY-MM-DD", help="only items published on or after this date")
    p_rss.add_argument("--limit", type=int, default=10)
    return parser


def main(argv=None, fetcher=None, out=None):
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    fetcher = fetcher or Fetcher(delay=args.delay, respect_robots=not args.ignore_robots,
                          cache_dir=args.cache_dir)

    if args.command == "books":
        found = books.scrape(args.url, fetcher, max_pages=args.pages)
        if args.csv:
            with open(args.csv, "w", newline="", encoding="utf-8") as f:
                books.write_csv(found, f)
            print("Wrote {} books to {}".format(len(found), args.csv), file=out)
        else:
            for book in found:
                print("{:>8}  {}".format(str(book.price), book.title), file=out)
    elif args.command == "weather":
        days = weather.forecast_days(fetcher.get(args.url))
        print(weather.format_days(days, args.fahrenheit), file=out)
    elif args.command == "rss":
        items = rss.newest_first(rss.parse_rss(fetcher.get(args.url)))
        if args.since:
            cutoff = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            items = rss.since(items, cutoff)
        for item in items[:args.limit]:
            when = item["published"].strftime("%Y-%m-%d") if item["published"] else "no date"
            print("{}  {}\n            {}".format(when, item["title"], item["link"]), file=out)
    return 0
