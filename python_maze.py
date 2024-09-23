import random
import argparse
from pathlib import PurePath, Path
import multiprocessing as mp
from functools import partial


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

    def __init__(self, sizes, output_file=None):
        self.dimensions_sizes = sizes
        self._output_file = output_file
        self.total_cells = 1
        for size in self.dimensions_sizes:
            self.total_cells *= size
        self.cells = {}

    def out(self, content):
        if self._output_file:
            with open(self._output_file, "a") as file:
                file.write(f"{content}\n")
        else:
            print(content)

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

    @staticmethod
    def generate_section(start, end, total_cells, dimensions_sizes):
        if start >= end or start >= total_cells:
            return {}, set()

        cells = {}
        visited = set()
        stack = [random.randint(start, min(end - 1, total_cells - 1))]

        def get_cell(cell_id):
            if cell_id not in cells:
                cells[cell_id] = Maze.Cell(cell_id, dimensions_sizes)
            return cells[cell_id]

        def calculate_neighbors(cell_id):
            neighbors = []
            for dim_index, size in enumerate(dimensions_sizes):
                offset_divisor = 1
                for i in range(dim_index):
                    offset_divisor *= dimensions_sizes[i]

                for offset in [-1, 1]:
                    neighbor_id = cell_id
                    delta = offset * offset_divisor
                    pos_in_dim = (cell_id // offset_divisor) % size + offset
                    if 0 <= pos_in_dim < size:
                        neighbor_id += delta
                        if 0 <= neighbor_id < total_cells:
                            neighbors.append(neighbor_id)
            return neighbors

        while stack:
            current = stack[-1]
            if current not in visited:
                visited.add(current)
                current_cell = get_cell(current)
                neighbors = calculate_neighbors(current)
                unvisited_neighbors = [
                    n for n in neighbors if n not in visited and start <= n < end
                ]

                if unvisited_neighbors:
                    neighbor = random.choice(unvisited_neighbors)
                    neighbor_cell = get_cell(neighbor)
                    current_cell.connect(neighbor)
                    neighbor_cell.connect(current)
                    stack.append(neighbor)
                else:
                    stack.pop()
            else:
                stack.pop()

        return cells, visited

    def generate(self):
        num_processes = min(mp.cpu_count(), self.total_cells)
        chunk_size = max(1, self.total_cells // num_processes)

        with mp.Pool(processes=num_processes) as pool:
            sections = [
                (i * chunk_size, min((i + 1) * chunk_size, self.total_cells))
                for i in range(num_processes)
                if i * chunk_size < self.total_cells
            ]

            results = pool.starmap(
                partial(
                    Maze.generate_section,
                    total_cells=self.total_cells,
                    dimensions_sizes=self.dimensions_sizes,
                ),
                sections,
            )

        for cells, _ in results:
            self.cells.update(cells)

        visited = set()
        for _, section_visited in results:
            visited.update(section_visited)

        self.connect_sections(visited)

    def connect_sections(self, visited):
        for cell_id in visited:
            cell = self.get_cell(cell_id)
            neighbors = self.calculate_neighbors(cell_id)
            for neighbor in neighbors:
                if neighbor in visited and neighbor not in cell.links:
                    neighbor_cell = self.get_cell(neighbor)
                    if random.random() < 0.3:  # 30% chance to connect sections
                        cell.connect(neighbor)
                        neighbor_cell.connect(cell_id)

    def display_maze_3d(self):
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
                    if (cell_id - layer_size) in cell.links:
                        vert_marker += "."
                    else:
                        vert_marker += " "
                    if (cell_id + layer_size) in cell.links:
                        vert_marker += "o"
                    else:
                        vert_marker += " "
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
    parser.add_argument(
        "--sizes",
        nargs=3,
        type=int,
        default=[2, 3, 2],
        help="Dimensions of the maze (x, y, z)",
    )
    parser.add_argument("-x", type=int, required=True, help="X dimension of the maze")
    parser.add_argument("-y", type=int, required=True, help="Y dimension of the maze")
    parser.add_argument("-z", type=int, required=True, help="Z dimension of the maze")
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="Output file path"
    )
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

    maze = Maze([args.x, args.y, args.z], output_path)
    maze.generate()
    maze.display_maze_3d()
