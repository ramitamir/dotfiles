#!/usr/bin/env python3
"""
fetch.py — Pre-fetch company research data before Claude synthesis.
Usage: python fetch.py "Company Name"
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
    except Exception as e:
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
# Website fetching
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
            # Strip HTML tags crudely
            import re
            text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:max_chars]
    except Exception as e:
        return f"[Failed to fetch: {e}]"


# ---------------------------------------------------------------------------
# Job board endpoints
# ---------------------------------------------------------------------------

async def fetch_greenhouse_jobs(session: aiohttp.ClientSession, slug: str) -> str:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        async with session.get(url, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            jobs = data.get("jobs", [])
            if not jobs:
                return f"Greenhouse board found for '{slug}' but 0 open roles."
            dept_counts: dict[str, int] = {}
            locations: list[str] = []
            for job in jobs:
                dept = (job.get("departments") or [{}])[0].get("name", "Unknown")
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                loc = (job.get("offices") or [{}])[0].get("name", "")
                if loc and loc not in locations:
                    locations.append(loc)
            lines = [f"**Greenhouse jobs ({len(jobs)} open roles)**"]
            for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  - {dept}: {count}")
            lines.append(f"  Locations: {', '.join(locations[:8])}")
            return "\n".join(lines)
    except Exception:
        return None


async def fetch_lever_jobs(session: aiohttp.ClientSession, slug: str) -> str:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        async with session.get(url, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                return None
            jobs = await resp.json()
            if not isinstance(jobs, list) or not jobs:
                return None
            dept_counts: dict[str, int] = {}
            locations: list[str] = []
            for job in jobs:
                dept = job.get("categories", {}).get("team", "Unknown")
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                loc = job.get("categories", {}).get("location", "")
                if loc and loc not in locations:
                    locations.append(loc)
            lines = [f"**Lever jobs ({len(jobs)} open roles)**"]
            for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  - {dept}: {count}")
            lines.append(f"  Locations: {', '.join(locations[:8])}")
            return "\n".join(lines)
    except Exception:
        return None


async def fetch_jobs(session: aiohttp.ClientSession, company: str) -> str:
    slug = company.lower().replace(" ", "").replace("-", "")
    slug_hyphen = company.lower().replace(" ", "-")

    results = await asyncio.gather(
        fetch_greenhouse_jobs(session, slug),
        fetch_greenhouse_jobs(session, slug_hyphen),
        fetch_lever_jobs(session, slug),
        fetch_lever_jobs(session, slug_hyphen),
    )

    found = [r for r in results if r]
    if not found:
        return "No Greenhouse, Lever, or Ashby board found. Use search results below."
    # Deduplicate (same board, different slug formats)
    seen = set()
    deduped = []
    for r in found:
        key = r[:40]
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return "\n\n".join(deduped)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(company: str):
    slug = company.lower().replace(" ", "-")
    domain_guess = f"https://www.{company.lower().replace(' ', '')}.com"

    print(f"# Research data for: {company}")
    print(f"*Fetched at {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}*\n")

    async with aiohttp.ClientSession() as session:

        # Run everything in parallel
        (
            homepage,
            about_page,
            pricing_page,
            customers_page,
            jobs_data,
            news_results,
            tc_results,
            jobs_search_results,
            reviews_results,
            linkedin_results,
            crunchbase_results,
        ) = await asyncio.gather(
            fetch_page(session, domain_guess),
            fetch_first_valid(session, [
                f"{domain_guess}/about",
                f"{domain_guess}/about-us",
                f"{domain_guess}/company",
                f"{domain_guess}/who-we-are",
            ]),
            fetch_first_valid(session, [
                f"{domain_guess}/pricing",
                f"{domain_guess}/plans",
                f"{domain_guess}/pricing-plans",
            ]),
            fetch_first_valid(session, [
                f"{domain_guess}/customers",
                f"{domain_guess}/case-studies",
                f"{domain_guess}/customers-stories",
                f"{domain_guess}/clients",
            ]),
            fetch_jobs(session, company),
            brave_search(session, f'"{company}" (funding OR layoffs OR "leadership change" OR acquisition OR controversy)', freshness="py"),
            brave_search(session, f'"{company}" (site:techcrunch.com OR site:reuters.com OR site:bloomberg.com OR site:wsj.com OR site:forbes.com)', freshness="py"),
            brave_search(session, f'"{company}" (site:greenhouse.io OR site:lever.co OR site:ashbyhq.com OR "careers" OR "we\'re hiring")'),
            brave_search(session, f'"{company}" (site:g2.com OR site:capterra.com OR site:glassdoor.com/Reviews OR site:trustpilot.com)'),
            brave_search(session, f'"{company}" company site:linkedin.com/company'),
            brave_search(session, f'"{company}" (site:crunchbase.com OR "series" OR "raised" OR "valuation" OR "investors")'),
        )

    # Output structured document
    sections = [
        ("## Company Website — Homepage", homepage),
        ("## Company Website — About", about_page),
        ("## Company Website — Pricing", pricing_page),
        ("## Company Website — Customers", customers_page),
    ]
    for heading, content in sections:
        print(heading)
        print(content[:3000])
        print()

    print("## Job Board Data (structured)")
    print(jobs_data)
    print()

    print("## Job Board Search Results")
    print(format_results(jobs_search_results))
    print()

    print("## News & Events (last 12 months)")
    print(format_results(news_results))
    print()

    print("## TechCrunch / Reuters / Bloomberg Coverage")
    print(format_results(tc_results))
    print()

    print("## Customer Reviews (G2 / Capterra / Glassdoor / Trustpilot)")
    print(format_results(reviews_results))
    print()

    print("## LinkedIn")
    print(format_results(linkedin_results))
    print()

    print("## Crunchbase / Funding")
    print(format_results(crunchbase_results))
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch.py \"Company Name\"", file=sys.stderr)
        sys.exit(1)
    company = " ".join(sys.argv[1:])
    asyncio.run(main(company))
