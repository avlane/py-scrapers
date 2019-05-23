class FakeResponse:
    def __init__(self, text="", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}


class FakeSession:
    """Stands in for requests.Session. responses maps url -> response (or a list used in order)."""

    def __init__(self, responses):
        self.responses = dict(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, timeout=None):
        self.calls.append(url)
        if url not in self.responses and url.endswith("/robots.txt"):
            return FakeResponse("", 404)  # most sites in the tests have no robots.txt
        found = self.responses[url]
        if isinstance(found, list):
            found = found.pop(0)
        return found
