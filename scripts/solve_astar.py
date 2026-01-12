# scripts/solve_astar.py
from __future__ import annotations

import argparse
from pathlib import Path

from sudoku.core import parse_puzzle, format_grid, SudokuProblem, is_valid_state
from sudoku.astar import astar


def load_puzzle(path: str | None, puzzle_str: str | None) -> str:
    if puzzle_str and puzzle_str.strip():
        return puzzle_str
    if path:
        return Path(path).read_text(encoding="utf-8")
    raise ValueError("Provide either --puzzle-string or --puzzle-file")


def main() -> None:
    ap = argparse.ArgumentParser(description="Solve Sudoku with A* (Homework AI).")
    ap.add_argument("--index", type=int, default=0, help="Which puzzle (line index) to solve from a multi-line benchmark file.")
    ap.add_argument("--puzzle-file", type=str, default=None, help="Path to a puzzle text file (81 chars, . or 0 for empty).")
    ap.add_argument("--puzzle-string", type=str, default=None, help="Puzzle as a raw string (81 chars, . or 0 for empty).")
    ap.add_argument("--heur", type=str, choices=["zero", "empty"], default="empty", help="Heuristic: zero or empty-cells.")
    args = ap.parse_args()
    
    puzzle_text = load_puzzle(args.puzzle_file, args.puzzle_string)

    # If a benchmark file contains multiple puzzles (one per line), pick one.
    lines = [ln.strip() for ln in puzzle_text.splitlines() if ln.strip()]
    if len(lines) == 1:
        puzzle_one = lines[0]
    else:
        if args.index < 0 or args.index >= len(lines):
            raise ValueError(f"--index out of range. File has {len(lines)} puzzles (0..{len(lines)-1}).")
        puzzle_one = lines[args.index]

    start = parse_puzzle(puzzle_one)

    prob = SudokuProblem(start)

    if args.heur == "zero":
        h = prob.heuristic_zero
    else:
        h = prob.heuristic_empty_cells

    res = astar(
        start=prob.initial_state(),
        is_goal=prob.is_goal,
        successors=prob.successors,
        heuristic=h,
    )

    print("=== A* Result ===")
    print("Found:", res.found)
    print("Cost:", res.cost)
    print("Expanded:", res.expanded)
    print("Generated:", res.generated)
    print("Max frontier:", res.max_frontier)
    print("Max closed:", res.max_closed)
    print("Runtime (s):", f"{res.runtime_s:.6f}")

    if res.found:
        sol = res.path[-1]
        print("\n=== Solution ===")
        print(format_grid(sol))
        print("\nValid solution:", is_valid_state(sol) and all(v != 0 for v in sol))


if __name__ == "__main__":
    main()

