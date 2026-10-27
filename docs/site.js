/* A timestamped snapshot is not called live when refresh fails or ages out. */
(async () => {
  const score = document.getElementById('leader-score');
  const status = document.getElementById('leader-status');
  if (!score || !status) return;
  try {
    const response = await fetch('data/leaderboard.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('Feed unavailable');
    const data = await response.json();
    const observation = data.observation || data.previous_observation;
    if (observation && Number.isFinite(observation.score) && observation.score >= 0 && observation.score <= 1) {
      score.textContent = observation.score.toFixed(4);
    } else {
      score.textContent = '—';
    }
    const date = data.observed_utc || data.previous_observed_utc || 'unknown date';
    const age = Date.now() - Date.parse(date);
    if (data.status === 'fresh' && Number.isFinite(age) && age >= 0 && age < 24 * 60 * 60 * 1000) {
      status.textContent = `Public #1 observed ${date}. The board may have changed since.`;
    } else if (observation) {
      status.textContent = `Dated snapshot from ${date}; refresh is stale or unavailable. Do not treat as current.`;
    } else {
      status.textContent = 'Leaderboard feed unavailable. Check the organizer directly.';
    }
  } catch (_) {
    status.textContent = 'Snapshot shown; automated feed unavailable. Check the organizer directly.';
  }
})();
