import unittest

from py_scrapers.http import FetchError, Fetcher
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
        return Fetcher(session, delay=delay, sleep=clock.sleep, clock=clock.time), session, clock

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


if __name__ == "__main__":
    unittest.main()
