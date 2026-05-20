#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List

from lower_bounds import lower_bound
from vrp_io import load_metadata, read_instance, size_group, validate_solution


FIELDS = [
    "case_id", "split", "distribution", "N", "K", "seed", "size_group",
    "solver", "language", "run_id", "time_limit", "valid", "obj",
    "total_length", "std_length", "runtime_sec", "best_known",
    "gap_to_best", "lower_bound", "gap_to_lb", "error",
]


def list_instances(root: Path) -> List[Path]:
    if root.is_file():
        return [root]
    return sorted(p for p in root.rglob("*") if p.suffix in {".in", ".txt"} and not p.name.endswith(".json"))


def run_solver(solver: Dict, instance_text: str, n: int, time_limit: float) -> tuple[str, str, float, str]:
    if solver.get("max_n") and n > int(solver["max_n"]):
        return "", "", 0.0, f"SKIPPED_N_GT_{solver['max_n']}"
    cmd = solver["cmd"].format(time_limit=time_limit)
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", str(Path("benchmark/results/.mplconfig").resolve()))
    env["VRP_TIME_LIMIT_SEC"] = str(time_limit)
    deps = Path("benchmark/.deps").resolve()
    if deps.exists():
        old_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(deps) + (os.pathsep + old_pythonpath if old_pythonpath else "")
    start = time.perf_counter()
    try:
        margin = float(solver.get("timeout_margin", 0.4 if solver.get("language") == "python" else 0.1))
        proc = subprocess.run(
            cmd.split(),
            input=instance_text.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=time_limit + margin,
            env=env,
        )
        runtime = time.perf_counter() - start
        stdout = proc.stdout.decode(errors="replace")
        stderr = proc.stderr.decode(errors="replace")
        if proc.returncode != 0:
            return stdout, stderr, runtime, f"EXIT_{proc.returncode}: {stderr.strip()[:200]}"
        return stdout, stderr, runtime, ""
    except subprocess.TimeoutExpired as exc:
        runtime = time.perf_counter() - start
        stdout = (exc.stdout or b"").decode(errors="replace")
        stderr = (exc.stderr or b"").decode(errors="replace")
        return stdout, stderr, runtime, "TIMEOUT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", required=True)
    parser.add_argument("--solvers", required=True)
    parser.add_argument("--time-limit", type=float, default=5.0)
    parser.add_argument("--runs-per-case", type=int, default=1)
    parser.add_argument("--output", default="benchmark/results/raw_runs.csv")
    parser.add_argument("--solutions-dir", default="benchmark/results/solutions")
    args = parser.parse_args()

    solvers = json.loads(Path(args.solvers).read_text(encoding="utf-8"))
    rows: List[Dict] = []
    solutions_dir = Path(args.solutions_dir)
    solutions_dir.mkdir(parents=True, exist_ok=True)

    for instance in list_instances(Path(args.instances)):
        try:
            n, k, dist = read_instance(instance)
        except Exception as exc:
            print(f"skip malformed {instance}: {exc}")
            continue
        meta = load_metadata(instance)
        instance_text = Path(instance).read_text(encoding="utf-8")
        lb = lower_bound(n, k, dist)
        case_rows: List[Dict] = []
        for solver in solvers:
            for run_id in range(args.runs_per_case):
                stdout, stderr, runtime, run_error = run_solver(solver, instance_text, n, args.time_limit)
                validation = validate_solution(n, k, dist, stdout) if not run_error else {"valid": False, "error": run_error}
                if validation.get("valid"):
                    sol_path = solutions_dir / solver["name"] / f"{meta.get('case_id', instance.stem)}_run{run_id}.out"
                    sol_path.parent.mkdir(parents=True, exist_ok=True)
                    sol_path.write_text(stdout, encoding="utf-8")
                row = {
                    "case_id": meta.get("case_id", instance.stem),
                    "split": meta.get("split", instance.parent.parent.name if instance.parent.parent else ""),
                    "distribution": meta.get("distribution", instance.parent.name),
                    "N": n,
                    "K": k,
                    "seed": meta.get("seed", ""),
                    "size_group": size_group(n),
                    "solver": solver["name"],
                    "language": solver.get("language", ""),
                    "run_id": run_id,
                    "time_limit": args.time_limit,
                    "valid": bool(validation.get("valid")),
                    "obj": validation.get("objective", ""),
                    "total_length": validation.get("total_length", ""),
                    "std_length": validation.get("std_route_lengths", ""),
                    "runtime_sec": runtime,
                    "best_known": "",
                    "gap_to_best": "",
                    "lower_bound": lb,
                    "gap_to_lb": "",
                    "error": validation.get("error") or (stderr.strip()[:200] if stderr.strip() else ""),
                }
                if row["valid"] and lb > 0:
                    row["gap_to_lb"] = (float(row["obj"]) - lb) / lb * 100
                case_rows.append(row)
                print(f"{row['case_id']} | {solver['name']} | valid={row['valid']} obj={row['obj']} time={runtime:.3f}s err={row['error']}")
        valid_objs = [float(r["obj"]) for r in case_rows if r["valid"]]
        best = min(valid_objs) if valid_objs else math.nan
        for row in case_rows:
            if row["valid"] and best > 0:
                row["best_known"] = best
                row["gap_to_best"] = (float(row["obj"]) - best) / best * 100
            elif valid_objs:
                row["best_known"] = best
            rows.append(row)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
