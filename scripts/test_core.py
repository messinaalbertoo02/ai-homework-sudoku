# scripts/test_core.py
from sudoku.core import parse_puzzle, format_grid, SudokuProblem

# Un puzzle facile ('.' = vuoto). Puoi sostituirlo con uno di Norvig.
PUZZLE = """
53..7....
6..195...
.98....6.
8...6...3
4..8.3..1
7...2...6
.6....28.
...419..5
....8..79
"""

def main():
    s0 = parse_puzzle(PUZZLE)
    print("Initial:")
    print(format_grid(s0))

    prob = SudokuProblem(s0)
    succ = prob.successors(s0)
    print("\n#successors from start (MRV):", len(succ))
    if succ:
        print("\nExample successor:")
        print(format_grid(succ[0][0]))
        print("heuristic_empty_cells:", prob.heuristic_empty_cells(succ[0][0]))

if __name__ == "__main__":
    main()
