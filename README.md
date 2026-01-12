# AI Homework — Sudoku: A* Search vs SAT

This repository contains the implementation and experimental evaluation of two different approaches to solving standard 9×9 Sudoku puzzles:

- **A\*** search on an explicit state-space formulation of the problem;
- **SAT-based solving**, using a propositional encoding of Sudoku constraints.

The objective of this project is to compare search-based and logic-based techniques in terms of runtime and search effort on benchmark Sudoku instances of increasing difficulty.

---

## Problem Description

Sudoku is modeled as a constraint satisfaction problem (CSP), where each cell must be assigned a digit from 1 to 9 such that:

- each row contains all digits exactly once;
- each column contains all digits exactly once;
- each 3×3 subgrid contains all digits exactly once.

In this project, the problem is addressed using two different paradigms:
1. **State-space search** with A\*;
2. **Logical inference** via reduction to propositional satisfiability (SAT).

---

## Repository Structure
ai-homework-sudoku/
│
├── sudoku/
│ ├── core.py # Sudoku representation, parsing, validity checks, MRV successor generation
│ ├── astar.py # A* search implementation
│ └── sat.py # SAT encoding and model decoding
│ └──__init__.py
│
├── scripts/
│ ├── solve_astar.py # Solve a single puzzle using A*
│ ├── solve_sat.py # Solve a single puzzle using SAT
│ ├── run_experiments.py # Run benchmarks and collect metrics
│ └── plot_results.py # Generate plots from experimental results
│
├── benchmarks/
│ ├── easy50.txt
│ ├── top95.txt
│ └── hardest.txt
│
├── results/
│ ├── results.csv # Raw experimental data
│ └── plots/ # Generated figures
│
└── Report_AI_Messina_Alberto.pdf


---

## Implemented Algorithms

### A* Search

- Each node represents a partially filled Sudoku grid.
- Successors are generated using the **Minimum Remaining Values (MRV)** heuristic.
- Duplicate states are discarded and nodes are not reopened.
- Two configurations are evaluated:
  - **Uniform-cost search** (`h = 0`);
  - **Informed A\*** with heuristic `h = number of empty cells`.

### SAT-Based Solver

- Sudoku constraints are encoded in **Conjunctive Normal Form (CNF)**.
- Boolean variables represent assignments of values to cells.
- Standard Sudoku constraints (cell, row, column, and subgrid) are enforced through clauses.
- A SAT solver is used to find a satisfying assignment, which is then decoded into a complete Sudoku solution.

---

## Benchmarks

Experiments are conducted on classic Sudoku benchmark sets originally proposed by Peter Norvig:

- `easy50.txt`
- `top95.txt`
- `hardest.txt`

Each file contains multiple Sudoku instances encoded as 81-character strings.

---

## Dependencies

The project was tested with **Python 3.10**.

The following external libraries are required:

- `python-sat` (PySAT)
- `matplotlib`

Install them with:

python -m pip install python-sat matplotlib

##How to Run

All commands must be executed from the root of the repository.

Solve a Single Puzzle with A*
python -m scripts.solve_astar \
  --puzzle-file benchmarks/easy50.txt \
  --index 0 \
  --heur empty


Options:

--index: index of the puzzle within the benchmark file

--heur: zero (h = 0) or empty (number of empty cells)

Solve a Single Puzzle with SAT
python -m scripts.solve_sat \
  --puzzle-file benchmarks/easy50.txt \
  --index 0

## Run Experimental Evaluation

To run all benchmarks and collect performance metrics:

python -m scripts.run_experiments \
  --benchmarks benchmarks/easy50.txt benchmarks/top95.txt benchmarks/hardest.txt \
  --out results/results.csv

## Generate Plots

To generate all plots used in the final report:

python -m scripts.plot_results --csv results/results.csv


Figures are saved in results/plots/.

## Reproducibility

All experimental results presented in the final report can be reproduced by:
executing run_experiments.py;

generating plots with plot_results.py.

No manual parameter tuning is required.
