import os
import tempfile
import unittest

from py_scrapers.http import FetchError, Fetcher, RobotsDisallowed, retry_after_seconds
from tests.helpers import FakeResponse, FakeSession


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FetcherTests(unittest.TestCase):
    def make(self, responses, delay=2.0):
        clock = Clock()
        session = FakeSession(responses)
        return Fetcher(session, delay=delay, sleep=clock.sleep, clock=clock.time, respect_robots=False), session, clock

    def test_returns_text(self):
        fetcher, _, _ = self.make({"http://x/a": FakeResponse("hello")})
        self.assertEqual(fetcher.get("http://x/a"), "hello")

    def test_first_request_does_not_wait(self):
        fetcher, _, clock = self.make({"http://x/a": FakeResponse("a")})
        fetcher.get("http://x/a")
        self.assertEqual(clock.sleeps, [])

    def test_waits_between_requests(self):
        fetcher, _, clock = self.make({"http://x/a": FakeResponse("a"), "http://x/b": FakeResponse("b")})
        fetcher.get("http://x/a")
        clock.now += 0.5
        fetcher.get("http://x/b")
        self.assertEqual(len(clock.sleeps), 1)
        self.assertAlmostEqual(clock.sleeps[0], 1.5)

    def test_no_wait_if_enough_time_has_passed(self):
        fetcher, _, clock = self.make({"http://x/a": FakeResponse("a"), "http://x/b": FakeResponse("b")})
        fetcher.get("http://x/a")
        clock.now += 10
        fetcher.get("http://x/b")
        self.assertEqual(clock.sleeps, [])

    def test_http_errors(self):
        fetcher, _, _ = self.make({"http://x/missing": FakeResponse("", 404)})
        with self.assertRaises(FetchError) as caught:
            fetcher.get("http://x/missing")
        self.assertEqual(caught.exception.status, 404)


class RetryTests(unittest.TestCase):
    def make(self, responses, **kwargs):
        clock = Clock()
        session = FakeSession(responses)
        fetcher = Fetcher(session, delay=0, respect_robots=False, sleep=clock.sleep, clock=clock.time, **kwargs)
        return fetcher, session, clock

    def test_retries_server_errors_with_exponential_backoff(self):
        fetcher, session, clock = self.make({"http://x/a": [FakeResponse("", 503), FakeResponse("", 502),
                                                            FakeResponse("done")]})
        self.assertEqual(fetcher.get("http://x/a"), "done")
        self.assertEqual(len(session.calls), 3)
        self.assertEqual(clock.sleeps, [2.0, 4.0])

    def test_gives_up_after_max_retries(self):
        fetcher, session, _ = self.make({"http://x/a": [FakeResponse("", 500)] * 3}, max_retries=2)
        with self.assertRaises(FetchError) as caught:
            fetcher.get("http://x/a")
        self.assertEqual(caught.exception.status, 500)
        self.assertEqual(len(session.calls), 3)

    def test_client_errors_are_not_retried(self):
        fetcher, session, _ = self.make({"http://x/a": [FakeResponse("", 404)]})
        with self.assertRaises(FetchError):
            fetcher.get("http://x/a")
        self.assertEqual(len(session.calls), 1)

    def test_rate_limit_is_retried(self):
        fetcher, _, clock = self.make({"http://x/a": [FakeResponse("", 429), FakeResponse("ok")]})
        self.assertEqual(fetcher.get("http://x/a"), "ok")
        self.assertEqual(clock.sleeps, [2.0])


class RetryAfterTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(retry_after_seconds({"Retry-After": "30"}, 0), 30.0)

    def test_header_name_is_case_insensitive(self):
        self.assertEqual(retry_after_seconds({"retry-after": "5"}, 0), 5.0)

    def test_http_date(self):
        # 2019-08-15 12:00:30 GMT is 30 seconds after the fake "now"
        now = 1565870400.0
        self.assertEqual(retry_after_seconds({"Retry-After": "Thu, 15 Aug 2019 12:00:30 GMT"}, now), 30.0)

    def test_missing_or_bad(self):
        self.assertIsNone(retry_after_seconds({}, 0))
        self.assertIsNone(retry_after_seconds({"Retry-After": "soon"}, 0))

    def test_fetcher_waits_at_least_as_long_as_asked(self):
        clock = Clock()
        session = FakeSession({"http://x/a": [FakeResponse("", 429, {"Retry-After": "10"}), FakeResponse("ok")]})
        fetcher = Fetcher(session, delay=0, respect_robots=False, sleep=clock.sleep, clock=clock.time)
        self.assertEqual(fetcher.get("http://x/a"), "ok")
        self.assertEqual(clock.sleeps, [10.0])

    def test_absurd_waits_are_capped(self):
        clock = Clock()
        session = FakeSession({"http://x/a": [FakeResponse("", 503, {"Retry-After": "86400"}), FakeResponse("ok")]})
        fetcher = Fetcher(session, delay=0, respect_robots=False, sleep=clock.sleep, clock=clock.time, max_wait=90)
        fetcher.get("http://x/a")
        self.assertEqual(clock.sleeps, [90])


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = [1000.0]

    def make(self, session, **kwargs):
        return Fetcher(session, delay=0, respect_robots=False, cache_dir=self.tmp.name,
                       now=lambda: self.now[0], sleep=lambda s: None, **kwargs)

    def test_second_get_comes_from_the_cache(self):
        session = FakeSession({"http://x/a": [FakeResponse("first"), FakeResponse("second")]})
        fetcher = self.make(session)
        self.assertEqual(fetcher.get("http://x/a"), "first")
        self.assertEqual(fetcher.get("http://x/a"), "first")
        self.assertEqual(len(session.calls), 1)

    def test_stale_cache_is_refetched(self):
        session = FakeSession({"http://x/a": [FakeResponse("first"), FakeResponse("second")]})
        fetcher = self.make(session, cache_max_age=60)
        fetcher.get("http://x/a")
        self.now[0] = os.path.getmtime(fetcher._cache_path("http://x/a")) + 61
        self.assertEqual(fetcher.get("http://x/a"), "second")

    def test_errors_are_not_cached(self):
        session = FakeSession({"http://x/a": [FakeResponse("", 404), FakeResponse("ok")]})
        fetcher = self.make(session)
        with self.assertRaises(FetchError):
            fetcher.get("http://x/a")
        self.assertEqual(fetcher.get("http://x/a"), "ok")


with open(os.path.join(os.path.dirname(__file__), "fixtures", "robots.txt")) as _f:
    ROBOTS_TXT = _f.read()


class RobotsTests(unittest.TestCase):
    def make(self, responses, **kwargs):
        clock = Clock()
        session = FakeSession(responses)
        return Fetcher(session, delay=0, sleep=clock.sleep, clock=clock.time, **kwargs), session

    def test_disallowed_path_is_not_fetched(self):
        fetcher, session = self.make({"http://x/robots.txt": FakeResponse(ROBOTS_TXT)})
        with self.assertRaises(RobotsDisallowed):
            fetcher.get("http://x/private/data")
        self.assertEqual(session.calls, ["http://x/robots.txt"])

    def test_allowed_path_is_fetched(self):
        fetcher, session = self.make({"http://x/robots.txt": FakeResponse(ROBOTS_TXT),
                                      "http://x/books": FakeResponse("ok")})
        self.assertEqual(fetcher.get("http://x/books"), "ok")

    def test_robots_is_fetched_once_per_host(self):
        fetcher, session = self.make({"http://x/robots.txt": FakeResponse(ROBOTS_TXT),
                                      "http://x/a": FakeResponse("a"), "http://x/b": FakeResponse("b")})
        fetcher.get("http://x/a")
        fetcher.get("http://x/b")
        self.assertEqual(session.calls.count("http://x/robots.txt"), 1)

    def test_missing_robots_allows_everything(self):
        fetcher, _ = self.make({"http://x/robots.txt": FakeResponse("", 404),
                                "http://x/private/data": FakeResponse("fine")})
        self.assertEqual(fetcher.get("http://x/private/data"), "fine")

    def test_can_be_switched_off(self):
        fetcher, session = self.make({"http://x/private/data": FakeResponse("secret")}, respect_robots=False)
        self.assertEqual(fetcher.get("http://x/private/data"), "secret")
        self.assertEqual(session.calls, ["http://x/private/data"])


if __name__ == "__main__":
    unittest.main()
