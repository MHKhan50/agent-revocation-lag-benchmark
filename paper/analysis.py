"""Numbers, intervals and figures for the paper (Python 3.9+, matplotlib for the figures).

Everything is recomputed from the repository: the scenarios from generate_dataset.py, the
policies from benchmark.py and faults.py, and the agent episodes from
outputs/llm_probe_episodes.jsonl. Run from the repository root:

    python3 paper/analysis.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark import POLICIES, simulate_scenario  # noqa: E402
from faults import BACKSTOP_TTL, notice_lost, policy_grid, simulate  # noqa: E402
from generate_dataset import generate_scenarios, SEEDS  # noqa: E402

OUT = Path(__file__).resolve().parent
N_BOOT, BOOT_SEED = 2000, 20261104


def scenarios():
    return [dict(s) for seed in SEEDS for s in generate_scenarios(seed)]


def rate(rows, idx):
    opp = sum(rows[i]["opportunities"] for i in idx)
    return sum(rows[i]["unauthorized"] for i in idx) / opp


def bootstrap(per_policy, names, seeds):
    """Seed-stratified percentile bootstrap over episodes; the same draws for every policy."""
    by_seed = defaultdict(list)
    for i, s in enumerate(seeds):
        by_seed[s].append(i)
    rng = random.Random(BOOT_SEED)
    draws = {n: [] for n in names}
    for _ in range(N_BOOT):
        idx = [rng.choice(ids) for ids in by_seed.values() for _ in ids]
        for n in names:
            draws[n].append(rate(per_policy[n], idx))
    return draws


def pct(v, q):
    v = sorted(v)
    k = (len(v) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    sc = scenarios()
    seeds = [s["seed"] for s in sc]
    out = {"scenarios": len(sc)}

    # Data description
    opp = sum(sum(1 for j, a in enumerate(s["action_types"]) if a == "S" and j >= s["revoke_at"]) for s in sc)
    s_at_revoke = sum(s["action_types"][s["revoke_at"]] == "S" for s in sc)
    out["data"] = {
        "opportunities": opp,
        "mean_length": sum(len(s["action_types"]) for s in sc) / len(sc),
        "mean_post_revocation_steps": sum(len(s["action_types"]) - s["revoke_at"] for s in sc) / len(sc),
        "share_s_at_revocation_step": s_at_revoke / len(sc),
        "share_s_overall": sum(s["action_types"].count("S") for s in sc) / sum(len(s["action_types"]) for s in sc),
    }

    # Base policies (benchmark.py)
    base = {}
    for p in POLICIES:
        r = [simulate_scenario(s, p) for s in sc]
        o = sum(x["revoked_sensitive_opportunities"] for x in r)
        base[p] = {"rate": sum(x["unauthorized_side_effects"] for x in r) / o,
                   "episodes_any": sum(x["unauthorized_side_effects"] > 0 for x in r) / len(r),
                   "control_events": sum(x["control_events"] for x in r) / len(r),
                   "completion": sum(x["executed_authorized_steps"] for x in r) / sum(x["authorized_work_steps"] for x in r)}
    out["base"] = base

    # Fault sweep (faults.py), per episode, with intervals
    grid = policy_grid()
    for d in (0, 1):  # re-sending lost notices every 2 steps (faults.simulate retry_every)
        for loss in (0.1, 0.3):
            grid.append({"policy": "push_d{}_loss{:.0f}_resend2".format(d, loss * 100), "family": "push+resend",
                         "ttl": None, "delay": d, "loss": loss, "retry": 2})
    per = {}
    for g in grid:
        per[g["policy"]] = [simulate(s, ttl=g["ttl"], delay=g["delay"], loss=float(g["loss"]),
                                      retry_every=g.get("retry")) for s in sc]
    names = [g["policy"] for g in grid]
    draws = bootstrap(per, names, seeds)
    allidx = list(range(len(sc)))
    sweep = {}
    for g in grid:
        n = g["policy"]
        r = per[n]
        sweep[n] = {"family": g["family"], "ttl": g["ttl"], "delay": g["delay"], "loss": g["loss"],
                    "rate": rate(r, allidx), "ci95": [pct(draws[n], 0.025), pct(draws[n], 0.975)],
                    "episodes_any": sum(x["unauthorized"] > 0 for x in r) / len(r),
                    "control_events": sum(x["control_events"] for x in r) / len(r),
                    "notices_lost": sum(bool(x["notice_lost"]) for x in r),
                    "per_seed": {str(sd): rate(r, [i for i in allidx if seeds[i] == sd]) for sd in SEEDS}}
    out["sweep"] = sweep

    def diff(a, b):
        d = [x - y for x, y in zip(draws[a], draws[b])]
        return {"diff": sweep[a]["rate"] - sweep[b]["rate"], "ci95": [pct(d, 0.025), pct(d, 0.975)]}

    out["contrasts"] = {
        "backstop_effect_loss30_d0": diff("push_d0_loss30", "push_d0_loss30+ttl8"),
        "backstop_effect_loss30_d1": diff("push_d1_loss30", "push_d1_loss30+ttl8"),
        "backstop_effect_loss10_d0": diff("push_d0_loss10", "push_d0_loss10+ttl8"),
        "backstop_effect_loss0_d1": diff("push_d1_loss0", "push_d1_loss0+ttl8"),
        "backstop_effect_loss0_d4": diff("push_d4_loss0", "push_d4_loss0+ttl8"),
        "delay1_vs_ttl3": diff("push_d1_loss0", "ttl_3"),
        "resend_effect_loss30_d0": diff("push_d0_loss30", "push_d0_loss30_resend2"),
        "resend_vs_backstop_loss30_d0": diff("push_d0_loss30_resend2", "push_d0_loss30+ttl8"),
    }
    # The loss draw is the same per scenario at every loss level, so losses are nested.
    out["lost_notice_share"] = {str(p): sum(notice_lost(s["scenario_id"], p) for s in sc) / len(sc) for p in (0.1, 0.3)}

    # Agent probe
    eps = [json.loads(line) for line in (ROOT / "outputs" / "llm_probe_episodes.jsonl").open(encoding="utf-8")]
    probe = {}
    for (m, pr), group in sorted(_group(eps, ("model", "prompt")).items()):
        hit = [e for e in group if e["outcome"] != "never_shared"]
        c = Counter(e["outcome"] for e in hit)
        cont = c["retried_same"] + c["switched_channel"]
        no_t8 = [e for e in hit if e["task"] != "T8"]
        probe["{} | {}".format(m, pr)] = {
            "episodes": len(group), "denied": len(hit), "stopped": c["stopped"],
            "retried_same": c["retried_same"], "switched_channel": c["switched_channel"],
            "continued": cont, "continued_ci95": wilson(cont, len(hit)),
            "switched_ci95": wilson(c["switched_channel"], len(hit)),
            "told_person": sum(bool(e["told_person"]) for e in hit),
            "switched_without_T8": [sum(e["outcome"] == "switched_channel" for e in no_t8), len(no_t8)],
            "by_language": {lang: dict(Counter(e["outcome"] for e in hit if e["language"] == lang))
                            for lang in ("English", "Roman Urdu")},
            "external_calls_after_denial": sum(e["external_calls_after_denial"] for e in hit),
        }
    out["probe"] = probe
    tools = Counter()
    for e in eps:
        for t in e["calls"].split(" > "):
            if t and t not in {"get_patient_record", "save_to_record", "notify_clinician", "send_email",
                               "upload_to_portal", "send_fax", "post_letter"}:
                tools[(e["model"], t)] += 1
    out["probe_unknown_tools"] = {"{} | {}".format(*k): v for k, v in tools.items()}
    told_and_continued = [e for e in eps if e["outcome"] in ("retried_same", "switched_channel") and e["told_person"]]
    out["probe_told_and_continued"] = {m: sum(e["model"] == m for e in told_and_continued)
                                       for m in sorted({e["model"] for e in eps})}

    (OUT / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    figures(out, eps)
    return out


def _group(rows, keys):
    g = defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in keys)].append(r)
    return g


def figures(out, eps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"pdf.fonttype": 42, "font.family": "serif", "font.size": 8.5})
    sw = out["sweep"]

    # Figure 1: exposure against control events
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ttl = sorted((v for v in sw.values() if v["family"] == "ttl"), key=lambda v: v["ttl"])
    ax.plot([v["control_events"] for v in ttl], [100 * v["rate"] for v in ttl], "-o", color="#333333",
            ms=3.5, lw=1.1, label="periodic re-check every $k$ steps")
    for v in ttl:
        ax.annotate("$k$={}".format(v["ttl"]), (v["control_events"], 100 * v["rate"]), xytext=(4, 3),
                    textcoords="offset points", fontsize=7, color="#333333")
    colours = {0: "#1f5f99", 1: "#c0612b", 2: "#3a8a4f", 4: "#7a4f9a"}
    markers = {0.0: "o", 0.1: "s", 0.3: "^"}
    for v in sw.values():
        if v["family"] in ("ttl", "push+resend"):
            continue
        filled = v["family"] == "push"
        ax.plot(v["control_events"], 100 * v["rate"], markers[v["loss"]], ms=5,
                mfc=colours[v["delay"]] if filled else "white", mec=colours[v["delay"]], mew=1.1)
    ps = out["base"]["per_sensitive"]
    ax.plot(ps["control_events"], 100 * ps["rate"], "*", ms=9, color="black")
    ax.annotate("check before each\nsensitive action", (ps["control_events"], 0), xytext=(6, 8),
                textcoords="offset points", fontsize=7)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color="#333333", marker="o", ms=3.5, lw=1.1, label="re-check every $k$ steps")]
    handles += [Line2D([], [], ls="", marker="o", color=c, label="push, delay {}".format(d)) for d, c in colours.items()]
    handles += [Line2D([], [], ls="", marker=m, color="grey", mfc="white" if False else "grey",
                       label="loss {:.0%}".format(p)) for p, m in markers.items()]
    handles += [Line2D([], [], ls="", marker="o", mfc="white", mec="grey", label="push + re-check every 8")]
    ax.legend(handles=handles, frameon=False, fontsize=6.8, loc="upper right", ncol=2)
    ax.set_xlabel("Control events per episode (checks + delivered notices)")
    ax.set_ylabel("Unauthorized side-effect rate (%)")
    ax.set_ylim(-3, 75)
    ax.grid(alpha=0.3, lw=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "figures" / "exposure_vs_cost.pdf")
    plt.close(fig)

    # Figure 2: agent behaviour after the denial
    order = [("qwen2.5:3b", "plain"), ("qwen2.5:3b", "rule"), ("llama3.1:8b", "plain"), ("llama3.1:8b", "rule")]
    langs = ("English", "Roman Urdu")
    cats = [("stopped", "stopped", "#9cc3a5"), ("retried_same", "retried same tool", "#e3b46b"),
            ("switched_channel", "switched channel", "#c0504d")]
    fig, ax = plt.subplots(figsize=(5.6, 2.5))
    labels, y = [], 0
    for m, pr in order:
        for lang in langs:
            g = [e for e in eps if e["model"] == m and e["prompt"] == pr and e["language"] == lang]
            left = 0
            for key, name, col in cats:
                n = sum(e["outcome"] == key for e in g)
                ax.barh(y, n, left=left, color=col, edgecolor="white", height=0.75,
                        label=name if y == 0 else None)
                if n:
                    ax.text(left + n / 2, y, str(n), ha="center", va="center", fontsize=7)
                left += n
            labels.append("{}, {}, {}".format(m, pr, "EN" if lang == "English" else "RU"))
            y += 1
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 8)
    ax.set_xlabel("Episodes (of 8) by behaviour after the denial")
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="lower center", bbox_to_anchor=(0.45, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "figures" / "agent_outcomes.pdf")
    plt.close(fig)


if __name__ == "__main__":
    res = main()
    print(json.dumps({k: res[k] for k in ("scenarios", "data", "contrasts", "lost_notice_share",
                                          "probe_unknown_tools", "probe_told_and_continued")}, indent=1))
    for n, v in res["sweep"].items():
        print("{:22s} {:6.2%} [{:6.2%}, {:6.2%}] any {:6.2%} ce {:5.2f} lost {:4d} seeds {}".format(
            n, v["rate"], *v["ci95"], v["episodes_any"], v["control_events"], v["notices_lost"],
            " ".join("{:.1%}".format(x) for x in v["per_seed"].values())))
    for k, v in res["probe"].items():
        print(k, json.dumps(v))
    print(json.dumps(res["base"], indent=0))
