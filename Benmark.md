# Benchmark Framework cho bài toán Min-Max VRP / Postman Routing

README này mô tả đầy đủ cách xây dựng một benchmark nội bộ để so sánh nhiều solution cho bài toán:

> Có `N` điểm cần thu gom bưu kiện, `K` bưu tá xuất phát từ bưu điện `0`, biết ma trận khoảng cách `d(i,j)`. Cần chia các điểm cho `K` bưu tá và sắp xếp thứ tự đi sao cho **quãng đường dài nhất của một bưu tá là nhỏ nhất**.

Mục tiêu benchmark không chỉ là chạy trên vài test mẫu, mà là đánh giá solution theo phong cách nghiên cứu giải thuật cho bài toán NP-Hard:

- nghiệm có hợp lệ không;
- chất lượng nghiệm tốt đến đâu;
- thuật toán ổn định trên nhiều dạng instance không;
- thuật toán chạy nhanh và cải thiện theo thời gian thế nào;
- thuật toán có bị overfit vào 13 test có sẵn không.

---

## 1. Định nghĩa bài toán

Input gồm:

```text
N K
d(0,0) d(0,1) ... d(0,N)
d(1,0) d(1,1) ... d(1,N)
...
d(N,0) d(N,1) ... d(N,N)
```

Trong đó:

- điểm `0` là depot / bưu điện;
- điểm `1..N` là các điểm cần thu gom;
- `K` là số bưu tá;
- `d(i,j)` là khoảng cách từ điểm `i` đến điểm `j`.

Output của solver gồm `K` route. Mỗi route bắt đầu bằng `0` và chứa một số điểm trong `1..N`.

Ví dụ output:

```text
3
4
0 5 2 7
3
0 1 6
4
0 3 4 8
```

Ý nghĩa:

```text
Bưu tá 1: 0 -> 5 -> 2 -> 7
Bưu tá 2: 0 -> 1 -> 6
Bưu tá 3: 0 -> 3 -> 4 -> 8
```

### 1.1. Tính độ dài route

Nếu route là:

```text
[0, a1, a2, ..., am]
```

thì độ dài route là:

```text
d(0,a1) + d(a1,a2) + ... + d(a_{m-1}, am)
```

Nếu đề yêu cầu quay về depot, có thể bật option `--return-to-depot` trong validator/metrics, khi đó route length sẽ cộng thêm:

```text
d(am, 0)
```

Mặc định benchmark này dùng format giống code hiện tại: **route bắt đầu từ 0, không bắt buộc quay lại 0 ở cuối**.

### 1.2. Objective

Với `K` route có độ dài:

```text
L1, L2, ..., LK
```

Objective là:

```text
max(L1, L2, ..., LK)
```

Mục tiêu là minimize objective này.

---

## 2. Mục tiêu của benchmark

Benchmark cần trả lời các câu hỏi sau:

1. Solver nào cho objective nhỏ nhất trung bình?
2. Solver nào ổn định nhất, ít case thua nặng nhất?
3. Solver nào chạy nhanh nhất trong cùng time limit?
4. Solver nào tốt ở short time, solver nào tốt ở long time?
5. Solver nào mạnh ở từng dạng dữ liệu: uniform, cluster, line, outlier, adversarial?
6. Thành phần cải tiến nào thật sự có tác dụng: greedy, threshold, relocate, swap, 2-opt, RL-inspired loop?
7. Solver có bị overfit vào 13 test mẫu không?

---

## 3. Cấu trúc thư mục đề xuất

Codex hãy tạo cấu trúc thư mục như sau:

```text
benchmark/
  README.md

  generators/
    gen_uniform.py
    gen_cluster.py
    gen_line.py
    gen_outlier.py
    gen_ring.py
    gen_grid.py
    gen_adversarial.py
    generate_all.py

  instances/
    dev/
      uniform/
      cluster/
      line/
      outlier/
      ring/
      grid/
      adversarial/
    holdout/
      uniform/
      cluster/
      line/
      outlier/
      ring/
      grid/
      adversarial/

  solvers/
    README.md
    sol_a.py
    sol_b.py
    sol_c.cpp
    sol_d.cpp
    baselines/
      greedy.py
      greedy_2opt.py
      random_insertion.py
      ortools_baseline.py

  build/
    # binary C++ sau khi compile

  tools/
    validator.py
    metrics.py
    lower_bounds.py
    runner.py
    compile_cpp.py
    report.py
    visualize.py
    exact_small.py

  results/
    raw_runs.csv
    summary_by_solver.csv
    summary_by_distribution.csv
    summary_by_size.csv
    performance_profile.csv
    hard_cases.csv
    plots/
```

---

## 4. Nhóm test cần sinh

Không chỉ random uniform. Cần nhiều distribution để tránh overfit.

### 4.1. Uniform Euclidean

Sinh tọa độ:

```text
x_i, y_i ~ Uniform(0, 1000)
```

Depot có thể đặt ở:

```text
(500, 500)
```

Distance:

```text
d(i,j) = round(sqrt((x_i-x_j)^2 + (y_i-y_j)^2))
```

Mục tiêu: test dạng ngẫu nhiên tổng quát.

---

### 4.2. Clustered instances

Sinh `C` cụm điểm.

Quy trình:

1. Sinh `C` tâm cụm.
2. Với mỗi điểm, chọn một cụm.
3. Tọa độ điểm = tâm cụm + Gaussian noise.

Gợi ý:

```text
C in [2, 3, 5, 8]
noise_sigma in [20, 40, 80]
```

Mục tiêu: kiểm tra solver có nhận ra cấu trúc cụm không.

---

### 4.3. Line / corridor instances

Điểm nằm gần một đường thẳng hoặc hành lang dài.

Các biến thể:

```text
Depot ở đầu đường
Depot ở giữa đường
Depot lệch khỏi đường
```

Mục tiêu: kiểm tra các thuật toán có chia route hợp lý trên cấu trúc tuyến tính không.

---

### 4.4. Outlier instances

Phần lớn điểm gần depot, một số điểm rất xa.

Ví dụ:

```text
90% điểm nằm trong bán kính nhỏ quanh depot
10% điểm là outlier rất xa
```

Mục tiêu: kiểm tra solver có chia đều các điểm xa không. Đây là nhóm rất quan trọng với objective Min-Max.

---

### 4.5. Ring / circle instances

Điểm nằm trên một hoặc nhiều vòng tròn quanh depot.

Biến thể:

```text
single ring
multi ring
ring + noise
partial arc
```

Mục tiêu: test khả năng routing thứ tự điểm trong cấu trúc hình học vòng.

---

### 4.6. Grid instances

Điểm nằm trên lưới 2D.

Biến thể:

```text
regular grid
grid + noise
missing cells
```

Mục tiêu: test trường hợp nhiều khoảng cách tương đồng, dễ gây tie-breaking xấu.

---

### 4.7. Adversarial / stress instances

Sinh các case cố tình làm khó solver:

```text
N rất lớn, K nhỏ
N nhỏ, K lớn
N không chia đều cho K
một cụm cực dày + một cụm cực xa
depot nằm lệch hẳn khỏi trung tâm
nhiều điểm có khoảng cách gần bằng nhau
một vài điểm cực xa nằm ở các hướng khác nhau
```

Mục tiêu: phát hiện worst-case behavior.

---

## 5. Ma trận benchmark đề xuất

### 5.1. Full benchmark

```text
Distributions: uniform, cluster, line, outlier, ring, grid, adversarial
Size groups:
  tiny:   N=8..16,    K=2..4
  small:  N=20..50,   K=3..8
  medium: N=80..150,  K=5..15
  large:  N=200..500, K=10..30
  stress: N=500..1000,K=5..50
Seeds per group: 10
```

Tổng số case xấp xỉ:

```text
7 distributions × 5 size groups × 10 seeds = 350 cases
```

Có thể tăng lên 700-2000 case nếu thời gian cho phép.

### 5.2. Mini benchmark nếu ít thời gian

```text
Distributions: uniform, cluster, line, outlier, adversarial
Sizes:
  N=30,  K=3
  N=80,  K=5
  N=150, K=10
  N=300, K=20
Seeds per setting: 10
```

Tổng:

```text
5 × 4 × 10 = 200 cases
```

### 5.3. Dev set và holdout set

Cần tách dữ liệu benchmark thành 2 phần:

```text
dev set: dùng để tune solver
holdout set: chỉ dùng để đánh giá cuối
```

Tỷ lệ đề xuất:

```text
70% dev
30% holdout
```

Không nên nhìn kết quả holdout quá nhiều, nếu không sẽ overfit.

---

## 6. Baseline cần có

Ngoài 4 solution của nhóm, nên thêm baseline để so sánh.

### 6.1. Greedy insertion

Baseline đơn giản:

- duyệt từng điểm;
- chèn vào route/vị trí làm tăng objective ít nhất.

Dùng để kiểm tra solution phức tạp có thật sự hơn greedy không.

### 6.2. Greedy + 2-opt

Sau greedy, chạy 2-opt trong từng route.

Dùng để tách hiệu quả của routing improvement.

### 6.3. Random insertion multi-start

Sinh nhiều nghiệm greedy/random khác nhau, lấy nghiệm tốt nhất.

Dùng làm baseline randomized.

### 6.4. OR-Tools baseline, optional

Nếu có thể cài OR-Tools, dùng làm external reference.

Gợi ý chạy:

```text
OR-Tools 1s
OR-Tools 5s
OR-Tools 30s
```

Nếu objective là Min-Max, cần model dimension hoặc cost callback phù hợp. Nếu chưa làm được Min-Max chuẩn, vẫn có thể dùng OR-Tools như heuristic reference, không phải optimum.

### 6.5. Exact solver cho tiny cases

Với `N <= 12` hoặc `N <= 16`, nên có exact hoặc near-exact để lấy optimum.

Một cách:

1. Dùng DP TSP cho mọi subset nhỏ.
2. Dùng DP partition để chia subset cho `K` route sao cho max route nhỏ nhất.

Dùng tiny exact để tính gap-to-optimum.

---

## 7. Validator

File cần viết:

```text
tools/validator.py
```

Validator cần kiểm tra:

1. Output có đúng `K` route không.
2. Mỗi route có độ dài khai báo đúng với số node in ra không.
3. Mỗi route bắt đầu bằng `0`.
4. Mỗi điểm `1..N` xuất hiện đúng một lần.
5. Không có điểm ngoài range `0..N`.
6. Không có điểm `0` xuất hiện giữa route nếu format không cho phép. Nếu muốn cho phép quay về depot ở cuối, bật option riêng.
7. Không thiếu điểm, không trùng điểm.
8. Không crash khi output rỗng hoặc sai format.

Output validator nên trả JSON hoặc dict:

```json
{
  "valid": true,
  "error": null,
  "route_lengths": [120, 100, 90],
  "objective": 120,
  "total_length": 310,
  "std_route_lengths": 12.47
}
```

Nếu invalid:

```json
{
  "valid": false,
  "error": "duplicate node 17"
}
```

---

## 8. Metrics cần lưu

Với mỗi lần chạy solver trên mỗi test case, lưu vào `results/raw_runs.csv`:

```csv
case_id,split,distribution,N,K,seed,solver,language,run_id,time_limit,valid,obj,total_length,std_length,runtime_sec,best_known,gap_to_best,lower_bound,gap_to_lb,error
```

Ý nghĩa:

- `case_id`: tên test case.
- `split`: `dev` hoặc `holdout`.
- `distribution`: uniform/cluster/line/outlier/ring/grid/adversarial.
- `N`, `K`, `seed`: metadata.
- `solver`: tên solver.
- `language`: python/cpp.
- `run_id`: lần chạy thứ mấy, quan trọng với randomized solver.
- `time_limit`: time limit cấp cho solver.
- `valid`: output hợp lệ không.
- `obj`: max route length.
- `total_length`: tổng độ dài các route.
- `std_length`: độ lệch chuẩn độ dài route.
- `runtime_sec`: thời gian chạy thực tế.
- `best_known`: objective tốt nhất giữa các solver/baseline trên case đó.
- `gap_to_best`: gap so với best-known.
- `lower_bound`: lower bound đơn giản hoặc exact optimum nếu có.
- `gap_to_lb`: gap so với lower bound.
- `error`: lỗi nếu invalid/timeout/crash.

Công thức:

```text
gap_to_best = (obj - best_known) / best_known * 100
```

```text
gap_to_lb = (obj - lower_bound) / lower_bound * 100
```

Nếu invalid hoặc timeout, set gap rất lớn hoặc để null nhưng thêm penalty khi ranking.

---

## 9. Lower bound

File cần viết:

```text
tools/lower_bounds.py
```

Mục tiêu: có một cận dưới đơn giản để biết nghiệm còn cách lý tưởng bao xa.

### 9.1. LB1: điểm xa nhất

Nếu route không quay về depot:

```text
LB1 = max_i d(0,i)
```

Nếu route phải quay về depot:

```text
LB1 = max_i 2*d(0,i)
```

### 9.2. LB2: MST/K

Tính MST trên graph đầy đủ gồm depot và các điểm.

```text
LB2 = MST_weight / K
```

### 9.3. LB tổng hợp

```text
LB = max(LB1, LB2)
```

Với tiny cases có exact optimum, dùng exact optimum làm lower bound.

---

## 10. Runner

File cần viết:

```text
tools/runner.py
```

Runner có nhiệm vụ:

1. Load danh sách instances.
2. Load danh sách solvers.
3. Compile C++ nếu cần.
4. Chạy từng solver với từng test.
5. Áp dụng timeout.
6. Capture stdout/stderr.
7. Validate output.
8. Tính metrics.
9. Append vào `raw_runs.csv`.

### 10.1. Command mẫu

```bash
python tools/runner.py \
  --instances instances/dev \
  --solvers solvers/config.json \
  --time-limit 2.0 \
  --runs-per-case 5 \
  --output results/raw_runs.csv
```

### 10.2. Config solver

File:

```text
solvers/config.json
```

Ví dụ:

```json
[
  {
    "name": "sol_a_python",
    "language": "python",
    "cmd": "python solvers/sol_a.py"
  },
  {
    "name": "sol_c_cpp",
    "language": "cpp",
    "source": "solvers/sol_c.cpp",
    "binary": "build/sol_c",
    "cmd": "./build/sol_c"
  },
  {
    "name": "greedy_baseline",
    "language": "python",
    "cmd": "python solvers/baselines/greedy.py"
  }
]
```

### 10.3. Timeout

Dùng `subprocess.run(..., timeout=time_limit + margin)`.

Margin đề xuất:

```text
0.2s cho Python
0.05s cho C++
```

Nhưng khi tính runtime vẫn lấy thời gian thực tế.

Nếu timeout:

```text
valid = false
error = TIMEOUT
```

---

## 11. So sánh công bằng Python và C++

Để benchmark công bằng:

1. Chạy cùng máy.
2. Tắt workload nặng khác.
3. Cùng input.
4. Cùng time limit.
5. Cùng seed nếu solver có random.
6. Mỗi randomized solver chạy nhiều lần.
7. Lưu cả best, mean, median, std.

Gợi ý:

```text
runs_per_case = 5 cho dev
runs_per_case = 10 cho đánh giá cuối nếu có thời gian
```

Với solver randomized, summary nên report:

```text
best objective
mean objective
median objective
std objective
best gap
mean gap
```

---

## 12. Time-limit profile

Cần benchmark ở nhiều mức thời gian:

```text
0.2s
0.5s
1.0s
2.0s
5.0s
```

Command ví dụ:

```bash
for t in 0.2 0.5 1.0 2.0 5.0; do
  python tools/runner.py \
    --instances instances/dev \
    --solvers solvers/config.json \
    --time-limit $t \
    --runs-per-case 3 \
    --output results/raw_runs_t${t}.csv
done
```

Mục tiêu:

- solver nào tốt ở short time;
- solver nào cải thiện khi tăng thời gian;
- solver nào plateau sớm.

---

## 13. Report

File cần viết:

```text
tools/report.py
```

Report sinh các bảng:

### 13.1. Summary by solver

```csv
solver,valid_rate,avg_gap,median_gap,worst_gap,best_count,within_1pct,within_5pct,avg_runtime
```

### 13.2. Summary by distribution

```csv
solver,distribution,avg_gap,median_gap,worst_gap,best_count,valid_rate
```

### 13.3. Summary by size group

```csv
solver,size_group,avg_gap,median_gap,worst_gap,best_count,valid_rate
```

### 13.4. Performance profile

Với mỗi case:

```text
best_known = min objective among valid solvers
ratio = obj / best_known
```

Report:

```csv
solver,best_pct,within_1pct,within_2pct,within_5pct,within_10pct,avg_ratio,worst_ratio
```

Trong đó:

```text
within_5pct = % case solver có obj <= 1.05 * best_known
```

Đây là bảng rất quan trọng để chọn solver cuối.

---

## 14. Hard-case analysis

File report cần sinh:

```text
results/hard_cases.csv
```

Mỗi dòng:

```csv
case_id,distribution,N,K,solver,obj,best_known,gap_to_best,error
```

Chọn các case:

1. Solver thua best-known trên 10%.
2. Solver timeout.
3. Solver invalid.
4. Các case mọi solver đều gap cao so với lower bound.
5. Các case có chênh lệch lớn giữa solvers.

Mục tiêu: dùng hard cases để cải tiến thuật toán.

---

## 15. Visualization

File cần viết:

```text
tools/visualize.py
```

Nếu instance được sinh từ tọa độ Euclidean, lưu kèm metadata tọa độ trong file `.json` hoặc `.meta.json`.

Visualization cần vẽ:

1. Điểm depot bằng marker đặc biệt.
2. Các điểm khách hàng.
3. Màu theo route/bưu tá.
4. Đường nối theo thứ tự route.
5. Highlight route dài nhất.
6. Ghi objective, total length, std length.

Command mẫu:

```bash
python tools/visualize.py \
  --instance instances/dev/outlier/outlier_N200_K10_seed3.in \
  --solution results/solutions/sol_a/outlier_N200_K10_seed3.out \
  --output results/plots/outlier_N200_K10_seed3_sol_a.png
```

Visualization cực kỳ hữu ích để hiểu solver sai ở đâu:

- route bị zigzag;
- một route nhận quá nhiều outlier;
- cụm bị chia sai;
- route dài nhất nằm ở đâu.

---

## 16. Ablation study

Nếu solver chính có nhiều module, cần benchmark từng biến thể.

Ví dụ với solver RL-inspired:

```text
V0: greedy only
V1: greedy + threshold
V2: V1 + relocate descent
V3: V2 + 2-opt
V4: V3 + RL-inspired loop
V5: V4 + swap descent
```

Tạo các flag trong solver:

```bash
python solvers/sol_a.py --no-threshold
python solvers/sol_a.py --no-relocate
python solvers/sol_a.py --no-two-opt
python solvers/sol_a.py --no-rl-loop
python solvers/sol_a.py --no-swap
```

Report ablation:

```csv
variant,avg_gap,median_gap,worst_gap,best_count,avg_runtime
```

Mục tiêu: biết module nào thật sự giúp cải thiện điểm.

---

## 17. Ranking solver cuối

Không chỉ chọn solver có average tốt nhất. Nên ưu tiên theo thứ tự:

1. `valid_rate` cao nhất.
2. `avg_gap` thấp.
3. `median_gap` thấp.
4. `worst_gap` không quá tệ.
5. `timeout_rate` thấp.
6. Runtime ổn định.
7. Performance profile tốt: nhiều case within 1% hoặc 5% best-known.

Công thức ranking nội bộ đề xuất:

```text
score = avg_gap + 0.5 * median_gap + 0.2 * worst_gap + timeout_penalty + invalid_penalty
```

Trong đó:

```text
timeout_penalty = 100 * timeout_rate
invalid_penalty = 1000 * invalid_rate
```

Solver có score thấp hơn tốt hơn.

---

## 18. Command workflow đề xuất

### 18.1. Generate benchmark

```bash
python generators/generate_all.py \
  --output instances \
  --dev-cases 250 \
  --holdout-cases 100 \
  --seed 2026
```

### 18.2. Compile C++ solvers

```bash
python tools/compile_cpp.py --config solvers/config.json
```

### 18.3. Run benchmark dev

```bash
python tools/runner.py \
  --instances instances/dev \
  --solvers solvers/config.json \
  --time-limit 2.0 \
  --runs-per-case 5 \
  --output results/raw_runs_dev.csv
```

### 18.4. Generate report

```bash
python tools/report.py \
  --input results/raw_runs_dev.csv \
  --output-dir results
```

### 18.5. Visualize hard cases

```bash
python tools/visualize.py \
  --hard-cases results/hard_cases.csv \
  --limit 20 \
  --output-dir results/plots
```

### 18.6. Final holdout benchmark

```bash
python tools/runner.py \
  --instances instances/holdout \
  --solvers solvers/config.json \
  --time-limit 2.0 \
  --runs-per-case 10 \
  --output results/raw_runs_holdout.csv

python tools/report.py \
  --input results/raw_runs_holdout.csv \
  --output-dir results/holdout_report
```

---

## 19. Implementation checklist cho Codex

### Phase 1: Core IO và validation

- [ ] Viết parser đọc input instance.
- [ ] Viết parser đọc output solver.
- [ ] Viết `calc_route_length`.
- [ ] Viết `validate_solution`.
- [ ] Viết unit tests cho validator.

### Phase 2: Generators

- [ ] Implement `gen_uniform.py`.
- [ ] Implement `gen_cluster.py`.
- [ ] Implement `gen_line.py`.
- [ ] Implement `gen_outlier.py`.
- [ ] Implement `gen_ring.py`.
- [ ] Implement `gen_grid.py`.
- [ ] Implement `gen_adversarial.py`.
- [ ] Implement `generate_all.py`.
- [ ] Lưu metadata `.json` cho các Euclidean instances.

### Phase 3: Baselines

- [ ] Implement greedy insertion baseline.
- [ ] Implement greedy + 2-opt baseline.
- [ ] Implement random multi-start insertion baseline.
- [ ] Optional: implement OR-Tools baseline.
- [ ] Optional: implement exact solver cho tiny cases.

### Phase 4: Runner

- [ ] Implement solver config JSON.
- [ ] Implement compile C++.
- [ ] Implement subprocess runner.
- [ ] Implement timeout handling.
- [ ] Capture stdout/stderr.
- [ ] Validate output.
- [ ] Ghi raw CSV.

### Phase 5: Metrics và reports

- [ ] Implement lower bound.
- [ ] Tính best-known theo case.
- [ ] Tính gap-to-best.
- [ ] Tính gap-to-lower-bound.
- [ ] Summary by solver.
- [ ] Summary by distribution.
- [ ] Summary by size.
- [ ] Performance profile.
- [ ] Hard-case report.

### Phase 6: Visualization

- [ ] Vẽ scatter điểm.
- [ ] Vẽ route theo màu.
- [ ] Highlight route dài nhất.
- [ ] Save plot PNG.
- [ ] Batch visualize hard cases.

### Phase 7: Ablation

- [ ] Thêm config cho solver variants.
- [ ] Chạy ablation trên dev set.
- [ ] Report variant comparison.

---

## 20. Nguyên tắc quan trọng

1. Không tune quá nhiều trên holdout.
2. Không chỉ nhìn average gap; phải nhìn worst gap và performance profile.
3. Luôn validate output trước khi tính điểm.
4. Với solver randomized, chạy nhiều lần.
5. Log đầy đủ stdout/stderr để debug crash.
6. Giữ benchmark cố định sau khi bắt đầu tune.
7. Mỗi lần cải tiến solver, chạy lại cùng benchmark để so sánh công bằng.
8. Nên lưu hard cases để phân tích sâu.

---

## 21. Kết luận

Benchmark tốt cho bài NP-Hard không chỉ là vài test mẫu. Benchmark cần bao phủ nhiều phân phối dữ liệu, nhiều kích thước, nhiều seed, nhiều time limit và nhiều baseline. Với framework này, nhóm có thể đánh giá 4 solution hiện tại một cách công bằng, phát hiện điểm yếu từng thuật toán, làm ablation study, và chọn solver cuối dựa trên dữ liệu thay vì cảm tính.

Một solver tốt không nhất thiết thắng mọi case, nhưng phải có:

```text
valid_rate cao
avg_gap thấp
median_gap thấp
worst_gap không quá xấu
runtime ổn định
performance profile tốt
```

Đây là hướng benchmark phù hợp cho một bài toán NP-Hard và đủ rõ ràng để Codex tiếp tục triển khai thành code.
