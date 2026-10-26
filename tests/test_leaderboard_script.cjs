const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../docs/assets/dashboard.js'), 'utf8');
async function render(payload, reject = false) {
  const nodes = {'leader-score': {textContent: '0.4437'}, 'leader-time': {textContent:'dated fallback'}, 'leader-state':{textContent:'DATED SNAPSHOT'}};
  const context = {document:{getElementById: id => nodes[id]}, fetch: async () => {
    if (reject) throw Error('offline');
    return {ok:true, json:async()=>payload};
  }, Date, Intl, Number, Boolean};
  vm.runInNewContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return nodes;
}
test('current score is displayed with an observation time', async () => {
  const d = await render({score:.3812, observed_utc:new Date().toISOString()});
  assert.equal(d['leader-score'].textContent, '0.3812');
  assert.equal(d['leader-state'].textContent, 'DATED SNAPSHOT');
  assert.match(d['leader-time'].textContent, /UTC/);
});
test('old score is clearly stale', async () => {
  const d = await render({score:.4437, observed_utc:'2020-01-01T00:00:00Z'});
  assert.equal(d['leader-state'].textContent, 'STALE SNAPSHOT');
});
test('invalid response and offline leave the dated fallback untouched', async () => {
  for (const d of [await render({score:3, observed_utc:'not-a-date'}), await render({}, true)]) {
    assert.equal(d['leader-score'].textContent, '0.4437');
    assert.equal(d['leader-time'].textContent, 'dated fallback');
  }
});
