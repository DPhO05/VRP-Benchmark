"""
Visualize generated VRP instances.
Vẽ bản đồ tọa độ điểm cho 3 loại phân phối: uniform, cluster, outlier
Lưu ảnh vào Figure/new_version/data_visualization.png
"""
import os
import sys
import math
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR  = os.path.join(ROOT_DIR, "Figure", "new_version")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Tái tạo tọa độ từ dist matrix (dùng MDS đơn giản / lấy lại từ gen) ──
# Vì gen_instance lưu dist matrix chứ không lưu tọa độ,
# ta gen lại tọa độ trực tiếp ở đây với cùng seed.

def euclidean(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))

def gen_coords_uniform(N, seed=42):
    rng = random.Random(seed)
    depot = (500, 500)
    pts   = [(rng.randint(0, 1000), rng.randint(0, 1000)) for _ in range(N)]
    return depot, pts

def gen_coords_cluster(N, seed=42, n_clusters=3):
    rng = random.Random(seed)
    depot   = (500, 500)
    centers = [(rng.randint(150, 850), rng.randint(150, 850)) for _ in range(n_clusters)]
    pts = []
    for _ in range(N):
        cx, cy = rng.choice(centers)
        x = min(1000, max(0, int(rng.gauss(cx, 80))))
        y = min(1000, max(0, int(rng.gauss(cy, 80))))
        pts.append((x, y))
    return depot, pts, centers

def gen_coords_outlier(N, seed=42):
    rng     = random.Random(seed)
    depot   = (500, 500)
    n_out   = max(1, N // 10)
    pts     = []
    for _ in range(N - n_out):
        x = min(1000, max(0, int(rng.gauss(500, 100))))
        y = min(1000, max(0, int(rng.gauss(500, 100))))
        pts.append((x, y))
    outliers = []
    for _ in range(n_out):
        corner = rng.choice([(50,50),(950,50),(50,950),(950,950)])
        x = min(1000, max(0, corner[0] + rng.randint(-30, 30)))
        y = min(1000, max(0, corner[1] + rng.randint(-30, 30)))
        outliers.append((x, y))
    return depot, pts, outliers


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Ba loại phân phối dữ liệu (N=80)
# ════════════════════════════════════════════════════════════════════════════
def plot_distributions():
    N    = 80
    seed = 42
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.patch.set_facecolor("#0f1117")
    titles = ["Uniform", "Cluster", "Outlier"]

    # ── Uniform ──
    ax = axes[0]
    ax.set_facecolor("#1a1d2e")
    depot, pts = gen_coords_uniform(N, seed)
    xs, ys = zip(*pts)
    ax.scatter(xs, ys, s=55, color="#4C72B0", alpha=0.85, zorder=3, label=f"Khách hàng (N={N})")
    ax.scatter(*depot, s=220, color="#FFD700", marker="*", zorder=5, label="Depot")
    ax.set_title("Uniform\nĐiểm phân bố đều ngẫu nhiên", color="white", fontsize=12, fontweight="bold")

    # ── Cluster ──
    ax = axes[1]
    ax.set_facecolor("#1a1d2e")
    depot, pts, centers = gen_coords_cluster(N, seed)
    CLUSTER_COLORS = ["#DD8452", "#55A868", "#C44E52"]
    # assign cluster
    rng = random.Random(seed)
    assigned = [rng.choice(range(len(centers))) for _ in range(N)]
    for ci, color in enumerate(CLUSTER_COLORS):
        cpts = [p for p, a in zip(pts, assigned) if a == ci]
        if cpts:
            cxs, cys = zip(*cpts)
            ax.scatter(cxs, cys, s=55, color=color, alpha=0.85, zorder=3, label=f"Cụm {ci+1}")
    # draw cluster centers
    for ci, (cx, cy) in enumerate(centers):
        ax.scatter(cx, cy, s=160, marker="D", color=CLUSTER_COLORS[ci],
                   edgecolors="white", linewidths=1.5, zorder=4)
    ax.scatter(*depot, s=220, color="#FFD700", marker="*", zorder=5, label="Depot")
    ax.set_title("Cluster\nĐiểm tập trung thành 3 cụm", color="white", fontsize=12, fontweight="bold")

    # ── Outlier ──
    ax = axes[2]
    ax.set_facecolor("#1a1d2e")
    depot, normal_pts, outlier_pts = gen_coords_outlier(N, seed)
    nxs, nys = zip(*normal_pts)
    oxs, oys = zip(*outlier_pts)
    ax.scatter(nxs, nys, s=55, color="#4C72B0", alpha=0.80, zorder=3, label=f"Điểm thường ({len(normal_pts)})")
    ax.scatter(oxs, oys, s=120, color="#FF4C4C", alpha=0.95, zorder=4,
               marker="^", label=f"Outlier xa ({len(outlier_pts)})")
    ax.scatter(*depot, s=220, color="#FFD700", marker="*", zorder=5, label="Depot")
    ax.set_title("Outlier\n90% gần depot, 10% xa ở 4 góc", color="white", fontsize=12, fontweight="bold")

    # ── Common style ──
    for ax in axes:
        ax.set_xlim(-30, 1030)
        ax.set_ylim(-30, 1030)
        ax.set_xlabel("X", color="#aaa", fontsize=10)
        ax.set_ylabel("Y", color="#aaa", fontsize=10)
        ax.tick_params(colors="#888")
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")
        ax.legend(fontsize=9, facecolor="#1a1d2e", edgecolor="#444",
                  labelcolor="white", loc="upper left")
        ax.grid(True, alpha=0.12, color="white")

    fig.suptitle(f"Ba loại phân phối dữ liệu (N={N}, seed={seed})",
                 color="white", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "data_distributions.png")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=160)
    plt.close(fig)
    print(f"Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Scalability: số điểm N tăng dần (uniform, K tỉ lệ)
# ════════════════════════════════════════════════════════════════════════════
def plot_scale_preview():
    configs = [(8, 2), (30, 4), (80, 8), (200, 15)]
    seed    = 42
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
    fig.patch.set_facecolor("#0f1117")

    for ax, (N, K) in zip(axes, configs):
        ax.set_facecolor("#1a1d2e")
        depot, pts = gen_coords_uniform(N, seed)
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=max(6, 60 - N//5), color="#4C72B0", alpha=0.80, zorder=3)
        ax.scatter(*depot, s=200, color="#FFD700", marker="*", zorder=5)
        ax.set_title(f"N={N}, K={K}", color="white", fontsize=12, fontweight="bold")
        ax.set_xlim(-30, 1030)
        ax.set_ylim(-30, 1030)
        ax.tick_params(colors="#888")
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")
        ax.grid(True, alpha=0.10, color="white")
        # annotation
        ax.text(500, -80, f"{N} điểm · {K} bưu tá",
                ha="center", color="#aaa", fontsize=9)

    # legend chung
    from matplotlib.lines import Line2D
    legend_els = [
        Line2D([0],[0], marker='o', color='w', markerfacecolor='#4C72B0',
               markersize=8, label='Khách hàng'),
        Line2D([0],[0], marker='*', color='w', markerfacecolor='#FFD700',
               markersize=12, label='Depot'),
    ]
    fig.legend(handles=legend_els, loc="lower center", ncol=2,
               facecolor="#1a1d2e", edgecolor="#444", labelcolor="white",
               fontsize=10, bbox_to_anchor=(0.5, -0.05))

    fig.suptitle("Scalability Study — Kích thước bài toán tăng dần (Uniform)",
                 color="white", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "data_scale_preview.png")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=160)
    plt.close(fig)
    print(f"Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Stats tổng hợp về dataset: bar chart số instance / loại
# ════════════════════════════════════════════════════════════════════════════
def plot_dataset_stats():
    dataset = {
        "Uniform":  {"N_range": "8–300", "count": 8+5},  # scale + timelimit
        "Cluster":  {"N_range": "8–200", "count": 4},
        "Outlier":  {"N_range": "8–200", "count": 4},
    }
    # đếm thực tế từ configs
    timelimit_count = 5   # 5 seeds
    scale_uniform   = 8
    scale_cluster   = 4
    scale_outlier   = 4

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.patch.set_facecolor("#0f1117")

    # ── Bar 1: số instances theo loại ──
    ax = axes[0]
    ax.set_facecolor("#1a1d2e")
    labels = ["Uniform\n(scale)", "Uniform\n(timelimit)", "Cluster", "Outlier"]
    counts = [scale_uniform, timelimit_count, scale_cluster, scale_outlier]
    colors = ["#4C72B0", "#4C72B0", "#DD8452", "#C44E52"]
    alphas = [1.0, 0.5, 1.0, 1.0]
    bars = ax.bar(labels, counts, color=colors, edgecolor="#444", linewidth=0.8)
    for bar, a in zip(bars, alphas):
        bar.set_alpha(a)
    for bar, c in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                str(c), ha="center", color="white", fontsize=11, fontweight="bold")
    ax.set_ylabel("Số instances", color="#aaa", fontsize=10)
    ax.set_title("Số Test Cases theo Loại", color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.set_ylim(0, 14)
    ax.yaxis.grid(True, alpha=0.2, color="white")
    ax.set_axisbelow(True)

    # ── Bar 2: phân bố theo N ──
    ax = axes[1]
    ax.set_facecolor("#1a1d2e")
    Ns     = [8, 16, 30, 50, 80, 120, 200, 300]
    counts2= [3, 1,  4,  1,  3,  1,   3,   1  ]   # số instance có N này
    colors2= ["#4C72B0" if c==1 else "#55A868" if c==3 else "#DD8452" for c in counts2]
    bars2 = ax.bar([str(n) for n in Ns], counts2, color=colors2, edgecolor="#444")
    for bar, c in zip(bars2, counts2):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(c), ha="center", color="white", fontsize=10)
    ax.set_xlabel("Số điểm N", color="#aaa", fontsize=10)
    ax.set_ylabel("Số instances", color="#aaa", fontsize=10)
    ax.set_title("Phân Bố theo Kích Thước N", color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.set_ylim(0, 5)
    ax.yaxis.grid(True, alpha=0.2, color="white")
    ax.set_axisbelow(True)

    # ── Bar 3: phân bố theo K ──
    ax = axes[2]
    ax.set_facecolor("#1a1d2e")
    Ks     = [2, 4, 5, 8, 10, 15, 20]
    countsK= [3, 6, 1, 3,  1,  3,  1]
    bars3 = ax.bar([str(k) for k in Ks], countsK, color="#C44E52", edgecolor="#444", alpha=0.85)
    for bar, c in zip(bars3, countsK):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(c), ha="center", color="white", fontsize=10)
    ax.set_xlabel("Số bưu tá K", color="#aaa", fontsize=10)
    ax.set_ylabel("Số instances", color="#aaa", fontsize=10)
    ax.set_title("Phân Bố theo Số Bưu Tá K", color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.set_ylim(0, 8)
    ax.yaxis.grid(True, alpha=0.2, color="white")
    ax.set_axisbelow(True)

    fig.suptitle("Tổng Quan Dataset: 21 Instances, 3 Phân Phối, N ∈ [8, 300]",
                 color="white", fontsize=13, fontweight="bold", y=1.03)
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "data_stats_overview.png")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=160)
    plt.close(fig)
    print(f"Saved: {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Distance matrix heatmap (một instance nhỏ N=8)
# ════════════════════════════════════════════════════════════════════════════
def plot_distance_matrix():
    import math
    N, K, seed = 8, 2, 42
    rng   = random.Random(seed)
    depot = (500, 500)
    pts   = [depot] + [(rng.randint(0, 1000), rng.randint(0, 1000)) for _ in range(N)]
    dist  = [[euclidean(pts[i], pts[j]) for j in range(N+1)] for i in range(N+1)]
    D     = np.array(dist)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#0f1117")

    # Heatmap
    ax = axes[0]
    ax.set_facecolor("#1a1d2e")
    im = ax.imshow(D, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(N+1))
    ax.set_yticks(range(N+1))
    labels = ["D"] + [str(i) for i in range(1, N+1)]
    ax.set_xticklabels(labels, color="#ccc", fontsize=9)
    ax.set_yticklabels(labels, color="#ccc", fontsize=9)
    for i in range(N+1):
        for j in range(N+1):
            ax.text(j, i, str(D[i,j]), ha="center", va="center",
                    fontsize=7, color="black" if D[i,j] > D.max()*0.5 else "white")
    plt.colorbar(im, ax=ax, label="Khoảng cách")
    ax.set_title(f"Ma Trận Khoảng Cách (N={N})\nD=Depot, 1–{N}=khách hàng",
                 color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#888")

    # Bản đồ điểm
    ax = axes[1]
    ax.set_facecolor("#1a1d2e")
    xs = [p[0] for p in pts[1:]]
    ys = [p[1] for p in pts[1:]]
    ax.scatter(xs, ys, s=120, color="#4C72B0", zorder=3)
    ax.scatter(*depot, s=280, color="#FFD700", marker="*", zorder=5)
    for i, (x, y) in enumerate(pts[1:], 1):
        ax.annotate(str(i), (x, y), textcoords="offset points",
                    xytext=(8, 6), color="white", fontsize=10)
    ax.annotate("D", depot, textcoords="offset points",
                xytext=(8, 6), color="#FFD700", fontsize=11, fontweight="bold")
    # vẽ edges từ depot đến mọi điểm
    for p in pts[1:]:
        ax.plot([depot[0], p[0]], [depot[1], p[1]],
                color="#555", linewidth=0.8, alpha=0.5, zorder=1)
    ax.set_xlim(-30, 1030)
    ax.set_ylim(-30, 1030)
    ax.set_title(f"Bản Đồ Instance (N={N}, K={K})",
                 color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.grid(True, alpha=0.12, color="white")

    fig.suptitle(f"Ví Dụ Instance Nhỏ: N={N}, K={K}",
                 color="white", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "data_instance_example.png")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=160)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    print(f"Saving all charts to: {FIG_DIR}\n")
    plot_distributions()
    plot_scale_preview()
    plot_dataset_stats()
    plot_distance_matrix()
    print("\n✅ Done! 4 charts saved.")
