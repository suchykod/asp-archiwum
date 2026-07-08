"""
dot_clusters.py

Generates N random cluster centers on a canvas, each with a distinct color.
Points are simple filled circles with gaussian density — dense at the core,
sparse at the edges. No transparency.

Output: dot_clusters.png
"""

import numpy as np
import matplotlib.pyplot as plt
import random
import os

# ── settings ─────────────────────────────────────────────────────────────────
TOTAL_POINTS  = 7000
N_CLUSTERS    = 7
CORE_FRACTION = 0.60   # fraction of points in the tight core (0.0–1.0)
HALO_RADIUS   = 0.40   # spread of the outer halo (canvas units, 0–1)
POINT_SIZE    = 1.5    # dot radius in points
WIDTH, HEIGHT = 14, 9  # canvas size in inches
DPI           = 150
BG_COLOR      = "#FDF5F0"

PALETTE = [
    "#C0392B", "#E67E22", "#D4AC0D", "#27AE60",
    "#2980B9", "#8E44AD", "#E91E8C", "#16A085",
    "#F39C12", "#1ABC9C", "#2C3E50", "#E74C3C",
]

# ── helpers ───────────────────────────────────────────────────────────────────
def random_centers(n, margin=0.10, min_dist=0.20):
    centers = []
    for _ in range(100_000):
        x = random.uniform(margin, 1 - margin)
        y = random.uniform(margin, 1 - margin)
        if all(np.hypot(x - cx, y - cy) > min_dist for cx, cy in centers):
            centers.append((x, y))
        if len(centers) == n:
            break
    return centers


def gaussian_cloud(cx, cy, n, sigma):
    xs = np.random.normal(cx, sigma, n)
    ys = np.random.normal(cy, sigma, n)
    return xs, ys


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    fig, ax = plt.subplots(figsize=(WIDTH, HEIGHT), dpi=DPI)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    centers = random_centers(N_CLUSTERS)
    colors  = random.sample(PALETTE, N_CLUSTERS)

    weights = np.random.dirichlet(np.ones(N_CLUSTERS))
    counts  = (weights * TOTAL_POINTS).astype(int)
    counts[-1] += TOTAL_POINTS - counts.sum()

    for (cx, cy), color, n in zip(centers, colors, counts):
        n_core = int(n * CORE_FRACTION)
        n_halo = n - n_core

        # tight core
        xs, ys = gaussian_cloud(cx, cy, n_core, HALO_RADIUS * 0.18)
        ax.scatter(xs, ys, s=POINT_SIZE, c=color, linewidths=0, alpha=1.0, zorder=2)

        # sparse halo
        xs, ys = gaussian_cloud(cx, cy, n_halo, HALO_RADIUS * 0.55)
        ax.scatter(xs, ys, s=POINT_SIZE, c=color, linewidths=0, alpha=1.0, zorder=2)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dot_clusters.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"Saved → {out}")


if __name__ == "__main__":
    main()