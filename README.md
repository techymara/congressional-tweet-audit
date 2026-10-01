# Congressional Tweet Audit

A single-page tool that sorts a member of Congress's posts on X into categories
(outrage & culture war, legislative work, district focus, and more you can switch
on) and charts the mix, how it changes over time, and which categories get the
most engagement.

- **Website (GitHub Pages):** https://techymara.github.io/congressional-tweet-audit/
- **claude.ai artifact:** https://claude.ai/artifact/3bVCw8t2p2EkWWto242PBj

## Where labeling works

| | claude.ai artifact | Website (GitHub Pages) |
|---|---|---|
| Sample data, charts, filters | Yes | Yes |
| Load your own posts | Yes | Yes |
| Label posts by hand | Yes | Yes |
| Label posts with Claude | Yes, on the viewer's claude.ai plan | Yes, with the viewer's own Anthropic API key |
| Export CSV, copy summary | Yes | Yes |

### Labeling on the website with an API key

1. Create an API key in the [Anthropic Console](https://console.anthropic.com/), add a
   little prepaid credit, and set a spend limit.
2. Paste the key into step 4 on the site. The browser sends it only to Anthropic. It's
   forgotten when the tab closes unless you tick "Remember the key on this device".
3. Pick a model. The page shows a rough cost before you start and the actual cost
   when the run finishes.

Rough cost per 1,000 posts (25 posts per request):

| Model | About |
|---|---|
| Claude Haiku 4.5 (cheapest) | $0.25 |
| Claude Sonnet 5.5 | $0.75 |
| Claude Opus 5.5 (most careful, the default) | $1.50 |

Opus and Sonnet requests use low effort, a JSON schema so every label comes back in
the right shape, and Anthropic's server-side fallback, so a batch a safety classifier
declines gets retried on another model.

## Getting posts within X's rules

- **Copy and paste** from the member's profile on x.com. Free, but manual.
- **The official X API.** Pay per use, about $0.005 per post read. The X API doesn't
  accept calls straight from a web page, so fetch with a script or small server and
  upload the JSON here.
- **An X data archive** (`tweets.js`) works only for an account you control.
- **Don't use scrapers** or unofficial "Twitter APIs". X's terms ban scraping.

If you use the X API, X's Developer Policy also applies:
- Don't use the posts to train AI models. Labeling them with Claude isn't training.
- Don't infer the member's political beliefs or affiliation. The categories here
  describe what a post does, so don't add ideology categories.
- Don't republish the posts you fetch. In this app they stay in your browser; don't
  commit them to this repo.

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
- `vendor/` holds a pinned browser build of the official Anthropic SDK, used for
  API-key labeling. See `vendor/README.md`.
- `.nojekyll` tells GitHub Pages to serve the files as they are, without running
  Jekyll.
