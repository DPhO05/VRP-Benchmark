#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <climits>
#include <iostream>
#include <random>
#include <string>
#include <tuple>
#include <vector>
using namespace std;

#define pii pair<int, int>
#define vi vector<int>
#define vvi vector<vi>

int num_vehicle, num_des;
int d[1005][1005];
chrono::steady_clock::time_point start_time;
int TIME_LIMIT_MS = 3800;

bool time_up()
{
    auto now = chrono::steady_clock::now();
    return chrono::duration_cast<chrono::milliseconds>(now - start_time).count() >= TIME_LIMIT_MS;
}

int cal_len(vi route)
{
    int len = 0;
    for (int i = 1; i < size(route); ++i)
    {
        len += d[route[i - 1]][route[i]];
    }

    return len;
}

vi cal_all_len(vvi routes)
{
    vi lens;
    for (vi route : routes)
    {
        lens.push_back(cal_len(route));
    }
    return lens;
}

// Define a solution.len(route[i])> len(route[i + 1]) for all i
struct solution
{
    int worse_len;
    vi lengths;
    vvi routes;

    solution(vvi init_routes) : routes(init_routes)
    {
        lengths = cal_all_len(routes);
        worse_len = *max_element(lengths.begin(), lengths.end());
    }

    void update_len(const vi &new_lengths)
    {
        lengths = new_lengths;
        worse_len = *max_element(lengths.begin(), lengths.end());
    }

    void update_len(int pos, const vi &new_route)
    {
        routes[pos] = new_route;
        lengths[pos] = cal_len(new_route);
        worse_len = *max_element(lengths.begin(), lengths.end());
    }

    void print()
    {
        cout << routes.size() << endl;
        for (const auto &route : routes)
        {
            cout << route.size() << "\n";
            for (int pt : route)
                cout << pt << " ";
            cout << "\n";
        }
    }
};

solution twoOptRoute(const vvi &routes, vi lens)
{
    int pos = max_element(lens.begin(), lens.end()) - lens.begin();
    vi route = routes[pos];
    int len = lens[pos];

    int sz = route.size();
    int min_delta = 1e9;
    vi new_route = route;

    for (int i = 1; i < sz - 1; i++)
    {
        for (int j = i + 1; j < sz; j++)
        {
            // delta = cost sau - cost trước khi đảo đoạn [i..j]
            int before = d[route[i - 1]][route[i]] + d[route[j]][j + 1 < sz ? route[j + 1] : route[j]];
            int after = d[route[i - 1]][route[j]] + d[route[i]][j + 1 < sz ? route[j + 1] : route[j]];
            // Nếu j là cuối route thì số hạng thứ 2 = 0 ở cả 2 vế
            // Tính lại đúng hơn:
            int costBefore = d[route[i - 1]][route[i]];
            int costAfter_start = d[route[i - 1]][route[j]];
            if (j + 1 < sz)
            {
                costBefore += d[route[j]][route[j + 1]];
                costAfter_start += d[route[i]][route[j + 1]];
            }

            int delta = costAfter_start - costBefore;
            if (delta < min_delta)
            {
                min_delta = delta;
                reverse(route.begin() + i, route.begin() + j + 1);
                new_route = route;
                reverse(route.begin() + i, route.begin() + j + 1);
            }
        }
    }

    solution res(routes);
    if (min_delta < 0)
        res.update_len(pos, new_route);
    else
        res.update_len(pos, route);
    return res;
}

solution intraRelocateRoute(vvi routes, vi lens)
{
    int pos = max_element(lens.begin(), lens.end()) - lens.begin();
    vi route = routes[pos];
    int len = lens[pos];

    int sz = route.size();
    if (sz <= 3)
    {
        solution res(routes);
        res.update_len(pos, route);
        return res;
    }

    int bestLen = len;
    vector<int> bestRoute;

    for (int from = 1; from < sz; from++)
    {
        for (int to = 1; to < sz; to++)
        {
            if (to == from)
                continue;

            vector<int> candidate = route;
            int pt = candidate[from];
            candidate.erase(candidate.begin() + from);
            candidate.insert(candidate.begin() + to, pt);

            int candLen = cal_len(candidate);
            if (candLen < bestLen)
            {
                bestLen = candLen;
                bestRoute.swap(candidate);
            }
        }
    }

    solution res(routes);
    if (!bestRoute.empty())
        res.update_len(pos, bestRoute);
    else
        res.update_len(pos, route);

    return res;
}

// ============================================================
// RELOCATE: chuyển 1 điểm từ tuyến dài nhất sang tuyến khác
// Cải tiến: chỉ xét tuyến dài nhất, tìm move tốt nhất (best improvement)
// ============================================================
solution relocate(vvi &routes, vi lens)
{
    // Tìm tuyến dài nhất
    int pos = max_element(lens.begin(), lens.end()) - lens.begin();

    vi route = routes[pos];
    if ((int)route.size() <= 2)
        return solution(routes);

    // Tìm move tốt nhất trong tất cả các điểm của route
    int bestNewMax = lens[pos];
    int bestPt = -1, bestPos_remove = -1, bestK2 = -1, bestPos_insert = -1;

    for (int i = 1; i < (int)route.size(); i++)
    {
        int pt = route[i];

        // Chi phí xóa pt khỏi route
        int prev = route[i - 1];
        int next = (i + 1 < (int)route.size()) ? route[i + 1] : -1;
        int removeDelta;
        if (next == -1)
            removeDelta = -d[prev][pt];
        else
            removeDelta = d[prev][next] - d[prev][pt] - d[pt][next];

        int newWorstLen = lens[pos] + removeDelta;

        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == pos)
                continue;

            for (int ins = 1; ins <= (int)routes[k2].size(); ins++)
            {
                int p = routes[k2][ins - 1];
                int nx = (ins < (int)routes[k2].size()) ? routes[k2][ins] : -1;
                int insertDelta;
                if (nx == -1)
                    insertDelta = d[p][pt];
                else
                    insertDelta = d[p][pt] + d[pt][nx] - d[p][nx];

                int newK2Len = lens[k2] + insertDelta;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < num_vehicle; k3++)
                    if (k3 != pos && k3 != k2)
                        newMax = max(newMax, lens[k3]);

                if (newMax < bestNewMax)
                {
                    bestNewMax = newMax;
                    bestPt = pt;
                    bestPos_remove = i;
                    bestK2 = k2;
                    bestPos_insert = ins;
                }
            }
        }
    }

    if (bestPt == -1)
        return solution(routes);

    // Thực hiện move tốt nhất
    route.erase(route.begin() + bestPos_remove);
    routes[pos] = route;
    routes[bestK2].insert(routes[bestK2].begin() + bestPos_insert, bestPt);

    solution res(routes);
    res.update_len(pos, route);
    return res;
}

// ============================================================
// SWAP: đổi 1 điểm giữa tuyến dài nhất và tuyến khác
// ============================================================
solution swapPoints(vvi routes, vi lens)
{
    int worstK = max_element(lens.begin(), lens.end()) - lens.begin();
    int maxLen = lens[worstK];

    int bestNewMax = *max_element(lens.begin(), lens.end());
    int bestI = -1, bestJ = -1, bestK2 = -1;

    auto &worst = routes[worstK];

    for (int i = 1; i < (int)worst.size(); i++)
    {
        int pi = worst[i];
        int prevI = worst[i - 1];
        int nextI = (i + 1 < (int)worst.size()) ? worst[i + 1] : -1;

        int removeCostI = (nextI == -1)
                              ? d[prevI][pi]
                              : d[prevI][pi] + d[pi][nextI];

        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == worstK)
                continue;

            for (int j = 1; j < (int)routes[k2].size(); j++)
            {
                int pj = routes[k2][j];
                int prevJ = routes[k2][j - 1];
                int nextJ = (j + 1 < (int)routes[k2].size()) ? routes[k2][j + 1] : -1;

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

                int newWorstLen = lens[worstK] - removeCostI + insertCostPjAtI;
                int newK2Len = lens[k2] - removeCostJ + insertCostPiAtJ;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < num_vehicle; k3++)
                    if (k3 != worstK && k3 != k2)
                        newMax = max(newMax, lens[k3]);

                if (newMax < bestNewMax)
                {
                    bestNewMax = newMax;
                    bestI = i;
                    bestJ = j;
                    bestK2 = k2;
                }
            }
        }
    }

    if (bestI == -1)
        return solution(routes);

    swap(routes[worstK][bestI], routes[bestK2][bestJ]);

    solution res(routes);
    res.update_len(worstK, routes[worstK]);
    res.update_len(bestK2, routes[bestK2]);

    return res;
}

solution orOpt(vvi routes, vi lens, int segLen = 2)
{
    int worstK = max_element(lens.begin(), lens.end()) - lens.begin();
    int maxLen = lens[worstK];
    int min_delta = 1e9;

    auto &worst = routes[worstK];
    if ((int)worst.size() <= 1 + segLen)
        return solution(routes);

    int bestNewMax = *max_element(lens.begin(), lens.end());
    int bestStart = -1, bestK2 = -1, bestIns = -1;

    for (int start = 1; start + segLen - 1 < (int)worst.size(); start++)
    {
        // Đoạn [start .. start+segLen-1]
        int prevSeg = worst[start - 1];
        int lastSeg = worst[start + segLen - 1];
        int nextSeg = (start + segLen < (int)worst.size()) ? worst[start + segLen] : -1;

        // Chi phí xóa đoạn
        int removeDelta;
        if (nextSeg == -1)
            removeDelta = -(d[prevSeg][worst[start]] + cal_len(vector<int>(worst.begin() + start, worst.begin() + start + segLen)));
        else
            removeDelta = d[prevSeg][nextSeg] - d[prevSeg][worst[start]] - cal_len(vector<int>(worst.begin() + start, worst.begin() + start + segLen)) + (segLen > 1 ? 0 : 0) // đã tính trong cal_len
                          - d[lastSeg][nextSeg];
        // Đơn giản hóa: tính lại trực tiếp
        int segCost = 0;
        for (int s = start; s + 1 < start + segLen; s++)
            segCost += d[worst[s]][worst[s + 1]];

        int removeActual;
        if (nextSeg == -1)
            removeActual = d[prevSeg][worst[start]] + segCost;
        else
            removeActual = d[prevSeg][worst[start]] + segCost + d[lastSeg][nextSeg] - d[prevSeg][nextSeg];

        int newWorstLen = lens[worstK] - removeActual;

        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == worstK)
                continue;

            for (int ins = 1; ins <= (int)routes[k2].size(); ins++)
            {
                int p = routes[k2][ins - 1];
                int nx = (ins < (int)routes[k2].size()) ? routes[k2][ins] : -1;

                int insertCost;
                if (nx == -1)
                    insertCost = d[p][worst[start]] + segCost + d[lastSeg][p]; // sai, fix:
                // fix:
                if (nx == -1)
                    insertCost = d[p][worst[start]] + segCost;
                else
                    insertCost = d[p][worst[start]] + segCost + d[lastSeg][nx] - d[p][nx];

                int newK2Len = lens[k2] + insertCost;

                int newMax = max(newWorstLen, newK2Len);
                for (int k3 = 0; k3 < num_vehicle; k3++)
                    if (k3 != worstK && k3 != k2)
                        newMax = max(newMax, lens[k3]);

                if (newMax < bestNewMax)
                {
                    bestNewMax = newMax;
                    bestStart = start;
                    bestK2 = k2;
                    bestIns = ins;
                }
            }
        }
    }

    if (bestStart == -1)
        return solution(routes);

    vector<int> seg(worst.begin() + bestStart, worst.begin() + bestStart + segLen);
    worst.erase(worst.begin() + bestStart, worst.begin() + bestStart + segLen);
    routes[bestK2].insert(routes[bestK2].begin() + bestIns, seg.begin(), seg.end());

    solution res(routes);
    res.update_len(worstK, routes[worstK]);
    res.update_len(bestK2, routes[bestK2]);

    return res;
}

mt19937 rng(42);

int insert_delta(const vi &route, int pos, int pt)
{
    int prev = route[pos - 1];
    if (pos == (int)route.size())
        return d[prev][pt];
    int nxt = route[pos];
    return d[prev][pt] + d[pt][nxt] - d[prev][nxt];
}

long long route_energy(const vi &lengths)
{
    long long e = 0;
    for (int x : lengths)
        e += 1LL * x * x;
    return e;
}

vvi greedy_initial_routes()
{
    vvi routes(num_vehicle);
    for (int i = 0; i < num_vehicle; i++)
        routes[i].push_back(0);

    vi lengths(num_vehicle, 0);
    vi nodes(num_des);
    for (int i = 0; i < num_des; i++)
        nodes[i] = i + 1;

    sort(nodes.begin(), nodes.end(), [](int a, int b)
         {
             if (d[0][a] != d[0][b])
                 return d[0][a] > d[0][b];
             return a < b;
         });

    for (int pt : nodes)
    {
        tuple<int, long long, int, int, int> best(INT_MAX, LLONG_MAX, INT_MAX, -1, -1);
        for (int k = 0; k < num_vehicle; k++)
        {
            for (int pos = 1; pos <= (int)routes[k].size(); pos++)
            {
                int delta = insert_delta(routes[k], pos, pt);
                vi cand = lengths;
                cand[k] += delta;
                int mx = *max_element(cand.begin(), cand.end());
                long long energy = 0;
                for (int x : cand)
                    energy += 1LL * x * x;
                best = min(best, make_tuple(mx, energy, delta, k, pos));
            }
        }

        int k = get<3>(best);
        int pos = get<4>(best);
        int delta = insert_delta(routes[k], pos, pt);
        routes[k].insert(routes[k].begin() + pos, pt);
        lengths[k] += delta;
    }

    return routes;
}

vi customer_order(int mode)
{
    vi nodes(num_des);
    for (int i = 0; i < num_des; i++)
        nodes[i] = i + 1;
    if (mode == 0)
    {
        sort(nodes.begin(), nodes.end(), [](int a, int b)
             { return d[0][a] > d[0][b]; });
    }
    else if (mode == 1)
    {
        sort(nodes.begin(), nodes.end(), [](int a, int b)
             { return d[0][a] < d[0][b]; });
    }
    else if (mode == 2)
    {
        shuffle(nodes.begin(), nodes.end(), rng);
    }
    else
    {
        sort(nodes.begin(), nodes.end(), [](int a, int b)
             { return d[0][a] > d[0][b]; });
        for (int i = 0; i < (int)nodes.size(); i += 10)
        {
            int r = min((int)nodes.size(), i + 10);
            shuffle(nodes.begin() + i, nodes.begin() + r, rng);
        }
    }
    return nodes;
}

vvi greedy_feasible(int z, int mode)
{
    vvi routes(num_vehicle);
    for (int i = 0; i < num_vehicle; i++)
        routes[i].push_back(0);
    vi lengths(num_vehicle, 0);
    vi nodes = customer_order(mode);

    for (int pt : nodes)
    {
        tuple<int, int, int, int> best(INT_MAX, INT_MAX, -1, -1);
        vi order(num_vehicle);
        for (int i = 0; i < num_vehicle; i++)
            order[i] = i;
        sort(order.begin(), order.end(), [&](int a, int b)
             { return lengths[a] < lengths[b]; });

        for (int k : order)
        {
            for (int pos = 1; pos <= (int)routes[k].size(); pos++)
            {
                int delta = insert_delta(routes[k], pos, pt);
                int newLen = lengths[k] + delta;
                if (newLen > z)
                    continue;
                int scoreLen = (mode == 0 ? newLen : (mode == 1 ? delta : lengths[k]));
                int scoreDelta = (mode == 0 ? delta : newLen);
                best = min(best, make_tuple(scoreLen, scoreDelta, k, pos));
            }
        }
        if (get<2>(best) == -1)
            return {};

        int k = get<2>(best);
        int pos = get<3>(best);
        int delta = insert_delta(routes[k], pos, pt);
        routes[k].insert(routes[k].begin() + pos, pt);
        lengths[k] += delta;
    }
    return routes;
}

vvi greedy_diverse_feasible(int z, int mode)
{
    vi nodes(num_des);
    for (int i = 0; i < num_des; i++)
        nodes[i] = i + 1;
    if (mode == 0 || mode == 3)
    {
        shuffle(nodes.begin(), nodes.end(), rng);
    }
    else if (mode == 1)
    {
        sort(nodes.begin(), nodes.end(), [](int a, int b)
             { return d[0][a] < d[0][b]; });
    }
    else
    {
        sort(nodes.begin(), nodes.end(), [](int a, int b)
             { return d[0][a] > d[0][b]; });
        for (int i = 0; i < (int)nodes.size(); i += 10)
        {
            int r = min((int)nodes.size(), i + 10);
            shuffle(nodes.begin() + i, nodes.begin() + r, rng);
        }
    }

    vvi routes(num_vehicle);
    for (int i = 0; i < num_vehicle; i++)
        routes[i].push_back(0);
    vi lengths(num_vehicle, 0);

    for (int pt : nodes)
    {
        int bestK = -1, bestPos = -1, bestCost = INT_MAX;
        long long bestScore = LLONG_MAX;
        vi order(num_vehicle);
        for (int i = 0; i < num_vehicle; i++)
            order[i] = i;
        sort(order.begin(), order.end(), [&](int a, int b)
             { return lengths[a] < lengths[b]; });

        for (int k : order)
        {
            for (int pos = 1; pos <= (int)routes[k].size(); pos++)
            {
                int cost = insert_delta(routes[k], pos, pt);
                int newLen = lengths[k] + cost;
                if (newLen > z)
                    continue;

                long long score;
                if (mode == 0)
                    score = 1000LL * newLen + cost;
                else if (mode == 1)
                    score = 1000LL * cost + newLen;
                else if (mode == 2)
                    score = 1000LL * lengths[k] + cost;
                else
                    score = 1000LL * cost + lengths[k];

                if (score < bestScore || (score == bestScore && cost < bestCost))
                {
                    bestScore = score;
                    bestCost = cost;
                    bestK = k;
                    bestPos = pos;
                }
            }
        }
        if (bestK == -1)
            return {};
        routes[bestK].insert(routes[bestK].begin() + bestPos, pt);
        lengths[bestK] += bestCost;
    }
    return routes;
}

vvi threshold_initial_routes()
{
    vvi best_routes = greedy_initial_routes();
    int best_obj = solution(best_routes).worse_len;
    int lo = 0, hi = best_obj;
    for (int i = 1; i <= num_des; i++)
        lo = max(lo, d[0][i]);

    while (lo < hi && !time_up())
    {
        int mid = (lo + hi) / 2;
        vvi found;
        for (int mode = 0; mode < 12 && !time_up(); mode++)
        {
            found = greedy_feasible(mid, mode % 4);
            if (found.empty())
                found = greedy_diverse_feasible(mid, mode % 4);
            if (!found.empty())
                break;
        }
        if (!found.empty())
        {
            best_routes = found;
            best_obj = solution(best_routes).worse_len;
            hi = min(mid, best_obj);
        }
        else
        {
            lo = mid + 1;
        }
    }
    return best_routes;
}

solution destroyRepair(vvi routes, vi lens)
{
    vi removed;
    int total_nodes = 0;
    for (auto &route : routes)
        total_nodes += max(0, (int)route.size() - 1);
    if (total_nodes == 0)
        return solution(routes);

    int q = max(2, min(30, total_nodes / 18 + 1));
    if (num_des <= 150)
        q = max(2, min(16, total_nodes / 10 + 1));

    for (int iter = 0; iter < q; iter++)
    {
        int worst = max_element(lens.begin(), lens.end()) - lens.begin();
        if ((int)routes[worst].size() <= 1)
            break;

        int pos = 1;
        if ((int)routes[worst].size() > 2 && rng() % 100 < 30)
        {
            pos = 1 + (rng() % ((int)routes[worst].size() - 1));
        }
        else
        {
            int far = -1;
            for (int p = 1; p < (int)routes[worst].size(); p++)
            {
                if (d[0][routes[worst][p]] > far)
                {
                    far = d[0][routes[worst][p]];
                    pos = p;
                }
            }
        }

        removed.push_back(routes[worst][pos]);
        routes[worst].erase(routes[worst].begin() + pos);
        lens[worst] = cal_len(routes[worst]);
    }

    while (!removed.empty())
    {
        int bestIdx = -1, bestK = -1, bestPos = -1;
        tuple<int, long long, int> bestKey(INT_MAX, LLONG_MAX, INT_MAX);
        for (int idx = 0; idx < (int)removed.size(); idx++)
        {
            int pt = removed[idx];
            for (int k = 0; k < num_vehicle; k++)
            {
                for (int pos = 1; pos <= (int)routes[k].size(); pos++)
                {
                    int delta = insert_delta(routes[k], pos, pt);
                    vi cand = lens;
                    cand[k] += delta;
                    tuple<int, long long, int> key(
                        *max_element(cand.begin(), cand.end()),
                        route_energy(cand),
                        delta);
                    if (key < bestKey)
                    {
                        bestKey = key;
                        bestIdx = idx;
                        bestK = k;
                        bestPos = pos;
                    }
                }
            }
        }
        int pt = removed[bestIdx];
        int delta = insert_delta(routes[bestK], bestPos, pt);
        routes[bestK].insert(routes[bestK].begin() + bestPos, pt);
        lens[bestK] += delta;
        removed.erase(removed.begin() + bestIdx);
    }

    return solution(routes);
}

solution neighbor(vvi &routes, vi &lens)
{
    vector<string> next_move = {"two-opt", "intrarelocate", "relocate", "swap", "or-opt2", "or-opt3", "destroy-repair"};

    int step = rng() % size(next_move);

    if (step == 0)
    {
        return twoOptRoute(routes, lens);
    }

    if (step == 1)
    {
        return intraRelocateRoute(routes, lens);
    }

    if (step == 2)
    {
        return relocate(routes, lens);
    }
    if (step == 3)
    {
        return swapPoints(routes, lens);
    }
    if (step == 4)
    {
        return orOpt(routes, lens);
    }
    if (step == 5)
    {
        return orOpt(routes, lens, 3);
    }
    if (step == 6)
    {
        return destroyRepair(routes, lens);
    }
    return solution(routes);
}

solution intensify(solution cur)
{
    bool improved = true;
    int rounds = 0;
    while (improved && !time_up() && rounds++ < 200)
    {
        improved = false;
        vector<solution> candidates;
        candidates.push_back(twoOptRoute(cur.routes, cur.lengths));
        candidates.push_back(intraRelocateRoute(cur.routes, cur.lengths));
        candidates.push_back(relocate(cur.routes, cur.lengths));
        candidates.push_back(swapPoints(cur.routes, cur.lengths));
        candidates.push_back(orOpt(cur.routes, cur.lengths));
        candidates.push_back(orOpt(cur.routes, cur.lengths, 3));

        solution bestCand = cur;
        for (auto &cand : candidates)
        {
            if (cand.worse_len < bestCand.worse_len)
                bestCand = cand;
        }
        if (bestCand.worse_len < cur.worse_len)
        {
            cur = bestCand;
            improved = true;
        }
    }
    return cur;
}

void sa_algo_solver()
{
    // Đọc input, khởi tạo solution ban đầu
    cin >> num_des >> num_vehicle;
    for (int i = 0; i <= num_des; i++)
        for (int j = 0; j <= num_des; j++)
            cin >> d[i][j];

    vvi routes = threshold_initial_routes();

    solution best(routes);
    solution current = intensify(best);
    best = current;

    double T = max(10.0, best.worse_len * 0.5);
    double cooling_rate = 0.995;

    while (!time_up())
    {
        solution next_sol = neighbor(current.routes, current.lengths);
        long long cur_score = 1000000LL * current.worse_len;
        long long next_score = 1000000LL * next_sol.worse_len;
        if (next_sol.worse_len < current.worse_len || exp((double)(cur_score - next_score) / max(1.0, T * 1000000.0)) > ((double)rng() / rng.max()))
        {
            current = next_sol;
            if (current.worse_len <= best.worse_len)
                current = intensify(current);

            if (current.worse_len < best.worse_len)
            {
                best = current;
            }
        }
        T *= cooling_rate;
        if (T < 0.5)
        {
            T = max(5.0, best.worse_len * 0.08);
            current = best;
        }
    }

    while (!time_up())
    {
        int target = best.worse_len - 1;
        bool improved = false;
        for (int attempt = 0; attempt < 80 && !time_up(); attempt++)
        {
            vvi cand_routes = greedy_feasible(target, attempt % 4);
            if (cand_routes.empty())
                cand_routes = greedy_diverse_feasible(target, attempt % 4);
            if (cand_routes.empty())
                continue;
            solution cand(cand_routes);
            cand = intensify(cand);
            if (cand.worse_len < best.worse_len)
            {
                best = cand;
                current = best;
                improved = true;
                break;
            }
        }
        if (!improved)
            break;
    }

    best.print();
}

int main()
{
    if (const char *env_limit = getenv("VRP_TIME_LIMIT_SEC"))
    {
        double seconds = atof(env_limit);
        if (seconds > 0)
            TIME_LIMIT_MS = max(100, (int)(seconds * 880.0));
    }
    start_time = chrono::steady_clock::now();
    sa_algo_solver();
}
