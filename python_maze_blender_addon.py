import bpy
import bmesh
import sys

path_to_add = "/home/olivier/projects/blender-maze"
if path_to_add not in sys.path:
    sys.path.append(path_to_add)

from python_maze import Maze

bl_info = {
    "name": "Créateur de Forme",
    "author": "Olivier Pons",
    "version": (1, 0),
    "blender": (4, 0, 1),
    "location": "View3D > Add > Mesh",
    "description": "Crée une forme complexe à partir de cubes",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}


class OBJECT_OT_add_shape(bpy.types.Operator):
    bl_idname = "mesh.add_shape"
    bl_label = "Maze v0.1"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
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
        maze = Maze([10, 5, 2], "/home/olivier/projects/blender-maze/out.txt")
        maze.generate()
        maze.display_maze_3d()
        out = maze.out
        x_size, y_size, z_size = maze.dimensions_sizes

        spacing = 5
        layer_size = x_size * y_size
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * layer_size
                    cell = maze.cells[cell_id]
                    xp, xn, yp, yn, zp, zn = cell.xp_xn_yp_yn_zp_zn()
                    center = [x * spacing, -y * spacing, z * spacing]
                    d = f"{cell_id=} : T{int(zp)}B{int(zn)} E{int(xp)}W{int(xn)} S{int(yp)}N{int(yn)}, {center=}"
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
                    # if not zp: c_l.append([center, 't'])
                    # if z == 0:
                    if not zn:
                        c_l.append([center, "b"])

        create_and_join_prisms(c_l, thickness=.8, distance=2.5)
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_add_shape.bl_idname, icon="MESH_CUBE")


def register():
    bpy.utils.register_class(OBJECT_OT_add_shape)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_shape)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()
