from pathlib import Path

import bpy
import bmesh
import sys

path_to_add = "/home/olivier/projects/blender-maze"
if path_to_add not in sys.path:
    sys.path.append(path_to_add)

from python_maze import Maze

bl_info = {
    "name": "Maze Generator",
    "author": "Olivier Pons",
    "version": (1, 2),
    "blender": (4, 0, 1),
    "location": "View3D > Add > Mesh",
    "description": "Generates a 3D maze",
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
    z_size: bpy.props.IntProperty(name="Z Size", default=2, min=1, max=100)
    thickness: bpy.props.FloatProperty(
        name="Wall Thickness", default=0.01, min=0.01, max=1.0
    )
    spacing: bpy.props.FloatProperty(
        name="Cell Spacing", default=1.5, min=0.1, max=10.0
    )

    def execute(self, context):
        self.generate_maze(
            context, self.x_size, self.y_size, self.z_size, self.thickness, self.spacing
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "x_size")
        layout.prop(self, "y_size")
        layout.prop(self, "z_size")
        layout.prop(self, "thickness")
        layout.prop(self, "spacing")

    @staticmethod
    def generate_maze(context, x_size, y_size, z_size, thickness, spacing):
        def out(msg):
            print(msg)

        def create_prism(location, direction, thickness, distance):
            vertices = [
                (-thickness, -distance, -distance),
                (+thickness, -distance, -distance),
                (+thickness, +distance, -distance),
                (-thickness, +distance, -distance),
                (-thickness, -distance, +distance),
                (+thickness, -distance, +distance),
                (+thickness, +distance, +distance),
                (-thickness, +distance, +distance),
            ]

            # Faces of the parallelepiped
            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (0, 3, 7, 4),
                (1, 2, 6, 5),
                (0, 1, 5, 4),
                (3, 2, 6, 7),
            ]

            # Creating the mesh
            mesh_data = bpy.data.meshes.new("prism_mesh_data")
            mesh_data.from_pydata(vertices, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new("Prism", mesh_data)
            bpy.context.collection.objects.link(obj)

            # Definition of rotation angles for each direction
            rotation_angles = {
                "n": (0, 0, 1.5708),
                "s": (0, 0, -1.5708),
                "e": (0, 0, 0),
                "w": (0, 0, 3.14159),
                "t": (0, 1.5708, 0),
                "b": (0, -1.5708, 0),
            }

            # Apply the rotation
            if direction in rotation_angles:
                obj.rotation_euler = rotation_angles[direction]

            # Offset to apply after rotation, taking into account the new orientation of the object
            offset_vectors = {
                "n": (0, distance, 0),
                "s": (0, -distance, 0),
                "e": (distance, 0, 0),
                "w": (-distance, 0, 0),
                "t": (0, 0, distance),
                "b": (0, 0, -distance),
            }

            # Apply the offset based on the direction
            if direction in offset_vectors:
                offset = offset_vectors[direction]
                # Using the object's offset method to apply the offset after the rotation
                obj.location = (
                    location[0] + offset[0],
                    location[1] + offset[1],
                    location[2] + offset[2],
                )

            out(f"{direction=} => {rotation_angles[direction]=}")
            return obj

        def create_and_join_prisms(prisms, thickness, distance):
            created_objects = []
            for location, direction in prisms:
                obj = create_prism(location, direction, thickness, distance)
                created_objects.append(obj)

            bpy.ops.object.select_all(action="DESELECT")
            for obj in created_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = created_objects[0]
            bpy.ops.object.join()

            # Switch to edit mode:
            bpy.ops.object.mode_set(mode="EDIT")

            # Prepare to use bmesh and merge by distance:
            bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

            # Count vertices before merging:
            verts_before = len(bm.verts)

            # Merge vertices by distance:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            # Count vertices after merging:
            verts_after = len(bm.verts)

            # Calculate the number of vertices removed:
            verts_removed = verts_before - verts_after

            # Update the mesh to reflect changes:
            bmesh.update_edit_mesh(bpy.context.active_object.data)

            # Switch back to object mode:
            bpy.ops.object.mode_set(mode="OBJECT")

            # Refresh the view:
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

            out(f"Vertices merged (removed): {verts_removed}")

        c_l = []
        maze = Maze(
            sizes=[x_size, y_size, z_size],
            output_file=Path("/home/olivier/projects/blender-maze/out.txt"),
            silent=False,
        )
        maze.generate()
        maze.display_maze_3d()
        out = maze.out
        layer_size = x_size * y_size

        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * layer_size
                    cell = maze.get_cell(cell_id)
                    center = [x * spacing, -y * spacing, z * spacing]

                    neighbors = maze.calculate_neighbors(cell_id)
                    xp = cell_id + 1 in cell.links
                    xn = cell_id - 1 in cell.links
                    yp = cell_id + x_size in cell.links
                    yn = cell_id - x_size in cell.links
                    zp = cell_id + layer_size in cell.links
                    zn = cell_id - layer_size in cell.links

                    d = (
                        f"{cell_id=} : "
                        f"N{int(yn)}S{int(yp)}"
                        f"E{int(xp)}W{int(xn)}"
                        f"T{int(zp)}B{int(zn)}"
                        f", {center=}"
                    )
                    w = []
                    if not xp:
                        w.append("e")
                    if not xn:
                        w.append("w")
                    if not yp:
                        w.append("s")
                    if not yn:
                        w.append("n")
                    if not zp:
                        w.append("t")
                    if not zn:
                        w.append("b")
                    maze.out("{}({})".format(d, "".join(w)).strip())
                    if not xp:
                        c_l.append([center, "e"])
                    if not xn:
                        c_l.append([center, "w"])
                    if not yp:
                        c_l.append([center, "s"])
                    if not yn:
                        c_l.append([center, "n"])
                    if not zn:
                        c_l.append([center, "b"])

        create_and_join_prisms(c_l, thickness=thickness, distance=spacing / 2)


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
        layout.prop(props, "thickness")
        layout.prop(props, "spacing")
        layout.operator("mesh.generate_maze")


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
