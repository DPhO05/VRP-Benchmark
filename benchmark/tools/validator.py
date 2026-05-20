#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from vrp_io import read_instance, validate_solution


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--solution", required=True)
    parser.add_argument("--return-to-depot", action="store_true")
    args = parser.parse_args()
    n, k, dist = read_instance(args.instance)
    text = Path(args.solution).read_text(encoding="utf-8")
    result = validate_solution(n, k, dist, text, args.return_to_depot)
    result.pop("routes", None)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

