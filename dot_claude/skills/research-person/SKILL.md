---
name: research-person
description: Research a person and produce a structured, honest profile. Use when the user runs /research-person or asks to research a specific person (founder, executive, investor, public figure, etc.).
---

# Research Person Skill

## Trigger
User runs `/research-person [person name]` or asks to "research [person]". The person's name is available as $ARGUMENTS.

## Your Task
Produce a structured, honest profile of this individual. Your job is to cut through self-promotional bios and surface what's actually verifiable.

## Step 0 — Identify who we're researching (REQUIRED BEFORE ANYTHING ELSE)

Before running the fetcher, you must know exactly who you're looking for. The fetcher is a crude parallel data collector — it only works well when given a clean, correct name. Don't run it blind.

**Parse $ARGUMENTS first:**
- Extract name and any context clue (e.g. "Arik Kol at NVIDIA" → name: "Arik Kol", context: "NVIDIA")

**Then run two WebSearches in parallel:**

1. Exact + ecosystem sites (catches the right person if spelling is correct):
   ```
   "[name as given]" (site:linkedin.com OR site:crunchbase.com OR site:techcrunch.com OR site:medium.com OR site:github.com)
   ```

2. Unquoted + broad tech signal (fuzzy/phonetic fallback — surfaces spelling variants):
   ```
   [name as given] tech
   ```

From the combined results, confirm:
1. **Correct spelling** — do results consistently show a different spelling? Use that going forward.
2. **Who they are** — current role, company, domain. If multiple people share the name, pick the most likely match given context (default assumption: tech/VC world unless user said otherwise).
3. **Context** — if the user didn't provide a company/domain, extract one from the results (e.g. "Battery Ventures", "NVIDIA"). This will sharpen the fetcher queries significantly.

If the name is completely ambiguous and you can't confidently identify the right person, **stop and ask the user** for more context before continuing.

Once you have a confirmed name and context, proceed to Step 1.

## Step 1 — Run the Data Fetcher

Run the pre-fetch script with the **confirmed correct name** and context from Step 0:

```bash
# With context (always preferred when available)
python3 ~/.claude/skills/research-person/fetch.py "Confirmed Name" "company or domain"

# Without context (only if none found)
python3 ~/.claude/skills/research-person/fetch.py "Confirmed Name"
```

This script fetches Wikipedia, personal site, and runs Brave Search for LinkedIn, Twitter/X, news, publications, talks, GitHub, and reputation signals in parallel. It takes ~5 seconds. Use its output as your primary data source.

If the script fails, fall back to manual research steps.

## Step 1.5 — LinkedIn (if browser tool is available)

Check whether a browser tool is available. If yes:
- Navigate to the LinkedIn profile URL found in Step 1
- Extract: current title, company, tenure; prior roles (last 3–4); education; follower/connection count; recent posts

If browser access is not available, use search-indexed snippets and note the limitation.

## Step 2 — Fill gaps with targeted searches

After reviewing fetcher output, use WebSearch or WebFetch only for specific gaps:
- If Wikipedia returned 404: search `"[name]" wikipedia`
- If no personal site: search `"[name]" personal site OR blog`
- If GitHub not found: search `"[name]" site:github.com`
- If still noisy results: add company or domain to every query

## Output Template

Use this exact 6-section structure. Do not skip sections — if data is unavailable, say so.

---

# [Name] — Profile
*[Today's date] | [inline list of source URLs actually used]*

> *(If name was corrected: Note: searched as "[original]", results consistently showed "[corrected]" — using corrected spelling.)*

## Who They Are
2–3 sentences. Current role, what they're known for, domain. Not their self-written bio — plain language.

## Career
- [Most recent role, company, ~dates]
- [Prior role, company, ~dates]
- [Prior role, company, ~dates]

1-sentence trajectory read: what does the arc tell you?

## Online Presence
- LinkedIn: [url] — [brief note on activity/followers, or "not found"]
- Twitter/X: [url] — [brief note, or "not found"]
- Site/blog: [url or "not found"]
- GitHub: [url or "not found"]

## Recent Activity (Last 12 Months)
- [date] — [event] ([source url])
- [date] — [event] ([source url])

*If nothing notable: "No significant activity found — may be low-profile, limited press coverage, or search noise from common name."*

## Signal
3–4 sentences. Opinionated synthesis — push past the resume. What does the trajectory, presence, and activity actually tell you? Include notable published work or talks if found. Flag uncertainty explicitly.

## Red Flags
- [bullet] or "Nothing significant — verify [X] if it matters."

---

## Constraints and Honesty Rules

- Never copy self-written bios verbatim — paraphrase into plain language
- If data is genuinely unavailable, say exactly that — do not fill with vague filler
- Cite sources inline so every claim is traceable
- LinkedIn: use browser tool if available; otherwise use search-indexed snippets and note the limitation
- If the person has a common name, note which disambiguating signals you used
- Signal must be a real synthesis, not a summary of the sections above
- Do not speculate about private individuals — note limits if subject is not a public figure
