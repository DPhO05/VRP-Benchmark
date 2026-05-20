#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

os.environ.setdefault("MPLCONFIGDIR", str(Path("benchmark/results/.mplconfig").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("benchmark/results/.cache").resolve()))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


TEAM_SOLVERS = ["Greedy_RL", "Greedy_LocalSearch_CPP", "MIP_CBC_ORTools"]
COLORS = {
    "Greedy_RL": "#D62728",
    "Greedy_LocalSearch_CPP": "#2CA02C",
    "MIP_CBC_ORTools": "#9467BD",
    "Meta_Greedy_SA_Tabu": "#1F77B4",
    "Greedy_SA": "#1F77B4",
    "Greedy_Tabu": "#FF7F0E",
    "Greedy_Pure": "#8C564B",
    "Hybrid_ALNS_SA": "#17BECF",
    "SA_Algo": "#D62728",
}


def fnum(value, default=math.nan):
    try:
        return float(value) if value != "" else default
    except Exception:
        return default


def read_rows(paths):
    allowed = set(TEAM_SOLVERS)
    rows = []
    for path in paths:
        with Path(path).open(newline="", encoding="utf-8") as f:
            rows.extend(r for r in csv.DictReader(f) if r["solver"] in allowed)
    return rows


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows, group_fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[g] for g in group_fields + ["solver"])].append(row)
    out = []
    for key, items in sorted(groups.items()):
        valid = [r for r in items if r["valid"] == "True"]
        gaps = [fnum(r["gap_to_best"]) for r in valid if not math.isnan(fnum(r["gap_to_best"]))]
        objs = [fnum(r["obj"]) for r in valid if not math.isnan(fnum(r["obj"]))]
        runtimes = [fnum(r["runtime_sec"]) for r in items if not math.isnan(fnum(r["runtime_sec"]))]
        rec = {field: value for field, value in zip(group_fields + ["solver"], key)}
        rec.update({
            "runs": len(items),
            "valid_rate": len(valid) / len(items) * 100 if items else 0,
            "mean_obj": mean(objs) if objs else "",
            "median_obj": median(objs) if objs else "",
            "avg_gap": mean(gaps) if gaps else "",
            "median_gap": median(gaps) if gaps else "",
            "worst_gap": max(gaps) if gaps else "",
            "best_count": sum(1 for g in gaps if abs(g) <= 1e-9),
            "avg_runtime": mean(runtimes) if runtimes else "",
        })
        out.append(rec)
    return out


def winners(rows, group_fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[g] for g in group_fields)].append(row)
    out = []
    for key, items in sorted(groups.items()):
        solver_objs = defaultdict(list)
        for row in items:
            if row["valid"] == "True":
                solver_objs[row["solver"]].append(fnum(row["obj"]))
        if not solver_objs:
            continue
        avg = {solver: mean(vals) for solver, vals in solver_objs.items() if vals}
        min_obj = min(avg.values())
        quality_winners = [solver for solver, value in avg.items() if abs(value - min_obj) <= 1e-9]
        runtime = {}
        for solver in quality_winners:
            vals = [fnum(r["runtime_sec"]) for r in items if r["solver"] == solver and not math.isnan(fnum(r["runtime_sec"]))]
            runtime[solver] = mean(vals) if vals else math.inf
        practical_winner = min(quality_winners, key=lambda s: runtime.get(s, math.inf))
        rec = {field: value for field, value in zip(group_fields, key)}
        rec["quality_winner"] = "+".join(sorted(quality_winners))
        rec["practical_winner"] = practical_winner
        rec["winner_mean_obj"] = avg[practical_winner]
        rec["winner_avg_runtime"] = runtime.get(practical_winner, "")
        rec["runner_up_gap_pct"] = ""
        if len(avg) > 1:
            ordered = sorted(avg.items(), key=lambda x: x[1])
            rec["runner_up_gap_pct"] = (ordered[1][1] - ordered[0][1]) / ordered[0][1] * 100 if ordered[0][1] else 0
        for solver in TEAM_SOLVERS:
            rec[f"{solver}_mean_obj"] = avg.get(solver, "")
        out.append(rec)
    return out


def bar_by_time(summary, figure_dir):
    time_values = sorted({float(r["time_limit"]) for r in summary if r.get("time_limit")})
    solvers = TEAM_SOLVERS
    width = 0.8 / len(solvers)
    xs = list(range(len(time_values)))
    plt.figure(figsize=(9, 5.2))
    for i, solver in enumerate(solvers):
        vals = []
        for t in time_values:
            matches = [r for r in summary if r["solver"] == solver and abs(float(r["time_limit"]) - t) < 1e-9]
            vals.append(mean([fnum(r["avg_gap"], 0) for r in matches]) if matches else 0)
        bars = plt.bar([x + i * width for x in xs], vals, width=width, label=solver, color=COLORS.get(solver))
        for bar, value in zip(bars, vals):
            if value <= 0.05:
                plt.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.2f}", ha="center", va="bottom", fontsize=8, rotation=90)
    plt.xticks([x + width for x in xs], [str(t).rstrip("0").rstrip(".") for t in time_values])
    plt.ylabel("avg gap to best-known (%)")
    plt.xlabel("time limit (s)")
    plt.title("Team solvers by time limit")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(Path(figure_dir) / "team3_avg_gap_by_time_limit.png", dpi=180)
    plt.close()


def grouped_metric(summary, group_field, metric, ylabel, title, output, normalize_obj=False, log_y=False):
    labels = sorted({r[group_field] for r in summary}, key=lambda x: (float(x) if str(x).replace(".", "", 1).isdigit() else str(x)))
    width = 0.82 / len(TEAM_SOLVERS)
    xs = list(range(len(labels)))
    values_by_solver = {solver: [] for solver in TEAM_SOLVERS}
    for label in labels:
        group_values = {}
        for solver in TEAM_SOLVERS:
            matches = [r for r in summary if r[group_field] == label and r["solver"] == solver]
            vals = [fnum(r[metric]) for r in matches if not math.isnan(fnum(r[metric]))]
            value = mean(vals) if vals else math.nan
            group_values[solver] = value
        if normalize_obj:
            valid_values = [v for v in group_values.values() if not math.isnan(v)]
            best = min(valid_values) if valid_values else math.nan
            group_values = {solver: (value / best if not math.isnan(value) and best else math.nan) for solver, value in group_values.items()}
        for solver in TEAM_SOLVERS:
            values_by_solver[solver].append(group_values[solver])

    plt.figure(figsize=(max(10, len(labels) * 1.35), 5.6))
    for i, solver in enumerate(TEAM_SOLVERS):
        vals = values_by_solver[solver]
        draw_vals = [0 if math.isnan(v) else v for v in vals]
        bars = plt.bar([x + i * width for x in xs], draw_vals, width=width, label=solver, color=COLORS.get(solver))
        for bar, value in zip(bars, vals):
            if not math.isnan(value):
                label = f"{value:.2f}" if normalize_obj or value < 10 else f"{value:.0f}"
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=7, rotation=90)
    plt.xticks([x + width * (len(TEAM_SOLVERS) - 1) / 2 for x in xs], labels, rotation=22, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    if log_y:
        plt.yscale("log")
    if normalize_obj:
        plt.axhline(1.0, color="#444444", linewidth=1, linestyle="--", alpha=0.6)
        plt.ylim(bottom=0.98)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def solver_scorecard(summary, figure_dir):
    rows = []
    for solver in TEAM_SOLVERS:
        matches = [r for r in summary if r["solver"] == solver]
        rows.append((
            solver,
            mean([fnum(r["avg_gap"], 0) for r in matches]) if matches else 0,
            mean([fnum(r["avg_runtime"], 0) for r in matches]) if matches else 0,
            mean([fnum(r["valid_rate"], 0) for r in matches]) if matches else 0,
        ))
    labels = [r[0] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    metrics = [
        ("avg gap (%)", [r[1] for r in rows], False),
        ("avg runtime (s)", [r[2] for r in rows], True),
        ("valid rate (%)", [r[3] for r in rows], False),
    ]
    for ax, (title, vals, log_y) in zip(axes, metrics):
        bars = ax.bar(labels, vals, color=[COLORS.get(s) for s in labels])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
        if log_y:
            ax.set_yscale("log")
        for bar, value in zip(bars, vals):
            txt = f"{value:.2f}" if value < 10 else f"{value:.0f}"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), txt, ha="center", va="bottom", fontsize=8)
    fig.suptitle("Team solver scorecard")
    fig.tight_layout()
    fig.savefig(Path(figure_dir) / "team3_solver_scorecard.png", dpi=180)
    plt.close(fig)


def winner_bars(winner_rows, field, figure_dir):
    groups = defaultdict(Counter)
    for row in winner_rows:
        groups[row[field]][row["practical_winner"]] += 1
    labels = sorted(groups)
    width = 0.8 / len(TEAM_SOLVERS)
    xs = list(range(len(labels)))
    plt.figure(figsize=(max(9, len(labels) * 1.2), 5))
    for i, solver in enumerate(TEAM_SOLVERS):
        vals = [groups[label][solver] for label in labels]
        plt.bar([x + i * width for x in xs], vals, width=width, label=solver, color=COLORS.get(solver))
    plt.xticks([x + width for x in xs], labels, rotation=20, ha="right")
    plt.ylabel("number of condition groups won")
    plt.title(f"Winner count by {field}")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(Path(figure_dir) / f"team3_winner_count_by_{field}.png", dpi=180)
    plt.close()


def recommendations(winner_rows, output):
    lines = ["# Team-3 solver condition analysis", ""]
    for field in ["time_limit", "size_group", "distribution"]:
        lines.append(f"## Winners by {field}")
        counts = defaultdict(Counter)
        for row in winner_rows:
            counts[row[field]][row["practical_winner"]] += 1
        for key in sorted(counts):
            winner, count = counts[key].most_common(1)[0]
            total = sum(counts[key].values())
            lines.append(f"- `{key}`: `{winner}` is practical winner in {count}/{total} condition groups.")
        lines.append("")
    lines.append("Interpretation notes:")
    lines.append("- MIP is only included for `N <= 35`; it is useful as a small-instance optimal/near-optimal reference, not as the main large-N solver.")
    lines.append("- `Greedy_LocalSearch_CPP` is expected to dominate runtime on larger cases because it is compiled and has cheaper local-search loops.")
    lines.append("- `Greedy_RL` can be competitive when extra time helps assignment rebalancing, but Python overhead is visible at short limits.")
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    global TEAM_SOLVERS
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output-dir", default="benchmark/results/team3")
    parser.add_argument("--figure-dir", default="Figure/team3")
    parser.add_argument("--solvers", nargs="+", default=TEAM_SOLVERS)
    args = parser.parse_args()
    TEAM_SOLVERS = args.solvers
    rows = read_rows(args.inputs)
    out = Path(args.output_dir)
    fig = Path(args.figure_dir)
    fig.mkdir(parents=True, exist_ok=True)

    by_time = summarize(rows, ["time_limit"])
    by_nk = summarize(rows, ["N", "K"])
    by_dist = summarize(rows, ["distribution"])
    by_size = summarize(rows, ["size_group"])
    by_condition = summarize(rows, ["time_limit", "distribution", "N", "K", "size_group"])
    win_rows = winners(rows, ["time_limit", "distribution", "N", "K", "size_group"])

    common = ["runs", "valid_rate", "mean_obj", "median_obj", "avg_gap", "median_gap", "worst_gap", "best_count", "avg_runtime"]
    write_csv(out / "summary_by_time_limit.csv", by_time, ["time_limit", "solver"] + common)
    write_csv(out / "summary_by_NK.csv", by_nk, ["N", "K", "solver"] + common)
    write_csv(out / "summary_by_distribution.csv", by_dist, ["distribution", "solver"] + common)
    write_csv(out / "summary_by_size_group.csv", by_size, ["size_group", "solver"] + common)
    write_csv(out / "summary_by_condition.csv", by_condition, ["time_limit", "distribution", "N", "K", "size_group", "solver"] + common)
    write_csv(out / "winner_by_condition.csv", win_rows, ["time_limit", "distribution", "N", "K", "size_group", "quality_winner", "practical_winner", "winner_mean_obj", "winner_avg_runtime", "runner_up_gap_pct"] + [f"{s}_mean_obj" for s in TEAM_SOLVERS])

    bar_by_time(by_time, fig)
    solver_scorecard(by_time, fig)
    grouped_metric(by_dist, "distribution", "mean_obj", "objective / best objective", "Solution quality by distribution (lower is better)", fig / "team3_quality_ratio_by_distribution.png", normalize_obj=True)
    grouped_metric(by_dist, "distribution", "avg_runtime", "runtime seconds, log scale", "Runtime by distribution", fig / "team3_runtime_by_distribution.png", log_y=True)
    grouped_metric(by_nk, "N", "mean_obj", "objective / best objective", "Solution quality by N (lower is better)", fig / "team3_quality_ratio_by_N.png", normalize_obj=True)
    grouped_metric(by_nk, "N", "avg_runtime", "runtime seconds, log scale", "Runtime by N", fig / "team3_runtime_by_N.png", log_y=True)
    winner_bars(win_rows, "distribution", fig)
    winner_bars(win_rows, "size_group", fig)
    recommendations(win_rows, out / "recommendations.md")
    print(f"wrote team-3 analysis to {out} and {fig}")


if __name__ == "__main__":
    main()
