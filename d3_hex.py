NORTH: int = 1  # bit 0 -> 0001
EAST: int = 2   # bit 1 -> 0010
SOUTH: int = 4  # bit 2 -> 0100
WEST: int = 8   # bit 3 -> 1000


def walls_to_int(north: bool, east: bool, south: bool, west: bool) -> int:
    """True 表示墙关闭 / True means the wall is closed."""
    value = 0
    if north:
        value |= NORTH
    if east:
        value |= EAST
    if south:
        value |= SOUTH
    if west:
        value |= WEST
    return value


def int_to_walls(value: int) -> dict[str, bool]:
    """反过来：整数 -> 四面墙 / the reverse direction."""
    return {
        "N": bool(value & NORTH),
        "E": bool(value & EAST),
        "S": bool(value & SOUTH),
        "W": bool(value & WEST),
    }


tests = [
    (False, False, False, False),  # 期望 0 / expect 0
    (True, True, False, False),    # 期望 3 / expect 3
    (False, True, False, True),    # 期望 10 = A / expect 10 = A
    (True, True, True, True),      # 期望 15 = F / expect 15 = F
]

for n, e, s, w in tests:
    v = walls_to_int(n, e, s, w)
    print(f"N={n!s:5} E={e!s:5} S={s!s:5} W={w!s:5} "
          f"-> bin {v:04b}  dec {v:2}  hex {v:X}")

# 共享墙：打通 a 的东墙，必须同时打通 b 的西墙
# Shared wall: opening a's East must also open b's West
a = 15
b = 15
a &= ~EAST
b &= ~WEST
print(f"a={a:X} b={b:X}")  # 应该是 D 和 7 / should be D and 7