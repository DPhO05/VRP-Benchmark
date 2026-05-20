#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("benchmark/results/.mplconfig").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("benchmark/results/.cache").resolve()))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from vrp_io import read_instance, route_length, parse_solution_text


def draw(instance: Path, solution: Path, output: Path) -> None:
    meta_path = Path(str(instance) + ".json")
    if not meta_path.exists():
        raise SystemExit(f"missing metadata coordinates: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    coords = meta["coords"]
    _, _, dist = read_instance(instance)
    routes = parse_solution_text(solution.read_text(encoding="utf-8"))
    lengths = [route_length(route, dist) for route in routes]
    worst = max(range(len(lengths)), key=lambda i: lengths[i]) if lengths else -1

    plt.figure(figsize=(8, 7))
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    plt.scatter(xs[1:], ys[1:], s=18, color="#666666", alpha=0.6)
    plt.scatter([xs[0]], [ys[0]], s=90, marker="*", color="#D62728", label="depot")
    cmap = plt.get_cmap("tab20")
    for rid, route in enumerate(routes):
        rx = [coords[node][0] for node in route]
        ry = [coords[node][1] for node in route]
        lw = 2.8 if rid == worst else 1.2
        alpha = 0.95 if rid == worst else 0.55
        plt.plot(rx, ry, color=cmap(rid % 20), linewidth=lw, alpha=alpha)
        plt.scatter(rx[1:], ry[1:], color=cmap(rid % 20), s=24, alpha=alpha)
    plt.title(f"{meta.get('case_id', instance.stem)} | obj={max(lengths) if lengths else 'NA'} | total={sum(lengths)}")
    plt.axis("equal")
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=180)
    plt.close()


def visualize_hard_cases(hard_cases: Path, instances_root: Path, solutions_root: Path, output_dir: Path, limit: int) -> None:
    count = 0
    with hard_cases.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["obj"] == "":
                continue
            matches = list(instances_root.rglob(row["case_id"] + ".in"))
            sol = solutions_root / row["solver"] / f"{row['case_id']}_run0.out"
            if not matches or not sol.exists():
                continue
            draw(matches[0], sol, output_dir / f"{row['case_id']}_{row['solver']}.png")
            count += 1
            if count >= limit:
                break
    print(f"visualized {count} hard cases into {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance")
    parser.add_argument("--solution")
    parser.add_argument("--output")
    parser.add_argument("--hard-cases")
    parser.add_argument("--instances-root", default="benchmark/instances")
    parser.add_argument("--solutions-root", default="benchmark/results/solutions")
    parser.add_argument("--output-dir", default="Figure/hard_cases")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.hard_cases:
        visualize_hard_cases(Path(args.hard_cases), Path(args.instances_root), Path(args.solutions_root), Path(args.output_dir), args.limit)
    else:
        if not (args.instance and args.solution and args.output):
            raise SystemExit("--instance, --solution and --output are required unless --hard-cases is used")
        draw(Path(args.instance), Path(args.solution), Path(args.output))


if __name__ == "__main__":
    main()
