#!/usr/bin/env python3
"""OR-Tools/CBC MIP solver for the open-route Min-Max VRP benchmark."""

import sys
import time

try:
    from ortools.linear_solver import pywraplp
except ModuleNotFoundError:
    print("ERROR: missing dependency ortools", file=sys.stderr)
    sys.exit(2)


def solve(n, k, dist, limit_sec=5.0):
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        raise RuntimeError("CBC solver unavailable")
    solver.SetTimeLimit(int(limit_sec * 1000))
    x, y, u = {}, {}, {}
    for i in range(n + 1):
        for j in range(1, n + 1):
            if i == j:
                continue
            for r in range(k):
                x[i, j, r] = solver.BoolVar(f"x_{i}_{j}_{r}")
    for i in range(1, n + 1):
        for r in range(k):
            y[i, r] = solver.BoolVar(f"y_{i}_{r}")
    for i in range(1, n + 1):
        u[i] = solver.IntVar(1, n, f"u_{i}")
    upper = max(1, sum(max(row) for row in dist))
    route_len = []
    for r in range(k):
        val = solver.NumVar(0, upper, f"d_{r}")
        solver.Add(val == sum(x[i, j, r] * dist[i][j] for i in range(n + 1) for j in range(1, n + 1) if i != j))
        route_len.append(val)
    for i in range(1, n + 1):
        solver.Add(sum(y[i, r] for r in range(k)) == 1)
    for j in range(1, n + 1):
        for r in range(k):
            solver.Add(sum(x[i, j, r] for i in range(n + 1) if i != j) == y[j, r])
    for i in range(1, n + 1):
        for r in range(k):
            incoming = sum(x[j, i, r] for j in range(n + 1) if j != i)
            outgoing = sum(x[i, j, r] for j in range(1, n + 1) if i != j)
            solver.Add(outgoing <= y[i, r])
            solver.Add(outgoing <= incoming)
    for r in range(k):
        depot_out = sum(x[0, j, r] for j in range(1, n + 1))
        served = sum(y[i, r] for i in range(1, n + 1))
        if k <= n:
            solver.Add(depot_out == 1)
            solver.Add(served >= 1)
        else:
            solver.Add(depot_out <= 1)
        solver.Add(served <= n * depot_out)
        solver.Add(served >= depot_out)
        # One open path per used vehicle: total endings equals one.
        solver.Add(
            sum(
                y[i, r] - sum(x[i, j, r] for j in range(1, n + 1) if i != j)
                for i in range(1, n + 1)
            ) == depot_out
        )
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                solver.Add(u[j] - u[i] >= 1 - n * (1 - sum(x[i, j, r] for r in range(k))))
    max_d = solver.NumVar(0, upper, "max_d")
    for val in route_len:
        solver.Add(max_d >= val)
    solver.Minimize(max_d)
    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise RuntimeError("no feasible MIP solution")
    routes = []
    for r in range(k):
        nxt = {}
        for i in range(n + 1):
            for j in range(1, n + 1):
                if i != j and (i, j, r) in x and x[i, j, r].solution_value() > 0.5:
                    nxt[i] = j
        route, cur = [0], 0
        while cur in nxt:
            cur = nxt[cur]
            route.append(cur)
        routes.append(route)
    return routes


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n, k = int(next(it)), int(next(it))
    dist = [[int(next(it)) for _ in range(n + 1)] for _ in range(n + 1)]
    limit = float(sys.argv[sys.argv.index("--time-limit") + 1]) if "--time-limit" in sys.argv else 5.0
    start = time.time()
    routes = solve(n, k, dist, limit)
    print(k)
    for route in routes:
        print(len(route))
        print(" ".join(map(str, route)))
    print(f"Runtime: {time.time() - start:.6f}", file=sys.stderr)


if __name__ == "__main__":
    main()
