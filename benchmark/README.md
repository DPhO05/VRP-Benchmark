# Benchmark framework for Min-Max VRP / Postman Routing

This folder contains a runnable benchmark for the three team solvers in `Solution/`.

Quick start:

```bash
python3 benchmark/generators/generate_all.py --output benchmark/instances --dev-cases 35 --holdout-cases 14 --seed 2026
python3 benchmark/tools/compile_cpp.py --config benchmark/solvers/config.json
python3 benchmark/tools/runner.py --instances benchmark/instances/dev --solvers benchmark/solvers/config.json --time-limit 5 --runs-per-case 1 --output benchmark/results/raw_runs_dev.csv
python3 benchmark/tools/report.py --input benchmark/results/raw_runs_dev.csv --output-dir benchmark/results --figure-dir Figure
```

Useful outputs:

- `benchmark/results/raw_runs_dev.csv`: one row per solver/case/run.
- `benchmark/results/summary_by_solver.csv`: overall ranking.
- `benchmark/results/summary_by_distribution.csv`: performance by data distribution.
- `benchmark/results/summary_by_size.csv`: performance by size group.
- `benchmark/results/performance_profile.csv`: percentage within 1%, 2%, 5%, 10% of best-known.
- `benchmark/results/hard_cases.csv`: invalid/timeout/bad-gap cases for debugging.
- `Figure/*.png`: bar charts comparing solvers.

The objective is open-route min-max: each route starts at depot `0` and does not need to return to depot.

## Team-only comparison

Use this when the goal is to compare only the three algorithms from `Solution/`:

```bash
python3 benchmark/tools/compile_cpp.py --config benchmark/solvers/config_solution3.json
python3 benchmark/generators/generate_team3_suite.py --output benchmark/instances_solution3 --seeds-per-setting 2 --seed 20260519

for t in 1 3 8; do
  python3 benchmark/tools/runner.py \
    --instances benchmark/instances_solution3/dev \
    --solvers benchmark/solvers/config_solution3.json \
    --time-limit $t \
    --runs-per-case 1 \
    --output benchmark/results/team3_raw_t${t}.csv
done

python3 benchmark/tools/team3_report.py \
  --inputs benchmark/results/team3_raw_t1.csv benchmark/results/team3_raw_t3.csv benchmark/results/team3_raw_t8.csv \
  --output-dir benchmark/results/team3 \
  --figure-dir Figure/team3
```

Outputs:

- `benchmark/results/team3/summary_by_time_limit.csv`
- `benchmark/results/team3/summary_by_NK.csv`
- `benchmark/results/team3/summary_by_distribution.csv`
- `benchmark/results/team3/winner_by_condition.csv`
- `benchmark/results/team3/recommendations.md`
- `Figure/team3/*.png`

`MIP_CBC_ORTools` is capped at `N <= 35` in `config_solution3.json`, because the integer model is meant as a small-instance reference and becomes expensive quickly.
