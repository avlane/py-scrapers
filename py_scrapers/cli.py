"""Command line entry point: python3 -m py_scrapers <command>."""
import argparse
import sys

from . import books, weather
from .http import Fetcher


def build_parser():
    parser = argparse.ArgumentParser(prog="py_scrapers", description="Small polite scrapers.")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait between requests (default 1)")
    parser.add_argument("--ignore-robots", action="store_true", help="do not read robots.txt (be careful)")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    p_books = sub.add_parser("books", help="list book prices from a catalogue")
    p_books.add_argument("url")
    p_books.add_argument("--pages", type=int, default=1, help="how many pages to follow (default 1)")
    p_books.add_argument("--csv", metavar="PATH", help="write the results to a CSV file")

    p_weather = sub.add_parser("weather", help="show a forecast table")
    p_weather.add_argument("url")
    p_weather.add_argument("--fahrenheit", action="store_true")
    return parser


def main(argv=None, fetcher=None, out=None):
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    fetcher = fetcher or Fetcher(delay=args.delay, respect_robots=not args.ignore_robots)

    if args.command == "books":
        found = books.scrape(args.url, fetcher, max_pages=args.pages)
        if args.csv:
            with open(args.csv, "w", newline="", encoding="utf-8") as f:
                books.write_csv(found, f)
            print("Wrote {} books to {}".format(len(found), args.csv), file=out)
        else:
            for book in found:
                print("{:>8}  {}".format(str(book["price"]), book["title"]), file=out)
    elif args.command == "weather":
        days = weather.forecast_days(fetcher.get(args.url))
        print(weather.format_days(days, args.fahrenheit), file=out)
    return 0
