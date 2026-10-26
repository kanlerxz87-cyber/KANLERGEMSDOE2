// The site remains useful without JavaScript. This only updates the public snapshot.
(async () => {
  const score = document.getElementById('leader-score');
  const time = document.getElementById('leader-time');
  const state = document.getElementById('leader-state');
  try {
    const response = await fetch('./data/leaderboard.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('snapshot unavailable');
    const data = await response.json();
    const observed = new Date(data.observed_utc);
    if (!Number.isFinite(data.score) || data.score < 0 || data.score > 1 || Number.isNaN(observed.valueOf())) throw new Error('invalid snapshot');
    const ageMs = Date.now() - observed.valueOf();
    const stale = ageMs > 24 * 60 * 60 * 1000 || ageMs < -60 * 60 * 1000 || Boolean(data.last_refresh_error);
    score.textContent = data.score.toFixed(4);
    const date = new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(observed);
    time.textContent = `Observed ${date} UTC. This is another participant’s public result, not a score for this project.`;
    state.textContent = stale ? 'STALE SNAPSHOT' : 'DATED SNAPSHOT';
  } catch (_) {
    // Preserve the clearly dated HTML fallback; never present an error as a new score.
    state.textContent = 'DATED SNAPSHOT';
  }
})();
