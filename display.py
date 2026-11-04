"""Terminal display and interactive menu for A-Maze-ing."""
from collections.abc import Callable

from mazegen import MazeGenerator
from mazegen.generator import MOVES

RESET = "\033[0m"
# ANSI 背景色代码 / ANSI background colour codes
WALL_COLORS: list[str] = ["47", "44", "42", "46", "100"]
PATTERN_COLORS: list[str] = ["45", "107", "106"]
FIXED_COLORS: dict[str, str] = {
    "A": "43",   # path: yellow
    "S": "102",  # entry: bright green
    "E": "41",   # exit: red
}


def build_canvas(maze: MazeGenerator, show_path: bool) -> list[list[str]]:
    """Convert the maze into a character-based display grid.

    Each maze cell occupies a position in the canvas. Walls and
    passages are represented by characters. The shortest path,
    entry, exit and '42' pattern are also displayed when applicable.

    Args:
        maze: MazeGenerator instance containing the maze data.
        show_path: Whether to display the shortest solution path.

    Returns:
        A two-dimensional list of characters representing the maze.
        Characters include '#', ' ', 'P', 'A', 'S' and 'E'.
    """

    h, w = maze.height, maze.width
    canvas = [["#"] * (2 * w + 1) for _ in range(2 * h + 1)]
    for y in range(h):
        for x in range(w):
            c = maze.cells[y][x]
            canvas[2 * y + 1][2 * x + 1] = " "
            for _, bit, dx, dy, _ in MOVES:
                if not c & bit:  # 这面墙是打开的 / this wall is open
                    canvas[2 * y + 1 + dy][2 * x + 1 + dx] = " "
    for x, y in maze.pattern_cells:
        canvas[2 * y + 1][2 * x + 1] = "P"
        for dx, dy in ((1, 0), (0, 1)):  # 相邻的图案格子连起来
            if (x + dx, y + dy) in maze.pattern_cells:
                canvas[2 * y + 1 + dy][2 * x + 1 + dx] = "P"
    if show_path:
        x, y = maze.entry
        for letter in maze.solution:
            move = next(m for m in MOVES if m[0] == letter)
            canvas[2 * y + 1 + move[3]][2 * x + 1 + move[2]] = "A"
            x, y = x + move[2], y + move[3]
            canvas[2 * y + 1][2 * x + 1] = "A"
    canvas[2 * maze.entry[1] + 1][2 * maze.entry[0] + 1] = "S"
    canvas[2 * maze.exit[1] + 1][2 * maze.exit[0] + 1] = "E"
    return canvas


def render(maze: MazeGenerator, show_path: bool,
           wall_idx: int, pattern_idx: int) -> None:
    """Display the maze in the terminal using ANSI background colours.

    Different colours represent walls, the '42' pattern, the
    shortest path, the entry and the exit.

    Args:
        maze: MazeGenerator instance containing the maze data.
        show_path: Whether to display the shortest solution path.
        wall_idx: Index selecting a colour from WALL_COLORS.
        pattern_idx: Index selecting a colour from PATTERN_COLORS.
    """

    colors = {"#": WALL_COLORS[wall_idx],
              "P": PATTERN_COLORS[pattern_idx], **FIXED_COLORS}
    lines: list[str] = []
    for row in build_canvas(maze, show_path):
        parts: list[str] = []
        for kind in row:
            if kind == " ":
                parts.append("  ")
            else:
                parts.append(f"\033[{colors[kind]}m  {RESET}")
        lines.append("".join(parts))
    print("\n".join(lines))


def run_menu(maze: MazeGenerator,
             on_new_maze: Callable[[MazeGenerator], None]) -> None:
    """Run the interactive maze menu until the user quits.

    Displays the maze and allows the user to regenerate it,
    toggle the solution path, change colours or quit.

    Args:
        maze: MazeGenerator instance to display and modify.
        on_new_maze: Callback function called after generating
            a new maze. Receives the updated MazeGenerator instance.
    """

    show_path = True
    wall_idx = 0
    pattern_idx = 0
    message = maze.pattern_error or ""
    while True:
        print("\033[2J\033[H", end="")  # 清屏 / clear the screen
        render(maze, show_path, wall_idx, pattern_idx)
        print("\n=== A-Maze-ing ===")
        print("S = entry (green), E = exit (red), yellow = shortest path")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Change the wall colour")
        print("4. Change the '42' colour")
        print("5. Quit")
        if message:
            print(f"Note: {message}")
            message = ""
        try:
            choice = input("Choice? (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            try:
                maze.generate()
                on_new_maze(maze)  # 重新写 output file
            except ValueError as error:
                message = str(error)
            else:
                message = maze.pattern_error or ""
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            wall_idx = (wall_idx + 1) % len(WALL_COLORS)
        elif choice == "4":
            pattern_idx = (pattern_idx + 1) % len(PATTERN_COLORS)
        elif choice == "5":
            return
        else:
            message = "invalid choice, please type a number from 1 to 5"
