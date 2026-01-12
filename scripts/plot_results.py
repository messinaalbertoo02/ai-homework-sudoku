# scripts/plot_results.py
from __future__ import annotations

import argparse
from pathlib import Path
import csv
from typing import Dict, List, Tuple, DefaultDict
from collections import defaultdict

import matplotlib.pyplot as plt


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def safe_get(row: Dict[str, str], key: str) -> str:
    v = row.get(key, "")
    return "" if v is None else v


def is_missing(x: str) -> bool:
    x = (x or "").strip().lower()
    return x in ("", "none", "nan", "null")


def to_float(x: str) -> float:
    return float(x)


def group_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def group_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = group_mean(values)
    var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return var ** 0.5


def ensure_outdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def bench_order_from_rows(rows: List[Dict[str, str]]) -> List[str]:
    order: List[str] = []
    for r in rows:
        b = safe_get(r, "benchmark")
        if b and b not in order:
            order.append(b)
    return order


def key_puzzle(row: Dict[str, str]) -> Tuple[str, int]:
    b = safe_get(row, "benchmark")
    i_str = safe_get(row, "puzzle_index")
    i = int(i_str)
    return b, i


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot results from results.csv")
    ap.add_argument("--csv", required=True, help="Path to results CSV")
    ap.add_argument("--outdir", default="results/plots", help="Output directory for plots")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    ensure_outdir(outdir)

    rows = read_csv(csv_path)
    bench_order = bench_order_from_rows(rows)

    # ------------------------------------------------------------
    # Helper: extract runtime lists per (benchmark, series)
    # series are: ("astar","zero"), ("astar","empty"), ("sat","")
    # ------------------------------------------------------------
    def runtimes_for(bench: str, algo: str, heur: str) -> List[float]:
        vals: List[float] = []
        for r in rows:
            if safe_get(r, "benchmark") != bench:
                continue
            if safe_get(r, "algorithm") != algo:
                continue
            rh = safe_get(r, "heuristic")
            if algo == "sat":
                # SAT heuristic might be empty/"None"
                pass
            else:
                if rh != heur:
                    continue
            rt = safe_get(r, "runtime_s")
            if is_missing(rt):
                continue
            vals.append(to_float(rt))
        return vals

    # Plot 1: Runtime mean ± std by benchmark 
    
    series = [
        ("astar", "zero", "A* (h=0)"),
        ("astar", "empty", "A* (h=#empty)"),
        ("sat", "", "SAT"),
    ]

    plt.figure()
    for algo, heur, label in series:
        means: List[float] = []
        stds: List[float] = []
        for bench in bench_order:
            vals = runtimes_for(bench, algo, heur)
            means.append(group_mean(vals))
            stds.append(group_std(vals))
        plt.errorbar(bench_order, means, yerr=stds, marker="o", linewidth=1, label=label)

    plt.xlabel("Benchmark set")
    plt.ylabel("Runtime (s)")
    plt.title("Runtime by benchmark (mean ± std)")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    out1 = outdir / "runtime_by_benchmark.png"
    plt.savefig(out1, dpi=200)
    plt.close()


    # Plot 2: Expanded nodes mean ± std 
    
    plt.figure()
    for algo, heur, label in [("astar", "zero", "A* (h=0)"), ("astar", "empty", "A* (h=#empty)")]:
        means: List[float] = []
        stds: List[float] = []
        for bench in bench_order:
            vals: List[float] = []
            for r in rows:
                if safe_get(r, "benchmark") != bench:
                    continue
                if safe_get(r, "algorithm") != algo:
                    continue
                if safe_get(r, "heuristic") != heur:
                    continue
                ex = safe_get(r, "expanded")
                if is_missing(ex):
                    continue
                vals.append(to_float(ex))
            means.append(group_mean(vals))
            stds.append(group_std(vals))
        plt.errorbar(bench_order, means, yerr=stds, marker="o", linewidth=1, label=label)

    plt.xlabel("Benchmark set")
    plt.ylabel("Expanded nodes")
    plt.title("A* expanded nodes by benchmark (mean ± std)")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    out2 = outdir / "expanded_by_benchmark.png"
    plt.savefig(out2, dpi=200)
    plt.close()


    # Plot 3: Max frontier size mean ± std 
    
    plt.figure()
    for algo, heur, label in [("astar", "zero", "A* (h=0)"), ("astar", "empty", "A* (h=#empty)")]:
        means: List[float] = []
        stds: List[float] = []
        for bench in bench_order:
            vals: List[float] = []
            for r in rows:
                if safe_get(r, "benchmark") != bench:
                    continue
                if safe_get(r, "algorithm") != algo:
                    continue
                if safe_get(r, "heuristic") != heur:
                    continue
                mf = safe_get(r, "max_frontier")
                if is_missing(mf):
                    continue
                vals.append(to_float(mf))
            means.append(group_mean(vals))
            stds.append(group_std(vals))
        plt.errorbar(bench_order, means, yerr=stds, marker="o", linewidth=1, label=label)

    plt.xlabel("Benchmark set")
    plt.ylabel("Max frontier size")
    plt.title("A* max frontier size by benchmark (mean ± std)")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    out3 = outdir / "max_frontier_by_benchmark.png"
    plt.savefig(out3, dpi=200)
    plt.close()


    # Plot 4: Runtime boxplots by benchmark (A* h=0, A* h=#empty, SAT)
    
    for bench in bench_order:
        data = [
            runtimes_for(bench, "astar", "zero"),
            runtimes_for(bench, "astar", "empty"),
            runtimes_for(bench, "sat", ""),
        ]
        labels = ["A* (h=0)", "A* (h=#empty)", "SAT"]

        plt.figure()
        plt.boxplot(data, labels=labels, showfliers=True)
        plt.xlabel("Algorithm")
        plt.ylabel("Runtime (s)")
        plt.title(f"Runtime distribution (boxplot) — {bench}")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        outb = outdir / f"runtime_boxplot_{bench}.png"
        plt.savefig(outb, dpi=200)
        plt.close()

    # Build per-puzzle table for ratio plots & scatter
  
    per_puzzle: Dict[Tuple[str, int], Dict[str, float]] = defaultdict(dict)

    for r in rows:
        b = safe_get(r, "benchmark")
        if not b:
            continue
        pi = int(safe_get(r, "puzzle_index"))
        algo = safe_get(r, "algorithm")
        heur = safe_get(r, "heuristic")
        rt = safe_get(r, "runtime_s")
        if is_missing(rt):
            continue

        key = (b, pi)
        if algo == "sat":
            per_puzzle[key]["sat_rt"] = to_float(rt)
        elif algo == "astar" and heur == "zero":
            per_puzzle[key]["astar0_rt"] = to_float(rt)
            ex = safe_get(r, "expanded")
            if not is_missing(ex):
                per_puzzle[key]["astar0_expanded"] = to_float(ex)
        elif algo == "astar" and heur == "empty":
            per_puzzle[key]["astarE_rt"] = to_float(rt)
            ex = safe_get(r, "expanded")
            if not is_missing(ex):
                per_puzzle[key]["astarE_expanded"] = to_float(ex)


    # Plot 5: Runtime ratio boxplot: (A*/SAT) per benchmark
    # Two ratios: A*(h=0)/SAT and A*(h=#empty)/SAT

    ratio0_by_bench: Dict[str, List[float]] = {b: [] for b in bench_order}
    ratioE_by_bench: Dict[str, List[float]] = {b: [] for b in bench_order}

    for (b, _), d in per_puzzle.items():
        sat = d.get("sat_rt")
        if sat is None or sat <= 0:
            continue

        r0 = d.get("astar0_rt")
        rE = d.get("astarE_rt")
        if r0 is not None:
            ratio0_by_bench[b].append(r0 / sat)
        if rE is not None:
            ratioE_by_bench[b].append(rE / sat)

    # Prepare grouped boxplots:
    # positions like: for each bench i, two boxes at i*3+1 and i*3+2
    data_all: List[List[float]] = []
    positions: List[float] = []
    labels_pos: List[str] = []
    for i, b in enumerate(bench_order):
        base = i * 3
        data_all.append(ratio0_by_bench[b])
        positions.append(base + 1)
        data_all.append(ratioE_by_bench[b])
        positions.append(base + 2)
        labels_pos.append(b)

    plt.figure(figsize=(max(8, 1.6 * len(bench_order)), 5))
    plt.boxplot(data_all, positions=positions, widths=0.6, showfliers=True)
    # Custom x ticks centered on each benchmark group
    xticks = [i * 3 + 1.5 for i in range(len(bench_order))]
    plt.xticks(xticks, labels_pos, rotation=20, ha="right")
    plt.xlabel("Benchmark set")
    plt.ylabel("Runtime ratio (A* / SAT)")
    plt.title("Runtime ratio distribution (A*/SAT) by benchmark")

    plt.text(
        0.02, 0.98,
        "Within each benchmark: left box = A*(h=0)/SAT, right box = A*(h=#empty)/SAT",
        transform=plt.gca().transAxes,
        va="top",
        fontsize=9
    )
    plt.tight_layout()
    out_ratio = outdir / "runtime_ratio_astar_over_sat_boxplot.png"
    plt.savefig(out_ratio, dpi=200)
    plt.close()

    # Plot 6 : Scatter runtime vs expanded nodes (A* only)

    for heur_key, title_suffix in [("astar0", "A* (h=0)"), ("astarE", "A* (h=#empty)")]:
        xs: List[float] = []
        ys: List[float] = []

        exp_key = f"{heur_key}_expanded"
        rt_key = f"{heur_key}_rt"

        for (b, _), d in per_puzzle.items():
            exp = d.get(exp_key)
            rt = d.get(rt_key)
            if exp is None or rt is None:
                continue
            xs.append(exp)
            ys.append(rt)

        plt.figure()
        plt.scatter(xs, ys, s=12)
        plt.xlabel("Expanded nodes")
        plt.ylabel("Runtime (s)")
        plt.title(f"Runtime vs expanded nodes — {title_suffix}")
        plt.tight_layout()
        out_scatter = outdir / f"scatter_runtime_vs_expanded_{heur_key}.png"
        plt.savefig(out_scatter, dpi=200)
        plt.close()

    print(f"Saved plots to: {outdir}")
    print(f"- {out1}")
    print(f"- {out2}")
    print(f"- {out3}")
    print("Additional plots:")
    for bench in bench_order:
        print(f"- {outdir / f'runtime_boxplot_{bench}.png'}")
    print(f"- {out_ratio}")
    print(f"- {outdir / 'scatter_runtime_vs_expanded_astar0.png'}")
    print(f"- {outdir / 'scatter_runtime_vs_expanded_astarE.png'}")


if __name__ == "__main__":
    main()

