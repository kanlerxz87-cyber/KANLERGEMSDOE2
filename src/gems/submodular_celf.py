"""Exact case-control Bayes calibration & Minoux lazy-greedy (CELF) 300 m DTI allocation.

Mathematical formulation:
  1. Case-control Bayes posterior calibration (Prentice & Pyke 1979; Elkan & Noto 2008):
     Given model probability `p(x)` trained on a subsampled dataset with positive fraction
     `pi_sample` while true domain prevalence is `pi_true`, the exact posterior probability is:
         pi(x) = (gamma * p(x)) / (gamma * p(x) + 1 - p(x)),
     where `gamma = (pi_true * (1 - pi_sample)) / (pi_sample * (1 - pi_true))`.

  2. Exact 300 m triangular-kernel submodular coverage maximization (Minoux 1978 CELF):
     For active off-catalogue domain `A` and calibrated pixel inclusion probability `pi(y)` (`0`
     outside `A`), expected weighted true positives under the competition's 300 m (`3.0 px`)
     linearly decaying kernel `K(d) = max(0, 1 - d / 3)` are:
         F(S) = sum_{y in A} pi(y) * max_{x in S} K(||x - y||_2).
     `F(S)` is monotone non-decreasing and submodular (`F(S u {x}) - F(S) >= F(T u {x}) - F(T)`
     for `S subseteq T`), so Minoux lazy-greedy heap evaluation returns the exact greedy sequence
     with `(1 - 1/e)` optimality guarantee in seconds on CPU.
"""
from __future__ import annotations

import heapq
import math
import numpy as np


# Exact 25 offsets on the 100 m grid with Euclidean distance < 3.0 px (300 m)
KERNEL_OFFSETS: tuple[tuple[int, int, float], ...] = tuple(
    (dy, dx, 1.0 - math.hypot(dy, dx) / 3.0)
    for dy in range(-2, 3)
    for dx in range(-2, 3)
    if math.hypot(dy, dx) < 3.0
)


def bayes_case_control_calibrate(
    p_model: np.ndarray,
    pi_true: float,
    pi_sample: float,
    eps: float = 1e-6,
) -> np.ndarray:
    """Convert subsampled classifier probabilities to true-prevalence Bayes posteriors."""
    p = np.clip(np.asarray(p_model, dtype=np.float32), eps, 1.0 - eps)
    pi_t = float(np.clip(pi_true, 1e-5, 0.5))
    pi_s = float(np.clip(pi_sample, 1e-5, 0.99))
    gamma = (pi_t * (1.0 - pi_s)) / (pi_s * (1.0 - pi_t))
    gp = gamma * p
    return (gp / (gp + (1.0 - p))).astype(np.float32)


def greedy_disk_allocate(
    score2d: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    min_spacing_px: float = 3.0,
) -> np.ndarray:
    """Baseline hard-disk greedy dot emitter (`EXP-1`, `EXP-2`, and `BASE_E1_XGHGB`)."""
    H, W = score2d.shape
    out = np.zeros((H, W), dtype=np.float32)
    if budget <= 0 or not allowed.any():
        return out
    ys, xs = np.nonzero(allowed & np.isfinite(score2d) & (score2d > 0.0))
    if ys.size == 0:
        return out
    vals = score2d[ys, xs]
    max_cand = min(ys.size, max(budget * 14, 60_000))
    if ys.size > max_cand:
        part = np.argpartition(vals, -max_cand)[-max_cand:]
        ys, xs, vals = ys[part], xs[part], vals[part]
    order = np.argsort(vals)[::-1]
    ys, xs = ys[order], xs[order]

    rad = int(math.ceil(min_spacing_px))
    dy, dx = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    disk = (dy * dy + dx * dx) <= (min_spacing_px * min_spacing_px + 1e-9)
    ody, odx = np.nonzero(disk)
    ody = (ody - rad).astype(np.int32)
    odx = (odx - rad).astype(np.int32)

    blocked = ~allowed.copy()
    picked = 0
    for r, c in zip(ys.tolist(), xs.tolist()):
        if blocked[r, c]:
            continue
        out[r, c] = 1.0
        picked += 1
        if picked >= budget:
            break
        rr = r + ody
        cc = c + odx
        ok = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
        blocked[rr[ok], cc[ok]] = True
    return out


def celf_submodular_allocate(
    pi2d: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    min_marginal_gain: float = 0.0,
    candidate_mult: int = 9,
) -> np.ndarray:
    """Exact Minoux lazy-greedy (CELF) 300 m triangular-kernel coverage allocator (`EXP-3`)."""
    H, W = pi2d.shape
    out = np.zeros((H, W), dtype=np.float32)
    if budget <= 0 or not allowed.any():
        return out

    # Pad by 2 pixels on all borders so flat neighbor offsets never wrap around row boundaries!
    Hp, Wp = H + 4, W + 4
    pi_pad = np.zeros((Hp, Wp), dtype=np.float32)
    w_in = np.where(allowed & np.isfinite(pi2d) & (pi2d > 0.0), pi2d, 0.0).astype(np.float32)
    pi_pad[2 : H + 2, 2 : W + 2] = w_in

    # Vectorized exact initial marginal gain for every allowed candidate pixel
    init_gain = np.zeros((H, W), dtype=np.float32)
    for dy, dx, k in KERNEL_OFFSETS:
        init_gain += pi_pad[2 + dy : H + 2 + dy, 2 + dx : W + 2 + dx] * np.float32(k)

    ys, xs = np.nonzero(allowed & (init_gain > min_marginal_gain))
    if ys.size == 0:
        return out
    gains0 = init_gain[ys, xs]
    max_cand = min(ys.size, max(budget * candidate_mult, 80_000))
    if ys.size > max_cand:
        part = np.argpartition(gains0, -max_cand)[-max_cand:]
        ys, xs, gains0 = ys[part], xs[part], gains0[part]

    # Flat indices in padded (Hp, Wp) array
    flat_cands = ((ys + 2).astype(np.int64) * Wp + (xs + 2).astype(np.int64)).tolist()
    pi_flat = pi_pad.ravel()
    cov_flat = np.zeros(Hp * Wp, dtype=np.float32)

    off_steps = tuple((dy * Wp + dx, float(k)) for dy, dx, k in KERNEL_OFFSETS)

    # Min-heap of (-upper_bound, step_evaluated, padded_flat_idx)
    heap = [(-float(g), 0, fidx) for g, fidx in zip(gains0.tolist(), flat_cands)]
    heapq.heapify(heap)

    picked = 0
    step_now = 0
    heappop = heapq.heappop
    heappush = heapq.heappush

    while heap and picked < budget:
        neg_ub, eval_step, fidx = heappop(heap)
        if eval_step == step_now:
            gain = -neg_ub
            if gain <= min_marginal_gain:
                break
            r = (fidx // Wp) - 2
            c = (fidx % Wp) - 2
            out[r, c] = 1.0
            for d_off, k in off_steps:
                nb = fidx + d_off
                if k > cov_flat[nb]:
                    cov_flat[nb] = k
            picked += 1
            step_now += 1
        else:
            # Recompute exact marginal gain under current coverage `cov_flat`
            g_exact = 0.0
            for d_off, k in off_steps:
                nb = fidx + d_off
                rem = k - cov_flat[nb]
                if rem > 0.0:
                    w_nb = pi_flat[nb]
                    if w_nb > 0.0:
                        g_exact += w_nb * rem
            if g_exact > min_marginal_gain:
                heappush(heap, (-g_exact, step_now, fidx))

    return out
