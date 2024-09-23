import random
import argparse
from pathlib import PurePath, Path
from typing import Callable


class Maze:
    class Cell:
        def __init__(self, cell_id, dimensions_sizes):
            self.id = cell_id
            self.dimensions_sizes = dimensions_sizes
            self.links = set()

        def connect(self, neighbor):
            self.links.add(neighbor)

        def spatial(self, cell_id):
            coordinates = []
            divisor = 1
            for size in self.dimensions_sizes:
                coordinates.append((cell_id // divisor) % size)
                divisor *= size
            return tuple(coordinates)

    def __init__(self, *, sizes, output_file=None, silent=False):
        self.dimensions_sizes = sizes
        self._output_file = output_file
        self.total_cells = 1
        for size in self.dimensions_sizes:
            self.total_cells *= size
        self.cells = {}
        self.out: Callable = self._out_silent if silent else self._out_verbose
        self.display_maze_3d = (
            self._display_maze_3d_silent if silent else self._display_maze_3d_verbose
        )

    def _out_verbose(self, content):
        if self._output_file:
            with open(self._output_file, "a") as file:
                file.write(f"{content}\n")
        else:
            print(content)

    def _out_silent(self, content):
        pass

    def get_cell(self, cell_id):
        if cell_id not in self.cells:
            self.cells[cell_id] = Maze.Cell(cell_id, self.dimensions_sizes)
        return self.cells[cell_id]

    def calculate_neighbors(self, cell_id):
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

    def generate(self):
        visited = set()
        stack = [random.randint(0, self.total_cells - 1)]

        while stack:
            current = stack[-1]
            if current not in visited:
                visited.add(current)
                current_cell = self.get_cell(current)
                neighbors = self.calculate_neighbors(current)
                unvisited_neighbors = [n for n in neighbors if n not in visited]

                if unvisited_neighbors:
                    # Choose the next cell with a bias towards changing direction
                    if len(stack) > 1:
                        prev_direction = (stack[-1] - stack[-2],)
                        different_direction = [
                            n
                            for n in unvisited_neighbors
                            if (n - current,) != prev_direction
                        ]
                        if different_direction:
                            neighbor = random.choice(different_direction)
                        else:
                            neighbor = random.choice(unvisited_neighbors)
                    else:
                        neighbor = random.choice(unvisited_neighbors)

                    neighbor_cell = self.get_cell(neighbor)
                    current_cell.connect(neighbor)
                    neighbor_cell.connect(current)
                    stack.append(neighbor)
                else:
                    stack.pop()
            else:
                stack.pop()

        # Connect any remaining unvisited cells
        for cell_id in range(self.total_cells):
            if cell_id not in visited:
                neighbors = self.calculate_neighbors(cell_id)
                if neighbors:
                    neighbor = random.choice(neighbors)
                    self.get_cell(cell_id).connect(neighbor)
                    self.get_cell(neighbor).connect(cell_id)

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
                    right = (
                        "|"
                        if ((cell_id + 1) % x_size) == 0
                        or (cell_id + 1) not in cell.links
                        else " "
                    )
                    bottom += (
                        "       +"
                        if (cell_id + x_size) in cell.links
                        and cell_id + x_size < self.total_cells
                        else "-------+"
                    )
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
