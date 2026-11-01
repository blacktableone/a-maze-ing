import random

WIDTH: int = 4
HEIGHT: int = 3

# 方向: (dx, dy, 自己的墙位, 对面的墙位) / direction: (dx, dy, my bit, opposite bit)
# N=1, E=2, S=4, W=8
DIRS: dict[str, tuple[int, int, int, int]] = {
    "N": (0, -1, 1, 4),
    "E": (1, 0, 2, 8),
    "S": (0, 1, 4, 1),
    "W": (-1, 0, 8, 2),
}

# 每个 cell 一开始四面都是墙 (15 = 1111) / every cell starts with all 4 walls
cells: list[list[int]] = [[15] * WIDTH for _ in range(HEIGHT)]


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < WIDTH and 0 <= y < HEIGHT


def generate() -> None:
    start = (0, 0)      # tuple ()
    visited = {start}   # 去过的格子 / cells we have been to / dict {}
    stack = [start]     # 来时的路 (面包屑) / our trail of breadcrumbs /list []

    while stack:                      # 栈空了 = 全部走完 / empty stack = finished
        x, y = stack[-1]              # 当前所在的格子 (只看不取) / current cell (peek)

        # 第 1 步: 找出没去过、没出界的邻居
        options = []
        for dx, dy, bit, opp in DIRS.values():
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and (nx, ny) not in visited:
                options.append((nx, ny, bit, opp))

        if options:
            # 第 2 步: 随机选一个，把两边的墙都打通，然后走过去
            nx, ny, bit, opp = random.choice(options)
            cells[y][x] &= ~bit       # 清掉我这边的墙 / clear my wall
            cells[ny][nx] &= ~opp     # 清掉对面那一边的墙 / clear the neighbour's wall
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            # 第 3 步: 无路可走，往回退一格 (这就是 backtrack)
            stack.pop()


def draw() -> None:
    print("+" + "---+" * WIDTH)
    for y in range(HEIGHT):
        row = "|"
        below = "+"
        for x in range(WIDTH):
            c = cells[y][x]
            row += "   " + ("|" if c & 2 else " ")
            below += ("---" if c & 4 else "   ") + "+"
        print(row)
        print(below)


random.seed(42)
generate()
for row in cells:
    print("".join(f"{c:X}" for c in row))
draw()