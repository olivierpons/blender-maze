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

    x_size: bpy.props.IntProperty(name="X Size", default=2, min=1, max=100)
    y_size: bpy.props.IntProperty(name="Y Size", default=2, min=1, max=100)
    z_size: bpy.props.IntProperty(name="Z Size", default=1, min=1, max=100)
    wall_thickness: bpy.props.FloatProperty(
        name="Wall Thickness", default=0.1, min=0.01, max=1.0
    )
    wall_height: bpy.props.FloatProperty(
        name="Wall Height", default=1.0, min=0.1, max=5.0
    )
    spacing: bpy.props.FloatProperty(
        name="Cell Spacing", default=1.5, min=0.1, max=10.0
    )
    octagon_radius: bpy.props.FloatProperty(
        name="Octagon Radius", default=0.1, min=0.01, max=1.0
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
            self.octagon_radius,
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
        layout.prop(self, "octagon_radius")

    @staticmethod
    def create_octagon(location, radius, height):
        vertices = []
        faces = []

        for i in range(8):
            angle = i * (2 * math.pi / 8) + (math.pi / 8)  # Rotate by 22.5 degrees
            _x = location[0] + radius * math.cos(angle)
            _y = location[1] + radius * math.sin(angle)
            _z = location[2]
            vertices.append((_x, _y, _z))
            vertices.append((_x, _y, _z + height))

        for i in range(8):
            faces.append([2 * i, (2 * i + 2) % 16, (2 * i + 3) % 16, 2 * i + 1])
        faces.append(list(range(0, 16, 2)))
        faces.append(list(range(1, 16, 2))[::-1])

        return vertices, faces

    def create_wall(self, oct1_offset, oct2_offset, side, is_bottom=False):
        if not is_bottom:
            idx1 = side * 2 + 2
            idx2 = (side * 2 + 4) % 16
            result_faces = [
                [
                    oct1_offset + idx1,
                    oct1_offset + idx1 + 1,
                    oct2_offset + idx2 + 1,
                    oct2_offset + idx2,
                ],  # Front face
                [
                    oct1_offset + idx2,
                    oct1_offset + idx2 + 1,
                    oct2_offset + (idx2 + 2) % 16 + 1,
                    oct2_offset + (idx2 + 2) % 16,
                ],  # Back face
                [
                    oct1_offset + idx1,
                    oct2_offset + idx2,
                    oct2_offset + (idx2 + 2) % 16,
                    oct1_offset + idx2,
                ],  # Top face
                [
                    oct1_offset + idx1 + 1,
                    oct1_offset + idx2 + 1,
                    oct2_offset + (idx2 + 2) % 16 + 1,
                    oct2_offset + idx2 + 1,
                ],  # Bottom face
            ]
            self.out(result_faces)
        else:
            # For vertical walls, connect all sides
            result_faces = []
            # for i in range(8):
            #     idx1 = i * 2
            #     idx2 = (i * 2 + 2) % 16
            #     result_faces.append(
            #         [
            #             oct1_offset + idx1,
            #             oct1_offset + idx2,
            #             oct2_offset + idx2,
            #             oct2_offset + idx1,
            #         ]
            #     )

        return result_faces

    def generate_maze(
        self,
        context,
        x_size,
        y_size,
        z_size,
        wall_thickness,
        wall_height,
        spacing,
        octagon_radius,
    ):
        maze = Maze(sizes=[x_size, y_size, z_size])
        maze.generate()

        all_vertices = []
        all_faces = []
        vertex_offset = 0

        # Calculate the offset for proper alignment
        x_offset = spacing * (math.sqrt(2) - 1) / 2
        y_offset = spacing * (math.sqrt(2) - 1) / 2

        # Create all octagons (floors and walls)
        octagon_positions = {}
        for z in range(z_size + 1):
            for y in range(y_size + 1):
                for x in range(x_size + 1):
                    # Floor octagon
                    floor_location = (
                        x * spacing + x_offset,
                        -(y * spacing + y_offset),
                        z * (wall_height + wall_thickness),
                    )
                    floor_verts, floor_faces = self.create_octagon(
                        floor_location, octagon_radius, wall_thickness
                    )
                    octagon_positions[(x, y, z, "floor")] = vertex_offset
                    all_vertices.extend(floor_verts)
                    all_faces.extend(
                        [[f + vertex_offset for f in face] for face in floor_faces]
                    )
                    vertex_offset += len(floor_verts)

                    # Wall octagon
                    if z < z_size:
                        wall_location = (
                            x * spacing + x_offset,
                            -(y * spacing + y_offset),
                            z * (wall_height + wall_thickness) + wall_thickness,
                        )
                        wall_verts, wall_faces = self.create_octagon(
                            wall_location, octagon_radius, wall_height
                        )
                        octagon_positions[(x, y, z, "wall")] = vertex_offset
                        all_vertices.extend(wall_verts)
                        all_faces.extend(
                            [[f + vertex_offset for f in face] for face in wall_faces]
                        )
                        vertex_offset += len(wall_verts)

        # Create walls between octagons
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * (x_size * y_size)
                    cell = maze.get_cell(cell_id)

                    # Check walls in each direction
                    if not cell.has_link_in_direction("e") and x < x_size - 1:
                        oct1_offset = octagon_positions[(x, y, z, "wall")]
                        oct2_offset = octagon_positions[(x + 1, y, z, "wall")]
                        wall_faces = self.create_wall(oct1_offset, oct2_offset, 2)
                        all_faces.extend(wall_faces)

                    if not cell.has_link_in_direction("s") and y < y_size - 1:
                        oct1_offset = octagon_positions[(x, y, z, "wall")]
                        oct2_offset = octagon_positions[(x, y + 1, z, "wall")]
                        wall_faces = self.create_wall(oct1_offset, oct2_offset, 4)
                        all_faces.extend(wall_faces)

                    if not cell.has_link_in_direction("u") and z < z_size - 1:
                        oct1_offset = octagon_positions[(x, y, z, "wall")]
                        oct2_offset = octagon_positions[(x, y, z + 1, "floor")]
                        wall_faces = self.create_wall(
                            oct1_offset, oct2_offset, 0, is_bottom=True
                        )
                        all_faces.extend(wall_faces)

        # Create the final mesh
        mesh = bpy.data.meshes.new("Maze")
        mesh.from_pydata(all_vertices, [], all_faces)
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
        layout.prop(props, "octagon_radius")
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
