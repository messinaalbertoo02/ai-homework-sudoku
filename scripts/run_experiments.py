# scripts/run_experiments.py
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Dict, List

from sudoku.core import parse_puzzle, SudokuProblem
from sudoku.astar import astar
from sudoku.sat import solve_sudoku_sat


def load_puzzles(path: Path) -> List[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines


def run_astar(problem: SudokuProblem, heuristic_name: str) -> Dict:
    if heuristic_name == "zero":
        h = problem.heuristic_zero
    elif heuristic_name == "empty":
        h = problem.heuristic_empty_cells
    else:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    res = astar(
        start=problem.initial_state(),
        is_goal=problem.is_goal,
        successors=problem.successors,
        heuristic=h,
    )

    return {
        "found": res.found,
        "cost": res.cost,
        "expanded": res.expanded,
        "generated": res.generated,
        "max_frontier": res.max_frontier,
        "max_closed": res.max_closed,
        "runtime_s": res.runtime_s,
    }


def run_sat(state) -> Dict:
    res = solve_sudoku_sat(state)
    return {
        "found": res.sat,
        "cost": None,              # not meaningful for SAT
        "expanded": None,
        "generated": None,
        "max_frontier": None,
        "max_closed": None,
        "runtime_s": res.runtime_s,
    }


def main():
    ap = argparse.ArgumentParser(description="Run A* and SAT experiments on Sudoku benchmarks.")
    ap.add_argument(
        "--benchmarks",
        nargs="+",
        required=True,
        help="List of benchmark files (each file: one puzzle per line).",
    )
    ap.add_argument(
        "--out",
        type=str,
        default="results/results.csv",
        help="Output CSV path.",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of puzzles per benchmark (for quick tests).",
    )
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "benchmark",
        "puzzle_index",
        "algorithm",
        "heuristic",
        "found",
        "cost",
        "expanded",
        "generated",
        "max_frontier",
        "max_closed",
        "runtime_s",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for bench in args.benchmarks:
            bench_path = Path(bench)
            puzzles = load_puzzles(bench_path)
            if args.limit is not None:
                puzzles = puzzles[: args.limit]

            print(f"\n=== Benchmark: {bench_path.name} ({len(puzzles)} puzzles) ===")

            for i, pzl in enumerate(puzzles):
                try:
                    state = parse_puzzle(pzl)
                except Exception as e:
                    print(f"[SKIP] Puzzle {i}: invalid ({e})")
                    continue

                problem = SudokuProblem(state)

                # --- A* with h = 0 ---
                r = run_astar(problem, heuristic_name="zero")
                writer.writerow({
                    "benchmark": bench_path.name,
                    "puzzle_index": i,
                    "algorithm": "astar",
                    "heuristic": "zero",
                    **r,
                })

                # --- A* with h = empty-cells ---
                r = run_astar(problem, heuristic_name="empty")
                writer.writerow({
                    "benchmark": bench_path.name,
                    "puzzle_index": i,
                    "algorithm": "astar",
                    "heuristic": "empty",
                    **r,
                })

                # --- SAT ---
                r = run_sat(state)
                writer.writerow({
                    "benchmark": bench_path.name,
                    "puzzle_index": i,
                    "algorithm": "sat",
                    "heuristic": None,
                    **r,
                })

                if (i + 1) % 10 == 0:
                    print(f"  processed {i+1}/{len(puzzles)}")

    print(f"\nDone. Results written to: {out_path}")


if __name__ == "__main__":
    main()

