# Congressional Tweet Audit

Pick any senator or representative, pull their recent posts from Bluesky or X, and
see how much of what they post is outrage, legislative work, district focus and more.
Claude labels each post, and the page charts the mix, how it changes over time, and
which categories get the most engagement.

- **Website (GitHub Pages):** https://techymara.github.io/congressional-tweet-audit/
- **claude.ai artifact:** https://claude.ai/artifact/3bVCw8t2p2EkWWto242PBj

## How it works

1. **Pick a member** from the list of all current senators and representatives.
   Their name, district and official X handle fill in automatically. Bluesky
   handles aren't in the public roster, so use **Find this member on Bluesky** and
   pick the official account.
2. **Analyze.** The page fetches their posts (Bluesky for free, or X through your
   own fetcher), then has Claude label each one.
3. **Come back any time.** Each member's analysis is saved in your browser, so
   picking them again loads it instantly. Fetching again only labels new posts.

Everything runs in the visitor's browser. Each visitor uses their own Anthropic API
key, and X fetching is billed to whoever runs the fetcher.

| | Website (GitHub Pages) | claude.ai artifact |
|---|---|---|
| Member picker, charts, saved analyses | Yes | Yes |
| Fetch posts from Bluesky | Yes, free | No (the artifact can't reach other sites) |
| Fetch posts from X | Yes, through your fetcher | No |
| Paste or upload posts | Yes | Yes |
| Label with Claude | Yes, with your Anthropic API key | Yes, on your claude.ai plan |

## Costs

| What | Cost |
|---|---|
| Hosting (GitHub Pages) and the roster | Free |
| Bluesky posts | Free |
| X posts | About $0.005 per post read, plus $0.01 per account lookup, from prepaid X credits |
| Claude labeling, per 1,000 posts | About $0.25 on Haiku 4.5, $0.75 on Sonnet 5.5, $1.50 on Opus 5.5 (the default) |
| X fetcher (Cloudflare Worker) | Free plan |

For example, a member who posts about 5 times a day has about 1,800 posts a year:
roughly $9 to fetch from X, and $0.45 to $2.70 to label. After that, a monthly
refresh is about $1.

## Labeling with an API key (website)

1. Create an API key in the [Anthropic Console](https://console.anthropic.com/), add a
   little prepaid credit, and set a spend limit.
2. Paste the key into step 4 on the site. Your browser sends it only to Anthropic,
   and it's forgotten when you close the tab unless you tick Remember.
3. Pick a model. The page shows a rough cost before a run and the actual cost after.

Opus and Sonnet requests use low effort, a JSON schema so every label comes back in
the right shape, and Anthropic's server-side fallback, which retries a batch on
another model if a safety classifier declines it.

## Getting posts

### Bluesky (free, built in)
Choose **Bluesky · free** in step 2 and select **Fetch posts**, or use **Fetch and
label posts** on the member's page. No account or key is needed.

### X, from the website: set up your fetcher (about 30 minutes, once)
X's API doesn't accept calls from web pages, and your X token must stay secret, so a
small free Cloudflare Worker (`worker/x-fetch.js`) holds the token and fetches for you.

1. **X developer account.** Sign up at [developer.x.com](https://developer.x.com),
   accept the Developer Agreement, and describe your use honestly, for example:
   "Content-type analysis of members of Congress's official posts. No model
   training, no inference of sensitive traits, no redistribution." Create an app,
   buy a small amount of credit, **set a spending limit**, and copy the app's
   **Bearer Token**.
2. **Cloudflare Worker.** Create a free [Cloudflare](https://dash.cloudflare.com)
   account, then go to **Workers & Pages → Create → Worker**. Deploy the starter,
   select **Edit code**, replace it with the contents of `worker/x-fetch.js`, and
   deploy again.
3. **Worker settings.** Under **Settings → Variables and Secrets**, add:
   - `X_BEARER_TOKEN` (Secret): the token from step 1
   - `ACCESS_CODE` (Secret): a long passphrase you make up
   - `ALLOWED_ORIGINS` (Text): `https://techymara.github.io`
4. **Connect the site.** In step 2 choose **X · paid**, then paste the Worker's
   address (like `https://congress-x-fetch.yourname.workers.dev`) and your access
   code. Tick Remember if this is your own computer.

Prefer the command line? Run `cd worker && npx wrangler deploy`, then
`npx wrangler secret put X_BEARER_TOKEN` and `npx wrangler secret put ACCESS_CODE`.

Anyone with the access code spends your X credits, so share it only with people
you trust.

### X or Bluesky, from your computer
`tools/fetch_posts.py` saves posts to a file you upload in step 2. It needs no
packages.

```bash
export X_BEARER_TOKEN=...            # only for X
python3 tools/fetch_posts.py x RepChipRoy --max 500 --since 2026-01-01
python3 tools/fetch_posts.py bluesky someone.bsky.social --max 500
```

The script shows the most X could charge and asks before it starts.

### Other ways in
- Copy and paste posts from a profile, one per line (start a line with a date to
  include it).
- Upload a CSV or JSON with a text column, or `tweets.js` from an X data archive of
  an account you control.
- Don't use scrapers or unofficial "Twitter APIs". X's terms ban scraping.

## X's rules, in short

- Don't use the posts to train AI models. Labeling them with Claude isn't training.
- Don't infer anyone's political beliefs or affiliation from the posts. The categories
  here describe what a post does, so don't add ideology categories. The party shown
  in the member picker comes from the public congressional roster, not from posts.
- Don't republish the posts you fetch. In this app they stay in your browser, and
  `.gitignore` keeps fetched files out of the repo.

## Files

- `index.html` is the whole app. GitHub Pages serves it from the root of `main`.
  Everything between `<body>` and `</body>` is what gets published to the claude.ai
  artifact; the `<head>` adds the base styles an artifact gets automatically.
- `data/members.json` is the roster of current members with their official X
  handles, built from the public-domain
  [congress-legislators](https://github.com/unitedstates/congress-legislators)
  project by `tools/build_members.py`. A GitHub Action
  (`.github/workflows/update-members.yml`) refreshes it every Monday.
- `worker/` is the X fetcher (Cloudflare Worker) and its tests:
  `node --test worker/x-fetch.test.mjs`.
- `tools/fetch_posts.py` fetches posts from your computer.
- `vendor/` holds a pinned browser build of the official Anthropic SDK, used for
  API-key labeling. See `vendor/README.md`.
- `.nojekyll` tells GitHub Pages to serve the files as they are.
