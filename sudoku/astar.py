# sudoku/astar.py
from __future__ import annotations

import time
import heapq
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Tuple, TypeVar

S = TypeVar("S")  # State type


@dataclass
class AStarResult(Generic[S]):
    found: bool
    path: List[S]                     # sequence of states from start to goal (inclusive)
    cost: float                       # total path cost (g at goal), 0.0 if not found
    expanded: int                     # number of expanded nodes (popped for expansion)
    generated: int                    # number of generated successor states (considered)
    max_frontier: int                 # max size of the frontier (heap length)
    max_closed: int                   # max size of closed set
    runtime_s: float                  # wall-clock runtime in seconds


def reconstruct_path(came_from: Dict[S, S], start: S, goal: S) -> List[S]:
    """Reconstruct path by following parents from goal to start."""
    cur = goal
    rev = [cur]
    while cur != start:
        cur = came_from[cur]
        rev.append(cur)
    rev.reverse()
    return rev


def astar(
    start: S,
    is_goal: Callable[[S], bool],
    successors: Callable[[S], List[Tuple[S, int]]],
    heuristic: Callable[[S], float],
) -> AStarResult[S]:
    """
    A* with duplicate elimination and no reopening (as required):
    - duplicate elimination via g_best
    - no reopening: once a state is expanded (in closed), it will never be expanded again
    - allows cost improvements for states still in frontier via lazy deletion (multiple heap entries)
    """
    t0 = time.perf_counter()

    # Frontier heap entries: (f, g, tie, state)
    # tie breaks deterministically by insertion order
    frontier: List[Tuple[float, float, int, S]] = []
    tie = 0

    g_best: Dict[S, float] = {start: 0.0}
    came_from: Dict[S, S] = {}

    closed: set[S] = set()

    f0 = heuristic(start)
    heapq.heappush(frontier, (f0, 0.0, tie, start))
    tie += 1

    expanded = 0
    generated = 0
    max_frontier = 1
    max_closed = 0

    while frontier:
        max_frontier = max(max_frontier, len(frontier))

        f, g, _, state = heapq.heappop(frontier)

        # Lazy deletion: skip outdated entries or already-closed states
        if state in closed:
            continue
        # If this heap entry doesn't match current best g, it's stale
        if g != g_best.get(state, float("inf")):
            continue

        # Expand
        expanded += 1

        if is_goal(state):
            runtime = time.perf_counter() - t0
            path = reconstruct_path(came_from, start, state)
            return AStarResult(
                found=True,
                path=path,
                cost=g,
                expanded=expanded,
                generated=generated,
                max_frontier=max_frontier,
                max_closed=max_closed,
                runtime_s=runtime,
            )

        closed.add(state)
        max_closed = max(max_closed, len(closed))

        # Generate successors
        for nxt, step_cost in successors(state):
            generated += 1

            if nxt in closed:
                # no reopening policy: never expand again once closed
                continue

            ng = g + float(step_cost)
            if ng < g_best.get(nxt, float("inf")):
                g_best[nxt] = ng
                came_from[nxt] = state
                nf = ng + float(heuristic(nxt))
                heapq.heappush(frontier, (nf, ng, tie, nxt))
                tie += 1

    runtime = time.perf_counter() - t0
    return AStarResult(
        found=False,
        path=[],
        cost=0.0,
        expanded=expanded,
        generated=generated,
        max_frontier=max_frontier,
        max_closed=max_closed,
        runtime_s=runtime,
    )

