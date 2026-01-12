# sudoku/core.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple


Digit = int
State = Tuple[int, ...]  # 81 entries, each in {0..9}, 0 = empty


def _rc_to_i(r: int, c: int) -> int:
    return r * 9 + c


def _i_to_rc(i: int) -> Tuple[int, int]:
    return divmod(i, 9)


def _box_index(r: int, c: int) -> int:
    return (r // 3) * 3 + (c // 3)


# Precompute peers for each cell index (set of indices that share row/col/box).
_PEERS: List[Set[int]] = []
_ROW_CELLS: List[List[int]] = []
_COL_CELLS: List[List[int]] = []
_BOX_CELLS: List[List[int]] = []

for r in range(9):
    _ROW_CELLS.append([_rc_to_i(r, c) for c in range(9)])
for c in range(9):
    _COL_CELLS.append([_rc_to_i(r, c) for r in range(9)])
for br in range(3):
    for bc in range(3):
        cells = []
        for dr in range(3):
            for dc in range(3):
                cells.append(_rc_to_i(br * 3 + dr, bc * 3 + dc))
        _BOX_CELLS.append(cells)

for i in range(81):
    r, c = _i_to_rc(i)
    row = set(_ROW_CELLS[r])
    col = set(_COL_CELLS[c])
    box = set(_BOX_CELLS[_box_index(r, c)])
    peers = (row | col | box)
    peers.remove(i)
    _PEERS.append(peers)


def parse_puzzle(puzzle: str) -> State:
    """
    Parse a Sudoku puzzle from a string of length 81.
    Accepts digits '1'..'9' and empty cells as '.' or '0'.
    Ignores whitespace/newlines.
    """
    s = "".join(ch for ch in puzzle if not ch.isspace())
    if len(s) != 81:
        raise ValueError(f"Puzzle must have 81 cells after stripping whitespace, got {len(s)}")

    cells: List[int] = []
    for ch in s:
        if ch in ".0":
            cells.append(0)
        elif ch.isdigit() and ch != "0":
            d = int(ch)
            if not (1 <= d <= 9):
                raise ValueError(f"Invalid digit: {ch}")
            cells.append(d)
        else:
            raise ValueError(f"Invalid character in puzzle: {ch}")

    state: State = tuple(cells)
    if not is_valid_state(state):
        raise ValueError("Initial puzzle violates Sudoku constraints (invalid clues).")
    return state


def format_grid(state: State) -> str:
    """Pretty-print a Sudoku state."""
    def cell_str(v: int) -> str:
        return "." if v == 0 else str(v)

    lines = []
    for r in range(9):
        row = []
        for c in range(9):
            row.append(cell_str(state[_rc_to_i(r, c)]))
            if c in (2, 5):
                row.append("|")
        lines.append(" ".join(row))
        if r in (2, 5):
            lines.append("-" * 21)
    return "\n".join(lines)


def is_goal(state: State) -> bool:
    """Goal: no empty cells and constraints satisfied."""
    return all(v != 0 for v in state) and is_valid_state(state)


def is_valid_state(state: State) -> bool:
    """Check that no row/col/box has duplicates among filled digits."""
    if len(state) != 81:
        return False

    def no_dupes(indices: Sequence[int]) -> bool:
        seen = set()
        for i in indices:
            v = state[i]
            if v == 0:
                continue
            if v in seen:
                return False
            seen.add(v)
        return True

    for r in range(9):
        if not no_dupes(_ROW_CELLS[r]):
            return False
    for c in range(9):
        if not no_dupes(_COL_CELLS[c]):
            return False
    for b in range(9):
        if not no_dupes(_BOX_CELLS[b]):
            return False
    return True


def legal_values(state: State, idx: int) -> Set[int]:
    """
    Return the set of legal digits for cell idx, given current assignments.
    If the cell is already filled, returns {value}.
    """
    v = state[idx]
    if v != 0:
        return {v}

    used = set()
    for j in _PEERS[idx]:
        w = state[j]
        if w != 0:
            used.add(w)

    return set(range(1, 10)) - used


def first_empty(state: State) -> Optional[int]:
    """Return the index of the first empty cell, or None if full."""
    try:
        return state.index(0)
    except ValueError:
        return None


def select_unassigned_mrv(state: State) -> Optional[Tuple[int, Set[int]]]:
    """
    MRV (Minimum Remaining Values): select an empty cell with smallest legal domain.
    Returns (idx, domain). If no empty cells, returns None.
    If some empty cell has empty domain, returns (idx, empty_set) immediately.
    """
    best_idx: Optional[int] = None
    best_domain: Optional[Set[int]] = None

    for idx, v in enumerate(state):
        if v != 0:
            continue
        dom = legal_values(state, idx)
        if best_domain is None or len(dom) < len(best_domain):
            best_idx = idx
            best_domain = dom
            if len(dom) == 0:
                break
            if len(dom) == 1:
                # can't do better than 1 except 0; keep scanning only if you want
                pass

    if best_idx is None:
        return None
    return best_idx, (best_domain or set())


def assign(state: State, idx: int, value: int) -> State:
    """Return a new state with state[idx] := value."""
    if not (1 <= value <= 9):
        raise ValueError("value must be in 1..9")
    if state[idx] != 0 and state[idx] != value:
        raise ValueError("Cannot assign a different value to a filled cell")

    lst = list(state)
    lst[idx] = value
    return tuple(lst)


def successors_mrv(state: State) -> List[Tuple[State, int]]:
    """
    Generate successors using MRV:
    - pick the empty cell with smallest domain
    - produce one successor per value in domain
    Cost per action = 1.
    Returns empty list if dead-end (some empty cell has no legal values).
    """
    sel = select_unassigned_mrv(state)
    if sel is None:
        return []
    idx, dom = sel
    if len(dom) == 0:
        return []  # dead-end

    # Sort for determinism (helps reproducibility/debugging)
    return [(assign(state, idx, v), 1) for v in sorted(dom)]


def num_empty(state: State) -> int:
    return sum(1 for v in state if v == 0)


@dataclass(frozen=True)
class SudokuProblem:
    """
    Minimal 'environment' wrapper for search algorithms.
    This is intentionally lightweight: A* can call these methods.
    """
    start: State

    def initial_state(self) -> State:
        return self.start

    def is_goal(self, s: State) -> bool:
        return is_goal(s)

    def successors(self, s: State) -> List[Tuple[State, int]]:
        return successors_mrv(s)

    def heuristic_empty_cells(self, s: State) -> int:
        # admissible: each move fills exactly one empty cell
        return num_empty(s)

    def heuristic_zero(self, s: State) -> int:
        return 0

