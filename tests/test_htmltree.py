import unittest

from py_scrapers.htmltree import parse


class HtmlTreeTests(unittest.TestCase):
    def test_find_and_get_text(self):
        root = parse("<div><p class='a b'>Hello <b>there</b></p></div>")
        p = root.find("p")
        self.assertEqual(p.get_text(), "Hello there")
        self.assertEqual(p["class"], ["a", "b"])

    def test_find_all_by_class(self):
        root = parse("<ul><li class=x>1</li><li>2</li><li class='x y'>3</li></ul>")
        self.assertEqual([li.text for li in root.find_all("li", class_="x")], ["1", "3"])

    def test_missing_returns_none(self):
        self.assertIsNone(parse("<p>hi</p>").find("table"))

    def test_void_elements_do_not_swallow_siblings(self):
        root = parse("<p>one<br>two<img src=a.png alt='x'>three</p>")
        self.assertEqual(root.find("p").text, "onetwothree")
        self.assertEqual(root.find("img")["src"], "a.png")

    def test_unclosed_list_items(self):
        root = parse("<ul><li>one<li>two<li>three</ul>")
        self.assertEqual([li.text for li in root.find_all("li")], ["one", "two", "three"])

    def test_unclosed_table_cells(self):
        root = parse("<table><tr><td>a<td>b<tr><td>c<td>d</table>")
        rows = root.find_all("tr")
        self.assertEqual(len(rows), 2)
        self.assertEqual([td.text for td in rows[1].find_all("td")], ["c", "d"])

    def test_entities_and_strip(self):
        root = parse("<p>  14&deg;C &amp; windy  </p>")
        self.assertEqual(root.find("p").get_text(strip=True), "14°C & windy")

    def test_script_text_is_ignored(self):
        root = parse("<div>a<script>var x = 1;</script>b</div>")
        self.assertEqual(root.find("div").text, "ab")

    def test_find_by_attrs(self):
        root = parse("<table id=a></table><table id=b></table>")
        self.assertEqual(root.find("table", attrs={"id": "b"})["id"], "b")

    def test_stray_end_tag(self):
        root = parse("<div>x</span></div>")
        self.assertEqual(root.find("div").text, "x")


if __name__ == "__main__":
    unittest.main()
