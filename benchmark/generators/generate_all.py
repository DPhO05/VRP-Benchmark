#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Callable, List, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1] / "tools"))
from vrp_io import euclidean_matrix, write_instance

Coord = Tuple[float, float]


def uniform(n: int, rng: random.Random) -> List[Coord]:
    return [(500.0, 500.0)] + [(rng.uniform(0, 1000), rng.uniform(0, 1000)) for _ in range(n)]


def cluster(n: int, rng: random.Random) -> List[Coord]:
    c = rng.choice([2, 3, 5, 8])
    centers = [(rng.uniform(120, 880), rng.uniform(120, 880)) for _ in range(c)]
    sigma = rng.choice([20, 40, 80])
    pts = [(500.0, 500.0)]
    for _ in range(n):
        cx, cy = rng.choice(centers)
        pts.append((min(1000, max(0, rng.gauss(cx, sigma))), min(1000, max(0, rng.gauss(cy, sigma)))))
    return pts


def line(n: int, rng: random.Random) -> List[Coord]:
    mode = rng.choice(["start", "middle", "off"])
    depot = {"start": (50.0, 500.0), "middle": (500.0, 500.0), "off": (500.0, 170.0)}[mode]
    pts = [depot]
    for _ in range(n):
        x = rng.uniform(80, 950)
        y = 500 + rng.gauss(0, 25)
        pts.append((x, y))
    return pts


def outlier(n: int, rng: random.Random) -> List[Coord]:
    pts = [(500.0, 500.0)]
    outliers = max(1, n // 10)
    for _ in range(n - outliers):
        angle = rng.uniform(0, 2 * math.pi)
        rad = abs(rng.gauss(0, 90))
        pts.append((500 + rad * math.cos(angle), 500 + rad * math.sin(angle)))
    for _ in range(outliers):
        angle = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(430, 720)
        pts.append((500 + rad * math.cos(angle), 500 + rad * math.sin(angle)))
    return pts


def ring(n: int, rng: random.Random) -> List[Coord]:
    pts = [(500.0, 500.0)]
    radii = rng.choice([[260], [180, 360], [220, 420]])
    arc = rng.choice([2 * math.pi, math.pi * 1.4])
    start = rng.uniform(0, 2 * math.pi)
    for i in range(n):
        angle = start + arc * i / max(1, n - 1) + rng.gauss(0, 0.04)
        rad = rng.choice(radii) + rng.gauss(0, 12)
        pts.append((500 + rad * math.cos(angle), 500 + rad * math.sin(angle)))
    return pts


def grid(n: int, rng: random.Random) -> List[Coord]:
    side = math.ceil(math.sqrt(n * 1.4))
    cells = [(i, j) for i in range(side) for j in range(side)]
    rng.shuffle(cells)
    pts = [(500.0, 500.0)]
    gap = 850 / max(1, side - 1)
    for i, j in cells[:n]:
        pts.append((75 + i * gap + rng.gauss(0, 6), 75 + j * gap + rng.gauss(0, 6)))
    return pts


def adversarial(n: int, rng: random.Random) -> List[Coord]:
    pts = [(rng.choice([80.0, 920.0]), rng.choice([80.0, 920.0]))]
    dense = max(1, int(n * 0.75))
    cx, cy = rng.uniform(250, 750), rng.uniform(250, 750)
    for _ in range(dense):
        pts.append((cx + rng.gauss(0, 18), cy + rng.gauss(0, 18)))
    for i in range(n - dense):
        angle = 2 * math.pi * i / max(1, n - dense) + rng.gauss(0, 0.03)
        pts.append((500 + 470 * math.cos(angle), 500 + 470 * math.sin(angle)))
    return pts


GENERATORS: dict[str, Callable[[int, random.Random], List[Coord]]] = {
    "uniform": uniform,
    "cluster": cluster,
    "line": line,
    "outlier": outlier,
    "ring": ring,
    "grid": grid,
    "adversarial": adversarial,
}

SIZES = [(12, 3), (30, 4), (80, 6), (150, 10), (300, 20)]


def clamp_coords(coords: List[Coord]) -> List[Coord]:
    return [(min(1200, max(-200, x)), min(1200, max(-200, y))) for x, y in coords]


def write_case(root: Path, split: str, dist_name: str, n: int, k: int, seed: int) -> None:
    rng = random.Random(seed)
    coords = clamp_coords(GENERATORS[dist_name](n, rng))
    matrix = euclidean_matrix(coords)
    case_id = f"{dist_name}_N{n}_K{k}_seed{seed}"
    path = root / split / dist_name / f"{case_id}.in"
    write_instance(path, n, k, matrix)
    meta = {
        "case_id": case_id,
        "split": split,
        "distribution": dist_name,
        "N": n,
        "K": k,
        "seed": seed,
        "coords": coords,
    }
    Path(str(path) + ".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="benchmark/instances")
    parser.add_argument("--dev-cases", type=int, default=35)
    parser.add_argument("--holdout-cases", type=int, default=14)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    root = Path(args.output)
    rng = random.Random(args.seed)
    distributions = list(GENERATORS)
    for split, count in [("dev", args.dev_cases), ("holdout", args.holdout_cases)]:
        for idx in range(count):
            dist_name = distributions[idx % len(distributions)]
            n, k = SIZES[(idx // len(distributions)) % len(SIZES)]
            seed = rng.randrange(1, 10**9)
            write_case(root, split, dist_name, n, k, seed)
    print(f"generated {args.dev_cases + args.holdout_cases} cases under {root}")


if __name__ == "__main__":
    main()

