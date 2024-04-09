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

        def create_prism(location, direction, thickness=0.2, mz=None):
            # Dimensions du parallélépipède
            width, depth, height = thickness, thickness * 4, thickness * 4

            # Ajustement des sommets selon l'épaisseur et la position, initial sans décalage
            w, d, h = width / 2.0, depth / 2.0, height / 2.0
            vertices = [
                (-w, -d, -h),
                (+w, -d, -h),
                (+w, +d, -h),
                (-w, +d, -h),
                (-w, -d, +h),
                (+w, -d, +h),
                (+w, +d, +h),
                (-w, +d, +h),
            ]

            # Les faces du parallélépipède
            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (0, 3, 7, 4),
                (1, 2, 6, 5),
                (0, 1, 5, 4),
                (3, 2, 6, 7),
            ]

            # Création du maillage
            mesh_data = bpy.data.meshes.new("prism_mesh_data")
            mesh_data.from_pydata(vertices, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new("Prism", mesh_data)
            bpy.context.collection.objects.link(obj)

            # Définition des angles de rotation pour chaque direction
            rotation_angles = {
                "n": (0, 0, 1.5708),
                "s": (0, 0, -1.5708),
                "e": (0, 0, 0),
                "w": (0, 0, 3.14159),
                "t": (0, 1.5708, 0),
                "b": (0, -1.5708, 0),
            }

            # Appliquer la rotation
            if direction in rotation_angles:
                obj.rotation_euler = rotation_angles[direction]

            # Décalage à appliquer après rotation, en tenant compte de la nouvelle orientation de l'objet
            offset_vectors = {
                "n": (0, depth / 2.0, 0),
                "s": (0, -depth / 2.0, 0),
                "e": (depth / 2.0, 0, 0),
                "w": (-depth / 2.0, 0, 0),
                "t": (0, 0, height / 2.0),
                "b": (0, 0, -height / 2.0),
            }

            # Appliquer le décalage en fonction de la direction
            if direction in offset_vectors:
                offset = offset_vectors[direction]
                # Utiliser la méthode de décalage sur l'objet pour appliquer le décalage après la rotation
                obj.location = (
                    location[0] + offset[0],
                    location[1] + offset[1],
                    location[2] + offset[2],
                )

            # if mz:
            #     mz.out(f"{direction=} => {rotation_angles[direction]=}")

            return obj

        def create_and_join_prisms(prisms, thickness=0.2, mz=None):
            created_objects = []
            for loc, d in prisms:
                obj = create_prism(loc, d, thickness, mz)
                created_objects.append(obj)

            bpy.ops.object.select_all(action="DESELECT")
            for obj in created_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = created_objects[0]
            bpy.ops.object.join()

            # Switch to edit mode
            bpy.ops.object.mode_set(mode="EDIT")

            # Prepare to use bmesh and merge by distance
            bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

            # Count vertices before merging
            verts_before = len(bm.verts)

            # Merge vertices by distance
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            # Count vertices after merging
            verts_after = len(bm.verts)

            # Calculate the number of vertices removed
            verts_removed = verts_before - verts_after

            # Update the mesh to reflect changes
            bmesh.update_edit_mesh(bpy.context.active_object.data)

            # Switch back to object mode
            bpy.ops.object.mode_set(mode="OBJECT")

            # Refresh the view
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

            mz.out(f"Vertices merged (removed): {verts_removed}")

        c_l = []
        maze = Maze([8, 6, 6], "/home/olivier/projects/blender-maze/out.txt")
        maze.generate()
        maze.display_maze_3d()
        x_size, y_size, z_size = maze.dimensions_sizes

        layer_size = x_size * y_size
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * layer_size
                    cell = maze.cells[cell_id]
                    xp, xn, yp, yn, zp, zn = cell.xp_xn_yp_yn_zp_zn()
                    center = [x * 5, -y * 5, z * 5]
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

        create_and_join_prisms(c_l, thickness=1, mz=maze)

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
