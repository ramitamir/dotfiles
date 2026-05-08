#!/usr/bin/env python3
"""
fetch.py — Pre-fetch person research data before Claude synthesis.
Usage: python fetch.py "Person Name" ["context/company"]
Output: structured markdown to stdout, ready to paste into Claude context.
"""

import sys
import os
import json
import time
import asyncio
import aiohttp
from urllib.parse import quote_plus, urlparse

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
if not BRAVE_API_KEY:
    # Try reading directly from ~/.zshrc as fallback
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.exists(zshrc):
        import re as _re
        with open(zshrc) as _f:
            match = _re.search(r'export BRAVE_API_KEY=["\']?([^"\'\\n]+)["\']?', _f.read())
            if match:
                BRAVE_API_KEY = match.group(1).strip()
if not BRAVE_API_KEY:
    print("ERROR: BRAVE_API_KEY not found in environment or ~/.zshrc", file=sys.stderr)
    sys.exit(1)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "X-Subscription-Token": BRAVE_API_KEY,
}

TIMEOUT = aiohttp.ClientTimeout(total=10)

# User-Agent to avoid Wikipedia 403
SESSION_HEADERS = {"User-Agent": "Mozilla/5.0 (research-person-skill/1.0)"}


# ---------------------------------------------------------------------------
# Brave search
# ---------------------------------------------------------------------------

async def brave_search(session: aiohttp.ClientSession, query: str, count: int = 10, freshness: str | None = None) -> list[dict]:
    params = {"q": query, "count": count, "search_lang": "en"}
    if freshness:
        params["freshness"] = freshness
    try:
        async with session.get(BRAVE_SEARCH_URL, headers=BRAVE_HEADERS, params=params, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("web", {}).get("results", [])
    except Exception:
        return []


def format_results(results: list[dict], max: int = 8) -> str:
    lines = []
    for r in results[:max]:
        title = r.get("title", "")
        url = r.get("url", "")
        desc = r.get("description", "")
        age = r.get("age", "")
        age_str = f" [{age}]" if age else ""
        lines.append(f"- [{title}]({url}){age_str}\n  {desc}")
    return "\n".join(lines) if lines else "No results found."


# ---------------------------------------------------------------------------
# Page fetching
# ---------------------------------------------------------------------------

async def fetch_first_valid(session: aiohttp.ClientSession, urls: list[str], max_chars: int = 3000) -> str:
    """Try multiple URLs in order, return first that succeeds."""
    for url in urls:
        result = await fetch_page(session, url, max_chars)
        if not result.startswith("[HTTP") and not result.startswith("[Failed"):
            return result
    return f"[Not found at: {', '.join(urls)}]"


async def fetch_page(session: aiohttp.ClientSession, url: str, max_chars: int = 4000) -> str:
    try:
        async with session.get(url, timeout=TIMEOUT, allow_redirects=True) as resp:
            if resp.status != 200:
                return f"[HTTP {resp.status}]"
            text = await resp.text(errors="replace")
            import re
            text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:max_chars]
    except Exception as e:
        return f"[Failed to fetch: {e}]"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(person: str, context: str | None = None):
    # Derive URL-friendly variants of the name
    name_slug = person.lower().replace(" ", "")          # "elonmusk"
    name_hyphen = person.lower().replace(" ", "-")        # "elon-musk"
    name_underscore = person.replace(" ", "_")            # "Elon_Musk"

    # Context qualifier appended to search queries when provided
    ctx_q = f' "{context}"' if context else ""

    print(f"# Research data for: {person}")
    if context:
        print(f"*Context: {context}*")
    print(f"*Fetched at {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}*\n")

    async with aiohttp.ClientSession(headers=SESSION_HEADERS) as session:

        # Run everything in parallel
        (
            wikipedia_page,
            personal_site,
            linkedin_results,
            twitter_results,
            news_results,
            publications_results,
            talks_results,
            github_results,
            crunchbase_results,
            controversy_results,
        ) = await asyncio.gather(
            # Wikipedia — best-effort direct fetch
            fetch_page(session, f"https://en.wikipedia.org/wiki/{name_underscore}", max_chars=4000),

            # Personal site — try common patterns
            fetch_first_valid(session, [
                f"https://{name_slug}.com",
                f"https://{name_hyphen}.com",
                f"https://{name_slug}.io",
                f"https://{name_hyphen}.io",
            ], max_chars=3000),

            # LinkedIn personal profile search
            brave_search(session, f'"{person}"{ctx_q} site:linkedin.com/in/'),

            # Twitter / X
            brave_search(session, f'"{person}"{ctx_q} (site:twitter.com OR site:x.com)'),

            # News — last 12 months
            brave_search(session, f'"{person}"{ctx_q} (news OR announcement OR interview OR profile)', freshness="py"),

            # Published writing — tightened to reduce SEO noise
            brave_search(session, f'"{person}"{ctx_q} (article OR essay OR "wrote" OR "published")'),

            # Talks, podcasts, interviews — tightened
            brave_search(session, f'"{person}"{ctx_q} (podcast OR interview OR keynote OR "guest on" OR "speaking at")'),

            # GitHub
            brave_search(session, f'"{person}"{ctx_q} site:github.com'),

            # Crunchbase / investor activity
            brave_search(session, f'"{person}"{ctx_q} (site:crunchbase.com OR "invested in" OR "portfolio" OR "angel investor" OR "venture")'),

            # Controversy / reputation signals — person name only, no context, to avoid firm-level noise
            brave_search(session, f'"{person}" (controversy OR allegations OR criticism OR lawsuit OR scandal OR fraud OR misconduct)'),
        )

    # Output structured document

    print("## Wikipedia")
    print(wikipedia_page[:3000])
    print()

    print("## Personal Website / Blog")
    print(personal_site[:3000])
    print()

    print("## LinkedIn Profile (search results)")
    print(format_results(linkedin_results))
    print()

    print("## Twitter / X")
    print(format_results(twitter_results))
    print()

    print("## News & Recent Activity (last 12 months)")
    print(format_results(news_results))
    print()

    print("## Publications & Writing")
    print(format_results(publications_results))
    print()

    print("## Talks & Podcasts")
    print(format_results(talks_results))
    print()

    print("## GitHub")
    print(format_results(github_results))
    print()

    print("## Crunchbase / Investor Activity")
    print(format_results(crunchbase_results))
    print()

    print("## Controversy / Reputation Signals")
    print(format_results(controversy_results))
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch.py \"Person Name\" [\"context/company\"]", file=sys.stderr)
        sys.exit(1)
    person = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) >= 3 else None
    asyncio.run(main(person, context))
