"""
Simple instance generator for VRP benchmark.
Generates Euclidean distance matrix instances.
"""
import random
import math
import sys


def euclidean(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))


def gen_uniform(N, K, seed=42):
    """Uniform random points in [0,1000]^2, depot at center."""
    rng = random.Random(seed)
    depot = (500, 500)
    pts = [depot] + [(rng.randint(0, 1000), rng.randint(0, 1000)) for _ in range(N)]
    dist = [[euclidean(pts[i], pts[j]) for j in range(N+1)] for i in range(N+1)]
    return N, K, dist


def gen_cluster(N, K, seed=42, n_clusters=3):
    """Clustered points."""
    rng = random.Random(seed)
    depot = (500, 500)
    centers = [(rng.randint(100, 900), rng.randint(100, 900)) for _ in range(n_clusters)]
    customers = []
    for _ in range(N):
        cx, cy = rng.choice(centers)
        x = min(1000, max(0, int(rng.gauss(cx, 80))))
        y = min(1000, max(0, int(rng.gauss(cy, 80))))
        customers.append((x, y))
    pts = [depot] + customers
    dist = [[euclidean(pts[i], pts[j]) for j in range(N+1)] for i in range(N+1)]
    return N, K, dist


def gen_outlier(N, K, seed=42):
    """90% points near depot, 10% far outliers."""
    rng = random.Random(seed)
    depot = (500, 500)
    customers = []
    n_outlier = max(1, N // 10)
    for _ in range(N - n_outlier):
        x = min(1000, max(0, int(rng.gauss(500, 100))))
        y = min(1000, max(0, int(rng.gauss(500, 100))))
        customers.append((x, y))
    for _ in range(n_outlier):
        # Far corner
        corner = rng.choice([(50, 50), (950, 50), (50, 950), (950, 950)])
        x = min(1000, max(0, corner[0] + rng.randint(-30, 30)))
        y = min(1000, max(0, corner[1] + rng.randint(-30, 30)))
        customers.append((x, y))
    pts = [depot] + customers
    dist = [[euclidean(pts[i], pts[j]) for j in range(N+1)] for i in range(N+1)]
    return N, K, dist


def write_instance(N, K, dist, filepath):
    with open(filepath, 'w') as f:
        f.write(f"{N} {K}\n")
        for row in dist:
            f.write(" ".join(map(str, row)) + "\n")


if __name__ == "__main__":
    import os
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "simple_bench/instances"
    os.makedirs(out_dir, exist_ok=True)

    configs = []
    # Time-limit study: fixed N=30,K=4 with varying seeds
    for seed in range(5):
        configs.append(("timelimit", "uniform", 30, 4, seed))

    # Scalability study
    for N, K in [(8,2),(16,4),(30,4),(50,5),(80,8),(120,10),(200,15),(300,20)]:
        configs.append(("scale", "uniform", N, K, 42))
    for N, K in [(8,2),(30,4),(80,8),(200,15)]:
        configs.append(("scale", "cluster", N, K, 42))
    for N, K in [(8,2),(30,4),(80,8),(200,15)]:
        configs.append(("scale", "outlier", N, K, 42))

    generators = {"uniform": gen_uniform, "cluster": gen_cluster, "outlier": gen_outlier}

    for study, dist_type, N, K, seed in configs:
        gen = generators[dist_type]
        n, k, dist = gen(N, K, seed)
        fname = f"{study}_{dist_type}_N{N}_K{K}_s{seed}.txt"
        write_instance(n, k, dist, os.path.join(out_dir, fname))
        print(f"Generated: {fname}")
