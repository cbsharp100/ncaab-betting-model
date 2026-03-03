import numpy as np
from typing import Union

Number = Union[float, int]
ArrayLike = Union[Number, np.ndarray]

def _as_array(x: ArrayLike) -> np.ndarray:
    return np.asarray(x, dtype=float)

def _maybe_scalar_out(arr: np.ndarray, original: ArrayLike):
    return arr.item() if np.isscalar(original) else arr

def prob_to_moneyline(p: ArrayLike) -> ArrayLike:
    """
    Convert probability (0..1) to American moneyline.
    Returns negative values for favorites, positive for underdogs.
    """
    a = _as_array(p)
    if np.any((a <= 0) | (a >= 1)):
        # guard: probabilities exactly 0 or 1 are not representable as finite moneylines
        # map them to large magnitude values instead
        a = np.clip(a, 1e-12, 1 - 1e-12)
    ml = np.empty_like(a)
    fav_mask = a >= 0.5
    ml[fav_mask] = - (a[fav_mask] / (1.0 - a[fav_mask])) * 100.0
    ml[~fav_mask] = ((1.0 - a[~fav_mask]) / a[~fav_mask]) * 100.0
    return _maybe_scalar_out(np.round(ml).astype(int), p)

def moneyline_to_prob(ml: ArrayLike) -> ArrayLike:
    """
    Convert American moneyline to implied probability (0..1).
    """
    a = _as_array(ml)
    prob = np.empty_like(a)
    neg_mask = a < 0
    prob[neg_mask] = np.abs(a[neg_mask]) / (np.abs(a[neg_mask]) + 100.0)
    prob[~neg_mask] = 100.0 / (a[~neg_mask] + 100.0)
    return _maybe_scalar_out(prob, ml)

def rating_to_spread(rating_diff: ArrayLike, factor: Number = 0.04) -> ArrayLike:
    """
    Convert rating differential into point spread estimate.
    Default factor: ~25 Elo ≈ 1 point spread.
    """
    a = _as_array(rating_diff)
    return _maybe_scalar_out(a * float(factor), rating_diff)


def spread_to_rating(spread: ArrayLike, factor: Number = 0.04) -> ArrayLike:
    """
    Inverse of rating_to_spread.
    """
    a = _as_array(spread)
    return _maybe_scalar_out(a / float(factor), spread)

def expected_value(prob_win: ArrayLike, odds: ArrayLike, stake: Number = 1.0) -> ArrayLike:
    """
    Expected profit per unit stake.
    prob_win: probability of winning (0..1)
    odds: American moneyline (e.g., -150, +200) or array matching prob_win
    stake: amount risked per bet (default 1.0)
    Returns expected profit (can be negative) per stake.
    """
    p = _as_array(prob_win)
    ml = _as_array(odds)
    if p.shape != ml.shape:
        # allow broadcasting
        p, ml = np.broadcast_arrays(p, ml)
    profit_if_win = np.where(ml < 0, 100.0 / np.abs(ml) * stake, (ml / 100.0) * stake)
    ev = p * profit_if_win - (1.0 - p) * stake
    return _maybe_scalar_out(ev, prob_win if np.isscalar(prob_win) else ev)