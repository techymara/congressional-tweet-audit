// Run with: node --test worker/x-fetch.test.mjs
// Exercises the Worker against a fake X API; no network or X credits needed.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker from './x-fetch.js';

const env = { X_BEARER_TOKEN: 'xtoken', ACCESS_CODE: 'open sesame', ALLOWED_ORIGINS: 'https://techymara.github.io', MAX_POSTS: '1000' };
const ORIGIN = 'https://techymara.github.io';

function fakeX({ total = 230, failUser = 0 } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    const u = new URL(url);
    calls.push({ path: u.pathname, params: Object.fromEntries(u.searchParams), auth: init.headers.Authorization });
    if (u.pathname.startsWith('/2/users/by/username/')) {
      if (failUser) return new Response(JSON.stringify({ title: 'Unauthorized' }), { status: failUser });
      return Response.json({ data: { id: '42', name: 'Rep. Test Person', username: 'RepTest' } });
    }
    const start = Number(u.searchParams.get('pagination_token') || 0);
    const n = Math.min(Number(u.searchParams.get('max_results')), total - start);
    const data = Array.from({ length: n }, (_, i) => ({
      id: String(1000 + start + i),
      text: 'Post ' + (start + i),
      created_at: '2026-09-' + String(1 + ((start + i) % 28)).padStart(2, '0') + 'T12:00:00.000Z',
      public_metrics: { like_count: start + i, retweet_count: 1 },
      ...(start + i === 0 ? { note_tweet: { text: 'Long version of post 0' } } : {}),
    }));
    const next = start + n < total ? String(start + n) : undefined;
    return Response.json({ data, meta: { result_count: n, ...(next ? { next_token: next } : {}) } });
  };
  return calls;
}

const get = (qs, code = 'open sesame') =>
  worker.fetch(new Request('https://w.example/x/posts?' + qs, { headers: { Authorization: 'Bearer ' + code, Origin: ORIGIN } }), env);

test('pages through the timeline and normalizes posts', async () => {
  const calls = fakeX({ total: 230 });
  const res = await get('handle=@RepTest&max=500&since=2026-01-01');
  assert.equal(res.status, 200);
  assert.equal(res.headers.get('Access-Control-Allow-Origin'), ORIGIN);
  const body = await res.json();
  assert.equal(body.posts.length, 230);
  assert.equal(body.member.name, 'Rep. Test Person');
  assert.deepEqual(body.posts[0], { text: 'Long version of post 0', date: '2026-09-01', likes: 0, reposts: 1, url: 'https://x.com/RepTest/status/1000' });
  assert.equal(body.estimatedCostUSD, 1.16);
  const pages = calls.filter((c) => c.path === '/2/users/42/tweets');
  assert.equal(pages.length, 3);
  assert.equal(pages[0].params.exclude, 'retweets,replies');
  assert.equal(pages[0].params.start_time, '2026-01-01T00:00:00Z');
  assert.equal(pages[0].auth, 'Bearer xtoken');
});

test('stops at max posts and respects the MAX_POSTS cap', async () => {
  fakeX({ total: 5000 });
  let body = await (await get('handle=RepTest&max=150')).json();
  assert.equal(body.posts.length, 150);
  body = await (await get('handle=RepTest&max=99999')).json();
  assert.equal(body.posts.length, 1000);
});

test('rejects a wrong access code and bad input', async () => {
  fakeX();
  assert.equal((await get('handle=RepTest', 'nope')).status, 401);
  assert.equal((await get('handle=not a handle!')).status, 400);
  assert.equal((await get('handle=RepTest&since=yesterday')).status, 400);
});

test('passes X errors through as readable messages', async () => {
  fakeX({ failUser: 401 });
  const res = await get('handle=RepTest');
  assert.equal(res.status, 502);
  assert.match((await res.json()).error, /rejected the bearer token/);
});

test('answers CORS preflight', async () => {
  const res = await worker.fetch(new Request('https://w.example/x/posts', { method: 'OPTIONS', headers: { Origin: ORIGIN } }), env);
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('Access-Control-Allow-Headers'), 'Authorization');
});
