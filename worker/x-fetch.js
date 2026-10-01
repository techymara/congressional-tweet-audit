// Congressional Tweet Audit: X fetcher (a Cloudflare Worker).
//
// Lets the website fetch a member's recent posts from the official X API.
// X's API doesn't accept calls from web pages, and the X bearer token must stay
// secret, so this small server holds the token and makes the calls.
//
//   GET /x/posts?handle=RepChipRoy&max=500&since=2026-01-01&replies=0
//   Authorization: Bearer <ACCESS_CODE>
//
// Settings (Worker → Settings → Variables and Secrets):
//   X_BEARER_TOKEN   secret  App bearer token from the X Developer Console
//   ACCESS_CODE      secret  A long passphrase you choose; the website sends it with each request
//   ALLOWED_ORIGINS  text    Comma-separated sites allowed to call this, e.g. https://techymara.github.io
//   MAX_POSTS        text    Optional cap on posts per request (default 1000, at most 3200)
//
// Posts pass straight through to the browser. Nothing is stored here, which keeps
// with X's rules on deletions and redistribution. Every post read is billed to your
// X credits (about $0.005 each), so keep the access code private and set a spending
// limit in the X Developer Console.

const X_API = 'https://api.x.com/2/';
const COST_PER_POST = 0.005;
const COST_PER_USER = 0.01;

export default {
  async fetch(request, env) {
    const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
    const origin = request.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : allowed[0] || 'null',
      'Access-Control-Allow-Headers': 'Authorization',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Max-Age': '86400',
      Vary: 'Origin',
    };
    const reply = (status, body) =>
      new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } });

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    if (url.pathname === '/' || url.pathname === '/health') return reply(200, { ok: true });
    if (url.pathname !== '/x/posts' || request.method !== 'GET') return reply(404, { error: 'Not found.' });

    if (!env.X_BEARER_TOKEN || !env.ACCESS_CODE) {
      return reply(500, { error: 'The fetcher is missing X_BEARER_TOKEN or ACCESS_CODE. Add both in the Worker settings.' });
    }
    const given = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
    if (!(await sameSecret(given, env.ACCESS_CODE))) return reply(401, { error: 'Wrong access code.' });

    const handle = (url.searchParams.get('handle') || '').trim().replace(/^@/, '');
    if (!/^[A-Za-z0-9_]{1,15}$/.test(handle)) return reply(400, { error: 'That isn’t a valid X handle.' });
    const cap = Math.min(3200, Number(env.MAX_POSTS) || 1000);
    const max = Math.min(cap, Math.max(5, parseInt(url.searchParams.get('max') || '500', 10) || 500));
    const since = url.searchParams.get('since') || '';
    if (since && !/^\d{4}-\d{2}-\d{2}$/.test(since)) return reply(400, { error: 'Use YYYY-MM-DD for since.' });
    const withReplies = url.searchParams.get('replies') === '1';

    const x = (path, params) =>
      fetch(X_API + path + '?' + new URLSearchParams(params), {
        headers: { Authorization: 'Bearer ' + env.X_BEARER_TOKEN },
      });

    let res = await x('users/by/username/' + handle, { 'user.fields': 'name' });
    if (!res.ok) return reply(res.status === 404 ? 404 : 502, { error: await xError(res) });
    const user = (await res.json()).data;
    if (!user) return reply(404, { error: `No X account named @${handle}.` });

    const posts = [];
    let token = '';
    let partial = '';
    // The free Workers plan allows 50 outbound requests per call; 3,200 posts take 33.
    while (posts.length < max) {
      const params = {
        max_results: String(Math.min(100, Math.max(5, max - posts.length))),
        'tweet.fields': 'created_at,public_metrics,note_tweet',
        exclude: withReplies ? 'retweets' : 'retweets,replies',
      };
      if (since) params.start_time = since + 'T00:00:00Z';
      if (token) params.pagination_token = token;
      res = await x('users/' + user.id + '/tweets', params);
      if (!res.ok) {
        if (!posts.length) return reply(502, { error: await xError(res) });
        partial = await xError(res);
        break;
      }
      const page = await res.json();
      for (const t of page.data || []) {
        if (posts.length >= max) break;
        const m = t.public_metrics || {};
        posts.push({
          text: (t.note_tweet && t.note_tweet.text) || t.text,
          date: (t.created_at || '').slice(0, 10),
          likes: m.like_count ?? null,
          reposts: m.retweet_count ?? null,
          url: `https://x.com/${user.username}/status/${t.id}`,
        });
      }
      token = (page.meta && page.meta.next_token) || '';
      if (!token) break;
    }

    return reply(200, {
      member: { name: user.name, handle: user.username, platform: 'x' },
      posts,
      estimatedCostUSD: Math.round((posts.length * COST_PER_POST + COST_PER_USER) * 1000) / 1000,
      ...(partial ? { warning: 'Stopped early: ' + partial } : {}),
    });
  },
};

async function xError(res) {
  let detail = '';
  try {
    const body = await res.json();
    detail = body.detail || body.title || (body.errors && body.errors[0] && body.errors[0].message) || '';
  } catch (e) {
    // not JSON
  }
  const what = {
    401: 'X rejected the bearer token.',
    402: 'Your X account is out of credits.',
    403: 'X refused the request. Check your app’s access level and credits in the X Developer Console.',
    404: 'X couldn’t find that account.',
    429: 'X’s rate limit was hit. Try again in 15 minutes.',
  }[res.status] || `X returned an error (${res.status}).`;
  return detail ? `${what} ${detail}` : what;
}

// Compare secrets without leaking their length or contents through timing.
async function sameSecret(a, b) {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest('SHA-256', enc.encode(a)),
    crypto.subtle.digest('SHA-256', enc.encode(b)),
  ]);
  const x = new Uint8Array(ha);
  const y = new Uint8Array(hb);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0 && a.length > 0;
}
