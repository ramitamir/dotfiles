---
name: screenshot
description: >
  Capture screenshots of web pages using Puppeteer. Supports login flows.
  Trigger phrases: "screenshot", "capture", "take a screenshot", "show me what it looks like",
  "capture the page", "what does it look like now", iterative design comparison loops.
---

# Screenshot Skill

Capture screenshots of web pages, with optional login support. Use this for iterative UI design loops: capture → compare → fix → recapture.

## Step 1: Determine if Login is Needed

**Never assume credentials.** Ask the user:
- Does this page require login?
- If yes, what are the email and password?
- Are there non-standard selectors for the login form?

If the user has previously provided credentials in this session, you may reuse them without asking again.

## Step 2: Resolve the URL

- If the user provided an explicit URL, use it.
- If working on a local project with a dev server running, use `http://localhost:<port>`.
- If unclear, ask the user.

## Step 3: Run the Capture Script

Run the capture script from the skill directory:

```bash
node ~/.claude/skills/screenshot/capture.mjs <url> [options]
```

**Options:**
- `--output <path>` — Output PNG path (default: auto-incremented in `./screenshots/`)
- `--email <email>` — Login email
- `--password <password>` — Login password
- `--email-selector <sel>` — Default: `input[type="email"]`
- `--password-selector <sel>` — Default: `input[type="password"]`
- `--submit-selector <sel>` — Default: smart fallback (button[type="submit"], then text match)
- `--wait-for <selector>` — Wait for element before capturing
- `--viewport <WxH>` — Default: `1280x800`
- `--full-page` — Capture full scrollable page (default: true)
- `--delay <ms>` — Extra settle time after load (default: 1500)
- `--chrome <path>` — Path to Chrome executable

The script prints `SCREENSHOT_PATH:<absolute-path>` on success. Parse this to get the output file path.

## Step 4: Analyze the Screenshot

After capturing, **read the output PNG with the Read tool** and analyze it. Claude can see images directly.

Describe what you see: layout, content, colors, spacing, any issues.

## Step 5: Iterative Design Loop

When comparing against a reference image or iterating on a design:

1. **Capture** the current state
2. **Compare** against the reference — be specific:
   - "Heading is ~32px but reference shows ~24px"
   - "Card gap is 16px but should be 24px"
   - "Background color is #1a1a2e but should be #0f0f23"
3. **Fix** the identified mismatches in code
4. **Recapture** and compare again
5. **Minimum 2 rounds** of capture-compare-fix. Stop only when no visible differences remain or the user says to stop.

Check these properties specifically:
- Spacing / padding / margins
- Font size, weight, line-height, letter-spacing
- Colors (exact hex values)
- Alignment and positioning
- Border-radius and shadows
- Image sizing and aspect ratios
