"""mazegen: a small, reusable maze generator."""
import random
from collections import deque

Point = tuple[int, int]
Move = tuple[str, int, int, int, int]  # (letter, my bit, dx, dy, opp bit)

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
MOVES: list[Move] = [
    ("N", NORTH, 0, -1, SOUTH),
    ("E", EAST, 1, 0, WEST),
    ("S", SOUTH, 0, 1, NORTH),
    ("W", WEST, -1, 0, EAST),
]

# 7 x 5 的 "42"，X 是完全封闭的 cell，中间那一列是空隙
PATTERN_42: list[str] = [
    "X.X.XXX",
    "X.X...X",
    "XXX.XXX",
    "..X.X..",
    "..X.XXX",
]


class MazeGenerator:
    """Generate a maze, its '42' pattern and its shortest solution.

    Args:
        width: number of columns (>= 2).
        height: number of rows (>= 2).
        entry: (x, y) of the entry cell.
        exit_: (x, y) of the exit cell (default: bottom-right).
        perfect: True for a perfect maze, False for a playable board.
        seed: same seed + same arguments gives the same first maze.

    Attributes:
        cells: cells[y][x] is a 4-bit int (N=1, E=2, S=4, W=8, 1=closed).
        solution: shortest path from entry to exit, e.g. "EESS".
        pattern_cells: cells that form the '42'.
        pattern_error: message if the '42' had to be skipped, else None.
    """

    def __init__(self, width: int, height: int,
                 entry: Point = (0, 0), exit_: Point | None = None,
                 perfect: bool = True, seed: int | None = None) -> None:
        if exit_ is None:
            exit_ = (width - 1, height - 1)
        if width < 2 or height < 2:
            raise ValueError("width and height must be at least 2")
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit_
        self.perfect = perfect
        for name, (x, y) in (("entry", entry), ("exit", exit_)):
            if not self._inside(x, y):
                raise ValueError(f"{name} {x},{y} is outside the maze")
        if entry == exit_:
            raise ValueError("entry and exit must be different")
        self.seed = seed if seed is not None else random.randrange(2**32)
        self._rng = random.Random(self.seed)
        self.cells: list[list[int]] = []
        self.solution = ""
        self.pattern_cells: set[Point] = set()
        self.pattern_error: str | None = None
        self.generate()

    # ---------- public API ----------
    def generate(self) -> None:
        """Build a new maze (calling it again gives a different maze)."""
        self.cells = [[15] * self.width for _ in range(self.height)]
        self._place_pattern()
        self._carve_tree()
        if not self.perfect:
            self._braid_dead_ends()
            self._add_loops()
        self.solution = self._solve()

    def hex_rows(self) -> list[str]:
        """Return one hexadecimal string per row (output file format)."""
        return ["".join(f"{c:X}" for c in row) for row in self.cells]

    def dead_ends(self) -> list[Point]:
        """Return the cells that have exactly one opening."""
        return [(x, y) for y in range(self.height)
                for x in range(self.width)
                if (x, y) not in self.pattern_cells
                and bin(self.cells[y][x]).count("1") == 3]

    def loop_count(self) -> int:
        """Number of independent loops: edges - nodes + 1."""
        nodes = self.width * self.height - len(self.pattern_cells)
        edges = 0
        for y in range(self.height):
            for x in range(self.width):
                c = self.cells[y][x]
                if x + 1 < self.width and not c & EAST:
                    edges += 1
                if y + 1 < self.height and not c & SOUTH:
                    edges += 1
        return edges - nodes + 1

    def has_open_area(self) -> bool:
        """True if some 3x3 block is completely open (forbidden)."""
        return any(self._open_block(bx, by)
                   for by in range(self.height - 2)
                   for bx in range(self.width - 2))

    # ---------- helpers ----------
    def _inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _open(self, x: int, y: int, move: Move) -> None:
        """Remove the wall between (x, y) and its neighbour, both sides."""
        _, bit, dx, dy, opp = move
        self.cells[y][x] &= ~bit
        self.cells[y + dy][x + dx] &= ~opp

    def _close(self, x: int, y: int, move: Move) -> None:
        _, bit, dx, dy, opp = move
        self.cells[y][x] |= bit
        self.cells[y + dy][x + dx] |= opp

    # ---------- the '42' ----------
    def _place_pattern(self) -> None:
        self.pattern_cells = set()
        self.pattern_error = None
        if self.width < 9 or self.height < 7:
            self.pattern_error = ("maze too small for the '42' pattern "
                                  "(needs at least 9x7)")
            return
        # 让图案的空隙列正好穿过正中心，这样中心 cell 不会被封死
        ox = self.width // 2 - 3
        oy = self.height // 2 - 2
        cells = {(ox + c, oy + r)
                 for r, row in enumerate(PATTERN_42)
                 for c, ch in enumerate(row) if ch == "X"}
        if self.entry in cells or self.exit in cells:
            self.pattern_error = ("entry or exit is inside the '42' "
                                  "pattern, pattern skipped")
            return
        self.pattern_cells = cells

    # ---------- perfect maze ----------
    def _carve_tree(self) -> None:
        """Recursive backtracker with an explicit stack."""
        visited: set[Point] = set(self.pattern_cells)
        visited.add(self.entry)
        stack: list[Point] = [self.entry]
        while stack:
            x, y = stack[-1]
            options = [m for m in MOVES
                       if self._inside(x + m[2], y + m[3])
                       and (x + m[2], y + m[3]) not in visited]
            if options:
                move = self._rng.choice(options)
                self._open(x, y, move)
                nxt = (x + move[2], y + move[3])
                visited.add(nxt)
                stack.append(nxt)
            else:
                stack.pop()

    # ---------- non-perfect maze ----------
    def _open_block(self, bx: int, by: int) -> bool:
        for dy in range(3):
            for dx in range(3):
                c = self.cells[by + dy][bx + dx]
                if dx < 2 and c & EAST:
                    return False
                if dy < 2 and c & SOUTH:
                    return False
        return True

    def _open_area_near(self, x: int, y: int) -> bool:
        for by in range(max(0, y - 2), min(y, self.height - 3) + 1):
            for bx in range(max(0, x - 2), min(x, self.width - 3) + 1):
                if self._open_block(bx, by):
                    return True
        return False

    def _try_open(self, x: int, y: int, move: Move) -> bool:
        """Open one wall unless it breaks a rule. True if opened."""
        nx, ny = x + move[2], y + move[3]
        if not self._inside(nx, ny):
            return False
        if (x, y) in self.pattern_cells or (nx, ny) in self.pattern_cells:
            return False
        if not self.cells[y][x] & move[1]:
            return False  # already open
        self._open(x, y, move)
        if self._open_area_near(x, y) or self._open_area_near(nx, ny):
            self._close(x, y, move)  # 会形成 3x3 空地，撤销
            return False
        return True

    def _braid_dead_ends(self) -> None:
        """Give every dead end a second exit (when allowed)."""
        ends = self.dead_ends()
        self._rng.shuffle(ends)
        for x, y in ends:
            if bin(self.cells[y][x]).count("1") != 3:
                continue  # 已经被邻居顺便修好了
            moves = MOVES[:]
            self._rng.shuffle(moves)
            for move in moves:
                if self._try_open(x, y, move):
                    break

    def _add_loops(self) -> None:
        """Make sure there are at least two independent loops."""
        loops = self.loop_count()
        if loops >= 2:
            return
        walls = [(x, y, m) for y in range(self.height)
                 for x in range(self.width) for m in MOVES[1:3]]
        self._rng.shuffle(walls)  # MOVES[1:3] = E 和 S，每面墙只出现一次
        for x, y, move in walls:
            if loops >= 2:
                break
            if self._try_open(x, y, move):
                loops += 1

    # ---------- BFS ----------
    def _solve(self) -> str:
        queue: deque[Point] = deque([self.entry])
        came_from: dict[Point, tuple[Point, str]] = {}
        seen: set[Point] = {self.entry}
        while queue:
            x, y = queue.popleft()
            if (x, y) == self.exit:
                break
            for letter, bit, dx, dy, _ in MOVES:
                nxt = (x + dx, y + dy)
                if (self._inside(*nxt) and not self.cells[y][x] & bit
                        and nxt not in seen):
                    seen.add(nxt)
                    came_from[nxt] = ((x, y), letter)
                    queue.append(nxt)
        if self.exit not in seen:
            raise ValueError("no path from entry to exit")
        letters: list[str] = []
        cur = self.exit
        while cur != self.entry:
            cur, letter = came_from[cur]
            letters.append(letter)
        return "".join(reversed(letters))
