"""Tests for A-Maze-ing."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from mazegen import MazeGenerator
from mazegen.generator import MOVES

MAIN = Path(__file__).resolve().parent.parent / "a_maze_ing.py"


def make_config(**changes: str) -> str:
    """Build a config text; a value of '' removes that key."""
    values = {"WIDTH": "20", "HEIGHT": "15", "ENTRY": "0,0",
              "EXIT": "19,14", "OUTPUT_FILE": "out.txt",
              "PERFECT": "True", "SEED": "1"}
    values.update(changes)
    return "".join(f"{k}={v}\n" for k, v in values.items() if v != "")


def run(tmp_path: Path, body: str) -> "subprocess.CompletedProcess[str]":
    cfg = tmp_path / "config.txt"
    cfg.write_text(body)
    return subprocess.run([sys.executable, str(MAIN), str(cfg)],
                          capture_output=True, text=True, cwd=tmp_path,
                          input="5\n")


# ---------- 清单 1: 太小的迷宫 ----------
@pytest.mark.parametrize("w,h", [(1, 1), (0, 5), (1, 10), (10, 1)])
def test_too_small_raises(w: int, h: int) -> None:
    with pytest.raises(ValueError):
        MazeGenerator(w, h)


def test_42_pattern_size_limit() -> None:
    small = MazeGenerator(5, 5, seed=1)
    assert small.pattern_error is not None and not small.pattern_cells
    big = MazeGenerator(9, 7, seed=1)
    assert big.pattern_error is None and big.pattern_cells


# ---------- 清单 2: entry / exit ----------
@pytest.mark.parametrize("entry,exit_", [
    ((-1, 0), (5, 5)), ((20, 0), (5, 5)), ((0, 0), (20, 14)),
    ((0, 0), (0, 15)), ((3, 3), (3, 3))])
def test_bad_entry_exit_in_class(entry: tuple[int, int],
                                 exit_: tuple[int, int]) -> None:
    with pytest.raises(ValueError):
        MazeGenerator(20, 15, entry=entry, exit_=exit_)


BAD_CONFIGS = [
    {"WIDTH": "1", "HEIGHT": "1", "EXIT": "0,0"},
    {"WIDTH": "abc"}, {"WIDTH": ""}, {"OUTPUT_FILE": ""},
    {"ENTRY": "99,99"}, {"EXIT": "-1,0"}, {"EXIT": "0,0"},
    {"ENTRY": "1;2"}, {"ENTRY": "a,b"}, {"ENTRY": "1,2,3"},
    {"PERFECT": "maybe"}, {"SEED": "x"},
    {"OUTPUT_FILE": "no_such_dir/out.txt"},
]


@pytest.mark.parametrize("changes", BAD_CONFIGS)
def test_bad_config_never_crashes(tmp_path: Path,
                                  changes: dict[str, str]) -> None:
    result = run(tmp_path, make_config(**changes))
    assert result.returncode == 1
    assert "Error" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_config_file(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, str(MAIN), "nope.txt"],
                            capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_line_without_equals(tmp_path: Path) -> None:
    result = run(tmp_path, "this is not a pair\n")
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_comments_and_blank_lines_ignored(tmp_path: Path) -> None:
    result = run(tmp_path, "# comment\n\n" + make_config())
    assert result.returncode == 0, result.stderr


# ---------- 清单 3-4: 墙一致、连通 ----------
SIZES = [(2, 2), (3, 3), (9, 7), (20, 15), (31, 21)]


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


def borders_closed(m: MazeGenerator) -> bool:
    for x in range(m.width):
        if not m.cells[0][x] & 1 or not m.cells[m.height - 1][x] & 4:
            return False
    for y in range(m.height):
        if not m.cells[y][0] & 8 or not m.cells[y][m.width - 1] & 2:
            return False
    return True


def reachable(m: MazeGenerator) -> int:
    seen = {m.entry}
    stack = [m.entry]
    while stack:
        x, y = stack.pop()
        for _, bit, dx, dy, _ in MOVES:
            nxt = (x + dx, y + dy)
            if not m.cells[y][x] & bit and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen)


@pytest.mark.parametrize("w,h", SIZES)
@pytest.mark.parametrize("perfect", [True, False])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_maze_rules(w: int, h: int, perfect: bool, seed: int) -> None:
    m = MazeGenerator(w, h, perfect=perfect, seed=seed)
    assert borders_closed(m)
    assert consistent(m)
    assert reachable(m) == w * h - len(m.pattern_cells)
    assert not m.has_open_area()
    # 走一遍 solution，确认每一步都没穿墙并且到达 exit
    x, y = m.entry
    for letter in m.solution:
        move = next(mv for mv in MOVES if mv[0] == letter)
        assert not m.cells[y][x] & move[1]
        x, y = x + move[2], y + move[3]
    assert (x, y) == m.exit
    if perfect:
        assert m.loop_count() == 0
    elif w >= 9 and h >= 7:
        assert m.loop_count() >= 2
        for cx, cy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                       (w // 2, h // 2)]:
            assert (cx, cy) not in m.pattern_cells


def test_same_seed_same_maze() -> None:
    a = MazeGenerator(20, 15, seed=7, perfect=False)
    b = MazeGenerator(20, 15, seed=7, perfect=False)
    assert a.cells == b.cells and a.solution == b.solution
    assert MazeGenerator(20, 15, seed=8).cells != MazeGenerator(
        20, 15, seed=9).cells


# ---------- 清单 6: 输出文件格式 ----------
@pytest.mark.parametrize("perfect", ["True", "False"])
def test_output_file_format(tmp_path: Path, perfect: str) -> None:
    result = run(tmp_path, make_config(PERFECT=perfect))
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "out.txt").read_text()
    assert text.endswith("\n") and "\r" not in text
    lines = text[:-1].split("\n")
    assert len(lines) == 15 + 4
    for row in lines[:15]:
        assert re.fullmatch(r"[0-9A-Fa-f]{20}", row)
    assert lines[15] == ""
    assert lines[16] == "0,0"
    assert lines[17] == "19,14"
    assert re.fullmatch(r"[NESW]+", lines[18])
