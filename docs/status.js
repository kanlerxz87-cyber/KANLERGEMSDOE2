/* Read the committed dated snapshot only; this never contacts DrivenData. */
(function () {
  const score = document.getElementById('board-score');
  const time = document.getElementById('board-time');
  const freshness = document.getElementById('board-freshness');
  if (!score || !time || !freshness) return;
  function show(data) {
    const observed = Date.parse(data.observed_utc);
    const age = Date.now() - observed;
    if (!Number.isFinite(observed) || !Number.isFinite(age) || age < -300000 ||
        !/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(String(data.top_public_dti)) ||
        data.source !== 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/') {
      freshness.textContent = 'Snapshot timestamp or value invalid; consult the official leaderboard.';
      freshness.className = 'freshness stale';
      return;
    }
    score.textContent = data.top_public_dti;
    time.textContent = 'Observed ' + data.observed_utc;
    const hours = Math.max(0, Math.floor(age / 3600000));
    freshness.textContent = age > 24 * 3600000 ? 'STALE · ' + hours + ' hours old. Check the official page.' :
      'Snapshot ' + hours + ' hours old; the public board may have changed.';
    freshness.className = 'freshness ' + (age > 24 * 3600000 ? 'stale' : 'fresh');
  }
  fetch('leaderboard_snapshot.json', { cache: 'no-store' }).then(r => {
    if (!r.ok) throw new Error('snapshot unavailable');
    return r.json();
  }).then(show).catch(() => {
    freshness.textContent = 'Snapshot refresh unavailable; check the observation time and official page.';
    freshness.className = 'freshness stale';
  });
})();
