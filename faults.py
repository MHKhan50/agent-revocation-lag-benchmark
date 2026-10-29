"""Revocation under realistic delivery faults (Python 3.9+).

The base benchmark (benchmark.py) shows that per-action checks and an
instant push notification both block every revoked action, by definition.
This module asks the harder question: what happens when the revocation
notice arrives late or not at all, and how often must a cached permission
be re-checked to bound the damage?

Policies (all run on the same 1,800 traces as benchmark.py):
  ttl_k            re-check the permission every k steps (k = 1 is a check before every step)
  push_dD_lossP    one check at start, then a revocation notice that arrives D steps late
                   and is lost with probability P (a lost notice is never re-sent)
  push_dD_lossP+ttl8  the same push, with a re-check every 8 steps as a backstop
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

TTLS = (1, 2, 3, 4, 6, 8)
DELAYS = (0, 1, 2, 4)
LOSSES = (0.0, 0.1, 0.3)
BACKSTOP_TTL = 8


def notice_lost(scenario_id: str, loss: float) -> bool:
    """Same random draw per scenario for every loss level, so higher loss only adds lost notices."""
    return random.Random("loss-" + scenario_id).random() < loss


def simulate(scenario: Dict[str, object], ttl: Optional[int] = None, delay: Optional[int] = None,
             loss: float = 0.0) -> Dict[str, object]:
    """ttl alone = periodic re-check; delay set = push notice; both = push with a TTL backstop."""
    actions = str(scenario["action_types"])
    revoke_at = int(scenario["revoke_at"])
    push = delay is not None
    arrive = None
    if push and not notice_lost(str(scenario["scenario_id"]), loss):
        arrive = revoke_at + int(delay)

    allowed = True
    checks = notifications = unauthorized = opportunities = 0
    first_block = None
    for step, action in enumerate(actions):
        if step == 0 or (ttl is not None and step % ttl == 0):
            checks += 1
            allowed = step < revoke_at
        if arrive is not None and step == arrive:
            notifications += 1
            allowed = False
        if action == "S" and step >= revoke_at:
            opportunities += 1
            if allowed:
                unauthorized += 1
            elif first_block is None:
                first_block = step
    return {
        "scenario_id": scenario["scenario_id"],
        "opportunities": opportunities,
        "unauthorized": unauthorized,
        "control_events": checks + notifications,
        "notice_lost": push and arrive is None,
    }


def policy_grid() -> List[Dict[str, object]]:
    grid: List[Dict[str, object]] = []
    for k in TTLS:
        grid.append({"policy": "ttl_{}".format(k), "family": "ttl", "ttl": k, "delay": None, "loss": 0.0})
    for d in DELAYS:
        for p in LOSSES:
            grid.append({"policy": "push_d{}_loss{:.0f}".format(d, p * 100), "family": "push",
                         "ttl": None, "delay": d, "loss": p})
            grid.append({"policy": "push_d{}_loss{:.0f}+ttl{}".format(d, p * 100, BACKSTOP_TTL),
                         "family": "push+backstop", "ttl": BACKSTOP_TTL, "delay": d, "loss": p})
    return grid


def sweep(scenarios: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for pol in policy_grid():
        res = [simulate(s, ttl=pol["ttl"], delay=pol["delay"], loss=float(pol["loss"])) for s in scenarios]
        opp = sum(r["opportunities"] for r in res)
        unauth = sum(r["unauthorized"] for r in res)
        rows.append({
            "policy": pol["policy"], "family": pol["family"],
            "ttl": "" if pol["ttl"] is None else pol["ttl"],
            "delay_steps": "" if pol["delay"] is None else pol["delay"],
            "loss": pol["loss"], "episodes": len(res),
            "unauthorized_side_effect_rate": round(unauth / opp, 4),
            "episodes_with_any_unauthorized_rate": round(sum(r["unauthorized"] > 0 for r in res) / len(res), 4),
            "mean_control_events_per_episode": round(sum(r["control_events"] for r in res) / len(res), 2),
            "notices_lost": sum(bool(r["notice_lost"]) for r in res),
        })
    return rows
