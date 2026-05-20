# 📊 Báo Cáo Benchmark — Bài Toán Min-Max VRP

> **Dự án:** So sánh hiệu suất các thuật toán giải bài toán phân công tuyến đường cho bưu tá  
> **Ngày chạy:** 20/05/2026  
> **Repo:** [github.com/DPhO05/VRP-Benchmark](https://github.com/DPhO05/VRP-Benchmark)

---

## 1. Bài Toán Cần Giải

### Mô tả

Có **N điểm** cần thu gom bưu kiện và **K bưu tá** xuất phát từ bưu điện (điểm `0`). Biết ma trận khoảng cách `d(i, j)` giữa các điểm.

**Mục tiêu:** Phân chia N điểm cho K bưu tá và sắp xếp thứ tự đi sao cho **quãng đường dài nhất của một bưu tá là nhỏ nhất** (Min-Max objective).

### Định dạng Input / Output

```
Input:
N K
d(0,0) d(0,1) ... d(0,N)
d(1,0) ...
...
d(N,0) ... d(N,N)

Output (ví dụ K=3):
3
4
0 5 2 7       ← Bưu tá 1: đi qua điểm 5→2→7
3
0 1 6         ← Bưu tá 2: đi qua điểm 1→6
4
0 3 4 8       ← Bưu tá 3: đi qua điểm 3→4→8
```

**Objective = max(L₁, L₂, ..., Lₖ)** — muốn minimize giá trị này.

---

## 2. Bốn Thuật Toán Được Benchmark

| # | Tên | Loại | Ngôn ngữ | File |
|---|-----|------|----------|------|
| 1 | **Greedy + Local Search** | Metaheuristic | C++ | `Greedy_localsearch.cpp` |
| 2 | **Simulated Annealing (SA)** | Metaheuristic | C++ | `SA_Algo.cpp` |
| 3 | **Tabu Search** | Metaheuristic | C++ | `Tabu_Search.cpp` |
| 4 | **MIP (CBC/OR-Tools)** | Exact (LP) | Python | `mip_postman_mip_only_improved.py` |

### Tóm tắt từng thuật toán

#### 🔵 Greedy + Local Search
- **Ý tưởng:** Binary search trên giá trị objective, với mỗi giá trị thử → greedy construction → local search
- **Local search moves:** Relocate, Swap, OR-Opt(2), OR-Opt(3), 2-Opt nội tuyến, Intra-Relocate
- **Ưu điểm:** Hội tụ nhanh, ổn định
- **Time limit:** Đọc từ biến môi trường `VRP_TIME_LIMIT_SEC`

#### 🟠 Simulated Annealing (SA)
- **Ý tưởng:** Bắt đầu từ nghiệm greedy → ngẫu nhiên chọn 1 trong 7 moves → chấp nhận nghiệm xấu hơn theo xác suất exp(-Δ/T)
- **Moves:** 2-Opt, Intra-Relocate, Relocate, Swap, OR-Opt(2), OR-Opt(3), Destroy & Repair
- **Ưu điểm:** Thoát local optima tốt, cải thiện đều khi tăng thời gian
- **Time limit:** Vòng lặp kiểm tra `time_up()` liên tục

#### 🟢 Tabu Search
- **Ý tưởng:** Tìm kiếm local với danh sách cấm (tabu list) để tránh lặp nghiệm đã xét
- **Parameters:** Tabu tenure = 50, 50 candidates mỗi vòng
- **Ưu điểm:** Diversification tốt với small N
- **Hạn chế:** Mỗi candidate cần encode thành string → chậm khi N lớn

#### 🔴 MIP (Mixed Integer Programming)
- **Ý tưởng:** Mô hình hóa bài toán thành bài toán tối ưu nguyên tuyến tính, giải bằng CBC solver
- **Objective:** Minimize biến `max_d` = max route length
- **Ưu điểm:** Nghiệm optimal (nếu đủ thời gian)
- **Hạn chế:** Số biến = O(N²×K) → chỉ feasible với N ≤ 30

---

## 3. Thiết Kế Benchmark

### 3.1 Hai nghiên cứu chính

```
Benchmark
├── Study 1: TIME-LIMIT    → Cố định N=30, K=4 — chạy 4 mức thời gian
│                            Hỏi: "Thuật toán nào tốt hơn ở mỗi mức thời gian?"
│
└── Study 2: SCALABILITY   → Tăng N từ 8 → 300 — cố định t=2s
                             Hỏi: "N,K lớn đến đâu thì thuật toán nào 'sập' trước?"
```

### 3.2 Các mức time limit được test

| Time Limit | Ý nghĩa |
|-----------|---------|
| **0.5s** | Ngắn — phản xạ nhanh |
| **1.0s** | Vừa |
| **2.0s** | Chuẩn (mức chính) |
| **5.0s** | Dài — cho phép tìm kiếm sâu |

### 3.3 Các kích thước bài toán (Scalability Study)

| Nhóm | N | K | Phân phối dữ liệu |
|------|---|---|------------------|
| Tiny | 8 | 2 | uniform, cluster, outlier |
| Small | 16, 30 | 4 | uniform, cluster, outlier |
| Medium | 50, 80 | 5, 8 | uniform, cluster, outlier |
| Large | 120, 200 | 10, 15 | uniform, cluster, outlier |
| Stress | 300 | 20 | uniform |

### 3.4 Loại dữ liệu (Instance distribution)

| Loại | Mô tả |
|------|-------|
| **Uniform** | Điểm phân bố đều ngẫu nhiên trong [0, 1000]² |
| **Cluster** | Điểm tập trung thành 3 cụm với nhiễu Gaussian |
| **Outlier** | 90% điểm gần depot, 10% điểm ở 4 góc xa |

### 3.5 Metrics đo lường

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **Objective** | max(L₁..Lₖ) | Quãng đường bưu tá dài nhất |
| **Gap to Best** | (obj − best) / best × 100% | Khoảng cách đến nghiệm tốt nhất |
| **Win Rate** | % lần đạt nghiệm tốt nhất | Độ tin cậy |
| **Runtime** | Thời gian chạy thực tế (giây) | Hiệu quả tính toán |

> **Best Known** = objective nhỏ nhất trong tất cả solver trên cùng 1 instance

---

## 4. Kết Quả

### 4.1 Bảng xếp hạng tổng thể (Leaderboard)

| Hạng | Solver | Win Rate | Avg Gap | Median Gap | Avg Runtime |
|------|--------|----------|---------|------------|-------------|
| 🥇 1 | **SA** | **79.8%** | **0.65%** | 0.00% | 1.87s |
| 🥈 2 | **Greedy_LS** | 77.4% | 0.87% | 0.00% | **0.44s** |
| 🥉 3 | Tabu | 23.8% | 64.6% | 14.71% | 2.17s |
| 4 | MIP | 25.0% | 70.5% | 68.21% | 1.74s |

> **Nhận xét:** SA và Greedy_LS vượt trội hoàn toàn. Greedy_LS nhanh gấp 4 lần SA nhưng chất lượng gần tương đương.

---

### 4.2 Ảnh hưởng của Time Limit

| Solver | t=0.5s | t=1.0s | t=2.0s | t=5.0s | Xu hướng |
|--------|--------|--------|--------|--------|-----------|
| **SA** | 76% | 71% | 81% | **90%** | ✅ Tăng mạnh |
| **Greedy_LS** | 76% | 81% | 76% | 76% | ➡ Ổn định |
| Tabu | 24% | 24% | 24% | 24% | ❌ Plateau |
| MIP | 25% | 25% | 25% | 25% | ❌ Plateau |

**Kết luận:**
- **SA** hưởng lợi nhiều nhất khi tăng thời gian → 90% win rate ở t=5s
- **Greedy_LS** hội tụ rất nhanh (≤ 0.5s), thêm thời gian không giúp ích nhiều
- **Tabu** plateau sớm do overhead encode solution khi N lớn
- **MIP** bị giới hạn bởi số biến, thêm thời gian chỉ cải thiện nhẹ

---

### 4.3 Giới Hạn Khi Tăng Kích Thước (Scalability)

| N | Greedy_LS | SA | Tabu | MIP |
|---|-----------|-----|------|-----|
| 8 | ✅ Tốt | ✅ Tốt | ✅ Tốt | ✅ Optimal |
| 30 | ✅ Tốt | ✅ Tốt | ✅ Khá | ⚠️ Khá |
| 80 | ✅ Tốt | ✅ Tốt | ⚠️ Kém hơn | ❌ Bỏ qua |
| 200 | ✅ Ổn định | ✅ Tốt | ⚠️ Gap cao | ❌ Bỏ qua |
| 300 | ✅ Ổn định | ✅ Tốt | ❌ Gap rất cao | ❌ Bỏ qua |

**MIP chỉ khả dụng với N ≤ 30** (số biến = O(N²×K) tăng bậc hai).

**Tabu bắt đầu suy giảm từ N ≥ 80** vì:
- Mỗi iteration phải encode toàn bộ solution thành string
- Hash lookup trong tabu list tốn O(N×K) mỗi candidate
- 50 candidates × nhiều iter = bottleneck rõ rệt

---

### 4.4 Hiệu suất theo Loại Dữ Liệu

| Solver | Uniform | Cluster | Outlier |
|--------|---------|---------|---------|
| **SA** | 🏆 Tốt | 🏆 Tốt | 🏆 Tốt |
| **Greedy_LS** | 🏆 Tốt | 🏆 Tốt | 🏆 Tốt |
| Tabu | ⚠️ Kém | ⚠️ Kém | ⚠️ Kém |
| MIP | ⚠️ Kém | ⚠️ Kém | ⚠️ Kém |

**Outlier instances** là loại khó nhất — các điểm xa buộc phải gán bưu tá riêng, tạo imbalance.

---

## 5. Biểu Đồ So Sánh

> Tất cả ảnh lưu tại: `Figure/new_version/`

| File | Nội dung |
|------|---------|
| `1_timelimit_comparison.png` | Objective trung bình theo mức time limit |
| `2_scalability_objective.png` | Objective vs N (t=2s) |
| `3_scalability_runtime.png` | Runtime vs N — thấy rõ MIP không scale |
| `4_winrate_heatmap.png` | Heatmap % thắng theo solver × time limit |
| `5_boxplot_by_distribution.png` | Phân phối objective theo loại dữ liệu |
| `6_improvement_over_time.png` | Mức cải thiện (%) khi tăng time limit |

---

## 6. Cách Chạy Lại Benchmark

### Yêu cầu
```bash
g++ --version   # Apple clang 17+ hoặc g++ 11+
python3 -m pip install matplotlib pandas ortools
```

### Chạy toàn bộ (3 lệnh)
```bash
# Bước 1: Compile
g++ -O2 -std=c++17 -o simple_bench/build/greedy Solution/Greedy_localsearch.cpp
g++ -O2 -std=c++17 -o simple_bench/build/sa     Solution/SA_Algo.cpp
g++ -O2 -std=c++17 -I simple_bench/build \
    -o simple_bench/build/tabu simple_bench/build/tabu_fixed.cpp

# Bước 2: Chạy benchmark
python3 -B simple_bench/run_benchmark.py

# Bước 3: Vẽ biểu đồ
python3 -B simple_bench/plot_results.py
```

---

## 7. Kết Luận

### Khuyến nghị sử dụng

| Tiêu chí | Khuyến nghị |
|----------|------------|
| **Chất lượng cao nhất** | **SA** — win rate 90% tại t=5s |
| **Nhanh nhất** | **Greedy_LS** — hội tụ trong < 0.5s |
| **Cân bằng** | **SA với t=2s** — tốt cho production |
| **Bài nhỏ (N≤12)** | MIP — cho kết quả optimal |

### Giới hạn thực tế

| Solver | Giới hạn |
|--------|---------|
| **SA** | Cần thời gian đủ dài (≥ 1s) để phát huy |
| **Greedy_LS** | Plateau sớm — thêm thời gian không giúp nhiều |
| **Tabu** | Không scale tốt với N ≥ 80 |
| **MIP** | Chỉ dùng được với N ≤ 30 |

### Phát hiện chính

> ✅ **SA và Greedy_LS** đều cho gap < 1% so với best-known trên hầu hết các instance  
> ❌ **Tabu** có kiến trúc tốt nhưng implementation hiện tại không tối ưu cho bài lớn  
> 💡 **Greedy_LS** là lựa chọn pragmatic nhất: nhanh, ổn định, chất lượng gần tối ưu

---

## 8. Cấu Trúc Thư Mục

```
VRP-Benchmark/
├── Solution/                    ← Code 4 thuật toán
│   ├── Greedy_localsearch.cpp
│   ├── SA_Algo.cpp
│   ├── Tabu_Search.cpp
│   └── mip_postman_mip_only_improved.py
│
├── simple_bench/                ← Benchmark framework
│   ├── gen_instance.py          → Sinh instances
│   ├── run_benchmark.py         → Chạy tất cả solver
│   ├── plot_results.py          → Vẽ biểu đồ
│   ├── instances/               → 21 test cases
│   └── results/
│       ├── raw_results.csv           → 300 lần chạy
│       ├── leaderboard.csv           → Xếp hạng tổng
│       ├── summary_by_solver_timelimit.csv
│       ├── summary_by_solver_dist.csv
│       ├── summary_by_solver_scale.csv
│       └── per_instance_t2s.csv
│
└── Figure/new_version/          ← 6 biểu đồ PNG
```

---

*Benchmark chạy trên macOS, single-threaded, cùng máy để đảm bảo so sánh công bằng.*
