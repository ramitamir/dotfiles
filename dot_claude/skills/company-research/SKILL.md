---
name: company-research
description: Research a company and produce a structured, honest company profile. Use when the user runs /company-research or asks to research a specific company.
---

# Company Research Skill

## Trigger
User runs `/company-research [company name]` or asks to "research [company]". The company name is available as $ARGUMENTS.

## Your Task
Produce a structured, honest company profile. Your job is to cut through marketing copy and surface what's actually happening. Every section must appear — if data isn't available, say so explicitly rather than omitting the section.

## Step 1 — Run the Data Fetcher (REQUIRED FIRST)

Before doing any research, run the pre-fetch script to collect raw data in parallel:

```bash
python3 ~/.claude/skills/company-research/fetch.py "$ARGUMENTS"
```

This script fetches the company website, job board data, Brave Search results for news/funding/reviews/LinkedIn in parallel. It takes ~5 seconds. Use its output as your primary data source for all sections below.

If the script fails (missing dependency, network error), fall back to manual research steps.

## Step 1.5 — LinkedIn (if browser tool is available)

Check whether a browser tool is available in your current environment (e.g., a Playwright, Puppeteer, or MCP browser tool). If yes, use it for LinkedIn — do not skip this step.

**Company page** — navigate to `https://www.linkedin.com/company/[company-slug]/` and extract:
- Employee count and the 6-month headcount growth % (shown below the count)
- Follower count
- Recent company posts (last 3–5): announcements, job posts, product news
- Open jobs count (shown on the "Jobs" tab)

**Founder / exec profiles** — for each named founder and C-suite exec, navigate to their LinkedIn profile URL (use the one found in Step 1, or search `"[name]" "[company]" site:linkedin.com`) and extract:
- Current title and tenure at the company
- Prior roles (last 2–3 positions, with company names and durations)
- Education, if notable

Use this data to enrich the **Founding & Team** section (accurate tenure, prior pedigree) and the **Hiring velocity** row of the Momentum Score (open roles count, headcount growth %).

If browser access is not available, fall back to search-indexed LinkedIn snippets as the current approach does — and note the limitation explicitly in the report.

## Step 2 — Fill gaps with targeted searches

The script covers most sources automatically. After reviewing its output, use WebSearch or WebFetch only to fill specific gaps:
- If key pages (pricing, customers) returned 404, try searching `site:[company].com pricing` or `site:[company].com customers`
- If job board wasn't found on Greenhouse/Lever/Ashby, search `"[company]" jobs site:linkedin.com`
- For LinkedIn profiles of named founders/executives (if no browser available): search `"[name]" "[company]" site:linkedin.com`
- For competitor websites: fetch each competitor's homepage directly

## Output Template

Use this exact structure. Do not reorder sections. Do not skip sections.

---

# [Company Name] — Research Report
*[Today's date] | Sources: [inline list of URLs actually fetched]*

## What They Actually Do
[2–3 sentences. Not their tagline. Explain the actual product, who buys it, and what problem it solves in plain language. If their website is vague, say so and explain what you could piece together from other sources.]

## Business Model
[How do they make money? SaaS subscription, usage-based, marketplace take rate, professional services, advertising, freemium-to-paid, enterprise licensing? If unclear, say unclear and explain what signals you used to guess.]

## Founding & Team
- **Founded:** [year], [city]
- **Founders:** [names (with LinkedIn URL) + one-line backgrounds — prior companies, notable exits, domain expertise]
- **CEO (current):** [name (with LinkedIn URL), how long in role]
- **Employees:** ~[count] (source: [LinkedIn / Crunchbase / news], as of [date])

## Funding
- **Total raised:** [amount or "undisclosed / not public"]
- **Latest round:** [Series X, $Xm, month year]
- **Key investors:** [names]

| Round | Amount | Date | Lead Investor |
|-------|--------|------|---------------|
| [Series A] | [$Xm] | [date] | [firm] |

*[Note if Crunchbase required login to see full amounts — if so, cross-reference news.]*

## Customers
- **Known customers:** [named logos from website, case studies, press releases, G2 reviews — cite source for each]
- **Customer profile:** [SMB / mid-market / enterprise; industries]
- **What customers say:** [1–2 sentence synthesis from G2/Capterra/Trustpilot — both praise and complaints]

⚠️ Customer lists for [company type] companies are often incomplete by design. Treat this as a floor, not a ceiling.

## Competitors
| Competitor | Website | How [Company] Differentiates |
|------------|---------|------------------------------|
| [Name] | [website URL] | [one line] |
| [Name] | [website URL] | [one line] |

[If positioning is unclear from their materials, say so.]

## Latest News (Last 12 Months)
- **[Date]** — [Event]. ([Source URL])
- **[Date]** — [Event]. ([Source URL])

[If nothing notable surfaced, say "No significant news found in last 12 months — this may indicate a quiet period or limited press coverage."]

## What's Actually Happening (Signal)
[This section is required to be opinionated. Synthesize what the job postings, reviews, news, and funding trajectory tell you that the website doesn't. Examples: "They're hiring aggressively in enterprise sales, suggesting a move upmarket." / "Three rounds of layoffs in 18 months alongside flat hiring in product — this looks like a profitability push, not growth." / "G2 reviews consistently mention slow support — this may be a customer retention risk." Be direct. Flag uncertainty explicitly.]

## Red Flags / Open Questions
- [Anything that seemed off, inconsistent, or worth investigating: leadership turnover, investor drop-off, vague pricing, unusually negative reviews, funding gap, etc.]
- [If nothing flagged, say "Nothing significant flagged — but verify [X] directly if this matters for your decision."]

## Momentum Score
**[X] / 10** — [one sentence verdict]

| Signal | Weight | Score | Notes |
|--------|--------|-------|-------|
| Recent funding (up-round, size, recency) | 25% | [0–10] | [1–2 words: e.g. "Series G, 2026"] |
| Revenue / growth trajectory | 20% | [0–10] | [e.g. "10x YoY, disclosed" or "unknown"] |
| Hiring velocity (open reqs, key roles) | 15% | [0–10] | [e.g. "450 open roles, expanding"] |
| News sentiment (last 12 months) | 15% | [0–10] | [e.g. "positive, no controversies"] |
| Customer traction (logos, growth signals) | 15% | [0–10] | [e.g. "Fortune 10, named logos"] |
| Employee sentiment (Glassdoor) | 10% | [0–10] | [e.g. "4.1/5, 85% recommend"] |

*Weighted average of the above = final score. 10 = category-defining hypergrowth. 1 = distress signals across the board. Flag if score is based on limited data.*

---

## Constraints and Honesty Rules

- Never quote a company's own tagline or marketing copy in "What They Actually Do" — paraphrase and translate into plain language
- If a section's data is genuinely unavailable (private company, no press coverage, paywalled), say exactly that — do not fill with vague filler
- Cite sources inline so every claim is traceable
- LinkedIn: if a browser tool is available, use it directly (see Step 1.5). If not, use only what's publicly indexed by search engines — and note this limitation in the report.
- Crunchbase funding amounts may be paywalled — note this and cross-reference news coverage
- "What's Actually Happening" must contain a real synthesis, not a summary of the above sections — push past the obvious
- Momentum Score must be evidence-based: every sub-score must map to a specific finding from the research. Do not inflate. If a signal is missing (e.g. no Glassdoor data, no disclosed revenue), score that row conservatively and note the gap explicitly.
- LinkedIn profile URLs: include the actual URL found via search. If no profile is found, write "LinkedIn not found" — do not omit the field or guess a URL.
- Competitor website URLs: use the company's actual homepage. If unsure, note it.
