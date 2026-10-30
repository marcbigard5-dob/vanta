import tempfile
import unittest
from pathlib import Path
from osihub.catalog import extract_links, classify_url, github_slug
from osihub.db import Store

class CatalogTests(unittest.TestCase):
    def test_extract_markdown_links_deduplicates(self):
        links = extract_links("[Repo](https://github.com/a/b) and https://github.com/a/b")
        self.assertEqual(links, ["https://github.com/a/b"])

    def test_classification(self):
        self.assertEqual(classify_url("https://github.com/a/b"), "repository")
        self.assertEqual(classify_url("https://example.org/docs"), "resource")

    def test_github_slug_rejects_topic_pages(self):
        self.assertEqual(github_slug("https://github.com/a/b/tree/main"), "a/b")
        self.assertIsNone(github_slug("https://github.com/topics/python"))

class StoreTests(unittest.TestCase):
    def test_upsert_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "test.sqlite3")
            store.upsert({"url":"https://github.com/a/tool","source":"test","kind":"repository","slug":"a/tool","title":"Tool","description":"A test tool","stars":12})
            self.assertEqual(store.count(), 1)
            self.assertEqual(store.search("test")[0]["slug"], "a/tool")
            store.upsert({"url":"https://github.com/a/tool","source":"test","kind":"repository","slug":"a/tool","title":"Tool updated","stars":15})
            self.assertEqual(store.count(), 1)
            self.assertEqual(store.search("updated")[0]["stars"], 15)

if __name__ == "__main__":
    unittest.main()
