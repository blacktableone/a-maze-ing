from mazegen import MazeGenerator


def consistent(m: MazeGenerator) -> bool:
    for y in range(m.height):
        for x in range(m.width):
            c = m.cells[y][x]
            if x + 1 < m.width and bool(c & 2) != bool(
                    m.cells[y][x + 1] & 8):
                return False
            if y + 1 < m.height and bool(c & 4) != bool(
                    m.cells[y + 1][x] & 1):
                return False
    return True


a = MazeGenerator(20, 15, seed=7, perfect=False)
b = MazeGenerator(20, 15, seed=7, perfect=False)
assert a.cells == b.cells, "same seed must give the same maze"
assert consistent(a) and not a.has_open_area()
assert a.loop_count() >= 2
print("non-perfect: loops", a.loop_count(), "dead ends", len(a.dead_ends()))

p = MazeGenerator(20, 15, seed=7, perfect=True)
assert consistent(p) and p.loop_count() == 0
print("perfect: loops", p.loop_count(), "solution", p.solution)

small = MazeGenerator(5, 5, seed=1)
print("small maze:", small.pattern_error)