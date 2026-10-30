import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from osihub.catalog import extract_links, classify_url, github_slug, load_sources
from osihub.db import Store
from osihub.sync import sync

class CatalogTests(unittest.TestCase):
    def test_extract_markdown_links_deduplicates(self):
        self.assertEqual(extract_links("[Repo](https://github.com/a/b) and https://github.com/a/b"), ["https://github.com/a/b"])
    def test_extract_link_with_title(self):
        self.assertEqual(extract_links('[docs](https://example.org/docs "guide")'), ["https://example.org/docs"])
    def test_classification(self):
        self.assertEqual(classify_url("https://github.com/a/b"), "repository")
        self.assertEqual(classify_url("https://example.org/docs"), "resource")
    def test_github_slug_rejects_topic_pages(self):
        self.assertEqual(github_slug("https://github.com/a/b/tree/main"), "a/b")
        self.assertIsNone(github_slug("https://github.com/topics/python"))
        self.assertEqual(github_slug("https://github.com/a/b.git"), "a/b")
    def test_load_sources_validates_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            path.write_text(json.dumps([{"name":"x"}]), encoding="utf-8")
            self.assertEqual(load_sources(path), [{"name":"x"}])
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_sources(path)

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

class SyncTests(unittest.TestCase):
    def test_sync_indexes_links_and_respects_metadata_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "sources.json"
            cfg.write_text(json.dumps([{"name":"fixture","owner":"x","repo":"y","readme":"README.md"}]), encoding="utf-8")
            store = Store(Path(tmp) / "db.sqlite3")
            class FakeClient:
                def __init__(self): self.calls = []
                def repository(self, slug):
                    self.calls.append(slug)
                    return {"stars":7,"description":"fixture repo","language":"Python","license":"MIT","archived":False,"pushed_at":"2026-01-01"}
            client = FakeClient()
            with patch("osihub.sync.fetch_text", return_value="[A](https://github.com/a/one) [B](https://github.com/b/two) https://example.org/api"):
                count, errors = sync(store, client, cfg, metadata_limit=1)
            self.assertEqual(count, 3)
            self.assertEqual(errors, [])
            self.assertEqual(client.calls, ["a/one"])
            self.assertEqual(store.count(), 3)
            self.assertEqual(store.search("fixture repo")[0]["stars"], 7)
    def test_sync_rejects_negative_metadata_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "db.sqlite3")
            with self.assertRaises(ValueError):
                sync(store, object(), Path(tmp) / "missing.json", metadata_limit=-1)

if __name__ == "__main__":
    unittest.main()
