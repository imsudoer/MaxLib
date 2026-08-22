"""
Unit tests for Markdown V2 and HTML rich text formatting parsers.
"""
import unittest
from maxlib.utils.formatting import parse_markdown, parse_html, format_text


class TestFormatting(unittest.TestCase):
    def test_markdown_bold(self):
        text, elements = parse_markdown("Hello **world**!")
        self.assertEqual(text, "Hello world!")
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]["type"], "STRONG")
        self.assertEqual(elements[0]["from"], 6)
        self.assertEqual(elements[0]["length"], 5)

    def test_markdown_multiple_elements(self):
        raw = "**Bold** and _italic_ and `code` and ||spoiler||"
        text, elements = parse_markdown(raw)
        self.assertEqual(text, "Bold and italic and code and spoiler")
        self.assertEqual(len(elements), 4)
        self.assertEqual(elements[0]["type"], "STRONG")
        self.assertEqual(elements[1]["type"], "EMPHASIS")
        self.assertEqual(elements[2]["type"], "CODE")
        self.assertEqual(elements[3]["type"], "SPOILER")

    def test_markdown_link(self):
        raw = "Check [Google](https://google.com) here"
        text, elements = parse_markdown(raw)
        self.assertEqual(text, "Check Google here")
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]["type"], "LINK")
        self.assertEqual(elements[0]["url"], "https://google.com")
        self.assertEqual(elements[0]["from"], 6)
        self.assertEqual(elements[0]["length"], 6)

    def test_html_tags(self):
        raw = "Hello <b>bold</b> and <i>italic</i> and <a href=\"https://max.ru\">MAX</a>"
        text, elements = parse_html(raw)
        self.assertEqual(text, "Hello bold and italic and MAX")
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0]["type"], "STRONG")
        self.assertEqual(elements[1]["type"], "EMPHASIS")
        self.assertEqual(elements[2]["type"], "LINK")
        self.assertEqual(elements[2]["url"], "https://max.ru")

    def test_cyrillic_and_unicode_offsets(self):
        raw = "Привет **мир**! 🚀 [Ссылка](https://example.com)"
        text, elements = parse_markdown(raw)
        self.assertEqual(text, "Привет мир! 🚀 Ссылка")
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0]["type"], "STRONG")
        self.assertEqual(elements[1]["type"], "LINK")


if __name__ == "__main__":
    unittest.main()
