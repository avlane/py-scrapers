"""Read a weather forecast table."""
import re
from collections import namedtuple

from .soup import make_soup

Day = namedtuple("Day", "day outlook high low rain_chance")
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def parse_number(text):
    """'14°C' -> 14, '80%' -> 80, '—' -> None"""
    match = NUMBER_RE.search(text)
    if not match:
        return None
    value = float(match.group(0))
    return int(value) if value.is_integer() else value


def parse_table(table):
    """Turn an HTML table into a list of dicts keyed by the lower-cased header text."""
    rows = table.find_all("tr")
    if not rows:
        return []
    headers = [cell.get_text(strip=True).lower() for cell in rows[0].find_all("th")]
    result = []
    for row in rows[1:]:
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if cells:
            result.append(dict(zip(headers, cells)))
    return result


def parse_forecast(html, table_id="forecast"):
    soup = make_soup(html)
    table = soup.find("table", attrs={"id": table_id})
    if table is None:
        raise ValueError("no table with id {!r} on the page".format(table_id))
    return parse_table(table)


def forecast_days(html, table_id="forecast"):
    days = []
    for row in parse_forecast(html, table_id):
        days.append(Day(row["day"], row["outlook"], parse_number(row["high"]),
                        parse_number(row["low"]), parse_number(row["rain"])))
    return days


def to_fahrenheit(celsius):
    return None if celsius is None else round(celsius * 9 / 5 + 32)


def format_days(days, fahrenheit=False):
    unit = "F" if fahrenheit else "C"
    convert = to_fahrenheit if fahrenheit else (lambda value: value)
    lines = ["{:<10} {:<16} {:>6} {:>6} {:>6}".format("Day", "Outlook", "High", "Low", "Rain")]
    for day in days:
        high, low = convert(day.high), convert(day.low)
        lines.append("{:<10} {:<16} {:>6} {:>6} {:>6}".format(
            day.day, day.outlook,
            "-" if high is None else "{}{}".format(high, unit),
            "-" if low is None else "{}{}".format(low, unit),
            "-" if day.rain_chance is None else "{}%".format(day.rain_chance)))
    return "\n".join(lines)
