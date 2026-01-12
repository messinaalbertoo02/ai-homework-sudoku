from __future__ import annotations

import argparse
from pathlib import Path

from sudoku.core import parse_puzzle, format_grid, is_valid_state
from sudoku.sat import solve_sudoku_sat


def load_one_puzzle(path: str, index: int) -> str:
    lines = [ln.strip() for ln in Path(path).read_text().splitlines() if ln.strip()]
    if index < 0 or index >= len(lines):
        raise ValueError(f"Index out of range: file has {len(lines)} puzzles")
    return lines[index]


def main():
    ap = argparse.ArgumentParser(description="Solve Sudoku via SAT (PySAT).")
    ap.add_argument("--puzzle-file", type=str, required=True)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--solver", type=str, default="glucose3")
    args = ap.parse_args()

    puzzle_str = load_one_puzzle(args.puzzle_file, args.index)
    start = parse_puzzle(puzzle_str)

    print("=== Input ===")
    print(format_grid(start))

    res = solve_sudoku_sat(start, solver_name=args.solver)

    print("\n=== SAT Result ===")
    print("SAT:", res.sat)
    print("Runtime (s):", f"{res.runtime_s:.6f}")

    if res.sat:
        print("\n=== Solution ===")
        print(format_grid(res.solution))
        print("Valid solution:", is_valid_state(res.solution) and all(v != 0 for v in res.solution))


if __name__ == "__main__":
    main()

