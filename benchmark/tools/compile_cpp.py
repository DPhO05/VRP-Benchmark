#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    for solver in config:
        source = solver.get("source")
        binary = solver.get("binary")
        if not source or not binary:
            continue
        Path(binary).parent.mkdir(parents=True, exist_ok=True)
        cmd = ["g++", "-O2", "-std=c++17", source, "-o", binary]
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

