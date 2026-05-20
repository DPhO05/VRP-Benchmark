from __future__ import annotations

from typing import List


def mst_weight(dist: List[List[int]]) -> int:
    n = len(dist)
    used = [False] * n
    best = [10**30] * n
    best[0] = 0
    total = 0
    for _ in range(n):
        v = -1
        for i in range(n):
            if not used[i] and (v == -1 or best[i] < best[v]):
                v = i
        used[v] = True
        total += best[v]
        for to in range(n):
            if not used[to] and dist[v][to] < best[to]:
                best[to] = dist[v][to]
    return int(total)


def lower_bound(n: int, k: int, dist: List[List[int]], return_to_depot: bool = False) -> float:
    if n == 0:
        return 0.0
    farthest = max(dist[0][i] for i in range(1, n + 1))
    if return_to_depot:
        farthest *= 2
    return max(float(farthest), mst_weight(dist) / max(1, k))

