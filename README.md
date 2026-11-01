*This project has been created as part of the 42 curriculum by nisu, plillian.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python 3.10+. It reads a
configuration file, generates a maze, writes it to a file using one
hexadecimal digit per cell, and displays it in the terminal with an
interactive menu.

Overview:

- Two generation modes: `PERFECT=True` (exactly one path between entry and
  exit) and `PERFECT=False` (a playable, Pac-Man-like board with loops).
- A visible "42" made of fully closed cells (when the maze is big enough).
- Reproducible mazes with a seed.
- Shortest path from entry to exit (BFS).
- The generation logic lives in a standalone, pip-installable package
  called `mazegen`.

## Instructions

Requirements: Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
make install        # install flake8, mypy, pytest, build
make run            # python3 a_maze_ing.py config.txt
```

| Command | What it does |
|---|---|
| `make install` | Installs the development tools |
| `make run` | Runs the program with `config.txt` |
| `make debug` | Runs the program inside `pdb` |
| `make clean` | Removes `__pycache__`, `.mypy_cache`, `build`, `dist`... |
| `make lint` | `flake8 .` and `mypy` with the required flags |
| `make lint-strict` | `flake8 .` and `mypy . --strict` (optional) |
| `make test` | Runs the unit tests (`pytest`) |

You can also run it directly: `python3 a_maze_ing.py config.txt`.

### Interactive menu

| Key | Action |
|---|---|
| 1 | Re-generate a new maze (the output file is rewritten) |
| 2 | Show / hide the shortest path |
| 3 | Change the wall colour |
| 4 | Change the colour of the "42" pattern |
| 5 | Quit |

Legend: green square = entry, red square = exit, yellow = shortest path.

## Config file format

One `KEY=VALUE` per line. Lines starting with `#` and empty lines are ignored.

| Key | Mandatory | Description | Example |
|---|---|---|---|
| `WIDTH` | yes | Number of columns, integer >= 2 | `WIDTH=20` |
| `HEIGHT` | yes | Number of rows, integer >= 2 | `HEIGHT=15` |
| `ENTRY` | yes | Entry cell `x,y`, inside the maze | `ENTRY=0,0` |
| `EXIT` | yes | Exit cell `x,y`, inside the maze, different from entry | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | Output file name | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` or `False` | `PERFECT=True` |
| `SEED` | no | Integer; same seed and config give the same first maze | `SEED=42` |

Invalid input (missing file, missing key, wrong type, out-of-range
coordinates, entry equal to exit, unwritable output file...) prints a clear
`Error: ...` message and exits with code 1. The program never crashes with a
traceback.

```txt
# config.txt  (default configuration)
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

```txt
# config_playable.txt  (non-perfect, Pac-Man-like board)
WIDTH=21
HEIGHT=15
ENTRY=0,0
EXIT=20,14
OUTPUT_FILE=maze_playable.txt
PERFECT=False
SEED=7
```

## Output file format

- One hexadecimal digit per cell, one row per line.
- Bits: `0` = North, `1` = East, `2` = South, `3` = West; a closed wall is `1`.
  Example: `3` (0011) = North and East closed; `A` (1010) = East and West closed.
- Then an empty line, then the entry `x,y`, the exit `x,y`, and the shortest
  path using the letters `N`, `E`, `S`, `W`.
- Every line ends with `\n`.

## Algorithms and why

**Perfect maze: recursive backtracker (depth-first search).** Start at the
entry, repeatedly move to a random unvisited neighbour while removing the wall
between the two cells, and when stuck go back along the path (backtrack). It is
implemented with an explicit stack instead of recursion, so large mazes cannot
hit Python's recursion limit. The result is a spanning tree, which guarantees
full connectivity and no loops, i.e. exactly one path between any two cells.
We chose it because it is simple to explain and to test, it makes long
winding corridors, and it is easy to make reproducible with a seeded random
generator. [EDIT: add your own reasons.]

**Non-perfect maze: braiding.** We first build a perfect maze, then open an
extra wall in every dead end (a cell with a single opening). Before each wall
is removed we check that no 3x3 fully open area appears, and we undo the
change if it does. Finally we count the independent loops
(`edges - nodes + 1`) and open a few more safe walls if there are fewer than
two. Corners and centre are never part of the "42", so they stay open.

**"42" pattern.** A 7x5 template of fully closed cells is placed so that its
empty middle column crosses the centre of the maze. Those cells are marked as
visited before generation, so the algorithm carves around them. It needs at
least a 9x7 maze; otherwise (or if entry/exit falls inside the pattern) an
error message is printed and the pattern is skipped.

**Shortest path: BFS.** Every move costs one step, so a breadth-first search
with a queue and a predecessor table finds a shortest path.

## Reusable module (`mazegen`)

The generation logic is the class `MazeGenerator` in `mazegen/generator.py`.
It has no dependency on the config parser or the display. It is packaged as
`mazegen-1.0.0-py3-none-any.whl` (at the root of this repository).

Install:

```bash
pip install ./mazegen-1.0.0-py3-none-any.whl
```

Basic example:

```python
from mazegen import MazeGenerator

maze = MazeGenerator(width=20, height=15)   # entry (0,0), exit bottom-right
print(maze.solution)                        # e.g. "EESSE..."
```

Custom parameters:

```python
maze = MazeGenerator(
    width=30, height=20,
    entry=(0, 0), exit_=(29, 19),
    perfect=False,       # False = playable board with loops
    seed=42,             # same seed + same arguments = same first maze
)
maze.generate()          # build a new maze (different from the previous one)
```

Accessing the result:

```python
maze.cells            # cells[y][x]: int 0-15 (N=1, E=2, S=4, W=8, 1 = closed)
maze.solution         # shortest path from entry to exit, e.g. "EESS"
maze.seed             # seed actually used
maze.pattern_cells    # set of (x, y) cells that form the "42"
maze.pattern_error    # message if the "42" was skipped, else None
maze.hex_rows()       # list of hex strings, one per row (output file format)
maze.loop_count()     # number of independent loops (0 for a perfect maze)
maze.dead_ends()      # list of dead-end cells
maze.has_open_area()  # True if a forbidden 3x3 open area exists
```

Invalid arguments (size < 2, coordinates outside the maze, entry equal to exit)
raise `ValueError`. The structure in `maze.cells` is not necessarily the same
format as the output file; `hex_rows()` converts it.

Rebuild the package from source:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install build
python3 -m build
cp dist/mazegen-1.0.0-py3-none-any.whl .
```

License: see `LICENSE.md` (MIT, which allows reuse and distribution).

## Project structure

```
a_maze_ing.py          main program: config parsing, output file, entry point
display.py             terminal rendering and interactive menu
mazegen/               reusable package (MazeGenerator)
test/                 unit test (pytest)
config.txt             default configuration
Makefile, pyproject.toml, LICENSE.md, README.md, .gitignore
mazegen-1.0.0-py3-none-any.whl
```

## Testing

`make test` runs the pytest suite: too-small mazes, invalid entry/exit,
invalid configs (the program must never crash), shared-wall consistency,
closed borders, connectivity, absence of 3x3 open areas, seed
reproducibility, loop count and output file format. `make lint` checks
flake8 and mypy. We also checked our output files with the provided
`maze_analyzer.py`.

## Team and project management


- **Roles:** nisu: ...need add / plillian: ...need add
- **Planned schedule and how it evolved:** need add
- **What worked well / what could be improved:**
- **Tools used:** Git, Python, venv, flake8, mypy, pytest, build, pdb, Makefile,
  `maze_analyzer.py`, ...

## Resources

- Python documentation: `random`, `collections.deque`, `pathlib`, `argparse`, `pdb`

- [Maze Generation: Recursive Backtracking](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking?utm_source=chatgpt.com)

- [Maze Algorithms](https://www.jamisbuck.org/mazes/?utm_source=chatgpt.com)

- [Maze Generation Algorithm on Python](https://www.youtube.com/watch?v=jZQ31-4_8KM)


### How AI was used

- Explaining concepts (recursive backtracking, BFS, bit masks, packaging) and
  suggesting a study plan.
- Drafting first versions of the config parser, `MazeGenerator`, the display
  menu and the tests; we typed, tested, and corrected them ourselves, and each
  team member can explain every part.
- Generating the README template and the Makefile skeleton.

