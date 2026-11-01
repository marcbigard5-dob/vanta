"""Command line interface."""
from __future__ import annotations
import argparse
from . import __version__
from .catalog import load_sources
from .db import Store
from .github import GitHubClient
from .sync import sync

def main():
    parser = argparse.ArgumentParser(prog="osihub", description="Open-source discovery and intelligence hub")
    parser.add_argument("--db", default="osihub.sqlite3", help="SQLite database path")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sources")
    sub.add_parser("sync")
    listing = sub.add_parser("list")
    listing.add_argument("--kind")
    listing.add_argument("--limit", type=int, default=30)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--kind")
    search.add_argument("--limit", type=int, default=30)
    info = sub.add_parser("info")
    info.add_argument("slug")
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == "sources":
        for source in load_sources():
            print(f"{source['name']}: https://github.com/{source['owner']}/{source['repo']} [{source['kind']}]")
    elif args.command == "sync":
        count, errors = sync(store, GitHubClient())
        print(f"Indexed {count} links. Local database contains {store.count()} unique entries.")
        for error in errors:
            print(f"WARNING: {error}")
    elif args.command in {"list", "search"}:
        rows = store.search(getattr(args, "query", ""), args.kind, args.limit)
        for row in rows:
            stars = f" ★{row['stars']}" if row["stars"] is not None else ""
            print(f"{row['title']}{stars}\n  {row['url']}\n  source={row['source']} kind={row['kind']}")
        print(f"\n{len(rows)} result(s)")
    elif args.command == "info":
        for row in store.search(args.slug, limit=10):
            print(f"{row['title']}\n{row['description']}\n{row['url']}\nlicense={row['license']} language={row['language']} stars={row['stars']}")

if __name__ == "__main__":
    main()
