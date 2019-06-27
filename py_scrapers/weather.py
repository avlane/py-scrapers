"""Read a weather forecast table."""
from .soup import make_soup


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
