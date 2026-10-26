(() => {
  'use strict';
  const feed = document.querySelector('[data-github-feed]');
  if (!feed) return;
  const button = feed.querySelector('[data-refresh]');
  const status = feed.querySelector('[data-status]');
  const items = Array.from(feed.querySelectorAll('[data-repo]'));
  if (!button || !status || !items.length) return;
  button.addEventListener('click', async () => {
    button.disabled = true;
    status.textContent = 'Checking public GitHub heads. This does not check scores or submission readiness.';
    let changed = 0, unavailable = 0;
    await Promise.all(items.map(async item => {
      const state = item.querySelector('[data-state-text]');
      const repo = item.dataset.repo;
      const expected = item.dataset.head;
      try {
        if (!/^buffedlizard55-lab\/GEMSDOE(24|25|27|28|30|31|32|33|36)$/.test(repo) || !/^[0-9a-f]{40}$/.test(expected)) throw new Error('missing snapshot');
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 10000);
        let body;
        try {
          const response = await fetch(`https://api.github.com/repos/${repo}/commits/main`, {signal: controller.signal, headers: {'Accept': 'application/vnd.github+json'}});
          if (!response.ok) throw new Error(`GitHub HTTP ${response.status}`);
          body = await response.json();
        } finally { window.clearTimeout(timeout); }
        if (!/^[0-9a-f]{40}$/.test(body.sha || '')) throw new Error('invalid GitHub response');
        if (body.sha === expected) {
          item.dataset.state = 'unchanged';
          state.textContent = 'Head unchanged';
        } else {
          changed += 1;
          item.dataset.state = 'changed';
          state.textContent = 'Updated · re-audit needed';
        }
      } catch (_) {
        unavailable += 1;
        item.dataset.state = 'unknown';
        state.textContent = 'Check unavailable';
      }
    }));
    const now = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    status.textContent = `Checked ${now}: ${changed} changed, ${unavailable} unavailable. Head checks do not validate scores or approve submissions.`;
    button.disabled = false;
  });
})();
