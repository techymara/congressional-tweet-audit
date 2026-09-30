# Congressional Tweet Audit

A single-page tool that sorts a member of Congress's posts on X into categories
(outrage & culture war, legislative work, district focus, and more you can switch
on) and charts the mix, how it changes over time, and which categories get the
most engagement.

Published as a claude.ai artifact: https://claude.ai/artifact/3bVCw8t2p2EkWWto242PBj

- **Input:** pasted posts (one per line, optionally starting with a date), a CSV
  with a text column, JSON from the X API, or `tweets.js` from an X data archive.
- **Labeling:** runs through the artifact runtime's `sample` capability, so each
  viewer's own Claude account labels the posts, 25 per request. Opened outside
  claude.ai, labeling is off, but you can still label posts by hand.
- **Storage:** posts and labels live in the viewer's browser (`localStorage`).

`index.html` is the artifact body, so it has no `<html>`/`<head>` wrapper. The
artifact platform adds that when it publishes the page.
