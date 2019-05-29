"""Fetching pages politely."""
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

USER_AGENT = "py-scrapers/0.1 (learning project)"


class FetchError(Exception):
    def __init__(self, url, status):
        super().__init__("{} returned HTTP {}".format(url, status))
        self.url = url
        self.status = status


class RobotsDisallowed(FetchError):
    def __init__(self, url):
        Exception.__init__(self, "robots.txt does not allow fetching {}".format(url))
        self.url = url
        self.status = None


def get_session():
    import requests  # imported here so the rest of the package works without it

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    return session


class Fetcher:
    """Fetch pages one at a time, waiting at least `delay` seconds between requests."""

    def __init__(self, session=None, delay=1.0, timeout=10, sleep=time.sleep, clock=time.monotonic,
                 respect_robots=True):
        self._session = session
        self.delay = delay
        self.timeout = timeout
        self.sleep = sleep
        self.clock = clock
        self._last_request = None
        self.respect_robots = respect_robots
        self._robots = {}

    @property
    def session(self):
        if self._session is None:
            self._session = get_session()
        return self._session

    def _wait(self):
        if self._last_request is None:
            return
        remaining = self.delay - (self.clock() - self._last_request)
        if remaining > 0:
            self.sleep(remaining)

    def _robots_for(self, url):
        parts = urlsplit(url)
        origin = "{}://{}".format(parts.scheme, parts.netloc)
        if origin not in self._robots:
            parser = RobotFileParser()
            self._wait()
            response = self.session.get(origin + "/robots.txt", timeout=self.timeout)
            self._last_request = self.clock()
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                parser.parse([])  # no robots.txt: everything is allowed
            self._robots[origin] = parser
        return self._robots[origin]

    def allowed(self, url):
        if not self.respect_robots:
            return True
        return self._robots_for(url).can_fetch(USER_AGENT, url)

    def get(self, url):
        if not self.allowed(url):
            raise RobotsDisallowed(url)
        self._wait()
        response = self.session.get(url, timeout=self.timeout)
        self._last_request = self.clock()
        if response.status_code >= 400:
            raise FetchError(url, response.status_code)
        return response.text
