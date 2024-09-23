import random
import argparse
from pathlib import PurePath, Path
from typing import Callable, List, Tuple, Optional, Set, Dict
from collections import deque


class Maze:
    class Cell:
        def __init__(self, cell_id: int, dimensions_sizes: List[int]):
            self.id = cell_id
            self.dimensions_sizes = dimensions_sizes
            self.links = set()

        def connect(self, neighbor: int):
            self.links.add(neighbor)

        def spatial(self, cell_id: int) -> Tuple[int, ...]:
            coordinates = []
            divisor = 1
            for size in self.dimensions_sizes:
                coordinates.append((cell_id // divisor) % size)
                divisor *= size
            return tuple(coordinates)

    def __init__(
        self,
        *,
        sizes: List[int],
        output_file: Path | str | None = None,
        silent: bool = False,
    ):
        self.dimensions_sizes = sizes
        self._output_file = output_file
        self.total_cells = 1
        for size in self.dimensions_sizes:
            self.total_cells *= size
        self.cells: Dict[int, Maze.Cell] = {}
        self.out: Callable[[str], None] = (
            self._out_silent if silent else self._out_verbose
        )
        self.display_maze_3d = (
            self._display_maze_3d_silent if silent else self._display_maze_3d_verbose
        )

    def generate(self):
        unvisited = set(range(self.total_cells))
        first = random.choice(list(unvisited))
        unvisited.remove(first)

        while unvisited:
            cell = random.choice(list(unvisited))
            path = self._wilson_walk(cell, unvisited)
            self._add_path_to_maze(path)
            unvisited -= set(path)

    def _wilson_walk(self, start: int, unvisited: Set[int]) -> List[int]:
        path = [start]
        while path[-1] in unvisited:
            neighbors = self.calculate_neighbors(path[-1])
            next_cell = self._choose_next_cell(path, neighbors)
            if next_cell in path:
                path = path[: path.index(next_cell) + 1]
            else:
                path.append(next_cell)
        return path

    @staticmethod
    def _choose_next_cell(path: List[int], neighbors: List[int]) -> int:
        if len(path) > 1:
            last_direction = path[-1] - path[-2]
            same_direction = [n for n in neighbors if n - path[-1] == last_direction]
            if (
                same_direction and random.random() < 0.3
            ):  # 30% chance to continue in the same direction
                return random.choice(same_direction)
        return random.choice(neighbors)

    def _add_path_to_maze(self, path: List[int]):
        for i in range(len(path) - 1):
            self.get_cell(path[i]).connect(path[i + 1])
            self.get_cell(path[i + 1]).connect(path[i])

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

    def find_path(self, start: int, end: int) -> Optional[List[int]]:
        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()
            if current == end:
                return path

            for neighbor in self.get_cell(current).links:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def connect_dead_ends(self):
        dead_ends = self.find_dead_ends()
        if len(dead_ends) < 2:
            self.out("Not enough dead ends to connect.")
            return

        start, end = random.sample(dead_ends, 2)
        self.out(f"Attempting to connect dead ends: {start} and {end}")

        path = self.find_path(start, end)
        if path:
            self.out(f"Path found: {' -> '.join(map(str, path))}")
        else:
            raise ValueError(f"No path found between {start} and {end}")

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

        range_z_size = range(z_size)
        for layer in range_z_size:
            self.out(f"Layer {layer + 1}/{len(range_z_size)}")
            self.out("+" + "-------+" * x_size)
            for y in range(y_size):
                top = "|"
                bottom = "+"
                for x in range(x_size):
                    cell_id = x + y * x_size + layer * layer_size
                    cell = self.get_cell(cell_id)
                    right = "|"
                    if ((cell_id + 1) % x_size) != 0 and (cell_id + 1) in cell.links:
                        right = " "

                    bottom = "-------+"
                    if (cell_id + x_size) in cell.links and (
                        cell_id + x_size < self.total_cells
                    ):
                        bottom = "       +"
                    vert_marker = " {:<2}".format(cell_id)
                    vert_marker += "*" if len(cell.links) == 1 else " "
                    vert_marker += "." if (cell_id - layer_size) in cell.links else " "
                    vert_marker += "o" if (cell_id + layer_size) in cell.links else " "
                    top += f" {vert_marker.strip():^5} " + right
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    output_path = PurePath(args.output) if args.output else None

    if output_path and args.clear:
        g_output_file = Path(output_path)
        if g_output_file.exists():
            g_output_file.unlink()

    maze = Maze(
        sizes=[args.x, args.y, args.z],
        output_file=output_path,
        silent=bool(args.silent),
    )
    maze.generate()
    maze.display_maze_3d()
    maze.connect_dead_ends()
