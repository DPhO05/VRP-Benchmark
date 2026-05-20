#!/usr/bin/env python3
import sys


def insertion_delta(route, pos, point, dist):
    prev = route[pos - 1]
    if pos == len(route):
        return dist[prev][point]
    nxt = route[pos]
    return dist[prev][point] + dist[point][nxt] - dist[prev][nxt]


def two_opt(route, dist):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                before = dist[route[i - 1]][route[i]]
                after = dist[route[i - 1]][route[j]]
                if j + 1 < len(route):
                    before += dist[route[j]][route[j + 1]]
                    after += dist[route[i]][route[j + 1]]
                if after < before:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True
                    break
            if improved:
                break


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n, k = int(next(it)), int(next(it))
    dist = [[int(next(it)) for _ in range(n + 1)] for _ in range(n + 1)]
    routes = [[0] for _ in range(k)]
    lengths = [0] * k
    customers = list(range(1, n + 1))
    customers.sort(key=lambda x: dist[0][x], reverse=True)
    for point in customers:
        best = None
        for r in range(k):
            for pos in range(1, len(routes[r]) + 1):
                delta = insertion_delta(routes[r], pos, point, dist)
                new_lengths = lengths[:]
                new_lengths[r] += delta
                key = (max(new_lengths), new_lengths[r], delta)
                if best is None or key < best[0]:
                    best = (key, r, pos, delta)
        _, r, pos, delta = best
        routes[r].insert(pos, point)
        lengths[r] += delta
    if "--two-opt" in sys.argv:
        for route in routes:
            two_opt(route, dist)
    out = [str(k)]
    for route in routes:
        out.append(str(len(route)))
        out.append(" ".join(map(str, route)))
    print("\n".join(out))


if __name__ == "__main__":
    main()

