#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "tools"))
from generate_all import GENERATORS, write_case


NK_MATRIX = [
    (8, 2), (8, 4),
    (12, 3), (12, 6),
    (16, 4), (16, 8),
    (24, 4), (24, 8),
    (32, 4), (32, 10),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="benchmark/instances_solution3")
    parser.add_argument("--seeds-per-setting", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260519)
    parser.add_argument("--split", default="dev")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    root = Path(args.output)
    for dist_name in GENERATORS:
        for n, k in NK_MATRIX:
            for _ in range(args.seeds_per_setting):
                write_case(root, args.split, dist_name, n, k, rng.randrange(1, 10**9))
    total = len(GENERATORS) * len(NK_MATRIX) * args.seeds_per_setting
    print(f"generated {total} team-3 comparison cases under {root}/{args.split}")


if __name__ == "__main__":
    main()

