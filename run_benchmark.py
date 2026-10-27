"""Run the benchmark, write tables and chart, and refresh article results."""
import csv
import json
from pathlib import Path
from benchmark import POLICIES, simulate_scenario, summarise
from generate_dataset import DATA_PATH, SEEDS, write_dataset
from plot_results import create_chart

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"


def read_scenarios(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for field in ("seed", "episode", "plan_length", "revoke_at"):
            row[field] = int(row[field])
    return rows


def write_csv(path, rows):
    if not rows:
        raise ValueError("Refusing to write an empty result table")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows):
    cols = [
        ("policy", "Policy"),
        ("unauthorized_side_effect_rate", "Unauthorized side-effect rate"),
        ("revoked_action_block_rate", "Revoked-action block rate"),
        ("authorized_work_completion_rate", "Authorized-work completion"),
        ("mean_control_events_per_episode", "Control events / episode"),
    ]
    head = "| " + " | ".join(label for _, label in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = []
    for row in rows:
        values = []
        for key, _ in cols:
            v = row[key]
            if key.endswith("_rate"):
                values.append("{:.1%}".format(float(v)))
            elif key == "mean_control_events_per_episode":
                values.append("{:.2f}".format(float(v)))
            else:
                values.append(str(v))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([head, sep] + body)


def update_article_table(table):
    article = ROOT / "article_draft.md"
    text = article.read_text(encoding="utf-8")
    start, end = "<!-- RESULTS_TABLE_START -->", "<!-- RESULTS_TABLE_END -->"
    if start not in text or end not in text:
        raise ValueError("Article results-table markers are missing")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    article.write_text(before + start + "\n" + table + "\n" + end + after, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = write_dataset(DATA_PATH)
    scenarios = read_scenarios(DATA_PATH)
    episode_results = [simulate_scenario(s, p) for s in scenarios for p in POLICIES]
    overall = summarise(episode_results)
    by_seed = summarise(episode_results, group_fields=("seed",))
    write_csv(OUT / "episode_results.csv", episode_results)
    write_csv(OUT / "policy_summary.csv", overall)
    write_csv(OUT / "per_seed_summary.csv", by_seed)
    summary = {
        "benchmark": "RevocationLag",
        "synthetic_scenarios": n,
        "seeds": list(SEEDS),
        "episodes_per_seed": 600,
        "policies": list(POLICIES),
        "metrics": overall,
        "interpretation_warning": "Synthetic simulator results only; not real-world agent measurements.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    table = markdown_table(overall)
    (OUT / "article_results_snippet.md").write_text(
        "## Results table\n\n" + table +
        "\n\nInterpretation: synthetic simulator results only; not real-world agent measurements.\n",
        encoding="utf-8"
    )
    update_article_table(table)
    chart = create_chart()
    print("Scenarios:", n)
    print("Policy evaluations:", len(episode_results))
    print("\n" + table)
    print("\nOutputs: outputs/policy_summary.csv, outputs/per_seed_summary.csv,")
    print("outputs/episode_results.csv, outputs/summary.json,")
    print(str(chart.relative_to(ROOT)), "and outputs/article_results_snippet.md")
    print("Refreshed article_draft.md results table.")


if __name__ == "__main__":
    main()
