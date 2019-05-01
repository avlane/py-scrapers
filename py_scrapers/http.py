"""Fetching pages."""

USER_AGENT = "py-scrapers/0.1 (learning project)"


def get_session():
    import requests  # imported here so the rest of the package works without it

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    return session


def fetch(url, session=None, timeout=10):
    """Return the body of url as text."""
    session = session or get_session()
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text
