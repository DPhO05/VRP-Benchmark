from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import pstdev
from typing import Dict, List, Tuple


def read_instance(path: str | Path) -> Tuple[int, int, List[List[int]]]:
    tokens = Path(path).read_text(encoding="utf-8").split()
    if len(tokens) < 2:
        raise ValueError("empty or malformed instance")
    n = int(tokens[0])
    k = int(tokens[1])
    need = 2 + (n + 1) * (n + 1)
    if len(tokens) < need:
        raise ValueError(f"expected {(n + 1) * (n + 1)} distance values, got {len(tokens) - 2}")
    values = list(map(int, tokens[2:need]))
    dist = [values[i * (n + 1):(i + 1) * (n + 1)] for i in range(n + 1)]
    return n, k, dist


def write_instance(path: str | Path, n: int, k: int, dist: List[List[int]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{n} {k}"]
    lines.extend(" ".join(map(str, row)) for row in dist)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def route_length(route: List[int], dist: List[List[int]], return_to_depot: bool = False) -> int:
    total = sum(dist[route[i]][route[i + 1]] for i in range(len(route) - 1))
    if return_to_depot and len(route) > 1:
        total += dist[route[-1]][0]
    return total


def parse_solution_text(text: str) -> List[List[int]]:
    tokens = text.split()
    if not tokens:
        raise ValueError("empty output")
    idx = 0
    k = int(tokens[idx])
    idx += 1
    routes: List[List[int]] = []
    for _ in range(k):
        if idx >= len(tokens):
            raise ValueError("missing route length")
        m = int(tokens[idx])
        idx += 1
        if idx + m > len(tokens):
            raise ValueError("route has fewer nodes than declared")
        route = list(map(int, tokens[idx:idx + m]))
        idx += m
        routes.append(route)
    return routes


def validate_solution(
    n: int,
    k: int,
    dist: List[List[int]],
    text: str,
    return_to_depot: bool = False,
) -> Dict:
    try:
        routes = parse_solution_text(text)
        if len(routes) != k:
            return {"valid": False, "error": f"expected {k} routes, got {len(routes)}"}
        seen = []
        for rid, route in enumerate(routes):
            if not route:
                return {"valid": False, "error": f"route {rid} is empty"}
            if route[0] != 0:
                return {"valid": False, "error": f"route {rid} does not start at depot 0"}
            for pos, node in enumerate(route):
                if node < 0 or node > n:
                    return {"valid": False, "error": f"node {node} out of range in route {rid}"}
                if pos > 0 and node == 0 and not return_to_depot:
                    return {"valid": False, "error": f"depot appears inside route {rid}"}
            seen.extend(route[1:])
        missing = sorted(set(range(1, n + 1)) - set(seen))
        duplicates = sorted({x for x in seen if seen.count(x) > 1})
        if missing:
            return {"valid": False, "error": f"missing nodes: {missing[:10]}"}
        if duplicates:
            return {"valid": False, "error": f"duplicate nodes: {duplicates[:10]}"}
        route_lengths = [route_length(route, dist, return_to_depot) for route in routes]
        objective = max(route_lengths) if route_lengths else 0
        return {
            "valid": True,
            "error": None,
            "routes": routes,
            "route_lengths": route_lengths,
            "objective": objective,
            "total_length": sum(route_lengths),
            "std_route_lengths": pstdev(route_lengths) if len(route_lengths) > 1 else 0.0,
        }
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


def load_metadata(instance_path: str | Path) -> Dict:
    meta_path = Path(str(instance_path) + ".json")
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    name = Path(instance_path).stem
    meta = {"case_id": name, "split": "sample", "distribution": "sample", "seed": None}
    for part in name.split("_"):
        if part.startswith("N") and part[1:].isdigit():
            meta["N"] = int(part[1:])
        if part.startswith("K") and part[1:].isdigit():
            meta["K"] = int(part[1:])
        if part.startswith("seed") and part[4:].isdigit():
            meta["seed"] = int(part[4:])
    return meta


def size_group(n: int) -> str:
    if n <= 16:
        return "tiny"
    if n <= 50:
        return "small"
    if n <= 150:
        return "medium"
    if n <= 500:
        return "large"
    return "stress"


def euclidean_matrix(coords: List[Tuple[float, float]]) -> List[List[int]]:
    dist = []
    for x1, y1 in coords:
        row = []
        for x2, y2 in coords:
            row.append(int(round(math.hypot(x1 - x2, y1 - y2))))
        dist.append(row)
    return dist

