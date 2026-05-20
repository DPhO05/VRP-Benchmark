#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

os.environ.setdefault("MPLCONFIGDIR", str(Path("benchmark/results/.mplconfig").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("benchmark/results/.cache").resolve()))
os.environ.setdefault("FONTCONFIG_PATH", str(Path("benchmark/results/.fontconfig").resolve()))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(value, default=math.nan):
    try:
        if value == "":
            return default
        return float(value)
    except Exception:
        return default


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_group(rows, group_fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[g] for g in group_fields)].append(row)
    out = []
    for key, items in sorted(groups.items()):
        valid = [r for r in items if r["valid"] == "True"]
        gaps = [fnum(r["gap_to_best"]) for r in valid if not math.isnan(fnum(r["gap_to_best"]))]
        runtimes = [fnum(r["runtime_sec"]) for r in items if not math.isnan(fnum(r["runtime_sec"]))]
        best_count = sum(1 for g in gaps if abs(g) <= 1e-9)
        row = {field: value for field, value in zip(group_fields, key)}
        row.update({
            "valid_rate": len(valid) / len(items) * 100 if items else 0,
            "avg_gap": mean(gaps) if gaps else "",
            "median_gap": median(gaps) if gaps else "",
            "worst_gap": max(gaps) if gaps else "",
            "best_count": best_count,
            "within_1pct": sum(1 for g in gaps if g <= 1) / len(gaps) * 100 if gaps else 0,
            "within_5pct": sum(1 for g in gaps if g <= 5) / len(gaps) * 100 if gaps else 0,
            "avg_runtime": mean(runtimes) if runtimes else "",
        })
        out.append(row)
    return out


def performance_profile(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["solver"]].append(row)
    out = []
    for solver, items in sorted(groups.items()):
        valid = [r for r in items if r["valid"] == "True" and fnum(r["best_known"]) > 0]
        ratios = [fnum(r["obj"]) / fnum(r["best_known"]) for r in valid]
        out.append({
            "solver": solver,
            "best_pct": sum(1 for x in ratios if x <= 1.0000001) / len(ratios) * 100 if ratios else 0,
            "within_1pct": sum(1 for x in ratios if x <= 1.01) / len(ratios) * 100 if ratios else 0,
            "within_2pct": sum(1 for x in ratios if x <= 1.02) / len(ratios) * 100 if ratios else 0,
            "within_5pct": sum(1 for x in ratios if x <= 1.05) / len(ratios) * 100 if ratios else 0,
            "within_10pct": sum(1 for x in ratios if x <= 1.10) / len(ratios) * 100 if ratios else 0,
            "avg_ratio": mean(ratios) if ratios else "",
            "worst_ratio": max(ratios) if ratios else "",
        })
    return out


def hard_cases(rows):
    out = []
    for row in rows:
        gap = fnum(row["gap_to_best"])
        if row["valid"] != "True" or (not math.isnan(gap) and gap > 10):
            out.append({
                "case_id": row["case_id"],
                "distribution": row["distribution"],
                "N": row["N"],
                "K": row["K"],
                "solver": row["solver"],
                "obj": row["obj"],
                "best_known": row["best_known"],
                "gap_to_best": row["gap_to_best"],
                "error": row["error"],
            })
    return out


def bar_chart(rows, x_field, y_field, title, output):
    vals = [(r[x_field], fnum(r[y_field])) for r in rows if not math.isnan(fnum(r[y_field]))]
    if not vals:
        return
    labels, values = zip(*vals)
    plt.figure(figsize=(max(8, len(labels) * 1.2), 5))
    plt.bar(labels, values, color="#4C78A8")
    plt.xticks(rotation=25, ha="right")
    plt.ylabel(y_field)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def grouped_gap_chart(rows, output):
    solvers = sorted({r["solver"] for r in rows})
    dists = sorted({r["distribution"] for r in rows})
    table = {(r["solver"], r["distribution"]): fnum(r["avg_gap"], 0) for r in rows}
    width = 0.8 / max(1, len(solvers))
    xs = list(range(len(dists)))
    plt.figure(figsize=(max(10, len(dists) * 1.5), 5.5))
    for i, solver in enumerate(solvers):
        ys = [table.get((solver, d), 0) for d in dists]
        plt.bar([x + i * width for x in xs], ys, width=width, label=solver)
    plt.xticks([x + width * (len(solvers) - 1) / 2 for x in xs], dists, rotation=20, ha="right")
    plt.ylabel("avg_gap_to_best (%)")
    plt.title("Average gap by distribution")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="benchmark/results")
    parser.add_argument("--figure-dir", default="Figure")
    args = parser.parse_args()
    rows = read_rows(Path(args.input))
    out = Path(args.output_dir)
    fig = Path(args.figure_dir)
    fig.mkdir(parents=True, exist_ok=True)

    by_solver = summarize_group(rows, ["solver"])
    by_dist = summarize_group(rows, ["solver", "distribution"])
    by_size = summarize_group(rows, ["solver", "size_group"])
    profile = performance_profile(rows)
    hard = hard_cases(rows)

    common = ["valid_rate", "avg_gap", "median_gap", "worst_gap", "best_count", "within_1pct", "within_5pct", "avg_runtime"]
    write_csv(out / "summary_by_solver.csv", by_solver, ["solver"] + common)
    write_csv(out / "summary_by_distribution.csv", by_dist, ["solver", "distribution"] + common)
    write_csv(out / "summary_by_size.csv", by_size, ["solver", "size_group"] + common)
    write_csv(out / "performance_profile.csv", profile, ["solver", "best_pct", "within_1pct", "within_2pct", "within_5pct", "within_10pct", "avg_ratio", "worst_ratio"])
    write_csv(out / "hard_cases.csv", hard, ["case_id", "distribution", "N", "K", "solver", "obj", "best_known", "gap_to_best", "error"])

    bar_chart(by_solver, "solver", "avg_gap", "Average gap to best-known by solver", fig / "avg_gap_by_solver.png")
    bar_chart(by_solver, "solver", "avg_runtime", "Average runtime by solver", fig / "avg_runtime_by_solver.png")
    bar_chart(profile, "solver", "within_5pct", "Percent of cases within 5% best-known", fig / "within_5pct_by_solver.png")
    grouped_gap_chart(by_dist, fig / "avg_gap_by_distribution.png")
    print(f"wrote reports to {out} and figures to {fig}")


if __name__ == "__main__":
    main()
