import sys
from dataclasses import dataclass
from pathlib import Path
from mazegen import MazeGenerator
from display import run_menu

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

# (字母, 我的墙位, dx, dy, 对面的墙位) / (letter, my bit, dx, dy, opposite bit)
MOVES: list[tuple[str, int, int, int, int]] = [
    ("N", NORTH, 0, -1, SOUTH),
    ("E", EAST, 1, 0, WEST),
    ("S", SOUTH, 0, 1, NORTH),
    ("W", WEST, -1, 0, EAST),
]
REQUIRED: list[str] = ["WIDTH", "HEIGHT", "ENTRY", "EXIT",
                       "OUTPUT_FILE", "PERFECT"]

Point = tuple[int, int]


class ConfigError(Exception):
    """配置有问题时抛出 / raised when the config is invalid."""


@dataclass
class Config:
    """Store the validated maze configuration.

    Attributes:
        width: Number of columns in the maze.
        height: Number of rows in the maze.
        entry: Starting position (x, y).
        exit: Destination position (x, y).
        output_file: Path to the output file.
        perfect: Whether to generate a perfect maze.
        seed: Optional random seed for reproducible generation.
    """

    width: int
    height: int
    entry: Point
    exit: Point
    output_file: str
    perfect: bool
    seed: int | None


# ---------- 读取并解析 config / read and parse ----------
def read_pairs(path_str: str) -> dict[str, str]:
    """Read configuration key-value pairs from a file.

    Empty lines and comments are ignored. Duplicate keys and
    invalid lines raise ConfigError.

    Args:
        path_str: Path to the configuration file.

    Returns:
        A dictionary containing configuration keys and values.

    Raises:
        ConfigError: If the file cannot be read or contains invalid data.
    """

    path = Path(path_str)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    pairs: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(f"line {number}: expected KEY=VALUE")
                key, value = line.split("=", 1)
                key = key.strip()
                if key in pairs:
                    raise ConfigError(f"line {number}: duplicate key {key}")
                pairs[key] = value.strip()
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"cannot read config file: {error}") from error
    return pairs


def to_int(text: str, name: str) -> int:
    """Convert a string into an integer.

    Args:
        text: String value to convert.
        name: Configuration key name used in error messages.

    Returns:
        The converted integer.

    Raises:
        ConfigError: If the string is not a valid integer.
    """

    try:
        return int(text)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got '{text}'") \
            from None


def to_point(text: str, name: str) -> Point:
    """Convert a coordinate string into an (x, y) tuple.

    Args:
        text: Coordinate string in the format 'x,y'.
        name: Configuration key name used in error messages.

    Returns:
        A tuple containing the x and y integer coordinates.

    Raises:
        ConfigError: If the format or coordinates are invalid.
    """

    parts = text.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{name} must look like x,y, got '{text}'")
    return to_int(parts[0].strip(), name), to_int(parts[1].strip(), name)


def to_bool(text: str, name: str) -> bool:
    """Convert a string into a boolean value.

    Args:
        text: String containing 'True' or 'False'.
        name: Configuration key name used in error messages.

    Returns:
        True or False based on the input string.

    Raises:
        ConfigError: If the string is not 'True' or 'False'.
    """

    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    raise ConfigError(f"{name} must be True or False, got '{text}'")


# ---------- 检查并验证 / check and validate ----------
def load_config(path_str: str) -> Config:
    """Load and validate the maze configuration.

    Reads the configuration file, checks required keys, converts
    values and validates maze dimensions and coordinates.

    Args:
        path_str: Path to the configuration file.

    Returns:
        A Config object containing validated configuration values.

    Raises:
        ConfigError: If required keys are missing or values are invalid.
    """

    pairs = read_pairs(path_str)
    missing = [key for key in REQUIRED if key not in pairs]
    if missing:
        raise ConfigError("missing keys: " + ", ".join(missing))

    width = to_int(pairs["WIDTH"], "WIDTH")
    height = to_int(pairs["HEIGHT"], "HEIGHT")
    if width < 2 or height < 2:
        raise ConfigError("WIDTH and HEIGHT must be at least 2")

    entry = to_point(pairs["ENTRY"], "ENTRY")
    exit_ = to_point(pairs["EXIT"], "EXIT")
    for name, (x, y) in (("ENTRY", entry), ("EXIT", exit_)):
        if not (0 <= x < width and 0 <= y < height):
            raise ConfigError(f"{name} {x},{y} is outside the maze")
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different")

    output_file = pairs["OUTPUT_FILE"]
    if not output_file:
        raise ConfigError("OUTPUT_FILE must not be empty")

    seed = to_int(pairs["SEED"], "SEED") if "SEED" in pairs else None
    return Config(width, height, entry, exit_, output_file,
                  to_bool(pairs["PERFECT"], "PERFECT"), seed)


# ---------- 写文件 / write the output file ----------
def write_output(cfg: Config, cells: list[list[int]], path: str) -> None:
    """Write the generated maze and solution to an output file.

    The file contains hexadecimal maze rows, entry coordinates,
    exit coordinates and the solution path.

    Args:
        cfg: Validated maze configuration.
        cells: Two-dimensional list containing maze wall values.
        path: String containing the solution directions.

    Raises:
        ConfigError: If the output file cannot be written.
    """

    try:
        with open(cfg.output_file, "w", encoding="utf-8") as f:
            for row in cells:
                f.write("".join(f"{c:X}" for c in row) + "\n")
            f.write("\n")
            f.write(f"{cfg.entry[0]},{cfg.entry[1]}\n")
            f.write(f"{cfg.exit[0]},{cfg.exit[1]}\n")
            f.write(path + "\n")
    except OSError as error:
        raise ConfigError(f"cannot write output file: {error}") from error


def main() -> int:
    """Run the maze generator application.

    Reads the configuration file, generates the maze, saves the
    output and starts the interactive menu.

    Returns:
        0 if the application finishes successfully, otherwise 1.
    """

    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        return 1
    try:
        cfg = load_config(sys.argv[1])
        maze = MazeGenerator(cfg.width, cfg.height, cfg.entry, cfg.exit,
                             cfg.perfect, cfg.seed)

        def save(current: MazeGenerator) -> None:
            """Save the current maze and its solution.

            Args:
                current: MazeGenerator instance containing the maze
                    and its solution.
            """
            write_output(cfg, current.cells, current.solution)

        save(maze)
        run_menu(maze, save)
    except (ConfigError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
