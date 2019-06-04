"""A very small HTML tree built on the standard library.

It copies the handful of BeautifulSoup calls this project uses (find, find_all, get_text,
get and indexing) so the parsers and their tests also run on a machine where beautifulsoup4
is not installed.
"""
from html.parser import HTMLParser

VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
# a new <key> implicitly closes an open element listed here
AUTO_CLOSE = {
    "li": {"li"},
    "p": {"p"},
    "td": {"td", "th"},
    "th": {"td", "th"},
    "tr": {"tr", "td", "th"},
    "option": {"option"},
}
SKIPPED_TEXT = frozenset(["script", "style"])


class Node:
    def __init__(self, name, attrs=None, parent=None):
        self.name = name
        self.attrs = attrs or {}
        self.parent = parent
        self.children = []  # Node or str

    def __getitem__(self, key):
        return self.attrs[key]

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def descendants(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                for node in child.descendants():
                    yield node

    def get_text(self, separator="", strip=False):
        parts = []
        for child in self.children:
            if isinstance(child, Node):
                if child.name not in SKIPPED_TEXT:
                    parts.append(child.get_text(separator, strip))
            else:
                parts.append(child)
        if strip:
            parts = [p.strip() for p in parts if p.strip()]
        return separator.join(parts)

    @property
    def text(self):
        return self.get_text()

    def _matches(self, name, class_, attrs):
        if name is not None and self.name != name:
            return False
        if class_ is not None and class_ not in self.attrs.get("class", []):
            return False
        for key, value in (attrs or {}).items():
            if self.attrs.get(key) != value:
                return False
        return True

    def find_all(self, name=None, class_=None, attrs=None, limit=None):
        found = []
        for node in self.descendants():
            if node._matches(name, class_, attrs):
                found.append(node)
                if limit and len(found) >= limit:
                    break
        return found

    def find(self, name=None, class_=None, attrs=None):
        found = self.find_all(name, class_, attrs, limit=1)
        return found[0] if found else None


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("[document]")
        self.current = self.root

    @staticmethod
    def _attrs(pairs):
        attrs = {}
        for key, value in pairs:
            value = value if value is not None else ""
            attrs[key] = value.split() if key == "class" else value
        return attrs

    def handle_starttag(self, tag, attrs):
        while self.current.name in AUTO_CLOSE.get(tag, ()):
            self.current = self.current.parent
        node = Node(tag, self._attrs(attrs), self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag, self._attrs(attrs), self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root:
            if node.name == tag:
                self.current = node.parent
                return
            node = node.parent
        # stray end tag: ignore it

    def handle_data(self, data):
        self.current.children.append(data)


def parse(html):
    builder = _Builder()
    builder.feed(html)
    builder.close()
    return builder.root
