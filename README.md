# Benchmark Min-Max VRP / Postman Collecting Packages

Repo này dùng để benchmark các thuật toán trong folder `Solution/` cho bài toán:

- Có `N` điểm cần thu gom và `K` bưu tá.
- Tất cả bưu tá xuất phát từ depot `0`.
- Mỗi điểm `1..N` phải được thăm đúng một lần.
- Route không bắt buộc quay về depot.
- Objective cần minimize là độ dài route lớn nhất trong `K` route.

Input:

```text
N K
d(0,0) d(0,1) ... d(0,N)
...
d(N,0) d(N,1) ... d(N,N)
```

Output hợp lệ:

```text
K
len_route_1
0 ...
len_route_2
0 ...
...
```

## Cấu Trúc Quan Trọng

```text
Solution/
  Greedy_localsearch.cpp
  SA_Algo.cpp
  mip_postman_mip_only_improved.py

13_sample_test/
  inputs/
  outputs/

Test_gen/
  dev/

benchmark/
  tools/
  solvers/
  results/

Figure/
  sample_test/
  bench_mark_overall/
```

Ba thuật toán benchmark hiện tại được khai báo ở:

[benchmark/solvers/config_solution_current3.json](/Users/dphong2005/Desktop/Benchmark/benchmark/solvers/config_solution_current3.json)

Gồm:

- `Greedy_LocalSearch_CPP`: chạy `Solution/Greedy_localsearch.cpp`
- `SA_Algo`: chạy `Solution/SA_Algo.cpp`
- `MIP_CBC_ORTools`: chạy `Solution/mip_postman_mip_only_improved.py`

## Cài Đặt / Dependency

Benchmark dùng:

- `python3`
- `g++` C++17
- `matplotlib` để vẽ biểu đồ
- `ortools` cho MIP

`ortools` đã được cài local trong:

```text
benchmark/.deps/
```

Runner tự thêm thư mục này vào `PYTHONPATH`, nên không cần cài global.

## Compile C++ Solvers

Chạy:

```bash
python3 benchmark/tools/compile_cpp.py \
  --config benchmark/solvers/config_solution_current3.json
```

Binary sẽ nằm trong:

```text
benchmark/build/
```

## Benchmark 13 Test Mẫu

Chạy:

```bash
python3 -B benchmark/tools/runner.py \
  --instances 13_sample_test/inputs \
  --solvers benchmark/solvers/config_solution_current3.json \
  --time-limit 4 \
  --runs-per-case 1 \
  --output benchmark/results/current3_sample_test_t4.csv
```

Sinh report và biểu đồ:

```bash
python3 -B benchmark/tools/team3_report.py \
  --inputs benchmark/results/current3_sample_test_t4.csv \
  --output-dir benchmark/results/current3_sample_test \
  --figure-dir Figure/sample_test \
  --solvers Greedy_LocalSearch_CPP SA_Algo MIP_CBC_ORTools
```

Kết quả:

```text
benchmark/results/current3_sample_test_t4.csv
benchmark/results/current3_sample_test/
Figure/sample_test/
```

## Benchmark Test Sinh Tự Động

Bộ test đã sinh nằm ở:

```text
Test_gen/dev/
```

Tổng hiện tại: `140` test, gồm các dạng:

- `uniform`
- `cluster`
- `line`
- `outlier`
- `ring`
- `grid`
- `adversarial`

Chạy benchmark:

```bash
python3 -B benchmark/tools/runner.py \
  --instances Test_gen/dev \
  --solvers benchmark/solvers/config_solution_current3.json \
  --time-limit 2 \
  --runs-per-case 1 \
  --output benchmark/results/current3_testgen_t2.csv
```

Sinh report và biểu đồ:

```bash
python3 -B benchmark/tools/team3_report.py \
  --inputs benchmark/results/current3_testgen_t2.csv \
  --output-dir benchmark/results/current3_bench_mark_overall \
  --figure-dir Figure/bench_mark_overall \
  --solvers Greedy_LocalSearch_CPP SA_Algo MIP_CBC_ORTools
```

Kết quả:

```text
benchmark/results/current3_testgen_t2.csv
benchmark/results/current3_bench_mark_overall/
Figure/bench_mark_overall/
```

## Ý Nghĩa Các Cột CSV

File raw CSV có các cột chính:

```text
case_id
distribution
N
K
solver
time_limit
valid
obj
runtime_sec
best_known
gap_to_best
lower_bound
gap_to_lb
error
```

Trong đó:

- `obj`: độ dài route lớn nhất.
- `best_known`: objective tốt nhất giữa các solver trong cùng case.
- `gap_to_best`: phần trăm kém hơn best-known.
- `valid`: output có hợp lệ không.
- `error`: timeout, crash, invalid format, hoặc skip.

## Các Biểu Đồ Chính

Sau khi chạy report, mỗi folder figure có:

```text
team3_solver_scorecard.png
team3_quality_ratio_by_N.png
team3_quality_ratio_by_distribution.png
team3_runtime_by_N.png
team3_runtime_by_distribution.png
team3_winner_count_by_distribution.png
team3_winner_count_by_size_group.png
```

Nên xem trước:

- `team3_solver_scorecard.png`: tổng quan chất lượng, runtime, valid rate.
- `team3_quality_ratio_by_distribution.png`: thuật toán nào tốt ở từng dạng dữ liệu.
- `team3_runtime_by_distribution.png`: thuật toán nào chạy nhanh/chậm.

## Validate Một Output Bất Kỳ

Ví dụ:

```bash
python3 -B benchmark/tools/validator.py \
  --instance 13_sample_test/inputs/test2.txt \
  --solution out.txt
```

Validator sẽ trả JSON gồm:

```json
{
  "valid": true,
  "objective": 66,
  "route_lengths": [...]
}
```

## Chạy Một Solver Thủ Công

Ví dụ với `SA_Algo.cpp`:

```bash
g++ -O2 -std=c++17 Solution/SA_Algo.cpp -o sa_algo
./sa_algo < 13_sample_test/inputs/test2.txt > out.txt
python3 -B benchmark/tools/validator.py \
  --instance 13_sample_test/inputs/test2.txt \
  --solution out.txt
```

Ví dụ với `Greedy_localsearch.cpp`:

```bash
g++ -O2 -std=c++17 Solution/Greedy_localsearch.cpp -o greedy_local
./greedy_local < 13_sample_test/inputs/test2.txt > out.txt
```

Ví dụ với MIP:

```bash
python3 Solution/mip_postman_mip_only_improved.py \
  < 13_sample_test/inputs/test1.txt \
  > out.txt
```

## Ghi Chú Về Time Limit

Runner truyền time limit qua biến môi trường:

```text
VRP_TIME_LIMIT_SEC
```

Các C++ solver có hỗ trợ biến này sẽ tự điều chỉnh thời gian chạy.

MIP thường chậm hơn heuristic rất nhiều. Với test lớn, nếu time limit thấp, MIP có thể chỉ tìm được feasible solution hoặc bị skip theo config.

## Tạo Lại Bộ Test Gen

Nếu muốn sinh lại `Test_gen`:

```bash
python3 -B benchmark/generators/generate_team3_suite.py \
  --output Test_gen \
  --seeds-per-setting 2 \
  --seed 20260519
```

Lệnh này sinh test từ tọa độ Euclidean rồi chuyển thành ma trận khoảng cách. File `.json` đi kèm lưu metadata/tọa độ để visualize.

