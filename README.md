# OpenSource Intelligence Hub

A local-first discovery and evaluation hub for open-source tools, APIs, LLM apps and MCP servers.

> This project indexes upstream catalogues; it does not copy their contents or claim that every listed project is safe, maintained, or Android-compatible.

## Initial sources
- [Public APIs](https://github.com/public-apis/public-apis) — API directory
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) — MCP server directory
- [Awesome LLM Apps](https://github.com/Shubhamsaboo/awesome-llm-apps) — LLM application examples
- [Awesome](https://github.com/sindresorhus/awesome) — curated list directory
- [Scrapling](https://github.com/D4Vinci/Scrapling) — optional scraping framework (a library, not a catalogue)

## First milestone
- Fetch README files from configured public GitHub repositories.
- Extract Markdown links and classify repository / API / resource links.
- Enrich GitHub repository links with metadata using the public GitHub REST API.
- Store results in a local SQLite database.
- Search and list cached entries offline.
- No account or token required for public repositories. Set `GITHUB_TOKEN` to raise API limits.

## Requirements
Python 3.10+. On Android, use Termux and install Python with `pkg install python`. Core features use only the standard library.

## Quick start
```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
osihub sources
osihub sync
osihub search "mcp"
```

## Commands
- `osihub sources` — show configured sources
- `osihub sync` — fetch and index catalogues
- `osihub list --kind repository` — list cached entries
- `osihub search <query>` — search local cache
- `osihub info <owner/repo>` — inspect cached metadata

## Safety and scope
The first version never executes downloaded code. Scrapling and MCP execution are not enabled by default. Android compatibility is not assumed; it must be tested per project. Respect upstream licences, terms, rate limits and robots policies.
