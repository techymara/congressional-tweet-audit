# Congressional Tweet Audit

A single-page tool that sorts a member of Congress's posts on X into categories
(outrage & culture war, legislative work, district focus, and more you can switch
on) and charts the mix, how it changes over time, and which categories get the
most engagement.

- **Website (GitHub Pages):** https://techymara.github.io/congressional-tweet-audit/
- **claude.ai artifact:** https://claude.ai/artifact/3bVCw8t2p2EkWWto242PBj

## Where labeling works

| | claude.ai artifact | GitHub Pages / local file |
|---|---|---|
| Sample data, charts, filters | Yes | Yes |
| Load your own posts | Yes | Yes |
| Label posts by hand | Yes | Yes |
| Label posts with Claude | Yes, on the viewer's own Claude account | No |
| Export CSV, copy summary | Yes | Yes |

Claude labeling uses the artifact runtime's `sample` capability, which only
exists when the page is opened inside claude.ai.

## Using it

- **Input:** pasted posts (one per line, optionally starting with a date), a CSV
  with a text column, JSON from the X API, or `tweets.js` from an X data archive.
- **Labeling:** 25 posts per request to Claude. Each post gets one category, a
  confidence level and a short reason. Labels you set by hand are kept when you
  re-label.
- **Storage:** posts and labels stay in the viewer's browser (`localStorage`).

## Files

- `index.html` is the whole app. GitHub Pages serves it from the root of `main`.
  Everything between `<body>` and `</body>` is exactly what gets published to
  the claude.ai artifact. The `<head>` only adds the base styles an artifact
  gets automatically.
- `.nojekyll` tells GitHub Pages to serve the files as they are, without running
  Jekyll.
