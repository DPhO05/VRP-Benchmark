#include <algorithm>
#include <chrono>
#include <climits>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>
using namespace std;

// ============================================================
// GLOBAL
// ============================================================
int n, K;
int d[1005][1005];
mt19937 rng(1);
bool BALANCE_PLATEAU = false;
bool USE_ALT_CONSTRUCT = false;
bool USE_DIVERSE_CONSTRUCT = false;

// Time limit
auto startTime = chrono::steady_clock::now();
int TIME_LIMIT_MS = 4000; // chừa biên an toàn cho overhead chạy chương trình

bool timeUp() {
    auto now = chrono::steady_clock::now();
    return chrono::duration_cast<chrono::milliseconds>(now - startTime).count() >= TIME_LIMIT_MS;
}

// ============================================================
// TÍNH ĐỘ DÀI ROUTE - cache lại để không tính lại nhiều lần
// ============================================================
int calcLen(const vector<int>& route) {
    int len = 0;
    for (int i = 0; i + 1 < (int)route.size(); i++)
        len += d[route[i]][route[i+1]];
    return len;
}

// Tính lại toàn bộ lengths và trả về max
int recalcAll(const vector<vector<int>>& routes, vector<int>& lengths) {
    lengths.resize(routes.size());
    int mx = 0;
    for (int i = 0; i < (int)routes.size(); i++) {
        lengths[i] = calcLen(routes[i]);
        mx = max(mx, lengths[i]);
    }
    return mx;
}

long long calcEnergy(const vector<int>& lengths) {
    long long energy = 0;
    for (int x : lengths) energy += 1LL * x * x;
    return energy;
}

// ============================================================
// GREEDY CONSTRUCTION
// Cải tiến: dùng random restart thực sự
//           dùng regret-based insertion thay vì nearest neighbor
// ============================================================

// Nearest neighbor với randomization có kiểm soát
vector<vector<int>> greedyConstruct(int z, int randomTop = 1) {
    vector<int> unvisited;
    for (int i = 1; i <= n; i++) unvisited.push_back(i);

    // Shuffle để đa dạng hóa thứ tự assign
    if (randomTop > 1)
        shuffle(unvisited.begin(), unvisited.end(), rng);

    vector<vector<int>> routes(K, vector<int>{0});
    vector<int> lengths(K, 0);

    // Sắp xếp điểm theo khoảng cách từ depot giảm dần (điểm xa nhất gán trước)
    sort(unvisited.begin(), unvisited.end(), [](int a, int b){
        return d[0][a] > d[0][b];
    });

    for (int pt : unvisited) {
        // Thử gán pt vào tuyến có chi phí thêm nhỏ nhất và không vượt z
        int bestK = -1, bestPos = -1, bestCost = INT_MAX;

        // Sắp xếp tuyến theo length tăng dần để ưu tiên tuyến ngắn
        vector<int> order(K);
        iota(order.begin(), order.end(), 0);
        sort(order.begin(), order.end(), [&](int a, int b){
            return lengths[a] < lengths[b];
        });

        for (int ki : order) {
            auto& route = routes[ki];
            // Tìm vị trí chèn tốt nhất trong route này
            for (int pos = 1; pos <= (int)route.size(); pos++) {
                int prev = route[pos-1];
                int next = (pos < (int)route.size()) ? route[pos] : -1;
                int cost;
                if (next == -1)
                    cost = d[prev][pt];
                else
                    cost = d[prev][pt] + d[pt][next] - d[prev][next];

                int newLen = lengths[ki] + cost;
                if (newLen <= z && cost < bestCost) {
                    bestCost = cost;
                    bestK = ki;
                    bestPos = pos;
                }
            }
            if (bestK != -1 && randomTop == 1) break; // greedy thuần: lấy tuyến đầu tiên đủ điều kiện
        }

        if (bestK == -1) return {}; // không feasible với z này

        routes[bestK].insert(routes[bestK].begin() + bestPos, pt);
        lengths[bestK] += bestCost;
    }

    return routes;
}

vector<vector<int>> greedyConstructAlt(int z, int mode) {
    vector<int> unvisited;
    for (int i = 1; i <= n; i++) unvisited.push_back(i);

    if (mode == 0) {
        shuffle(unvisited.begin(), unvisited.end(), rng);
    } else if (mode == 1) {
        sort(unvisited.begin(), unvisited.end(), [](int a, int b) {
            return d[0][a] < d[0][b];
        });
    } else {
        sort(unvisited.begin(), unvisited.end(), [](int a, int b) {
            return d[0][a] > d[0][b];
        });
        for (int i = 0; i + 1 < (int)unvisited.size(); i += 8) {
            int r = min((int)unvisited.size(), i + 8);
            shuffle(unvisited.begin() + i, unvisited.begin() + r, rng);
        }
    }

    vector<vector<int>> routes(K, vector<int>{0});
    vector<int> lengths(K, 0);

    for (int pt : unvisited) {
        int bestK = -1, bestPos = -1, bestCost = INT_MAX;
        long long bestScore = LLONG_MAX;

        for (int ki = 0; ki < K; ki++) {
            auto& route = routes[ki];
            for (int pos = 1; pos <= (int)route.size(); pos++) {
                int prev = route[pos - 1];
                int next = (pos < (int)route.size()) ? route[pos] : -1;
                int cost = (next == -1)
                    ? d[prev][pt]
                    : d[prev][pt] + d[pt][next] - d[prev][next];
                int newLen = lengths[ki] + cost;
                if (newLen > z) continue;

                long long score;
                if (mode == 0) score = 1000LL * cost + newLen;
                else score = 1000LL * newLen + cost;

                if (score < bestScore || (score == bestScore && cost < bestCost)) {
                    bestScore = score;
                    bestCost = cost;
                    bestK = ki;
                    bestPos = pos;
                }
            }
        }

        if (bestK == -1) return {};

        routes[bestK].insert(routes[bestK].begin() + bestPos, pt);
        lengths[bestK] += bestCost;
    }

    return routes;
}

vector<vector<int>> greedyConstructDiverse(int z, int mode) {
    vector<int> unvisited;
    for (int i = 1; i <= n; i++) unvisited.push_back(i);

    if (mode == 0 || mode == 3) {
        shuffle(unvisited.begin(), unvisited.end(), rng);
    } else if (mode == 1) {
        sort(unvisited.begin(), unvisited.end(), [](int a, int b) {
            return d[0][a] < d[0][b];
        });
    } else {
        sort(unvisited.begin(), unvisited.end(), [](int a, int b) {
            return d[0][a] > d[0][b];
        });
        for (int i = 0; i + 1 < (int)unvisited.size(); i += 10) {
            int r = min((int)unvisited.size(), i + 10);
            shuffle(unvisited.begin() + i, unvisited.begin() + r, rng);
        }
    }

    vector<vector<int>> routes(K, vector<int>{0});
    vector<int> lengths(K, 0);

    for (int pt : unvisited) {
        int bestK = -1, bestPos = -1, bestCost = INT_MAX;
        long long bestScore = LLONG_MAX;

        vector<int> order(K);
        iota(order.begin(), order.end(), 0);
        sort(order.begin(), order.end(), [&](int a, int b) {
            return lengths[a] < lengths[b];
        });

        for (int ki : order) {
            auto& route = routes[ki];
            for (int pos = 1; pos <= (int)route.size(); pos++) {
                int prev = route[pos - 1];
                int next = (pos < (int)route.size()) ? route[pos] : -1;
                int cost = (next == -1)
                    ? d[prev][pt]
                    : d[prev][pt] + d[pt][next] - d[prev][next];
                int newLen = lengths[ki] + cost;
                if (newLen > z) continue;

                long long score;
                if (mode == 0) score = 1000LL * newLen + cost;
                else if (mode == 1) score = 1000LL * cost + newLen;
                else if (mode == 2) score = 1000LL * lengths[ki] + cost;
                else score = 1000LL * cost + lengths[ki];

                if (score < bestScore || (score == bestScore && cost < bestCost)) {
                    bestScore = score;
                    bestCost = cost;
                    bestK = ki;
                    bestPos = pos;
                }
            }
        }

        if (bestK == -1) return {};

        routes[bestK].insert(routes[bestK].begin() + bestPos, pt);
        lengths[bestK] += bestCost;
    }

    return routes;
}

// ============================================================
// 2-OPT NỘI TUYẾN
// ============================================================
bool twoOptRoute(vector<int>& route, int& len, int z) {
    bool improved = false;
    int sz = route.size();
    if (sz <= 3) return false;

    for (int i = 1; i < sz - 1; i++) {
        for (int j = i + 1; j < sz; j++) {
            // delta = cost sau - cost trước khi đảo đoạn [i..j]
            int before = d[route[i-1]][route[i]] + d[route[j]][j+1 < sz ? route[j+1] : route[j]];
            int after  = d[route[i-1]][route[j]] + d[route[i]][j+1 < sz ? route[j+1] : route[j]];
            // Nếu j là cuối route thì số hạng thứ 2 = 0 ở cả 2 vế
            // Tính lại đúng hơn:
            int costBefore = d[route[i-1]][route[i]];
            int costAfter_start = d[route[i-1]][route[j]];
            if (j + 1 < sz) {
                costBefore += d[route[j]][route[j+1]];
                costAfter_start += d[route[i]][route[j+1]];
            }
            int delta = costAfter_start - costBefore;
            if (delta < 0 && len + delta <= z) {
                reverse(route.begin() + i, route.begin() + j + 1);
                len += delta;
                improved = true;
            }
        }
    }
    return improved;
}

void twoOptAll(vector<vector<int>>& routes, vector<int>& lengths, int z) {
    for (int k = 0; k < K; k++)
        while (twoOptRoute(routes[k], lengths[k], z));
}

bool intraRelocateRoute(vector<int>& route, int& len, int z) {
    int sz = route.size();
    if (sz <= 3) return false;

    int bestLen = len;
    vector<int> bestRoute;

    for (int from = 1; from < sz; from++) {
        for (int to = 1; to < sz; to++) {
            if (to == from) continue;

            vector<int> candidate = route;
            int pt = candidate[from];
            candidate.erase(candidate.begin() + from);
            candidate.insert(candidate.begin() + to, pt);

            int candLen = calcLen(candidate);
            if (candLen < bestLen && candLen <= z) {
                bestLen = candLen;
                bestRoute.swap(candidate);
            }
        }
    }

    if (bestRoute.empty()) return false;

    route.swap(bestRoute);
    len = bestLen;
    return true;
}

void intraRelocateAll(vector<vector<int>>& routes, vector<int>& lengths, int z) {
    for (int k = 0; k < K; k++)
        while (intraRelocateRoute(routes[k], lengths[k], z));
}

// ============================================================
// RELOCATE: chuyển 1 điểm từ tuyến dài nhất sang tuyến khác
// Cải tiến: chỉ xét tuyến dài nhất, tìm move tốt nhất (best improvement)
// ============================================================
bool relocate(vector<vector<int>>& routes, vector<int>& lengths, int& maxLen, int z) {
    // Tìm tuyến dài nhất
    int worstK = max_element(lengths.begin(), lengths.end()) - lengths.begin();

    auto& worst = routes[worstK];
    if ((int)worst.size() <= 2) return false; // depot + 1 điểm → không di chuyển

    // Tìm move tốt nhất trong tất cả các điểm của worst
    int bestNewMax = maxLen;
    long long curEnergy = calcEnergy(lengths);
    long long bestEnergy = curEnergy;
    int bestPt = -1, bestPos_remove = -1, bestK2 = -1, bestPos_insert = -1;

    for (int pos = 1; pos < (int)worst.size(); pos++) {
        int pt = worst[pos];

        // Chi phí xóa pt khỏi worst
        int prev = worst[pos-1];
        int next = (pos+1 < (int)worst.size()) ? worst[pos+1] : -1;
        int removeDelta;
        if (next == -1)
            removeDelta = -d[prev][pt];
        else
            removeDelta = d[prev][next] - d[prev][pt] - d[pt][next];

        int newWorstLen = lengths[worstK] + removeDelta;

        for (int k2 = 0; k2 < K; k2++) {
            if (k2 == worstK) continue;

            for (int ins = 1; ins <= (int)routes[k2].size(); ins++) {
                int p = routes[k2][ins-1];
                int nx = (ins < (int)routes[k2].size()) ? routes[k2][ins] : -1;
                int insertDelta;
                if (nx == -1)
                    insertDelta = d[p][pt];
                else
                    insertDelta = d[p][pt] + d[pt][nx] - d[p][nx];

                int newK2Len = lengths[k2] + insertDelta;
                if (newK2Len > z) continue;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < K; k3++)
                    if (k3 != worstK && k3 != k2)
                        newMax = max(newMax, lengths[k3]);

                long long newEnergy = curEnergy
                    - 1LL * lengths[worstK] * lengths[worstK]
                    - 1LL * lengths[k2] * lengths[k2]
                    + 1LL * newWorstLen * newWorstLen
                    + 1LL * newK2Len * newK2Len;

                if (newMax < bestNewMax ||
                    (BALANCE_PLATEAU && newMax == bestNewMax && newEnergy < bestEnergy)) {
                    bestNewMax = newMax;
                    bestEnergy = newEnergy;
                    bestPt = pt;
                    bestPos_remove = pos;
                    bestK2 = k2;
                    bestPos_insert = ins;
                }
            }
        }
    }

    if (bestPt == -1) return false;

    // Thực hiện move tốt nhất
    worst.erase(worst.begin() + bestPos_remove);
    routes[bestK2].insert(routes[bestK2].begin() + bestPos_insert, bestPt);

    // Cập nhật lengths
    lengths[worstK] = calcLen(routes[worstK]);
    lengths[bestK2] = calcLen(routes[bestK2]);
    maxLen = *max_element(lengths.begin(), lengths.end());
    return true;
}

// ============================================================
// SWAP: đổi 1 điểm giữa tuyến dài nhất và tuyến khác
// ============================================================
bool swapPoints(vector<vector<int>>& routes, vector<int>& lengths, int& maxLen, int z) {
    int worstK = max_element(lengths.begin(), lengths.end()) - lengths.begin();

    int bestNewMax = maxLen;
    long long curEnergy = calcEnergy(lengths);
    long long bestEnergy = curEnergy;
    int bestI = -1, bestJ = -1, bestK2 = -1;

    auto& worst = routes[worstK];

    for (int i = 1; i < (int)worst.size(); i++) {
        int pi = worst[i];
        int prevI = worst[i-1];
        int nextI = (i+1 < (int)worst.size()) ? worst[i+1] : -1;

        int removeCostI = (nextI == -1)
            ? d[prevI][pi]
            : d[prevI][pi] + d[pi][nextI];

        for (int k2 = 0; k2 < K; k2++) {
            if (k2 == worstK) continue;

            for (int j = 1; j < (int)routes[k2].size(); j++) {
                int pj = routes[k2][j];
                int prevJ = routes[k2][j-1];
                int nextJ = (j+1 < (int)routes[k2].size()) ? routes[k2][j+1] : -1;

                int removeCostJ = (nextJ == -1)
                    ? d[prevJ][pj]
                    : d[prevJ][pj] + d[pj][nextJ];

                // Sau khi swap: pi vào vị trí j, pj vào vị trí i
                int insertCostPjAtI = (nextI == -1)
                    ? d[prevI][pj]
                    : d[prevI][pj] + d[pj][nextI];
                int insertCostPiAtJ = (nextJ == -1)
                    ? d[prevJ][pi]
                    : d[prevJ][pi] + d[pi][nextJ];

                int newWorstLen = lengths[worstK] - removeCostI + insertCostPjAtI;
                int newK2Len    = lengths[k2]    - removeCostJ + insertCostPiAtJ;

                if (newK2Len > z || newWorstLen > z) continue;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < K; k3++)
                    if (k3 != worstK && k3 != k2)
                        newMax = max(newMax, lengths[k3]);

                long long newEnergy = curEnergy
                    - 1LL * lengths[worstK] * lengths[worstK]
                    - 1LL * lengths[k2] * lengths[k2]
                    + 1LL * newWorstLen * newWorstLen
                    + 1LL * newK2Len * newK2Len;

                if (newMax < bestNewMax ||
                    (BALANCE_PLATEAU && newMax == bestNewMax && newEnergy < bestEnergy)) {
                    bestNewMax = newMax;
                    bestEnergy = newEnergy;
                    bestI = i; bestJ = j; bestK2 = k2;
                }
            }
        }
    }

    if (bestI == -1) return false;

    swap(routes[worstK][bestI], routes[bestK2][bestJ]);
    lengths[worstK] = calcLen(routes[worstK]);
    lengths[bestK2] = calcLen(routes[bestK2]);
    maxLen = *max_element(lengths.begin(), lengths.end());
    return true;
}

// ============================================================
// OR-OPT: chuyển chuỗi 2-3 điểm liên tiếp từ tuyến dài → tuyến khác
// ============================================================
bool orOpt(vector<vector<int>>& routes, vector<int>& lengths, int& maxLen, int z, int segLen = 2) {
    int worstK = max_element(lengths.begin(), lengths.end()) - lengths.begin();
    auto& worst = routes[worstK];
    if ((int)worst.size() <= 1 + segLen) return false;

    int bestNewMax = maxLen;
    long long curEnergy = calcEnergy(lengths);
    long long bestEnergy = curEnergy;
    int bestStart = -1, bestK2 = -1, bestIns = -1;

    for (int start = 1; start + segLen - 1 < (int)worst.size(); start++) {
        // Đoạn [start .. start+segLen-1]
        int prevSeg = worst[start-1];
        int lastSeg = worst[start + segLen - 1];
        int nextSeg = (start + segLen < (int)worst.size()) ? worst[start+segLen] : -1;

        // Chi phí xóa đoạn
        int removeDelta;
        if (nextSeg == -1)
            removeDelta = -(d[prevSeg][worst[start]] + calcLen(vector<int>(worst.begin()+start, worst.begin()+start+segLen)));
        else
            removeDelta = d[prevSeg][nextSeg]
                        - d[prevSeg][worst[start]]
                        - calcLen(vector<int>(worst.begin()+start, worst.begin()+start+segLen))
                        + (segLen > 1 ? 0 : 0) // đã tính trong calcLen
                        - d[lastSeg][nextSeg];
        // Đơn giản hóa: tính lại trực tiếp
        int segCost = 0;
        for (int s = start; s + 1 < start + segLen; s++)
            segCost += d[worst[s]][worst[s+1]];

        int removeActual;
        if (nextSeg == -1)
            removeActual = d[prevSeg][worst[start]] + segCost;
        else
            removeActual = d[prevSeg][worst[start]] + segCost + d[lastSeg][nextSeg] - d[prevSeg][nextSeg];

        int newWorstLen = lengths[worstK] - removeActual;

        for (int k2 = 0; k2 < K; k2++) {
            if (k2 == worstK) continue;

            for (int ins = 1; ins <= (int)routes[k2].size(); ins++) {
                int p = routes[k2][ins-1];
                int nx = (ins < (int)routes[k2].size()) ? routes[k2][ins] : -1;

                int insertCost;
                if (nx == -1)
                    insertCost = d[p][worst[start]] + segCost + d[lastSeg][p]; // sai, fix:
                // fix:
                if (nx == -1)
                    insertCost = d[p][worst[start]] + segCost;
                else
                    insertCost = d[p][worst[start]] + segCost + d[lastSeg][nx] - d[p][nx];

                int newK2Len = lengths[k2] + insertCost;
                if (newK2Len > z) continue;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < K; k3++)
                    if (k3 != worstK && k3 != k2)
                        newMax = max(newMax, lengths[k3]);

                long long newEnergy = curEnergy
                    - 1LL * lengths[worstK] * lengths[worstK]
                    - 1LL * lengths[k2] * lengths[k2]
                    + 1LL * newWorstLen * newWorstLen
                    + 1LL * newK2Len * newK2Len;

                if (newMax < bestNewMax ||
                    (BALANCE_PLATEAU && newMax == bestNewMax && newEnergy < bestEnergy)) {
                    bestNewMax = newMax;
                    bestEnergy = newEnergy;
                    bestStart = start; bestK2 = k2; bestIns = ins;
                }
            }
        }
    }

    if (bestStart == -1) return false;

    vector<int> seg(worst.begin() + bestStart, worst.begin() + bestStart + segLen);
    worst.erase(worst.begin() + bestStart, worst.begin() + bestStart + segLen);
    routes[bestK2].insert(routes[bestK2].begin() + bestIns, seg.begin(), seg.end());

    lengths[worstK] = calcLen(routes[worstK]);
    lengths[bestK2] = calcLen(routes[bestK2]);
    maxLen = *max_element(lengths.begin(), lengths.end());
    return true;
}

// ============================================================
// LOCAL SEARCH ĐẦY ĐỦ
// ============================================================
void localSearch(vector<vector<int>>& routes, vector<int>& lengths, int& maxLen, int z) {
    bool improved = true;
    while (improved && !timeUp()) {
        improved = false;
        if (relocate(routes, lengths, maxLen, z))   { improved = true; continue; }
        if (swapPoints(routes, lengths, maxLen, z)) { improved = true; continue; }
        if (orOpt(routes, lengths, maxLen, z, 2))   { improved = true; continue; }
        if (orOpt(routes, lengths, maxLen, z, 3))   { improved = true; continue; }
        twoOptAll(routes, lengths, z);
        int beforeMax = maxLen;
        for (int k = 0; k < K && !timeUp(); k++) {
            if (lengths[k] == beforeMax) {
                while (intraRelocateRoute(routes[k], lengths[k], z) && !timeUp()) {}
            }
        }
        maxLen = *max_element(lengths.begin(), lengths.end());
        if (maxLen < beforeMax) improved = true;
    }
}

void localSearchBestVariant(vector<vector<int>>& routes, vector<int>& lengths, int& maxLen, int z) {
    auto strictRoutes = routes;
    auto balancedRoutes = routes;
    vector<int> strictLengths, balancedLengths;
    int strictMax = recalcAll(strictRoutes, strictLengths);
    int balancedMax = recalcAll(balancedRoutes, balancedLengths);

    BALANCE_PLATEAU = false;
    localSearch(strictRoutes, strictLengths, strictMax, z);

    BALANCE_PLATEAU = true;
    localSearch(balancedRoutes, balancedLengths, balancedMax, z);
    BALANCE_PLATEAU = false;

    if (balancedMax < strictMax) {
        routes = balancedRoutes;
        lengths = balancedLengths;
        maxLen = balancedMax;
    } else {
        routes = strictRoutes;
        lengths = strictLengths;
        maxLen = strictMax;
    }
}

// ============================================================
// KIỂM TRA FEASIBILITY với binary search
// ============================================================
pair<bool, vector<vector<int>>> canSolve(int z, int attempts) {
    // Lần 1: greedy thuần (không random)
    {
        auto routes = greedyConstruct(z, 1);
        if (!routes.empty()) return {true, routes};
    }

    // Lần 2..attempts: có random
    for (int i = 0; i < attempts && !timeUp(); i++) {
        auto routes = greedyConstruct(z, 3);
        if (!routes.empty()) return {true, routes};
    }

    if (USE_ALT_CONSTRUCT) {
        for (int i = 0; i < attempts && !timeUp(); i++) {
            auto routes = greedyConstructAlt(z, i % 3);
            if (!routes.empty()) return {true, routes};
        }
    }

    if (USE_DIVERSE_CONSTRUCT) {
        for (int i = 0; i < attempts && !timeUp(); i++) {
            auto routes = greedyConstructDiverse(z, i % 4);
            if (!routes.empty()) return {true, routes};
        }
    }

    return {false, {}};
}

// ============================================================
// MAIN
// ============================================================
pair<int, vector<vector<int>>> buildSolution() {
    int lo = 0, hi = 0;
    for (int i = 1; i <= n; i++)
        hi += d[0][i]; // worst case: đi từng điểm một từ depot

    // Tighten lower bound: mỗi bưu tá ít nhất phải đi đến 1 điểm
    // lo = min khoảng cách từ depot đến điểm bất kỳ
    lo = INT_MAX;
    for (int i = 1; i <= n; i++)
        lo = min(lo, d[0][i]);

    vector<vector<int>> bestRoutes;
    int bestMax = INT_MAX;

    int attempts = (n <= 200) ? 50 : (n <= 500) ? 20 : 10;

    // Binary search
    while (lo < hi && !timeUp()) {
        int mid = (lo + hi) / 2;
        auto [ok, routes] = canSolve(mid, attempts);
        if (ok) {
            hi = mid;
            bestRoutes = routes;
        } else {
            lo = mid + 1;
        }
    }

    // Đảm bảo có lời giải
    if (bestRoutes.empty()) {
        auto [ok, routes] = canSolve(lo, attempts * 2);
        if (ok) bestRoutes = routes;
        else {
            // fallback: greedy không giới hạn
            hi = INT_MAX / 2;
            auto [ok2, routes2] = canSolve(hi, 1);
            bestRoutes = routes2;
            lo = hi;
        }
    }

    // Local search để cải thiện
    if (!bestRoutes.empty()) {
        vector<int> lengths;
        int maxLen = recalcAll(bestRoutes, lengths);
        lo = maxLen; // update lo theo lời giải hiện tại

        localSearchBestVariant(bestRoutes, lengths, maxLen, maxLen);

        // Thử tiếp với maxLen nhỏ hơn
        while (!timeUp()) {
            int tryZ = maxLen - 1;
            auto [ok, routes] = canSolve(tryZ, attempts);
            if (ok) {
                vector<int> lens2;
                int mx2 = recalcAll(routes, lens2);
                localSearchBestVariant(routes, lens2, mx2, tryZ);
                if (mx2 < maxLen) {
                    bestRoutes = routes;
                    lengths = lens2;
                    maxLen = mx2;
                }
            } else break;
        }

        bestMax = maxLen;
    }

    return {bestMax, bestRoutes};
}

void solve() {
    cin >> n >> K;
    for (int i = 0; i <= n; i++)
        for (int j = 0; j <= n; j++)
            cin >> d[i][j];

    vector<int> seeds = {
        1, 2, 3, 4, 6, 10, 16, 35, 55, 56, 97, 132,
        5, 7, 8, 9, 11, 12, 13, 14, 15, 17, 18, 19, 20,
        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
        33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
        46, 47, 48, 49, 50
    };
    vector<vector<int>> bestRoutes;
    int bestMax = INT_MAX;

    for (int seed : seeds) {
        for (int variant = 0; variant < 3; variant++) {
            if (timeUp()) break;
            rng.seed(seed);
            USE_ALT_CONSTRUCT = (variant == 1);
            USE_DIVERSE_CONSTRUCT = (variant == 2);
            auto [mx, routes] = buildSolution();
            if (!routes.empty() && mx < bestMax) {
                bestMax = mx;
                bestRoutes = routes;
            }
        }
    }
    USE_ALT_CONSTRUCT = false;
    USE_DIVERSE_CONSTRUCT = false;

    cerr << "Objective (maxRouteLen) = " << bestMax << endl;

    // Output
    cout << K << "\n";
    for (auto& route : bestRoutes) {
        cout << route.size() << "\n";
        for (int i = 0; i < (int)route.size(); i++) {
            if (i > 0) cout << " ";
            cout << route[i];
        }
        cout << "\n";
    }
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    if (const char* envLimit = getenv("VRP_TIME_LIMIT_SEC")) {
        double seconds = atof(envLimit);
        if (seconds > 0) TIME_LIMIT_MS = max(1, (int)(seconds * 1000.0));
    }
    startTime = chrono::steady_clock::now();
    solve();
    return 0;
}
