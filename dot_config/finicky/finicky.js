// ~/.finicky.js  – v4-safe, with global profile constants
const PERSONAL = "Private";   // personal Chrome profile (was "Default")
const WORK     = "Work";      // work Chrome profile
const TENAYA   = "Profile 2"; // Tenaya Chrome profile (display name only; on-disk dir stays "Profile 2")

export default {
  // Anything that doesn’t match a handler → personal profile
  defaultBrowser: { name: "Google Chrome", profile: PERSONAL },

  options: { checkForUpdates: true, logRequests: false },

  handlers: [
    { match: /^https?:\/\/(?:[\w-]+\.)?zoom\.us\/.*\/j\/\d+/, browser: { name: "zoom.us", bundleId: "us.zoom.xos" } },
    { match: /^https?:\/\/(?:www\.)?teams\.microsoft\.com\/l\/meetup-join/, browser: { name: "Microsoft Teams" } },
    { match: /^https?:\/\/(?:www\.)?notion\.so\/.+/, browser: "Notion" },
    
    { match: (_url, { opener }) => opener?.bundleId === "com.tinyspeck.slackmacgap", browser: { name: "Google Chrome", profile: TENAYA } },
    { match: (_url, { opener }) => opener?.bundleId === "notion.id", browser: { name: "Google Chrome", profile: TENAYA } },

    { match: /.*force\.com.*/,         browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*atlassian.*\.com.*/,   browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*\.atlassian\.net.*/,   browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*notion\.so.*/,         browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*salto\.io.*/,          browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*tulip.*\.com.*/,       browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*comerica\.com.*/,      browser: { name: "Google Chrome", profile: WORK } },
    { match: /.*linear\.app.*/,        browser: { name: "Google Chrome", profile: TENAYA }},

    { match: /^(https?:\/\/)?(?:www\.)?(twitter\.com|x\.com)\/.+/, browser: { name: "Google Chrome", profile: PERSONAL } },
    { match: /^(https?:\/\/)?(?:www\.)?facebook\.com\/.+/, browser: { name: "Google Chrome", profile: PERSONAL } },
    { match: /^(https?:\/\/)?(?:www\.)?instagram\.com\/.+/, browser: { name: "Google Chrome", profile: PERSONAL } },
    { match: /^(https?:\/\/)?(?:www\.)?tiktok\.com\/.+/, browser: { name: "Google Chrome", profile: PERSONAL } },
    { match: /^(https?:\/\/)?(?:www\.|maps\.)?google\.[^\/]+\/maps\/?/, browser: { name: "Google Chrome", profile: PERSONAL } }
  ]
};