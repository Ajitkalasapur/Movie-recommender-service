"""Compare the two Locust runs and write results/load_results.md.

Run from the project root after both load tests:  python loadtest/summarize.py
"""
import csv
from pathlib import Path

SCENARIOS = [("A: 1 replica, no cache", "results/scenario_a"),
             ("B: 3 replicas + Redis cache", "results/scenario_b")]


def aggregated(prefix):
    with open(f"{prefix}_stats.csv", newline="") as f:
        row = next(r for r in csv.DictReader(f) if r["Name"] == "Aggregated")
    return {"rps": float(row["Requests/s"]), "median": float(row["Median Response Time"]),
            "p95": float(row["95%"]), "requests": int(row["Request Count"]), "failures": int(row["Failure Count"])}


if __name__ == "__main__":
    lines = ["# Load test results", "",
             "| Scenario | Requests/s | Median (ms) | 95th percentile (ms) | Requests | Failures |",
             "|---|---|---|---|---|---|"]
    for name, prefix in SCENARIOS:
        if not Path(f"{prefix}_stats.csv").exists():
            print(f"Missing {prefix}_stats.csv, so run that scenario first.")
            continue
        s = aggregated(prefix)
        lines.append(f"| {name} | {s['rps']:.1f} | {s['median']:.0f} | {s['p95']:.0f} | {s['requests']} | {s['failures']} |")
    Path("results").mkdir(exist_ok=True)
    Path("results/load_results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
