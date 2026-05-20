"""
Plot benchmark results and save to Figure/new_version/
Charts:
  1. Time-limit comparison (bar per solver per time limit)
  2. Scalability: objective vs N for each solver
  3. Scalability: runtime vs N for each solver
  4. Win-rate heatmap (solver × time_limit)
  5. Box plot: objective distribution per solver per distribution type
"""
import os, sys, csv, math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR  = os.path.join(ROOT_DIR, "Figure", "new_version")
RES_DIR  = os.path.join(BASE_DIR, "results")
CSV_PATH = os.path.join(RES_DIR, "raw_results.csv")

os.makedirs(FIG_DIR, exist_ok=True)

# ── Style ──────────────────────────────────────
SOLVER_COLORS = {
    "Greedy_LS": "#4C72B0",
    "SA":        "#DD8452",
    "Tabu":      "#55A868",
    "MIP":       "#C44E52",
}
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def load(csv_path):
    df = pd.read_csv(csv_path)
    df["objective"] = pd.to_numeric(df["objective"], errors="coerce")
    df["runtime"]   = pd.to_numeric(df["runtime"],   errors="coerce")
    return df


# ── Chart 1: Time-limit — avg objective per solver ──
def plot_timelimit(df, fig_dir):
    sub = df[(df["study"] == "timelimit") & (df["status"] == "OK")].copy()
    if sub.empty:
        print("  [skip] No timelimit data"); return

    grouped = sub.groupby(["solver","time_limit"])["objective"].mean().reset_index()
    time_limits = sorted(grouped["time_limit"].unique())
    solvers = sorted(grouped["solver"].unique())

    x = np.arange(len(time_limits))
    w = 0.8 / len(solvers)

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, sv in enumerate(solvers):
        vals = [grouped[(grouped["solver"]==sv) & (grouped["time_limit"]==t)]["objective"].values
                for t in time_limits]
        vals = [v[0] if len(v) else np.nan for v in vals]
        bars = ax.bar(x + i*w - 0.4 + w/2, vals, w*0.9,
                      label=sv, color=SOLVER_COLORS.get(sv, "#888"),
                      alpha=0.85, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{t}s" for t in time_limits])
    ax.set_xlabel("Time Limit", fontsize=12)
    ax.set_ylabel("Avg Objective (Max Route Length)", fontsize=12)
    ax.set_title("Chất lượng nghiệm theo Time Limit\n(thấp hơn = tốt hơn)", fontsize=13, fontweight="bold")
    ax.legend(title="Solver", fontsize=10)
    ax.yaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout()
    path = os.path.join(fig_dir, "1_timelimit_comparison.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Chart 2: Scalability — objective vs N ──
def plot_scale_obj(df, fig_dir):
    sub = df[(df["study"] == "scale") & (df["status"] == "OK") & (df["time_limit"] == 2.0)].copy()
    if sub.empty:
        # try any time_limit
        sub = df[(df["study"] == "scale") & (df["status"] == "OK")].copy()
        if sub.empty:
            print("  [skip] No scale data"); return
        sub = sub.groupby(["solver","N","K"])["objective"].mean().reset_index()
    else:
        sub = sub.groupby(["solver","N","K"])["objective"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    for sv in sorted(sub["solver"].unique()):
        d = sub[sub["solver"]==sv].sort_values("N")
        ax.plot(d["N"], d["objective"], "o-", label=sv,
                color=SOLVER_COLORS.get(sv, "#888"), linewidth=2, markersize=6)

    ax.set_xlabel("Số điểm N", fontsize=12)
    ax.set_ylabel("Objective (Max Route Length)", fontsize=12)
    ax.set_title("Chất lượng nghiệm theo kích thước bài toán (t=2s)\n(thấp hơn = tốt hơn)",
                 fontsize=13, fontweight="bold")
    ax.legend(title="Solver", fontsize=10)
    ax.yaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout()
    path = os.path.join(fig_dir, "2_scalability_objective.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Chart 3: Scalability — runtime vs N ──
def plot_scale_runtime(df, fig_dir):
    sub = df[(df["study"] == "scale") & (df["time_limit"] == 2.0)].copy()
    if sub.empty:
        sub = df[df["study"] == "scale"].copy()
    if sub.empty:
        print("  [skip] No scale runtime data"); return

    grp = sub.groupby(["solver","N"])["runtime"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    for sv in sorted(grp["solver"].unique()):
        d = grp[grp["solver"]==sv].sort_values("N")
        ax.plot(d["N"], d["runtime"], "s--", label=sv,
                color=SOLVER_COLORS.get(sv, "#888"), linewidth=2, markersize=6)

    ax.axhline(2.0, color="red", linestyle=":", linewidth=1.5, label="Time limit 2s")
    ax.set_xlabel("Số điểm N", fontsize=12)
    ax.set_ylabel("Runtime thực tế (giây)", fontsize=12)
    ax.set_title("Runtime theo kích thước bài toán\n(đường đỏ = time limit 2s)",
                 fontsize=13, fontweight="bold")
    ax.legend(title="Solver", fontsize=10)
    ax.yaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout()
    path = os.path.join(fig_dir, "3_scalability_runtime.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Chart 4: Win-rate table (solver × time_limit) ──
def plot_winrate(df, fig_dir):
    ok = df[df["status"] == "OK"].copy()
    if ok.empty:
        print("  [skip] No OK data for winrate"); return

    # Best (min) objective per (instance, time_limit)
    best = ok.groupby(["instance","time_limit"])["objective"].transform("min")
    ok = ok.copy()
    ok["is_best"] = (ok["objective"] - best).abs() < 0.5

    pivot = ok.groupby(["solver","time_limit"])["is_best"].mean().unstack(fill_value=0) * 100
    solvers = pivot.index.tolist()
    time_limits = pivot.columns.tolist()

    fig, ax = plt.subplots(figsize=(7, max(3, len(solvers)*0.9 + 1)))
    im = ax.imshow(pivot.values, cmap="YlGn", vmin=0, vmax=100, aspect="auto")

    ax.set_xticks(range(len(time_limits)))
    ax.set_xticklabels([f"{t}s" for t in time_limits])
    ax.set_yticks(range(len(solvers)))
    ax.set_yticklabels(solvers)
    ax.set_xlabel("Time Limit", fontsize=11)
    ax.set_title("Win-Rate (%) — % lần solver đạt nghiệm tốt nhất\n(xanh đậm = thắng nhiều hơn)",
                 fontsize=12, fontweight="bold")

    for i in range(len(solvers)):
        for j in range(len(time_limits)):
            ax.text(j, i, f"{pivot.values[i,j]:.0f}%",
                    ha="center", va="center", fontsize=11, fontweight="bold",
                    color="black" if pivot.values[i,j] < 65 else "white")

    plt.colorbar(im, ax=ax, label="Win %")
    fig.tight_layout()
    path = os.path.join(fig_dir, "4_winrate_heatmap.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Chart 5: Box plot per distribution type ──
def plot_boxplot_dist(df, fig_dir):
    ok = df[(df["status"] == "OK") & (df["time_limit"] == 2.0)].copy()
    if ok.empty:
        ok = df[df["status"] == "OK"].copy()
    if ok.empty:
        print("  [skip] No data for boxplot"); return

    dist_types = sorted(ok["dist"].unique())
    solvers = sorted(ok["solver"].unique())

    fig, axes = plt.subplots(1, len(dist_types), figsize=(5*len(dist_types), 5), sharey=False)
    if len(dist_types) == 1:
        axes = [axes]

    for ax, dt in zip(axes, dist_types):
        data = [ok[(ok["dist"]==dt) & (ok["solver"]==sv)]["objective"].dropna().values
                for sv in solvers]
        data = [d for d in data]
        bp = ax.boxplot(data, patch_artist=True, notch=False,
                        medianprops=dict(color="black", linewidth=2))
        for patch, sv in zip(bp["boxes"], solvers):
            patch.set_facecolor(SOLVER_COLORS.get(sv, "#888"))
            patch.set_alpha(0.75)
        ax.set_title(f"Phân phối: {dt}", fontsize=11, fontweight="bold")
        ax.set_xticks(range(1, len(solvers)+1))
        ax.set_xticklabels(solvers, rotation=20, ha="right", fontsize=9)
        ax.set_ylabel("Objective" if ax == axes[0] else "")
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

    patches = [mpatches.Patch(color=SOLVER_COLORS.get(sv,"#888"), label=sv) for sv in solvers]
    fig.legend(handles=patches, title="Solver", loc="upper right", fontsize=9)
    fig.suptitle("Objective theo phân phối dữ liệu (t=2s)\n(thấp hơn = tốt hơn)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    path = os.path.join(fig_dir, "5_boxplot_by_distribution.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Chart 6: Gap improvement over time (for uniform, N=30) ──
def plot_improvement_over_time(df, fig_dir):
    sub = df[(df["dist"]=="uniform") & (df["N"]==30) & (df["status"]=="OK")].copy()
    if sub.empty:
        print("  [skip] No improvement data"); return

    tl_sorted = sorted(sub["time_limit"].unique())
    solvers = sorted(sub["solver"].unique())

    # Normalize: compute ratio to best overall per instance×time_limit
    # Group by solver × time_limit → mean objective
    grp = sub.groupby(["solver","time_limit"])["objective"].mean().reset_index()

    # relative improvement from shortest time
    fig, ax = plt.subplots(figsize=(8, 5))
    for sv in solvers:
        d = grp[grp["solver"]==sv].sort_values("time_limit")
        if d.empty: continue
        base = d.iloc[0]["objective"]
        if base == 0: continue
        improvement = ((base - d["objective"]) / base * 100).values
        ax.plot(d["time_limit"].values, improvement, "o-", label=sv,
                color=SOLVER_COLORS.get(sv,"#888"), linewidth=2, markersize=7)

    ax.set_xlabel("Time Limit (s)", fontsize=12)
    ax.set_ylabel("Cải thiện so với t=0.5s (%)", fontsize=12)
    ax.set_title("Mức độ cải thiện khi tăng time limit\n(N=30, uniform — cao hơn = cải thiện nhiều hơn)",
                 fontsize=13, fontweight="bold")
    ax.legend(title="Solver", fontsize=10)
    ax.yaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)
    ax.axhline(0, color="gray", linewidth=0.8)

    fig.tight_layout()
    path = os.path.join(fig_dir, "6_improvement_over_time.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Run run_benchmark.py first.")
        sys.exit(1)

    df = load(CSV_PATH)
    print(f"Loaded {len(df)} rows from {CSV_PATH}")
    print(f"Solvers: {df['solver'].unique().tolist()}")
    print(f"Studies: {df['study'].unique().tolist()}\n")
    print(f"Saving charts to: {FIG_DIR}\n")

    plot_timelimit(df, FIG_DIR)
    plot_scale_obj(df, FIG_DIR)
    plot_scale_runtime(df, FIG_DIR)
    plot_winrate(df, FIG_DIR)
    plot_boxplot_dist(df, FIG_DIR)
    plot_improvement_over_time(df, FIG_DIR)

    print(f"\n✅ All charts saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
