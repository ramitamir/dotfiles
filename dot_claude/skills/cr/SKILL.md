---
name: cr
description: Use when the user asks what Clouds Rest machines or sites cost (any period, per site, per GPU type, per cloud, per day, as CSV), what the clouds actually billed versus the estimate, or wants to lease, list, renew, release or inspect a Clouds Rest lease or bundle from a laptop — the `cr` command is the way, never hand-built curl.
---

# cr — Clouds Rest from a laptop

`scripts/cr` in the cloudsrest checkout: one request through the door, the
answer printed. Every flag is one API parameter, 1:1; the script validates
nothing the API validates. `cr` with no verb prints the usage — read it
before guessing a flag.

## Install and environment

```bash
ln -s ~/Dev/cloudsrest/scripts/cr ~/.local/bin/cr   # bash + curl + jq, nothing to build
export CR_ACCESS_CLIENT_ID=$(sed -n 's/^RANGER_CF_ACCESS_CLIENT_ID=//p' ~/.camp4/site-edge-cred)
export CR_ACCESS_CLIENT_SECRET=$(sed -n 's/^RANGER_CF_ACCESS_CLIENT_SECRET=//p' ~/.camp4/site-edge-cred)
export CR_TOKEN=…        # mutations only: lease, renew, release, actuals-refresh
cr status                # the proof: a read that costs nothing
```

Reads need only the Access pair. No pair: a 302 from the door, not the API.
No token on a mutation: a 401/403 whose detail names the auth mode. A site
token acts on its own site's leases; an operator token on everything.

## The questions, and the command

| question | command |
|---|---|
| site X in August, by GPU type | `cr costs --period month:2026-08 --tag site:X --by sku` |
| per site, this month so far | `cr costs --period mtd --by tag:site` |
| every soak site in September, one row each | `cr costs --period month:2026-09 --tag 'site:soak-*' --by tag:site` |
| per day for the last week, both clouds | `cr costs --period 7d --bucket day` (`--by cloud` to split) |
| everything ever, per month, spot vs on-demand | `cr costs --period all --bucket month --by capacity` |
| the leases behind a number, as a file | `cr lines --period month:2026-08 --tag site:X --csv` |
| is capacity there before leasing | `cr availability nvidia-h100-80gb --nodes 2 --regions eu-west-2` |
| lease one raw machine for a site | `cr lease nvidia-h100-80gb --cloud aws --capacity on-demand --mode raw --user-data ./boot.sh --ttl 7200 --tags site=X` |
| a site's leases · one lease | `cr leases --tag site:X` · `cr lease-get ID` |
| keep it · let it go | `cr renew ID --seconds 3600` · `cr release ID [--force]` |
| an order Ranger placed | `cr bundle-get ID` (a read keeps the order hunting) |
| cluster vs ledger · catalog | `cr nodes` · `cr status` · `cr catalog [--kind cpu\|all]` |

Periods: `7d 30d mtd last_month month:YYYY-MM all`, or `--from D --to D`
(UTC; `to` is exclusive: `--to 2026-10-01` stops at the start of 1 Oct, so
"through yesterday" is `--to <today>`). `7d`/`30d` end now, so their edge
buckets are partial.
One `--by` key. `--filter` repeats and ORs within a key. `--tag k:v`
filters; `--tags k=v` on `lease` sets. A filter value holding `*`, `?` or
`[` is a case-sensitive pattern over the real value — quote it for the
shell; it never matches a lease that lacks the key, so `site:*` is every
tagged site, not every lease. `--csv` saves under the server's name
and prints the path; `--csv out.csv` names it, `--csv -` streams. `sku` is
a node shape, not a GPU count; one lease is one machine.

## Reading the numbers

- **SPEND / `usd`**: the estimate — the rate sealed when the VM was created ×
  wall time, compute only. `rate_source` says where the rate came from.
- **BILLED / `billed_usd`**: the cloud's bill, gross, per lease per day.
  `net_usd` is after credits, the paid number. `variance_usd` = billed − spend,
  present only when every lease in the cell is covered. GCP's bill lags about
  three days; `actuals.through` says where it stops.
- **`—` / null**: no bill row for that cell. Never 0, never the estimate. Hour
  buckets carry no bill. `unpriced` ran without a rate; `unattributed` has no
  purpose and no tags.
- Groups sum to the total; `leases` counts do not add across buckets.

## Errors

From the API: `✗ HTTP <code>: <detail>` on stderr, exit 1, nothing saved.
From the script: `✗ cr <verb>: …` — a flag the verb does not take, or a
non-integer where one is wanted. An unknown parameter is a 400 that lists
the known ones: fix the flag, never retry blind. Exit 0 with a `detail`
body on stdout is a bug, not a success.

## Leasing gotchas

- `nvidia-h100-80gb` on AWS is `p5.48xlarge`, eight GPUs; there is no
  one-GPU H100 key. AWS H100/H200 lanes are on-demand only in practice.
- A raw lease reaches READY on its first `renew` from the machine, not on boot.
- `--user-data` sends the file's bytes verbatim; keep it under 16 KB.
