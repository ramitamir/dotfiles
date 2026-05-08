#!/usr/bin/env node

import { createRequire } from "module";
import { resolve, dirname, basename, join } from "path";
import { existsSync, mkdirSync, readdirSync } from "fs";
import { fileURLToPath } from "url";

// Resolve puppeteer-core from the skill's own node_modules, regardless of cwd
const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

// --- CLI argument parsing ---
const args = process.argv.slice(2);

function getArg(name, defaultValue) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1 || idx + 1 >= args.length) return defaultValue;
  return args[idx + 1];
}

function hasFlag(name) {
  return args.includes(`--${name}`);
}

const url = args.find((a) => !a.startsWith("--") && (args.indexOf(a) === 0 || !args[args.indexOf(a) - 1]?.startsWith("--")));

if (!url) {
  console.error("Usage: node capture.mjs <url> [options]");
  console.error("");
  console.error("Options:");
  console.error("  --output <path>           Output PNG path (default: ./screenshots/screenshot-<N>.png)");
  console.error("  --email <email>           Login email");
  console.error("  --password <password>     Login password");
  console.error("  --email-selector <sel>    Default: input[type=\"email\"]");
  console.error("  --password-selector <sel> Default: input[type=\"password\"]");
  console.error("  --submit-selector <sel>   Default: smart fallback");
  console.error("  --wait-for <selector>     Wait for element before capturing");
  console.error("  --viewport <WxH>          Default: 1280x800");
  console.error("  --full-page               Capture full scrollable page (default: true)");
  console.error("  --delay <ms>              Extra settle time (default: 1500)");
  console.error("  --chrome <path>           Path to Chrome executable");
  process.exit(1);
}

const email = getArg("email", null);
const password = getArg("password", null);
const emailSelector = getArg("email-selector", 'input[type="email"]');
const passwordSelector = getArg("password-selector", 'input[type="password"]');
const submitSelector = getArg("submit-selector", null);
const waitForSelector = getArg("wait-for", null);
const viewportArg = getArg("viewport", "1280x800");
const fullPage = hasFlag("full-page") || !args.some((a) => a === "--no-full-page");
const delay = parseInt(getArg("delay", "1500"), 10);
const outputArg = getArg("output", null);

// Chrome path detection
const defaultChromePaths = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
  "/usr/bin/chromium-browser",
  "/usr/bin/chromium",
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
];

function findChrome() {
  const explicit = getArg("chrome", null);
  if (explicit) return explicit;
  for (const p of defaultChromePaths) {
    if (existsSync(p)) return p;
  }
  return null;
}

// Auto-increment output filename
function resolveOutputPath() {
  if (outputArg) return resolve(outputArg);

  const dir = resolve("./screenshots");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  const existing = readdirSync(dir).filter((f) => /^screenshot-\d+\.png$/.test(f));
  const numbers = existing.map((f) => parseInt(f.match(/screenshot-(\d+)\.png/)[1], 10));
  const next = numbers.length > 0 ? Math.max(...numbers) + 1 : 1;

  return join(dir, `screenshot-${next}.png`);
}

// Parse viewport
const [vpWidth, vpHeight] = viewportArg.split("x").map(Number);

async function main() {
  const chromePath = findChrome();
  if (!chromePath) {
    console.error("ERROR: Could not find Chrome. Install Google Chrome or pass --chrome <path>");
    process.exit(1);
  }

  console.log(`Launching Chrome from: ${chromePath}`);
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: vpWidth || 1280, height: vpHeight || 800 });

  try {
    console.log(`Navigating to: ${url}`);
    await page.goto(url, { waitUntil: "networkidle2", timeout: 30000 });

    // Login flow
    if (email && password) {
      console.log("Attempting login...");
      try {
        await page.waitForSelector(emailSelector, { timeout: 10000 });
        await page.type(emailSelector, email, { delay: 50 });
        await page.type(passwordSelector, password, { delay: 50 });

        // Find and click submit
        if (submitSelector) {
          await page.click(submitSelector);
        } else {
          // Smart fallback: try common submit selectors
          const submitted = await page.evaluate(() => {
            const selectors = [
              'button[type="submit"]',
              'input[type="submit"]',
              "button.login",
              "button.signin",
              'button[data-testid="login"]',
              'button[data-testid="submit"]',
            ];
            for (const sel of selectors) {
              const el = document.querySelector(sel);
              if (el) {
                el.click();
                return true;
              }
            }
            // Text-based fallback
            const buttons = document.querySelectorAll("button");
            for (const btn of buttons) {
              const text = btn.textContent.toLowerCase().trim();
              if (["sign in", "log in", "login", "signin", "submit"].includes(text)) {
                btn.click();
                return true;
              }
            }
            return false;
          });

          if (!submitted) {
            console.warn("WARNING: Could not find a submit button. Pressing Enter on password field.");
            await page.keyboard.press("Enter");
          }
        }

        // Wait for navigation after login
        console.log("Waiting for post-login navigation...");
        await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 15000 }).catch(() => {
          console.warn("WARNING: No navigation detected after login. Page may already be loaded or login may have failed.");
        });
      } catch (loginErr) {
        console.warn(`WARNING: Login flow encountered an error: ${loginErr.message}`);
        console.warn("Continuing to capture screenshot for diagnostic purposes...");
      }
    }

    // Wait for specific element if requested
    if (waitForSelector) {
      console.log(`Waiting for selector: ${waitForSelector}`);
      await page.waitForSelector(waitForSelector, { timeout: 15000 }).catch((err) => {
        console.warn(`WARNING: Timed out waiting for "${waitForSelector}": ${err.message}`);
      });
    }

    // Extra settle time
    if (delay > 0) {
      console.log(`Waiting ${delay}ms for page to settle...`);
      await new Promise((r) => setTimeout(r, delay));
    }

    // Capture
    const outputPath = resolveOutputPath();
    await page.screenshot({ path: outputPath, fullPage });

    console.log(`Screenshot saved to: ${outputPath}`);
    console.log(`SCREENSHOT_PATH:${outputPath}`);
  } catch (err) {
    console.error(`ERROR: ${err.message}`);

    // Try to capture whatever is on screen for diagnostics
    try {
      const outputPath = resolveOutputPath();
      await page.screenshot({ path: outputPath, fullPage: false });
      console.log(`Diagnostic screenshot saved to: ${outputPath}`);
      console.log(`SCREENSHOT_PATH:${outputPath}`);
    } catch (_) {
      // Give up
    }

    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
