#!/usr/bin/env python3
"""Save a member of Congress's recent posts to a JSON file the website can load.

Uses only official APIs: the X API (paid per post read) or Bluesky's public API (free).
No packages to install. The output stays on your computer; upload it in step 2 of
the site. Don't commit it to the repo, since republishing posts goes against X's rules.

  # X: needs an app bearer token from the X Developer Console. About $0.005 per post.
  export X_BEARER_TOKEN=...
  python3 tools/fetch_posts.py x RepChipRoy --max 500 --since 2026-01-01

  # Bluesky: free, no account needed.
  python3 tools/fetch_posts.py bluesky someone.bsky.social --max 500
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

X_API = "https://api.x.com/2/"
BSKY_API = "https://public.api.bsky.app/xrpc/"
COST_PER_POST = 0.005
COST_PER_USER = 0.01


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "congressional-tweet-audit", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            body = json.load(e)
            detail = body.get("detail") or body.get("message") or body.get("title") or ""
        except ValueError:
            detail = ""
        raise SystemExit(f"Request failed ({e.code}). {detail}".strip())


def fetch_x(handle, since, max_posts, replies, token):
    auth = {"Authorization": "Bearer " + token}
    user = get_json(X_API + "users/by/username/" + urllib.parse.quote(handle) + "?user.fields=name", auth).get("data")
    if not user:
        raise SystemExit(f"No X account named @{handle}.")
    posts, next_token = [], ""
    while len(posts) < max_posts:
        params = {
            "max_results": str(min(100, max(5, max_posts - len(posts)))),
            "tweet.fields": "created_at,public_metrics,note_tweet",
            "exclude": "retweets" if replies else "retweets,replies",
        }
        if since:
            params["start_time"] = since + "T00:00:00Z"
        if next_token:
            params["pagination_token"] = next_token
        page = get_json(X_API + f"users/{user['id']}/tweets?" + urllib.parse.urlencode(params), auth)
        for t in page.get("data") or []:
            if len(posts) >= max_posts:
                break
            m = t.get("public_metrics") or {}
            posts.append({
                "text": (t.get("note_tweet") or {}).get("text") or t["text"],
                "date": (t.get("created_at") or "")[:10],
                "likes": m.get("like_count"),
                "reposts": m.get("retweet_count"),
                "url": f"https://x.com/{user['username']}/status/{t['id']}",
            })
        print(f"  {len(posts)} posts…", file=sys.stderr)
        next_token = (page.get("meta") or {}).get("next_token")
        if not next_token:
            break
    return {"name": user["name"], "handle": user["username"], "platform": "x"}, posts


def fetch_bluesky(handle, since, max_posts, replies):
    posts, cursor, name = [], "", ""
    while len(posts) < max_posts:
        params = {"actor": handle, "limit": "100", "filter": "posts_with_replies" if replies else "posts_no_replies"}
        if cursor:
            params["cursor"] = cursor
        page = get_json(BSKY_API + "app.bsky.feed.getAuthorFeed?" + urllib.parse.urlencode(params))
        feed = page.get("feed") or []
        older = False
        for item in feed:
            if item.get("reason"):  # reposts and pinned posts
                continue
            post = item["post"]
            rec = post.get("record") or {}
            if post["author"]["handle"] != handle and post["author"].get("did") != handle:
                continue
            date = (rec.get("createdAt") or post.get("indexedAt") or "")[:10]
            if since and date and date < since:
                older = True
                break
            if not (rec.get("text") or "").strip() or len(posts) >= max_posts:
                continue
            name = name or post["author"].get("displayName") or ""
            posts.append({
                "text": rec["text"],
                "date": date,
                "likes": post.get("likeCount"),
                "reposts": post.get("repostCount"),
                "url": f"https://bsky.app/profile/{post['author']['handle']}/post/{post['uri'].rsplit('/', 1)[-1]}",
            })
        print(f"  {len(posts)} posts…", file=sys.stderr)
        cursor = page.get("cursor")
        if older or not cursor or not feed:
            break
    return {"name": name, "handle": handle, "platform": "bluesky"}, posts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("platform", choices=["x", "bluesky"])
    ap.add_argument("handle", help="X handle (RepChipRoy) or Bluesky handle (name.bsky.social)")
    ap.add_argument("--max", type=int, default=500, help="most posts to fetch (default 500)")
    ap.add_argument("--since", help="only posts on or after this date, YYYY-MM-DD")
    ap.add_argument("--replies", action="store_true", help="include the member's replies (skipped by default)")
    ap.add_argument("--yes", action="store_true", help="skip the X cost confirmation")
    ap.add_argument("-o", "--out", help="output file (default: <handle>-<platform>.json)")
    args = ap.parse_args()

    handle = args.handle.strip().lstrip("@")
    max_posts = max(5, min(args.max, 3200))
    if args.since:
        datetime.date.fromisoformat(args.since)

    if args.platform == "x":
        token = os.environ.get("X_BEARER_TOKEN")
        if not token:
            raise SystemExit("Set X_BEARER_TOKEN to your X app's bearer token first.")
        most = max_posts * COST_PER_POST + COST_PER_USER
        if not args.yes:
            answer = input(f"This reads up to {max_posts} posts from X, about ${most:.2f} at most. Continue? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                raise SystemExit("Cancelled.")
        member, posts = fetch_x(handle, args.since, max_posts, args.replies, token)
    else:
        member, posts = fetch_bluesky(handle, args.since, max_posts, args.replies)

    out = args.out or f"{handle.replace('.', '-')}-{args.platform}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"member": member, "fetched": datetime.date.today().isoformat(), "posts": posts}, f, ensure_ascii=False, indent=1)
    cost = f" X charges about ${len(posts) * COST_PER_POST + COST_PER_USER:.2f}." if args.platform == "x" else ""
    print(f"Saved {len(posts)} posts to {out}.{cost} Upload it in step 2 of the site.")


if __name__ == "__main__":
    main()
