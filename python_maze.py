import argparse
import random
import sys
from collections import deque
from copy import deepcopy
from pathlib import PurePath, Path
from typing import Callable, List, Tuple, Optional, Dict

running_in_blender = 'bpy' in sys.modules
if not running_in_blender:
    from tqdm import tqdm
else:
    # Define a dummy tqdm function for use in Blender
    def tqdm(iterable, *args, **kwargs):
        return iterable

# random.seed(41)


class Maze:
    class Cell:
        def __init__(self, cell_id: int, dimensions_sizes: List[int]):
            self.id = cell_id
            self.dimensions_sizes = dimensions_sizes
            self.links = set()
            self._precalculate_neighbors()

        def _precalculate_neighbors(self):
            self.neighbors = {}
            self.valid_directions = set()
            coords = list(self.spatial(self.id))

            for direction, (dim_index, offset) in {
                "e": (0, 1),
                "w": (0, -1),
                "s": (1, 1),
                "n": (1, -1),
                "u": (2, 1),
                "d": (2, -1),
            }.items():
                if 0 <= coords[dim_index] + offset < self.dimensions_sizes[dim_index]:
                    new_coords = coords.copy()
                    new_coords[dim_index] += offset
                    neighbor_id = self._coords_to_id(new_coords)
                    self.neighbors[direction] = neighbor_id
                    self.valid_directions.add(direction)

        def connect(self, neighbor: int):
            self.links.add(neighbor)

        def spatial(self, cell_id: int) -> Tuple[int, ...]:
            coordinates = []
            divisor = 1
            for size in self.dimensions_sizes:
                coordinates.append((cell_id // divisor) % size)
                divisor *= size
            return tuple(coordinates)

        def has_link_in_direction(self, direction: str) -> bool:
            return (
                direction in self.valid_directions
                and self.neighbors[direction] in self.links
            )

        def _coords_to_id(self, coords: List[int]) -> int:
            cell_id = 0
            multiplier = 1
            for i, coord in enumerate(coords):
                cell_id += coord * multiplier
                multiplier *= self.dimensions_sizes[i]
            return cell_id

    def __init__(
        self,
        *,
        sizes: List[int],
        output_file: Path | str | None = None,
        silent: bool = False,
        direction_weights: Dict[str, float] = None,
    ):
        self.dimensions_sizes = sizes
        self._output_file = output_file
        self.total_cells = 1
        for size in self.dimensions_sizes:
            self.total_cells *= size
        self.cells: Dict[int, Maze.Cell] = {}
        self._silent = silent
        self._update_out()
        self._update_display_maze_3d()
        # self.out: Callable[[str], None] = (
        #     self._out_silent if silent else self._out_verbose
        # )
        self.display_maze_3d = (
            self._display_maze_3d_silent if silent else self._display_maze_3d_verbose
        )
        self.direction_weights = direction_weights or {
            "e": 1, "w": 1, "s": 1, "n": 1, "u": 1, "d": 1
        }


    @property
    def silent(self) -> bool:
        return self._silent

    @silent.setter
    def silent(self, value: bool):
        self._silent = value
        self._update_out()
        self._update_display_maze_3d()

    def _update_out(self):
        self.out: Callable[[str], None] = (
            self._out_silent if self._silent else self._out_verbose
        )

    def _update_display_maze_3d(self):
        self.display_maze_3d = (
            self._display_maze_3d_silent
            if self._silent
            else self._display_maze_3d_verbose
        )

    def generate(self):
        unvisited = set(range(self.total_cells))
        first = random.choice(list(unvisited))
        unvisited.remove(first)

        while unvisited:
            cell = random.choice(list(unvisited))
            _path = self._wilson_walk(cell, unvisited)
            self._add_path_to_maze(_path)
            unvisited -= set(_path)

    def _wilson_walk(self, start_cell: int, unvisited: set[int]) -> List[int]:
        current_path = [start_cell]
        while current_path[-1] in unvisited:
            current_cell = current_path[-1]
            neighbors = self.calculate_neighbors(current_cell)
            next_cell = self._choose_next_cell(current_path, neighbors)
            if next_cell in current_path:
                current_path = current_path[: current_path.index(next_cell) + 1]
            else:
                current_path.append(next_cell)
        return current_path

    def _choose_next_cell(self, current_path: List[int], neighbors: List[int]) -> int:
        if len(current_path) > 1:
            last_cell = current_path[-1]
            current_cell = self.get_cell(last_cell)

            weighted_neighbors = []
            for direction, neighbor_id in current_cell.neighbors.items():
                if neighbor_id in neighbors:
                    weight = self.direction_weights[direction]
                    weighted_neighbors.extend([neighbor_id] * int(weight * 10))

            if weighted_neighbors:
                return random.choice(weighted_neighbors)

        return random.choice(neighbors)

    def _add_path_to_maze(self, path_to_add: List[int]):
        for i in range(len(path_to_add) - 1):
            self.get_cell(path_to_add[i]).connect(path_to_add[i + 1])
            self.get_cell(path_to_add[i + 1]).connect(path_to_add[i])

    def get_cell(self, cell_id: int) -> Cell:
        if cell_id not in self.cells:
            self.cells[cell_id] = Maze.Cell(cell_id, self.dimensions_sizes)
        return self.cells[cell_id]

    def calculate_neighbors(self, cell_id: int) -> List[int]:
        neighbors = []
        for dim_index, size in enumerate(self.dimensions_sizes):
            offset_divisor = 1
            for i in range(dim_index):
                offset_divisor *= self.dimensions_sizes[i]

            for offset in [-1, 1]:
                neighbor_id = cell_id
                delta = offset * offset_divisor
                pos_in_dim = (cell_id // offset_divisor) % size + offset
                if 0 <= pos_in_dim < size:
                    neighbor_id += delta
                    if 0 <= neighbor_id < self.total_cells:
                        neighbors.append(neighbor_id)
        return neighbors

    def find_dead_ends(self) -> List[int]:
        return [cell_id for cell_id, cell in self.cells.items() if len(cell.links) == 1]

    def find_path(self, start_cell: int, end_cell: int) -> Optional[List[int]]:
        queue = deque([(start_cell, [start_cell])])
        visited = {start_cell}

        while queue:
            current_cell, current_path = queue.popleft()
            if current_cell == end_cell:
                return current_path

            for neighbor_cell in self.get_cell(current_cell).links:
                if neighbor_cell not in visited:
                    visited.add(neighbor_cell)
                    queue.append((neighbor_cell, current_path + [neighbor_cell]))

        return None

    def find_longest_dead_end_path(self) -> Optional[List[int]]:
        dead_end_cells = self.find_dead_ends()
        if len(dead_end_cells) < 2:
            self.out("Not enough dead ends to connect.")
            return None

        longest_path = []
        all_paths = []

        for i, start_cell in enumerate(dead_end_cells):
            for end_cell in dead_end_cells[i + 1 :]:  # Only check pairs once
                current_path = self.find_path(start_cell, end_cell)
                if current_path:
                    current_path_length = len(current_path)
                    all_paths.append(
                        (start_cell, end_cell, current_path, current_path_length)
                    )
                    if current_path_length > len(longest_path):
                        longest_path = current_path
                else:
                    self.out(
                        f"No path found between dead ends {start_cell} and {end_cell}"
                    )

        # Sort and display all paths
        all_paths.sort(key=lambda x: x[3], reverse=True)
        self.out("\nAll paths between dead ends (sorted by length):")
        for (
            start_cell,
            end_cell,
            path_between_ends,
            path_length_between_ends,
        ) in all_paths:
            self.out(
                f"Dead ends {start_cell} and {end_cell}: "
                f"path: {' -> '.join(map(str, path_between_ends))}, "
                f"length: {path_length_between_ends}"
            )
        return longest_path

    def connect_dead_ends(self):
        longest_path = self.find_longest_dead_end_path()
        if longest_path:
            _start, _end = longest_path[0], longest_path[-1]
            self.out(
                f"Longest path found between dead ends {_start} and {_end}, "
                f"path: {' -> '.join(map(str, longest_path))}, "
                f"length: {len(longest_path)}"
            )
            # Connect the cells along the path
            for i in range(len(longest_path) - 1):
                self.get_cell(longest_path[i]).connect(longest_path[i + 1])
                self.get_cell(longest_path[i + 1]).connect(longest_path[i])
        else:
            self.out("No path found between dead ends.")

    def _out_verbose(self, content):
        if self._output_file:
            with open(self._output_file, "a") as file:
                file.write(f"{content}\n")
        else:
            print(content)

    def _out_silent(self, content):
        pass

    def _display_maze_3d_silent(self):
        pass

    def _display_maze_3d_verbose(self):
        if len(self.dimensions_sizes) != 3:
            self.out("This method only supports 3D mazes.")
            return

        x_size, y_size, z_size = self.dimensions_sizes
        layer_size = x_size * y_size
        if layer_size * z_size > 1000:
            display_cell_id_format = " {:<4}"
            display_cell_links_format = " {:^7} {}"
            wall_separator = "---------+"
            empty_separator = "         +"
        elif layer_size * z_size > 100:
            display_cell_id_format = " {:<3}"
            display_cell_links_format = " {:^6} {}"
            wall_separator = "--------+"
            empty_separator = "        +"
        else:
            display_cell_id_format = " {:<2}"
            display_cell_links_format = " {:^5} {}"
            wall_separator = "-------+"
            empty_separator = "       +"

        range_z_size = range(z_size)
        print(display_cell_links_format)
        for layer in range_z_size:
            self.out(f"Layer {layer + 1}/{len(range_z_size)}")
            self.out("+" + wall_separator * x_size)
            for y in range(y_size):
                top = "|"
                bottom = "+"
                for x in range(x_size):
                    cell_id = x + y * x_size + layer * layer_size
                    cell = self.get_cell(cell_id)
                    right = "|"
                    if ((cell_id + 1) % x_size) != 0 and (cell_id + 1) in cell.links:
                        right = " "

                    if (cell_id + x_size) in cell.links and (
                        cell_id + x_size < self.total_cells
                    ):
                        bottom += empty_separator
                    else:
                        bottom += wall_separator
                    vert_marker = display_cell_id_format.format(cell_id)
                    vert_marker += "*" if len(cell.links) == 1 else " "
                    vert_marker += "." if (cell_id - layer_size) in cell.links else " "
                    vert_marker += "o" if (cell_id + layer_size) in cell.links else " "
                    top += display_cell_links_format.format(vert_marker.strip(), right)
                self.out(top)
                self.out(bottom)

    def dump(self):
        if len(self.dimensions_sizes) != 3:
            self.out("This method only supports 3D mazes.")
            return

        x_size, y_size, z_size = self.dimensions_sizes
        layer_size = x_size * y_size

        for layer in range(z_size):
            self.out(f"Layer {layer + 1}:")
            for y in range(y_size):
                for x in range(x_size):
                    _id = x + y * x_size + layer * layer_size
                    cell = self.get_cell(_id)
                    links = [link_id for link_id in cell.links]
                    self.out(f"Cell {cell.spatial(_id)} (ID: {_id}) - Links: {links}")
        self.out("\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a 3D maze")
    parser.add_argument("-x", type=int, required=True, help="X dimension of the maze")
    parser.add_argument("-y", type=int, required=True, help="Y dimension of the maze")
    parser.add_argument("-z", type=int, required=True, help="Z dimension of the maze")
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="Output file path"
    )
    parser.add_argument("-s", "--silent", type=int, default=0, help="Silent mode")
    parser.add_argument(
        "--clear", action="store_true", help="Clear the output file before writing"
    )
    parser.add_argument(
        "-n", "--total", type=int, default=100, help="Number of mazes to generate"
    )
    parser.add_argument("--weight-e", type=float, default=1.0, help="Weight for east direction")
    parser.add_argument("--weight-w", type=float, default=1.0, help="Weight for west direction")
    parser.add_argument("--weight-s", type=float, default=1.0, help="Weight for south direction")
    parser.add_argument("--weight-n", type=float, default=1.0, help="Weight for north direction")
    parser.add_argument("--weight-u", type=float, default=1.0, help="Weight for up direction")
    parser.add_argument("--weight-d", type=float, default=1.0, help="Weight for down direction")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    g_direction_weights = {
        "e": args.weight_e,
        "w": args.weight_w,
        "s": args.weight_s,
        "n": args.weight_n,
        "u": args.weight_u,
        "d": args.weight_d
    }
    output_path = PurePath(args.output) if args.output else None

    if output_path and args.clear:
        g_output_file = Path(output_path)
        if g_output_file.exists():
            g_output_file.unlink()

    best_maze = None
    longest_path_length = 0

    g_all_paths = []
    g_silent: bool = bool(args.silent)
    # Create progress bar
    pbar = tqdm(
        total=args.total, desc="Generating mazes", unit=" maze", disable=g_silent
    )
    for g_i in range(args.total):
        maze = Maze(
            sizes=[args.x, args.y, args.z],
            output_file=output_path,
            silent=True,
            direction_weights=g_direction_weights,
        )
        maze.generate()

        # Find and store all paths
        dead_ends = maze.find_dead_ends()
        maze_paths = []
        for start in dead_ends:
            for end in dead_ends:
                if start != end:
                    path = maze.find_path(start, end)
                    if path:
                        path_length = len(path)
                        maze_paths.append((start, end, path, path_length))
                        if path_length > longest_path_length:
                            longest_path_length = path_length
                            best_maze = maze
                            g_all_paths = deepcopy(maze_paths)
        # Update progress bar
        if not g_silent:
            pbar.set_postfix_str("best path: {}".format(longest_path_length))
            pbar.update(1)
    pbar.close()

    if best_maze and g_all_paths:
        # Display the best maze
        best_maze.silent = bool(args.silent)
        best_maze.silent = False
        best_maze.out(
            f"\nBest maze found (longest path length: {longest_path_length}):"
        )
        best_maze.display_maze_3d()

        if args.silent:
            # Sort and display all paths
            g_all_paths.sort(key=lambda x: x[3], reverse=True)
            g_longest_path = g_all_paths[0][2]
            best_maze.silent = False
            best_maze.out(
                f"\nLongest path found between "
                f"dead ends {g_longest_path[0]} and {g_longest_path[-1]}, "
                f"path: {' -> '.join(map(str, g_longest_path))}, "
                f"length: {len(g_longest_path)}"
            )
        else:
            best_maze.connect_dead_ends()
    else:
        print("No valid maze was generated.")
