"""
Simple VRP Benchmark Runner
Tập trung vào 2 câu hỏi:
  1. Time-limit: thuật toán nào tốt hơn ở mỗi mức thời gian?
  2. Scalability: N,K lớn đến đâu thì thuật toán nào "sập" trước?

Usage:
  python simple_bench/run_benchmark.py
"""
import os, sys, subprocess, time, csv, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(BASE_DIR, "build")
INST_DIR  = os.path.join(BASE_DIR, "instances")
RES_DIR   = os.path.join(BASE_DIR, "results")
MIP_PY    = os.path.join(ROOT_DIR, "Solution", "mip_postman_mip_only_improved.py")

os.makedirs(RES_DIR, exist_ok=True)

# ─── Solver configs ────────────────────────────────────────────────────────
#   output_format:
#     "greedy_sa" → line0=K, then pairs: (size\n  node0 node1...)
#     "tabu"      → line0=Iter... (stderr mirrored), line1=objective int,
#                   then lines: "size node0 node1 ..."
#     "mip"       → same as greedy_sa
SOLVERS = {
    "Greedy_LS": {"cmd": [os.path.join(BUILD_DIR, "greedy")], "fmt": "greedy_sa"},
    "SA":        {"cmd": [os.path.join(BUILD_DIR, "sa")],     "fmt": "greedy_sa"},
    "Tabu":      {"cmd": [os.path.join(BUILD_DIR, "tabu")],   "fmt": "tabu"},
    "MIP":       {"cmd": [sys.executable, "-B", MIP_PY],      "fmt": "mip"},
}


# ─── Instance helpers ──────────────────────────────────────────────────────
def read_instance(path):
    with open(path) as f:
        tokens = f.read().split()
    it = iter(tokens)
    N, K = int(next(it)), int(next(it))
    dist = [[int(next(it)) for _ in range(N+1)] for _ in range(N+1)]
    return N, K, dist


def route_length(route, dist):
    return sum(dist[route[i]][route[i+1]] for i in range(len(route)-1))


# ─── Output parsers ───────────────────────────────────────────────────────
def parse_greedy_sa(raw, N, K, dist):
    """
    K
    size
    node0 node1 ...
    size
    node0 node1 ...
    """
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    if not lines:
        return None, "EMPTY_OUTPUT"
    try:
        k = int(lines[0])
    except ValueError:
        return None, "PARSE_ERROR"
    routes = []
    i = 1
    while i < len(lines) and len(routes) < k:
        try:
            sz = int(lines[i]); i += 1
        except (ValueError, IndexError):
            break
        if i >= len(lines):
            break
        pts = list(map(int, lines[i].split())); i += 1
        routes.append(pts)
    if not routes:
        return None, "NO_ROUTES"
    obj = max(route_length(r, dist) for r in routes)
    return obj, "OK"


def parse_tabu(raw, N, K, dist):
    """
    Iter X Best = Y   ← skip these
    12                ← objective on first non-Iter line
    2 0 3             ← size node0 node1 ...
    3 0 1 2
    """
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    # skip "Iter ..." lines
    data_lines = [l for l in lines if not l.startswith("Iter")]
    if not data_lines:
        return None, "EMPTY_OUTPUT"
    try:
        obj = int(data_lines[0])
        return obj, "OK"
    except ValueError:
        return None, "PARSE_ERROR"


def parse_output(raw, fmt, N, K, dist):
    if fmt in ("greedy_sa", "mip"):
        return parse_greedy_sa(raw, N, K, dist)
    elif fmt == "tabu":
        return parse_tabu(raw, N, K, dist)
    return None, "UNKNOWN_FMT"


# ─── Run one solver ────────────────────────────────────────────────────────
def run_solver(name, cfg, inst_path, time_limit, N, K, dist):
    env = os.environ.copy()
    env["VRP_TIME_LIMIT_SEC"] = str(time_limit)

    with open(inst_path) as f:
        inp = f.read()

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cfg["cmd"], input=inp, capture_output=True, text=True,
            timeout=time_limit + 8, env=env
        )
        elapsed = time.perf_counter() - t0
        raw = proc.stdout
    except subprocess.TimeoutExpired:
        return None, time_limit + 8, "TIMEOUT"
    except Exception as e:
        return None, 0.0, f"ERROR:{e}"

    obj, status = parse_output(raw, cfg["fmt"], N, K, dist)
    return obj, round(time.perf_counter() - t0, 3), status


# ─── Main ─────────────────────────────────────────────────────────────────
def run_all(time_limits, output_csv):
    # Generate instances
    print("Generating instances...")
    subprocess.run(
        [sys.executable, "-B", os.path.join(BASE_DIR, "gen_instance.py"), INST_DIR],
        check=True
    )

    instances = sorted(f for f in os.listdir(INST_DIR) if f.endswith(".txt"))
    solver_names = list(SOLVERS.keys())
    total = sum(
        len(time_limits) * (len(solver_names) if read_instance(os.path.join(INST_DIR,f))[0] <= 30
                            else len(solver_names) - 1)   # skip MIP on large
        for f in instances
    )
    print(f"Instances: {len(instances)} | Solvers: {solver_names} | TLs: {time_limits}\n")

    rows = []
    done = 0
    for inst_file in instances:
        inst_path = os.path.join(INST_DIR, inst_file)
        N, K, dist = read_instance(inst_path)
        parts = inst_file.replace(".txt", "").split("_")
        study, dist_type = parts[0], parts[1]

        for tl in time_limits:
            for name, cfg in SOLVERS.items():
                if name == "MIP" and N > 30:
                    continue   # MIP too slow for large N
                done += 1
                print(f"  [{done}] {inst_file} | {name:10s} | t={tl}s ... ", end="", flush=True)
                obj, elapsed, status = run_solver(name, cfg, inst_path, tl, N, K, dist)
                print(f"obj={obj}  rt={elapsed:.2f}s  [{status}]")
                rows.append({
                    "instance": inst_file, "study": study, "dist": dist_type,
                    "N": N, "K": K, "solver": name,
                    "time_limit": tl, "objective": obj,
                    "runtime": elapsed, "status": status,
                })

    with open(output_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\n✅ Saved {len(rows)} rows → {output_csv}")
    return rows


if __name__ == "__main__":
    TIME_LIMITS = [0.5, 1.0, 2.0, 5.0]
    out_csv = os.path.join(RES_DIR, "raw_results.csv")
    run_all(TIME_LIMITS, out_csv)
