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
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        def create_cube(location, size=1):
            # Calcul pour ajuster les sommets du cube selon la taille et la position
            s = size / 2.0
            vertices = [
                (location[0] - s, location[1] - s, location[2] - s),
                (location[0] + s, location[1] - s, location[2] - s),
                (location[0] + s, location[1] + s, location[2] - s),
                (location[0] - s, location[1] + s, location[2] - s),
                (location[0] - s, location[1] - s, location[2] + s),
                (location[0] + s, location[1] - s, location[2] + s),
                (location[0] + s, location[1] + s, location[2] + s),
                (location[0] - s, location[1] + s, location[2] + s)
            ]
            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (0, 3, 7, 4),
                (1, 2, 6, 5),
                (0, 1, 5, 4),
                (3, 2, 6, 7)
            ]
            mesh_data = bpy.data.meshes.new("cube_mesh_data")
            mesh_data.from_pydata(vertices, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new("Cube", mesh_data)
            bpy.context.collection.objects.link(obj)
            return obj

        def create_and_join_cubes(cube_locations, cube_size=1):
            created_objects = []
            for location in cube_locations:
                obj = create_cube(location, cube_size)
                created_objects.append(obj)

            bpy.ops.object.select_all(action='DESELECT')
            for obj in created_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = created_objects[0]
            bpy.ops.object.join()

            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')

            # Prepare to use bmesh and merge by distance
            bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

            # Count vertices before merging
            verts_before = len(bm.verts)

            # Merge vertices by distance
            result = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            # Count vertices after merging
            verts_after = len(bm.verts)

            # Calculate the number of vertices removed
            verts_removed = verts_before - verts_after

            # Update the mesh to reflect changes
            bmesh.update_edit_mesh(bpy.context.active_object.data)

            # Switch back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Refresh the view
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

            print(f"Vertices merged (removed): {verts_removed}")

        c_l = []

        maze = Maze([4, 3, 2], "/home/olivier/projects/blender-maze/out.txt")
        maze.generate()
        maze.display_maze_3d()
        x_size, y_size, z_size = maze.dimensions_sizes
        for z in range(z_size):
            for y in range(y_size):
                for x in range(x_size):
                    cell_id = x + y * x_size + z * z_size
                    cell = maze.cells[cell_id]
                    xp, xn, yp, yn, zp, zn = cell.xp_xn_yp_yn_zp_zn()
                    c_l.append((x*5-1, y*5-1, z*5-1))
                    c_l.append((x*5-1, y*5-1, z*5+1))
                    c_l.append((x*5-1, y*5+1, z*5-1))
                    c_l.append((x*5-1, y*5+1, z*5+1))
                    c_l.append((x*5+1, y*5-1, z*5-1))
                    c_l.append((x*5+1, y*5-1, z*5+1))
                    c_l.append((x*5+1, y*5+1, z*5-1))
                    c_l.append((x*5+1, y*5+1, z*5+1))
                    if not xp:
                        c_l.append((x*5+1, y*5, z*5))
                    if not xn:
                        c_l.append((x*5-1, y*5, z*5))
                    if not yp:
                        c_l.append((x*5, y*5+1, z*5))
                    if not yn:
                        c_l.append((x*5, y*5-1, z*5))
                    if not zp:
                        c_l.append((x*5, y*5, z*5+1))
                    if not zn:
                        c_l.append((x*5, y*5, z*5-1))
        create_and_join_cubes(c_l)

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_add_shape.bl_idname, icon='MESH_CUBE')


def register():
    bpy.utils.register_class(OBJECT_OT_add_shape)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_shape)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()
