import math
from pathlib import Path
from typing import Callable

import bpy
import sys

path_to_add = "/home/olivier/projects/blender-maze"
if path_to_add not in sys.path:
    sys.path.append(path_to_add)

from python_maze import Maze

bl_info = {
    "name": "Maze Generator",
    "author": "Olivier Pons",
    "version": (1, 2),
    "blender": (4, 2, 1),
    "location": "View3D > Add > Mesh",
    "description": "Generates a 3D maze with octagons for floors and walls, with proper vertical connections",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}


class MAZE_OT_generator_popup(bpy.types.Operator):
    bl_idname = "mesh.generate_maze_popup"
    bl_label = "Generate Maze"
    bl_options = {"REGISTER", "UNDO"}

    x_size: bpy.props.IntProperty(name="X Size", default=2, min=1, max=20)
    y_size: bpy.props.IntProperty(name="Y Size", default=1, min=1, max=20)
    z_size: bpy.props.IntProperty(name="Z Size", default=1, min=1, max=20)
    wall_thickness: bpy.props.FloatProperty(
        name="Wall Thickness", default=0.1, min=0.01, max=1.0
    )
    spacing: bpy.props.FloatProperty(
        name="Cell Spacing", default=1.0, min=0.1, max=10.0
    )

    def _out_verbose(self, content):
        if self._output_file:
            with open(self._output_file, "a") as file:
                file.write(f"{content}\n")
        else:
            print(content)

    def execute(self, context):
        self.generate_maze(
            context,
            self.x_size,
            self.y_size,
            self.z_size,
            self.wall_thickness,
            self.spacing,
        )
        return {"FINISHED"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output_file = Path("/home/olivier/projects/blender-maze/out.txt")
        self.out: Callable[[str], None] = self._out_verbose

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "x_size")
        layout.prop(self, "y_size")
        layout.prop(self, "z_size")
        layout.prop(self, "wall_thickness")
        layout.prop(self, "spacing")

    @staticmethod
    def generate_maze(context, x_size, y_size, z_size, wall_thickness, spacing):
        maze = Maze(sizes=[x_size, y_size, z_size], silent=False)
        maze.generate()
        maze.display_maze_3d()

        vertices = []
        faces = []

        # Generate all vertices
        for idx_z in range(z_size):
            for idx_y in range(y_size):
                for idx_x in range(x_size):
                    step = wall_thickness + spacing
                    s2 = spacing / 2
                    center_x = idx_x * step
                    center_y = idx_y * step
                    center_z = idx_z * step
                    c_x_sub_2 = round(center_x - s2, 2)
                    c_x_add_2 = round(center_x + s2, 2)
                    c_y_sub_2 = round(center_y - s2, 2)
                    c_y_add_2 = round(center_y + s2, 2)
                    c_z_sub_2 = round(center_z - s2, 2)
                    c_z_add_2 = round(center_z + s2, 2)
                    vertices.append((c_x_sub_2, c_y_sub_2, c_z_sub_2))
                    vertices.append((c_x_add_2, c_y_sub_2, c_z_sub_2))
                    vertices.append((c_x_add_2, c_y_add_2, c_z_sub_2))
                    vertices.append((c_x_sub_2, c_y_add_2, c_z_sub_2))
                    vertices.append((c_x_sub_2, c_y_sub_2, c_z_add_2))
                    vertices.append((c_x_add_2, c_y_sub_2, c_z_add_2))
                    vertices.append((c_x_add_2, c_y_add_2, c_z_add_2))
                    vertices.append((c_x_sub_2, c_y_add_2, c_z_add_2))

        print(", ".join([f"{idx}: {a}" for idx, a in enumerate(vertices)]))
        print(f"{len(vertices)}")
        # Create faces for walls
        # Create faces for walls
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    base = (x + y * x_size + z * x_size * y_size) * 8
                    cell_id = x + y * x_size + z * (x_size * y_size)
                    cell = maze.get_cell(cell_id)
                    print(str(cell))

                    # North wall
                    if y == y_size - 1 or not cell.has_link_in_direction("n"):
                        faces.append([base + 2, base + 3, base + 7, base + 6])

                    # East wall
                    if x == x_size - 1 or not cell.has_link_in_direction("e"):
                        faces.append([base + 1, base + 2, base + 6, base + 5])

                    # South wall
                    if y == 0 or not cell.has_link_in_direction("s"):
                        faces.append([base + 0, base + 1, base + 5, base + 4])

                    # West wall
                    if x == 0 or not cell.has_link_in_direction("w"):
                        faces.append([base + 0, base + 3, base + 7, base + 4])

                    # Up wall
                    # if z == z_size - 1 or not cell.has_link_in_direction("u"):
                    #     faces.append([base + 4, base + 5, base + 6, base + 7])

                    # Down wall
                    if z == 0 or not cell.has_link_in_direction("d"):
                        faces.append([base + 0, base + 1, base + 2, base + 3])

                    # Log information for debugging
                    print(f"Cell {cell_id} at ({x}, {y}, {z}):")
                    print(f"  Links: {cell.links}")
                    print(f"  Faces: {faces[-6:]}")
        # Create the mesh
        mesh = bpy.data.meshes.new("Maze")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        obj = bpy.data.objects.new("Maze", mesh)
        bpy.context.collection.objects.link(obj)

        # Clean up the geometry
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.object.mode_set(mode="OBJECT")


class MAZE_PT_generator_panel(bpy.types.Panel):
    bl_label = "Maze Generator"
    bl_idname = "MAZE_PT_generator_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.maze_generator_props

        layout.prop(props, "x_size")
        layout.prop(props, "y_size")
        layout.prop(props, "z_size")
        layout.prop(props, "wall_thickness")
        layout.prop(props, "spacing")
        layout.operator("mesh.generate_maze_popup")


def menu_func(self, context):
    self.layout.operator(MAZE_OT_generator_popup.bl_idname, icon="MESH_CUBE")


def register():
    bpy.utils.register_class(MAZE_OT_generator_popup)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(MAZE_OT_generator_popup)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()
