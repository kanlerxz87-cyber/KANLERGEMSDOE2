'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('docs/assets/site.js', 'utf8');
let listener;
const button = {disabled: false, addEventListener: (type, handler) => { assert.equal(type, 'click'); listener = handler; }};
const status = {textContent: ''};
function item(id, head = 'a'.repeat(40)) {
  const text = {textContent: ''};
  return {dataset: {repo: `buffedlizard55-lab/GEMSDOE${id}`, head}, text,
          querySelector: () => text};
}
const items = [item(24), item(25), item(27), item(28), item(30, ''), item(31), item(36)];
const feed = {querySelector: q => q === '[data-refresh]' ? button : status,
              querySelectorAll: () => items};
const calls = [];
const context = {
  document: {querySelector: () => feed},
  // Shorten only the test timeout. The app uses a real 10 second timeout.
  window: {setTimeout: fn => setTimeout(fn, 5), clearTimeout}, AbortController, Date,
  fetch: async (url, options) => {
    calls.push(url);
    if (url.includes('GEMSDOE24')) return {ok: true, json: async () => ({sha: 'a'.repeat(40)})};
    if (url.includes('GEMSDOE25')) return {ok: true, json: async () => ({sha: 'b'.repeat(40)})};
    if (url.includes('GEMSDOE27')) return {ok: false, status: 403};
    if (url.includes('GEMSDOE31')) return {ok: true, json: async () => ({sha: 'malformed'})};
    if (url.includes('GEMSDOE36')) return {ok: true, json: () => new Promise((_, reject) => {
      options.signal.addEventListener('abort', () => reject(new Error('timed out')));
    })};
    throw new Error('offline');
  }
};
vm.runInNewContext(source, context);
(async () => {
  await Promise.race([listener(), new Promise((_, reject) => setTimeout(() => reject(new Error('refresh got stuck')), 300))]);
  assert.equal(button.disabled, false);
  assert.equal(items[0].dataset.state, 'unchanged');
  assert.equal(items[1].dataset.state, 'changed');
  for (const index of [2, 3, 4, 5, 6]) assert.equal(items[index].dataset.state, 'unknown');
  assert.match(status.textContent, /1 changed, 5 unavailable/);
  assert.match(status.textContent, /do not validate scores or approve submissions/);
  assert(calls.every(url => url.startsWith('https://api.github.com/repos/')));
  assert(!calls.some(url => url.includes('GEMSDOE30')), 'invalid snapshots must not be fetched');
  console.log('GitHub head feed: unchanged, changed, rate-limit, offline, invalid and stalled-body cases passed.');
})().catch(err => { console.error(err); process.exitCode = 1; });
