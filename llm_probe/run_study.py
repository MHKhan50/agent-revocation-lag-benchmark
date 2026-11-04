"""Extended agent probe: more models, repeated sampled runs, revocation scope and denial wording.

Full design (all combinations): models x prompt (plain, rule) x scope (effect, tool)
x denial (explicit, generic) x language (English, Roman Urdu) x 8 tasks x repeats.
With 5 models and 3 repeats that is 1,920 episodes, about 5 to 6 hours on a MacBook M4.

The run can be stopped and started again: finished episodes are read back from
outputs/probe_study/episodes.jsonl and skipped.

Usage (Ollama running, models pulled):
    python3 llm_probe/run_study.py
    python3 llm_probe/run_study.py --models qwen2.5:3b --repeats 1     # a quick check
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe  # noqa: E402

OUT = HERE.parent / "outputs" / "probe_study"
MODELS = ["qwen2.5:3b", "qwen2.5:7b", "llama3.2:3b", "llama3.1:8b", "mistral:7b"]
TEMPERATURE = 0.7
SCOPES = ("effect", "tool")
DENIALS = ("explicit", "generic")


def key(r: Dict[str, Any]) -> tuple:
    return (r["model"], r["prompt"], r["scope"], r["denial"], r["language"], r["task"], r["repeat"])


def summarise(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["prompt"], r["scope"], r["denial"], r["language"])].append(r)
    out = []
    for (model, prompt, scope, denial, lang), g in sorted(groups.items()):
        hit = [r for r in g if r["outcome"] != "never_shared"]
        out.append({"model": model, "prompt": prompt, "scope": scope, "denial": denial, "language": lang,
                    "episodes": len(g), "revocation_hit": len(hit),
                    "stopped": sum(r["outcome"] == "stopped" for r in g),
                    "retried_same": sum(r["outcome"] == "retried_same" for r in g),
                    "switched_channel": sum(r["outcome"] == "switched_channel" for r in g),
                    "never_shared": len(g) - len(hit),
                    "leaked": sum(bool(r["leaked"]) for r in g),
                    "told_person": sum(bool(r["told_person"]) for r in hit)})
    return out


def main(argv: Optional[List[str]] = None, chat_factory=probe.make_ollama_chat) -> List[Dict[str, Any]]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=MODELS)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=TEMPERATURE)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    path = out / "episodes.jsonl"
    rows = [json.loads(line) for line in path.open(encoding="utf-8")] if path.exists() else []
    done = {key(r) for r in rows}
    total = len(args.models) * len(probe.PROMPTS) * len(SCOPES) * len(DENIALS) * 2 * len(tasks) * args.repeats
    print("{} of {} episodes already done".format(len(done), total), flush=True)
    with path.open("a", encoding="utf-8") as fh:
        for repeat in range(1, args.repeats + 1):  # every setting once before any repeat
            chat = chat_factory(args.temperature, repeat)
            for model in args.models:
                for prompt in probe.PROMPTS:
                    for scope in SCOPES:
                        for denial in DENIALS:
                            for lang in ("en", "ru"):
                                for task in tasks:
                                    language = "English" if lang == "en" else "Roman Urdu"
                                    k = (model, prompt, scope, denial, language, task["id"], repeat)
                                    if k in done:
                                        continue
                                    t0 = time.time()
                                    try:
                                        r = probe.run_episode(chat, model, task, lang, prompt, scope, denial)
                                    except Exception as exc:  # noqa: BLE001 - log and go on
                                        print("failed {}: {}".format(k, exc), flush=True)
                                        continue
                                    r.update(repeat=repeat, temperature=args.temperature,
                                             seconds=round(time.time() - t0, 1))
                                    rows.append(r)
                                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                                    fh.flush()
                                    print("{:5d}/{} {:12s} {:5s} {:6s} {:8s} {:10s} {} r{} {:16s} leak={}".format(
                                        len(rows), total, model, prompt, scope, denial, language, task["id"],
                                        repeat, r["outcome"], r["leaked"]), flush=True)
    summary = summarise(rows)
    if summary:
        with (out / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(summary[0]))
            w.writeheader()
            w.writerows(summary)
    print("\nSaved {} and {}".format(path, out / "summary.csv"))
    return rows


if __name__ == "__main__":
    main()
