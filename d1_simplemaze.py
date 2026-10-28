WIDTH: int = 4
HEIGHT: int = 3 # why captical letter?

# create a grid 创建 4 × 3 的 grid。
grid: list[list[tuple[int, int]]] = [
    (x, y) for x in range (WIDTH) for y in range(HEIGHT)
] # why here is []


# 写一个 function，输入 x、y，判断坐标是否在 grid 内。
def in_bound(x: int, y: int) -> bool:
    return 0 <= x < WIDTH and 0 <= y < HEIGHT


# 找出坐标 (1, 1) 的北、东、南、西四个邻居。
DIRECTIONS: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
    "S": (0, 1),
} # why here is {}

def get_neighbours (x: int, y: int) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for name, (dx, dy) in DIRECTIONS.items(): # how do i know here should use items()? is it a function?
        result[name] = (x + dx, y + dy)
    return result

print("get neighbours of(1, 1): ", get_neighbours(1, 1))


# 尝试访问最左边 cell 的西侧，解释为什么它越界。
wx, wy = get_neighbours(0, 1)["W"]
print("west of (0, 1)", (wx, wy), "is in bounds?", in_bound(wx, wy))


# 5. 输出每个 cell 的坐标 / print every cell
for y in range(HEIGHT):
    for x in range(WIDTH):
        print((x, y), end=" ")
    print()