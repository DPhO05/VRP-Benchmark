#include <bits/stdc++.h>
using namespace std;

#define pii pair<int, int>
#define vi vector<int>
#define vvi vector<vi>

int num_vehicle, num_des;
int d[1005][1005];

mt19937 rng(42);

int cal_len(const vi &route)
{
    int len = 0;

    for (int i = 1; i < (int)route.size(); ++i)
    {
        len += d[route[i - 1]][route[i]];
    }

    return len;
}

vi cal_all_len(const vvi &routes)
{
    vi lens;

    for (const vi &route : routes)
    {
        lens.push_back(cal_len(route));
    }

    return lens;
}

// =====================================================
// SOLUTION
// =====================================================
struct solution
{
    int worse_len;
    vi lengths;
    vvi routes;

    solution() {}

    solution(vvi init_routes)
    {
        routes = init_routes;
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

    void print() const
    {
        cout << worse_len << endl;

        for (const auto &route : routes)
        {
            cout << route.size() << " ";

            for (int pt : route)
            {
                cout << pt << " ";
            }

            cout << endl;
        }
    }
};

// =====================================================
// TWO OPT
// =====================================================
solution twoOptRoute(vvi routes, vi lens)
{
    int pos = max_element(lens.begin(), lens.end()) - lens.begin();

    vi route = routes[pos];

    int sz = route.size();

    int bestDelta = 0;

    vi bestRoute = route;

    for (int i = 1; i < sz - 1; i++)
    {
        for (int j = i + 1; j < sz; j++)
        {
            int before = d[route[i - 1]][route[i]];

            int after = d[route[i - 1]][route[j]];

            if (j + 1 < sz)
            {
                before += d[route[j]][route[j + 1]];
                after += d[route[i]][route[j + 1]];
            }

            int delta = after - before;

            if (delta < bestDelta)
            {
                bestDelta = delta;

                vi candidate = route;

                reverse(candidate.begin() + i,
                        candidate.begin() + j + 1);

                bestRoute = candidate;
            }
        }
    }

    routes[pos] = bestRoute;

    return solution(routes);
}

// =====================================================
// INTRA RELOCATE
// =====================================================
solution intraRelocateRoute(vvi routes, vi lens)
{
    int pos = max_element(lens.begin(), lens.end()) - lens.begin();

    vi route = routes[pos];

    int bestLen = lens[pos];

    vi bestRoute = route;

    int sz = route.size();

    if (sz <= 3)
    {
        return solution(routes);
    }

    for (int from = 1; from < sz; from++)
    {
        for (int to = 1; to < sz; to++)
        {
            if (from == to)
                continue;

            vi candidate = route;

            int node = candidate[from];

            candidate.erase(candidate.begin() + from);

            candidate.insert(candidate.begin() + to, node);

            int candLen = cal_len(candidate);

            if (candLen < bestLen)
            {
                bestLen = candLen;
                bestRoute = candidate;
            }
        }
    }

    routes[pos] = bestRoute;

    return solution(routes);
}

// =====================================================
// RELOCATE BETWEEN ROUTES
// =====================================================
solution relocate(vvi routes, vi lens)
{
    int worstK = max_element(lens.begin(), lens.end()) - lens.begin();

    int bestMax = *max_element(lens.begin(), lens.end());

    int bestFrom = -1;
    int bestToRoute = -1;
    int bestInsert = -1;

    for (int i = 1; i < (int)routes[worstK].size(); i++)
    {
        int node = routes[worstK][i];

        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == worstK)
                continue;

            for (int ins = 1; ins <= (int)routes[k2].size(); ins++)
            {
                vvi candidate = routes;

                candidate[worstK].erase(candidate[worstK].begin() + i);

                candidate[k2].insert(candidate[k2].begin() + ins,
                                     node);

                solution cand(candidate);

                if (cand.worse_len < bestMax)
                {
                    bestMax = cand.worse_len;

                    bestFrom = i;
                    bestToRoute = k2;
                    bestInsert = ins;
                }
            }
        }
    }

    if (bestFrom == -1)
    {
        return solution(routes);
    }

    int node = routes[worstK][bestFrom];

    routes[worstK].erase(routes[worstK].begin() + bestFrom);

    routes[bestToRoute].insert(
        routes[bestToRoute].begin() + bestInsert,
        node);

    return solution(routes);
}

// =====================================================
// SWAP
// =====================================================
solution swapPoints(vvi routes, vi lens)
{
    int worstK = max_element(lens.begin(), lens.end()) - lens.begin();

    int bestMax = *max_element(lens.begin(), lens.end());

    int bestI = -1;
    int bestJ = -1;
    int bestK2 = -1;

    for (int i = 1; i < (int)routes[worstK].size(); i++)
    {
        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == worstK)
                continue;

            for (int j = 1; j < (int)routes[k2].size(); j++)
            {
                vvi candidate = routes;

                swap(candidate[worstK][i],
                     candidate[k2][j]);

                solution cand(candidate);

                if (cand.worse_len < bestMax)
                {
                    bestMax = cand.worse_len;

                    bestI = i;
                    bestJ = j;
                    bestK2 = k2;
                }
            }
        }
    }

    if (bestI == -1)
    {
        return solution(routes);
    }

    swap(routes[worstK][bestI],
         routes[bestK2][bestJ]);

    return solution(routes);
}

// =====================================================
// OR OPT
// =====================================================
solution orOpt(vvi routes, vi lens, int segLen = 2)
{
    int worstK = max_element(lens.begin(), lens.end()) - lens.begin();

    int bestMax = *max_element(lens.begin(), lens.end());

    int bestStart = -1;
    int bestK2 = -1;
    int bestIns = -1;

    if ((int)routes[worstK].size() <= segLen + 1)
    {
        return solution(routes);
    }

    for (int start = 1;
         start + segLen <= (int)routes[worstK].size();
         start++)
    {
        vi segment(routes[worstK].begin() + start,
                   routes[worstK].begin() + start + segLen);

        for (int k2 = 0; k2 < num_vehicle; k2++)
        {
            if (k2 == worstK)
                continue;

            for (int ins = 1;
                 ins <= (int)routes[k2].size();
                 ins++)
            {
                vvi candidate = routes;

                candidate[worstK].erase(
                    candidate[worstK].begin() + start,
                    candidate[worstK].begin() + start + segLen);

                candidate[k2].insert(
                    candidate[k2].begin() + ins,
                    segment.begin(),
                    segment.end());

                solution cand(candidate);

                if (cand.worse_len < bestMax)
                {
                    bestMax = cand.worse_len;

                    bestStart = start;
                    bestK2 = k2;
                    bestIns = ins;
                }
            }
        }
    }

    if (bestStart == -1)
    {
        return solution(routes);
    }

    vi segment(routes[worstK].begin() + bestStart,
               routes[worstK].begin() + bestStart + segLen);

    routes[worstK].erase(
        routes[worstK].begin() + bestStart,
        routes[worstK].begin() + bestStart + segLen);

    routes[bestK2].insert(
        routes[bestK2].begin() + bestIns,
        segment.begin(),
        segment.end());

    return solution(routes);
}

// =====================================================
// RANDOM NEIGHBOR
// =====================================================
solution neighbor(vvi &routes, vi &lens)
{
    int step = rng() % 6;

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
        return orOpt(routes, lens, 2);
    }

    return orOpt(routes, lens, 3);
}

// =====================================================
// ENCODE SOLUTION
// =====================================================
string encode_solution(const solution &sol)
{
    string s;

    for (const auto &route : sol.routes)
    {
        for (int x : route)
        {
            s += to_string(x) + ",";
        }

        s += "|";
    }

    return s;
}

void greedy_initial(vvi &routes)
{
    for (int i = 0; i < num_vehicle; i++)
    {
        routes[i].push_back(0);
    }

    set<int> unvisited;
    for (int i = 1; i <= num_des; i++)
        unvisited.insert(i);

    while (!unvisited.empty())
    {
        int bestK = -1;
        int bestPt = -1;
        int bestCost = INT_MAX;

        for (int pt : unvisited)
        {
            for (int k = 0; k < num_vehicle; k++)
            {
                int prev = routes[k].back();
                int cost = d[prev][pt];
                if (cost < bestCost)
                {
                    bestCost = cost;
                    bestPt = pt;
                    bestK = k;
                }
            }
        }
        routes[bestK].push_back(bestPt);
        unvisited.erase(bestPt);
    }
}

// =====================================================
// TABU SEARCH
// =====================================================
void tabu_search_solver()
{
    cin >> num_des >> num_vehicle;

    for (int i = 0; i <= num_des; i++)
    {
        for (int j = 0; j <= num_des; j++)
        {
            cin >> d[i][j];
        }
    }

    // ==========================================
    // Initial solution
    // ==========================================
    vvi routes(num_vehicle);
    greedy_initial(routes);

    solution current(routes);

    solution best = current;

    // ==========================================
    // TABU
    // ==========================================
    unordered_map<string, int> tabu;

    int TABU_TENURE = 50;

    int MAX_ITER = 5000;

    int NUM_CANDIDATES = 50;

    int noImprove = 0;

    for (int iter = 0; iter < MAX_ITER; iter++)
    {
        solution bestCandidate;

        bool found = false;

        // ======================================
        // Candidate list
        // ======================================
        for (int k = 0; k < NUM_CANDIDATES; k++)
        {
            solution cand =
                neighbor(current.routes,
                         current.lengths);

            string code = encode_solution(cand);

            bool isTabu =
                (tabu.count(code) &&
                 tabu[code] > iter);

            // aspiration
            if (isTabu &&
                cand.worse_len >= best.worse_len)
            {
                continue;
            }

            if (!found ||
                cand.worse_len < bestCandidate.worse_len)
            {
                bestCandidate = cand;
                found = true;
            }
        }

        if (!found)
        {
            continue;
        }

        current = bestCandidate;

        string curCode = encode_solution(current);

        tabu[curCode] = iter + TABU_TENURE;

        // ======================================
        // Update best
        // ======================================
        if (current.worse_len < best.worse_len)
        {
            best = current;

            noImprove = 0;

            cout << "Iter "
                 << iter
                 << " Best = "
                 << best.worse_len
                 << endl;
        }
        else
        {
            noImprove++;
        }

        // ======================================
        // Intensification
        // ======================================
        if (noImprove >= 100)
        {
            current = best;
            noImprove = 0;
        }

        // ======================================
        // Diversification
        // ======================================
        if (iter % 500 == 0)
        {
            current =
                neighbor(current.routes,
                         current.lengths);
        }
    }

    // ==========================================
    // OUTPUT
    // ==========================================
    cout << best.worse_len << endl;

    for (const auto &route : best.routes)
    {
        cout << route.size() << " ";

        for (int pt : route)
        {
            cout << pt << " ";
        }

        cout << endl;
    }
}

// =====================================================
// MAIN
// =====================================================
int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    freopen("/home/pthi35/code/Hust/Optimization/test_cases/inputs/test2.txt", "r", stdin);
    tabu_search_solver();

    return 0;
}