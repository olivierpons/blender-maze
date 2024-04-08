import random


class Maze:
    class Cell:
        def __init__(self, cell_id, dimensions_sizes):
            self.id = cell_id
            self.dimensions_sizes = dimensions_sizes
            self.links = set()
            self.not_done = set()

        def add_neighbor(self, neighbor_id):
            self.not_done.add(neighbor_id)

        def connect(self, neighbor):
            self.links.add(neighbor)
            if neighbor in self.not_done:
                self.not_done.remove(neighbor)

        @staticmethod
        def spatial(cell_id, dimensions_sizes):
            coordinates = []
            divisor = 1
            for size in reversed(dimensions_sizes):
                coordinates.append((cell_id // divisor) % size)
                divisor *= size
            coordinates.reverse()
            return tuple(coordinates)

    def __init__(self, *dimensions_sizes):
        self.dimensions_sizes = dimensions_sizes
        self.cells = self.generate_cells()

    def generate_cells(self):
        total_cells = 1
        for size in self.dimensions_sizes:
            total_cells *= size

        cells = {}
        for cell_id in range(total_cells):
            cell = Maze.Cell(cell_id, self.dimensions_sizes)
            neighbors = self.calculate_neighbors(cell_id)
            for neighbor_id in neighbors:
                cell.add_neighbor(neighbor_id)
            cells[cell_id] = cell
        return cells

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
                    total_cells = 1
                    for sz in self.dimensions_sizes:
                        total_cells *= sz
                    if 0 <= neighbor_id < total_cells:
                        neighbors.append(neighbor_id)
        return neighbors

    def generate(self):
        stack = []
        visited = set()

        start = random.choice(list(self.cells.keys()))
        stack.append(start)
        visited.add(start)

        while stack:
            current = stack[-1]
            current_cell = self.cells[current]
            unvisited_neighbors = [n for n in current_cell.not_done if n not in visited]

            if not unvisited_neighbors:
                stack.pop()
            else:
                neighbor = random.choice(unvisited_neighbors)
                current_cell.connect(neighbor)
                self.cells[neighbor].connect(current)
                visited.add(neighbor)
                stack.append(neighbor)

    def display_maze_3d(self):
        if len(self.dimensions_sizes) != 3:
            print("Cette méthode supporte uniquement des labyrinthes 3D.")
            return

        x_size, y_size, z_size = self.dimensions_sizes
        layer_size = x_size * y_size

        for layer in range(z_size):
            print(f"Layer {layer + 1}:")
            print("+" + "-------+" * x_size)
            for y in range(y_size):
                top = "|"
                bottom = "+"
                for x in range(x_size):
                    cell_id = x + y * x_size + layer * layer_size
                    cell = self.cells[cell_id]
                    right = "|" if ((cell_id + 1) % x_size) == 0 or (cell_id + 1) not in cell.links else " "
                    bottom += (
                        "       +"
                        if (cell_id + x_size) in cell.links
                        and cell_id + x_size < len(self.cells)
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
                print(top)
                print(bottom)

    def dump(self):
        if len(self.dimensions_sizes) != 3:
            print("Cette méthode supporte uniquement des labyrinthes 3D.")
            return

        x_size, y_size, z_size = self.dimensions_sizes
        layer_size = x_size * y_size

        for layer in range(z_size):
            print(f"Layer {layer + 1}:")
            for y in range(y_size):
                for x in range(x_size):
                    _id = x + y * x_size + layer * layer_size
                    cell = self.cells[_id]
                    coords = Maze.Cell.spatial(_id, self.dimensions_sizes)
                    links = [link_id for link_id in cell.links]
                    walls = [wall_id for wall_id in cell.not_done]
                    print(f"Cell {coords} (ID: {_id}) - Liens: {links}, Murs: {walls}")
        print("\n")


# random.seed(42)
maze_3d = Maze(10, 3, 3)
maze_3d.generate()
maze_3d.display_maze_3d()
# maze_3d.dump()
