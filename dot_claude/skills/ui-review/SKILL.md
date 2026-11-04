---
name: ui-review
description: Review a rendered camp4 page (Ranger's /ui, any future dashboard) against Rami's rules before he sees it — few facts upfront, the rest behind a click, no piles, nothing primary in grey. Use on every UI PR round, and as the implementor's self-check before the done-report.
---

# UI review — the page is scanned, not read

Rami's rules, in his words, from the first status-page rounds (2026-09-04):

- "If there is no way to know what operation it is and what it does, it's meaningless."
- "Why is the right side like a comment? I don't need the summary, I need the name and the type clear. Don't pile; give the right info and make it clear."
- "This info pile as comment is too much, this is an AI tendency that is a bad UI/UX. Pick what info is upfront and important and the rest should be behind a click. Review it again, per card."
- "More is NOT better, it's just cluttered."

## Procedure

1. Capture the render, don't imagine it. Fixture server: `cd ranger && uv run --locked python -m tests.ui_fixture` (port 8431), then
   `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,2400 --virtual-time-budget=10000 --screenshot=<png> <url>`
   Two captures: at rest, and with every details toggle open. Read the PNGs. Save them in the session scratchpad and attach them to the ticket; nothing goes under docs/ui (TEN-2008).
2. Go card by card. For each card write three lines: what is upfront, what is behind the click, what is wrong. Then the page-wide list.
3. Fixture data must carry the full shape (a published workload, two nodes, a control lease, a running op with a plan, a failed op with a reason, a component with a door) so nothing renders as a dash for want of data.

## The checklist — every item is a finding when it fails

**Upfront vs behind a click**
- A card shows a handful of facts upfront: the name, the type, the state, the URL, the cost. Everything else is behind a click (a row expands, a details toggle). If you cannot say why a fact is upfront, it is not.
- A long document (the manifest, a log) is collapsed by default.
- A running operation shows what it does and its current step; a finished one, what it did and how long it took.

**No piles**
- One fact per labelled cell. No dot-joined strings (`spot · aws · us-east-1a · g6.xlarge · $0.28/h`). Columns have headers.
- A fact appears once per card. The same URL, model or pool name in two places on one card is a defect.
- Counts that repeat the rows below ("1/2 machines joined", "3 in the journal", "1 serving") go.
- Unknown is `—` in its cell, never a sentence. The reason can live in a hover title.

**Nothing primary in grey**
- No grey top-right asides ("born …", "site row: ready", "control machine · sited 0.5.13"). A fact that matters becomes a labelled cell in the header line; the rest goes.
- The muted colour is for secondary text only: the "ago" of a timestamp, a note.
- One header grammar for every card and row, left to right: `NAME — TYPE` in ink · STATE pill(s) · … · a RATE cell only for a thing that costs money, labelled, in the same trailing position on every row that has one · the details toggle. The trailing slot means money or nothing; no other fact ever sits there (Rami: "the comment is sometimes cost, sometimes a tidbit of info; it has to be unified").
- The top-right corner of a card holds ONLY the details toggle. Nothing else ever goes there (a GPU type or a rate parked beside the toggle is a comment again).
- A card is balanced: no half-empty column. A header with six facts is one stat strip of six labelled cells, evenly spaced.
- The GPU and the pool a workload runs on are primary: in the header line, in ink (`m1 — Qwen/Qwen3.5-27B · nvidia-h100-80gb ×1 on p1`).
- The header of a group names the thing once, in ink: `p1 — nvidia-h100-80gb, 8 GPUs per machine`, `m1 — Qwen/Qwen3.5-27B`, `control — cpu-standard-4`.

**Lifecycle on the page (from the live births of 2026-09-05, Rami's words in quotes)**
- A card is populated with the DECLARED items and their real state, never an empty sentence beside a list elsewhere: "we already have cards for each below, just populate it with the right state." The Site card shows the health word only; no details list repeating the cards (TEN-905).
- A landed machine never disappears. From `up` on, the Machines card merges the site's own report with Clouds Rest's ledger rows the site has not reported yet ("once the cpu booted the machines disappeared" — TEN-905).
- The Machines card shows the CURRENT order only. Dead members of earlier orders are history behind the click; a terminated row is never labelled "hunting for" ("why do I need to see hunts that failed?" — TEN-902).
- Once a member has landed, its hunt is history: TRIES / LAST TRY / ANSWERED go behind the click and the row reads like any machine ("what does 11 tries mean??" — TEN-902).
- No heartbeat lines in a narration ("… 30 s" × 40: "we need to remove these prints, it's useless"). A wait is one updating line saying what is awaited and for how long (TEN-903).
- After a deploy the browser may still run the old page code: the page must carry its build and reload itself when Ranger's build changes (TEN-901). Reviewing a live page: hard-reload first.
- Health exists from `up` on only; before that the state and its fact are the whole story.

**Numbers are facts, not arithmetic**
- Money is read from Clouds Rest's ledger (`hourly_usd`, `cost_so_far_usd`), never computed on the page or in Ranger (TEN-799). No "estimate" labels on a figure the ledger owns.
- A launch line comes from the render's own composition function, never a hand copy.

**Plumbing stays out of sight**
- Watch/probe timers, journal ids, wire field names, "site row: ready" — behind the click or gone.
- No control that changes anything. The page never writes. One exception, by Rami's ruling (2026-10-05, TEN-1877): the Recordings page (`/ui/recordings`) has three acts, download, record and delete. They live in that page's own files, every write is guarded against another site's request, a delete asks before it acts, and a control that cannot act right now is off and says why.

**Design book**
- Clouds Rest's: IBM Plex Sans, ground `#f6f4ee`, ink `#23211b`, accent `#2e54c4`, hairline `#c8c2b0`; pills for state; the `cr-*` vocabulary. No new colours for emphasis; weight and position carry importance.

## Verdict shape

Per card: `CARD — upfront: …; behind the click: …; wrong: …`. Then `PAGE-WIDE: …`. End with the one change that matters most if only one is made. Send the findings to the implementor with the capture path; nothing goes to Rami until the page passes this list.
