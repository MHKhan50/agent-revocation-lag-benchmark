"""Generate reproducible synthetic permission-revocation scenarios."""
import csv
import random
from pathlib import Path

SEEDS = (17, 29, 43)
EPISODES_PER_SEED = 600
ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "scenarios.csv"


def generate_scenarios(seed, episodes=EPISODES_PER_SEED):
    rng = random.Random(seed)
    for i in range(episodes):
        length = rng.randint(8, 16)
        revoke_at = rng.randint(2, length - 3)
        actions = ["S" if rng.random() < 0.42 else "B" for _ in range(length)]
        if "S" not in actions[revoke_at:]:
            actions[revoke_at] = "S"
        if "S" not in actions[:revoke_at]:
            actions[0] = "S"
        yield {
            "scenario_id": "seed{}_episode{:04d}".format(seed, i + 1),
            "seed": seed,
            "episode": i + 1,
            "plan_length": length,
            "revoke_at": revoke_at,
            "action_types": "".join(actions),
        }


def write_dataset(path=DATA_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["scenario_id", "seed", "episode", "plan_length", "revoke_at", "action_types"]
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for seed in SEEDS:
            for row in generate_scenarios(seed):
                writer.writerow(row)
                count += 1
    return count


def main():
    count = write_dataset()
    print("Generated {} scenarios: {}".format(count, DATA_PATH))
    print("Seeds: {}; episodes per seed: {}".format(SEEDS, EPISODES_PER_SEED))


if __name__ == "__main__":
    main()
