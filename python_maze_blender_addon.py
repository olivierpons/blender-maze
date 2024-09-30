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

    x_size: bpy.props.IntProperty(name="X Size", default=3, min=1, max=100)
    y_size: bpy.props.IntProperty(name="Y Size", default=3, min=1, max=100)
    z_size: bpy.props.IntProperty(name="Z Size", default=1, min=1, max=100)
    wall_thickness: bpy.props.FloatProperty(
        name="Wall Thickness", default=0.1, min=0.01, max=1.0
    )
    wall_height: bpy.props.FloatProperty(
        name="Wall Height", default=1.0, min=0.1, max=5.0
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
            self.wall_height,
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
        layout.prop(self, "wall_height")
        layout.prop(self, "spacing")

    def generate_maze(self, context, x_size, y_size, z_size, wall_thickness, wall_height, spacing):
        maze = Maze(sizes=[x_size, y_size, z_size])
        maze.generate()

        vertices = []
        faces = []

        def add(idx_x, idx_y, vz):
            wt_div_2 = wall_thickness / 2
            base_x = idx_x * spacing
            base_y = idx_y * spacing
            vertices.append((base_x - wt_div_2, base_y - wt_div_2, vz))
            vertices.append((base_x + wt_div_2, base_y - wt_div_2, vz))
            vertices.append((base_x + wt_div_2, base_y + wt_div_2, vz))
            vertices.append((base_x - wt_div_2, base_y + wt_div_2, vz))

        # Generate all vertices
        for z in range(z_size + 2):
            for y in range(y_size + 1):
                for x in range(x_size + 1):
                    add(x, y, z * wall_height)
                    add(x, y, z * wall_height + wall_thickness)

        # done = False
        for y in range(y_size + 1):
            for x in range(x_size + 1):
                base = (y * (x_size + 1) + x) * 8
                faces.append([base, base + 1, base + 2])
                if x <= x_size - 1:
                    faces.append([base + 1, base + 8, base + 8 + 3, base + 2])

        # Create faces for walls
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * (x_size * y_size)
                    cell = maze.get_cell(cell_id)
        #
        #             base_index = (x + y * (x_size + 1) + z * (x_size + 1) * (y_size + 1)) * 16
        #
        #             # East wall
        #             if not cell.has_link_in_direction("e") and x < x_size - 1:
        #                 for i in range(8):
        #                     faces.append([
        #                         base_index + i * 2,
        #                         base_index + ((i + 1) % 8) * 2,
        #                         base_index + ((i + 1) % 8) * 2 + 1,
        #                         base_index + i * 2 + 1
        #                     ])
        #
        #             # South wall
        #             if not cell.has_link_in_direction("s") and y < y_size - 1:
        #                 south_base = base_index + (x_size + 1) * 16
        #                 for i in range(8):
        #                     faces.append([
        #                         base_index + ((i + 6) % 8) * 2,
        #                         south_base + ((i + 6) % 8) * 2,
        #                         south_base + ((i + 7) % 8) * 2,
        #                         base_index + ((i + 7) % 8) * 2
        #                     ])
        #
        #             # Up wall
        #             if not cell.has_link_in_direction("u") and z < z_size - 1:
        #                 up_base = base_index + (x_size + 1) * (y_size + 1) * 16
        #                 for i in range(8):
        #                     faces.append([
        #                         base_index + i * 2 + 1,
        #                         base_index + ((i + 1) % 8) * 2 + 1,
        #                         up_base + ((i + 1) % 8) * 2,
        #                         up_base + i * 2
        #                     ])

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
        layout.prop(props, "wall_height")
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
