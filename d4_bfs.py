from collections import deque

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

# 固定的 4x4 迷宫，每个字符是一个 cell 的十六进制编码 (grid[y][x])
# A fixed 4x4 maze, one hex digit per cell
MAZE: list[str] = [
    "D13B",
    "96C2",
    "83D2",
    "EC56",
]

# (方向字母, 墙位, dx, dy)
MOVES: list[tuple[str, int, int, int]] = [
    ("N", NORTH, 0, -1),
    ("E", EAST, 1, 0),
    ("S", SOUTH, 0, 1),
    ("W", WEST, -1, 0),
]

HEIGHT: int = len(MAZE)
WIDTH: int = len(MAZE[0])
cells: list[list[int]] = [[int(ch, 16) for ch in row] for row in MAZE]


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < WIDTH and 0 <= y < HEIGHT


def get_neighbors(x: int, y: int) -> list[tuple[int, int, str]]:
    """返回能走过去的邻居 / neighbours reachable through an open wall."""
    result: list[tuple[int, int, str]] = []
    for letter, bit, dx, dy in MOVES:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny) and not cells[y][x] & bit:  # 该墙是打开的
            result.append((nx, ny, letter))
    return result


def bfs(entry: tuple[int, int], exit_: tuple[int, int]) -> str:
    queue: deque[tuple[int, int]] = deque([entry])
    visited: set[tuple[int, int]] = {entry}
    # predecessor[cell] = (从哪个 cell 来的, 走的方向字母)
    predecessor: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}

    while queue:
        x, y = queue.popleft()            # 先进先出 / first in, first out
        print("visit:", (x, y))           # 第 3 步：打印访问顺序
        if (x, y) == exit_:
            break
        for nx, ny, letter in get_neighbors(x, y):
            if (nx, ny) not in visited:   # 第 4 步：不重复访问
                visited.add((nx, ny))
                predecessor[(nx, ny)] = ((x, y), letter)  # 第 5 步
                queue.append((nx, ny))

    # 从 exit 倒着走回 entry，再反转 / walk back from exit, then reverse
    path: list[str] = []
    current = exit_
    while current != entry:
        prev, letter = predecessor[current]
        path.append(letter)
        current = prev
    path.reverse()
    return "".join(path)                  # 第 6 步


print("path:", bfs((0, 0), (3, 3)))       # 应该是 EESESS