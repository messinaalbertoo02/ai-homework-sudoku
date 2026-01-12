# sudoku/sat.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from sudoku.core import State, is_valid_state

# PySAT imports 
from pysat.formula import CNF
from pysat.solvers import Solver


def var_id(r: int, c: int, v: int) -> int:
    if not (1 <= r <= 9 and 1 <= c <= 9 and 1 <= v <= 9):
        raise ValueError("r,c,v must be in 1..9")
    return (r - 1) * 81 + (c - 1) * 9 + v  # 1..729


def inv_var_id(x: int) -> Tuple[int, int, int]:
    """Inverse mapping of var_id."""
    if not (1 <= x <= 729):
        raise ValueError("var id must be in 1..729")
    x0 = x - 1
    r = x0 // 81
    rem = x0 % 81
    c = rem // 9
    v = rem % 9
    return r + 1, c + 1, v + 1


def exactly_one(cnf: CNF, lits: List[int]) -> None:
    """
    Add CNF clauses enforcing exactly one of the literals is True:
      - at least one
      - at most one (pairwise)
    """
    if not lits:
        # no variable can be true -> UNSAT, encode by empty clause
        cnf.append([])
        return
    # at least one
    cnf.append(lits[:])
    # at most one (pairwise)
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            cnf.append([-lits[i], -lits[j]])


def sudoku_to_cnf(state: State) -> CNF:
    """
    Encode a 9x9 Sudoku into CNF:
    Variables: X_{r,c,v} meaning cell (r,c) has value v.

    Constraints:
    1) Each cell has exactly one value.
    2) Each row has each value exactly once.
    3) Each column has each value exactly once.
    4) Each 3x3 box has each value exactly once.
    5) Clues are enforced as unit clauses.
    """
    if len(state) != 81:
        raise ValueError("State must have length 81")

    if not is_valid_state(state):
        raise ValueError("Initial Sudoku state violates constraints (invalid clues).")

    cnf = CNF()

    # 1) Each cell exactly one value
    for r in range(1, 10):
        for c in range(1, 10):
            lits = [var_id(r, c, v) for v in range(1, 10)]
            exactly_one(cnf, lits)

    # 2) Each row: for each value v, exactly one column c
    for r in range(1, 10):
        for v in range(1, 10):
            lits = [var_id(r, c, v) for c in range(1, 10)]
            exactly_one(cnf, lits)

    # 3) Each column: for each value v, exactly one row r
    for c in range(1, 10):
        for v in range(1, 10):
            lits = [var_id(r, c, v) for r in range(1, 10)]
            exactly_one(cnf, lits)

    # 4) Each 3x3 box: for each value v, exactly one cell in the box
    for br in range(0, 3):
        for bc in range(0, 3):
            r0 = br * 3 + 1
            c0 = bc * 3 + 1
            for v in range(1, 10):
                lits = []
                for dr in range(0, 3):
                    for dc in range(0, 3):
                        lits.append(var_id(r0 + dr, c0 + dc, v))
                exactly_one(cnf, lits)

    # 5) Clues: unit clauses
    for idx, val in enumerate(state):
        if val == 0:
            continue
        r = idx // 9 + 1
        c = idx % 9 + 1
        cnf.append([var_id(r, c, int(val))])

    return cnf


def model_to_state(model: List[int]) -> State:
    """
    Decode a SAT model into a Sudoku State.
    The model is a list of signed ints; positive ints indicate True vars.
    """
    grid = [0] * 81

    for lit in model:
        if lit <= 0:
            continue
        if 1 <= lit <= 729:
            r, c, v = inv_var_id(lit)
            idx = (r - 1) * 9 + (c - 1)
            # There should be exactly one v per (r,c)
            grid[idx] = v

    return tuple(grid)


@dataclass
class SatResult:
    sat: bool
    solution: Optional[State]
    runtime_s: float
    # You can extend this with solver stats if you want (conflicts, decisions, etc.)


def solve_sudoku_sat(state: State, solver_name: str = "glucose3") -> SatResult:
    """
    Solve Sudoku via SAT using PySAT.
    solver_name examples: "glucose3", "minisat22", "cadical153", ...
    """
    import time

    cnf = sudoku_to_cnf(state)

    t0 = time.perf_counter()
    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
        sat = solver.solve()
        runtime = time.perf_counter() - t0
        if not sat:
            return SatResult(sat=False, solution=None, runtime_s=runtime)

        model = solver.get_model()
        sol = model_to_state(model)

    # Safety check (should always pass)
    if sol is None or (not is_valid_state(sol)) or any(v == 0 for v in sol):
        raise RuntimeError("SAT solver returned an invalid or incomplete solution (unexpected).")

    return SatResult(sat=True, solution=sol, runtime_s=runtime)

