import bpy
import json
import mathutils
from bpy.app.handlers import persistent

bl_info = {
    "name": "Amarillo's Pose Library",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 0, 17),
    "author": "Your Name",
    "description": "Save and manage multiple pose libraries per Blender file.",
}

addon_name = 'AmarillosPoseLibrary'  # Keep the original addon name for preferences

class AmarilloExpressionsPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_name  # Keep the original bl_idname

    armature_names: bpy.props.StringProperty(
        name="Default Armature Names",
        description="Comma-separated list of default armature names to include when saving poses",
        default=""
    )
    
    reset_unsaved_bones: bpy.props.BoolProperty(
        name="Reset Unsaved Bones to Initial Transform",
        description="Reset all bones not present in the saved pose to their initial transforms (position zero, rotation zero, scale one)",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Default Armature Names:")
        layout.prop(self, "armature_names", text="")
        layout.prop(self, "reset_unsaved_bones")

class PoseItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Pose Name")
    data: bpy.props.StringProperty(name="Pose Data")

class PoseLibraryItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Library Name")
    poses: bpy.props.CollectionProperty(type=PoseItem)
    poses_index: bpy.props.IntProperty(name="Index for poses", default=0)

class PoseLibrary:
    def __init__(self, context):
        self.scene = context.scene
        self.libraries = self.scene.pose_libraries
        self.active_library_index = self.scene.active_pose_library_index

    @property
    def active_library(self):
        if self.active_library_index >= 0 and self.active_library_index < len(self.libraries):
            return self.libraries[self.active_library_index]
        return None

    def save_pose(self, operator, name):
        pose_data = {}
        context = bpy.context

        # Check for active library
        library = self.active_library
        if not library:
            operator.report({'WARNING'}, "No active pose library selected.")
            return {'CANCELLED'}

        # Check if there is an active armature in pose mode
        active_obj = context.active_object
        if active_obj and active_obj.type == 'ARMATURE' and active_obj.mode == 'POSE':
            obj = active_obj
            armature_data = {}
            for bone in obj.pose.bones:
                bone_data = {
                    'location': list(bone.location),
                    'rotation_quaternion': list(bone.rotation_quaternion),
                    'scale': list(bone.scale)
                }
                armature_data[bone.name] = bone_data
            pose_data[obj.name] = armature_data
        else:
            prefs = bpy.context.preferences.addons[addon_name].preferences
            armature_names = [arm_name.strip() for arm_name in prefs.armature_names.split(",") if arm_name.strip() != ""]

            if not armature_names:
                operator.report({'WARNING'}, "No default armature names specified in addon preferences.")
                return {'CANCELLED'}

            for arm_name in armature_names:
                obj = bpy.data.objects.get(arm_name)
                if obj and obj.type == 'ARMATURE':
                    armature_data = {}
                    for bone in obj.pose.bones:
                        bone_data = {
                            'location': list(bone.location),
                            'rotation_quaternion': list(bone.rotation_quaternion),
                            'scale': list(bone.scale)
                        }
                        armature_data[bone.name] = bone_data
                    pose_data[obj.name] = armature_data
                else:
                    continue

        if not pose_data:
            operator.report({'WARNING'}, "No valid armatures found to save.")
            return {'CANCELLED'}

        pose_json = json.dumps(pose_data)
        existing = None
        for item in library.poses:
            if item.name == name:
                existing = item
                break
        if existing:
            existing.data = pose_json
            operator.report({'INFO'}, f"Updated pose: {name}")
        else:
            item = library.poses.add()
            item.name = name
            item.data = pose_json
            library.poses_index = len(library.poses) - 1
            operator.report({'INFO'}, f"Saved new pose: {name}")

    def load_pose(self, operator, name):
        library = self.active_library
        if not library:
            operator.report({'WARNING'}, "No active pose library selected.")
            return {'CANCELLED'}

        pose_item = None
        for item in library.poses:
            if item.name == name:
                pose_item = item
                break

        if pose_item:
            pose_data = json.loads(pose_item.data)

            prefs = bpy.context.preferences.addons[addon_name].preferences
            reset_unsaved_bones = prefs.reset_unsaved_bones

            for armature_name, armature_data in pose_data.items():
                obj = bpy.data.objects.get(armature_name)
                if obj and obj.type == 'ARMATURE':
                    for bone in obj.pose.bones:
                        if bone.name in armature_data:
                            bone_data = armature_data[bone.name]
                            bone.location = mathutils.Vector(bone_data['location'])
                            bone.rotation_quaternion = mathutils.Quaternion(bone_data['rotation_quaternion'])
                            bone.scale = mathutils.Vector(bone_data['scale'])
                        elif reset_unsaved_bones:
                            # Reset unsaved bones to initial transform
                            bone.location = mathutils.Vector((0, 0, 0))
                            bone.rotation_quaternion = mathutils.Quaternion((1, 0, 0, 0))
                            bone.scale = mathutils.Vector((1, 1, 1))
            bpy.context.view_layer.update()
            operator.report({'INFO'}, f"Loaded pose: {name}")
        else:
            operator.report({'WARNING'}, f"Pose '{name}' not found in the active library.")

    def delete_pose(self, operator, name):
        library = self.active_library
        if not library:
            operator.report({'WARNING'}, "No active pose library selected.")
            return

        for index, item in enumerate(library.poses):
            if item.name == name:
                library.poses.remove(index)
                operator.report({'INFO'}, f"Deleted pose: {name}")
                return
        operator.report({'WARNING'}, f"Pose '{name}' not found in the active library.")

class PoseLibraryUIList(bpy.types.UIList):
    bl_idname = "AMARILLO_UL_pose_library"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        pose = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=pose.name)
            load_op = row.operator("amarillo_pose.load_direct", text="", icon='IMPORT', emboss=False)
            load_op.pose_name = pose.name
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")

class PoseLibrariesUIList(bpy.types.UIList):
    bl_idname = "AMARILLO_UL_pose_libraries"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        library = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=library.name, icon='FILE_FOLDER')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='FILE_FOLDER')

class PoseLibraryPanel(bpy.types.Panel):
    bl_label = "Amarillo's Pose Library"
    bl_idname = "AMARILLO_PT_pose_library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Amarillo'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column()
        row = col.row()
        row.template_list("AMARILLO_UL_pose_libraries", "", scene, "pose_libraries", scene, "active_pose_library_index")

        lib_ops = row.column(align=True)
        lib_ops.operator("amarillo_pose.add_library", icon='ADD', text="")
        lib_ops.operator("amarillo_pose.remove_library", icon='REMOVE', text="")

        lib_ops.separator()
        lib_ops.operator("amarillo_pose.rename_library", icon='OUTLINER_DATA_FONT', text="")

        col.separator()
        col.operator("amarillo_pose.export_library", text="Export Library")
        col.operator("amarillo_pose.import_library", text="Import Library")

        library = None
        if scene.active_pose_library_index >= 0 and scene.active_pose_library_index < len(scene.pose_libraries):
            library = scene.pose_libraries[scene.active_pose_library_index]

        if library:
            col.separator()
            col.operator("amarillo_pose.save", text="Save Pose")

            if library.poses:
                row = col.row()
                row.template_list("AMARILLO_UL_pose_library", "", library, "poses", library, "poses_index")

                pose_ops = row.column(align=True)
                pose_ops.operator("amarillo_pose.move_pose", icon='TRIA_UP', text="").direction = 'UP'
                pose_ops.operator("amarillo_pose.move_pose", icon='TRIA_DOWN', text="").direction = 'DOWN'

                pose_ops.separator()
                pose_ops.operator("amarillo_pose.delete", icon='REMOVE', text="")

                col.operator("amarillo_pose.load", text="Load Selected Pose")
            else:
                col.label(text="No poses in this library.")
        else:
            col.label(text="No pose library selected.")

class AddPoseLibraryOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.add_library"
    bl_label = "Add Pose Library"

    library_name: bpy.props.StringProperty(name="Library Name", default="New Library")

    def execute(self, context):
        scene = context.scene
        new_lib = scene.pose_libraries.add()
        new_lib.name = self.library_name
        scene.active_pose_library_index = len(scene.pose_libraries) - 1
        return {'FINISHED'}

    def invoke(self, context, event):
        self.library_name = "New Library"
        return context.window_manager.invoke_props_dialog(self)

class RemovePoseLibraryOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.remove_library"
    bl_label = "Remove Pose Library"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        index = scene.active_pose_library_index
        if index >= 0 and index < len(scene.pose_libraries):
            scene.pose_libraries.remove(index)
            scene.active_pose_library_index = min(index, len(scene.pose_libraries) - 1)
            self.report({'INFO'}, "Pose library deleted.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

    def invoke(self, context, event):
        scene = context.scene
        index = scene.active_pose_library_index
        if index >= 0 and index < len(scene.pose_libraries):
            return context.window_manager.invoke_props_dialog(self)
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        index = scene.active_pose_library_index
        library_name = scene.pose_libraries[index].name
        layout.label(text=f"Remove Pose Library '{library_name}'?")
        layout.label(text="This will make you lose all the poses in it.")

class RenamePoseLibraryOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.rename_library"
    bl_label = "Rename Pose Library"

    new_name: bpy.props.StringProperty(name="New Name")

    def execute(self, context):
        scene = context.scene
        index = scene.active_pose_library_index
        if index >= 0 and index < len(scene.pose_libraries):
            scene.pose_libraries[index].name = self.new_name
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

    def invoke(self, context, event):
        scene = context.scene
        index = scene.active_pose_library_index
        if index >= 0 and index < len(scene.pose_libraries):
            self.new_name = scene.pose_libraries[index].name
            return context.window_manager.invoke_props_dialog(self)
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

class SavePoseOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.save"
    bl_label = "Save Pose"

    pose_name: bpy.props.StringProperty(name="Pose Name")

    def execute(self, context):
        if not self.pose_name.strip():
            self.report({'WARNING'}, "Pose name cannot be empty")
            return {'CANCELLED'}

        library = PoseLibrary(context)
        result = library.save_pose(self, self.pose_name.strip())
        return result if result else {'FINISHED'}

    def invoke(self, context, event):
        library = PoseLibrary(context)
        active_lib = library.active_library
        if active_lib:
            index = active_lib.poses_index
            if index >= 0 and index < len(active_lib.poses):
                self.pose_name = active_lib.poses[index].name
            else:
                self.pose_name = ""
            return context.window_manager.invoke_props_dialog(self)
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

class LoadPoseOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.load"
    bl_label = "Load Pose"

    def execute(self, context):
        library = PoseLibrary(context)
        active_lib = library.active_library
        if active_lib:
            index = active_lib.poses_index
            if index >= 0 and index < len(active_lib.poses):
                pose_name = active_lib.poses[index].name
                library.load_pose(self, pose_name)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No pose selected")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

class DeletePoseOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.delete"
    bl_label = "Delete Pose"
    bl_options = {'UNDO'}

    pose_name: bpy.props.StringProperty()

    def execute(self, context):
        library = PoseLibrary(context)
        library.delete_pose(self, self.pose_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        library = PoseLibrary(context)
        active_lib = library.active_library
        if active_lib:
            index = active_lib.poses_index
            if index >= 0 and index < len(active_lib.poses):
                self.pose_name = active_lib.poses[index].name
                return context.window_manager.invoke_confirm(self, event)
            else:
                self.report({'WARNING'}, "No pose selected")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

class LoadPoseDirectOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.load_direct"
    bl_label = "Load Pose Directly"

    pose_name: bpy.props.StringProperty()

    def execute(self, context):
        library = PoseLibrary(context)
        library.load_pose(self, self.pose_name)
        return {'FINISHED'}

class MovePoseOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.move_pose"
    bl_label = "Move Pose"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))

    def execute(self, context):
        scene = context.scene
        library = PoseLibrary(context).active_library
        if not library:
            self.report({'WARNING'}, "No pose library selected.")
            return {'CANCELLED'}

        index = library.poses_index

        if self.direction == 'UP':
            new_index = index - 1
            if new_index >= 0:
                library.poses.move(index, new_index)
                library.poses_index = new_index
        elif self.direction == 'DOWN':
            new_index = index + 1
            if new_index < len(library.poses):
                library.poses.move(index, new_index)
                library.poses_index = new_index

        return {'FINISHED'}

class ExportPoseLibraryOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.export_library"
    bl_label = "Export Pose Library"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        library = PoseLibrary(context).active_library
        if not library:
            self.report({'WARNING'}, "No active pose library selected.")
            return {'CANCELLED'}
        
        export_data = {
            "library_name": library.name,
            "poses": [{"name": pose.name, "data": pose.data} for pose in library.poses]
        }
        
        with open(self.filepath, 'w') as file:
            json.dump(export_data, file, indent=4)
        
        self.report({'INFO'}, f"Pose library '{library.name}' exported successfully.")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportPoseLibraryOperator(bpy.types.Operator):
    bl_idname = "amarillo_pose.import_library"
    bl_label = "Import Pose Library"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        
        with open(self.filepath, 'r') as file:
            import_data = json.load(file)
        
        new_library = scene.pose_libraries.add()
        new_library.name = import_data.get("library_name", "Imported Library")
        
        for pose in import_data.get("poses", []):
            pose_item = new_library.poses.add()
            pose_item.name = pose.get("name", "Unnamed Pose")
            pose_item.data = pose.get("data", "{}")
        
        scene.active_pose_library_index = len(scene.pose_libraries) - 1
        self.report({'INFO'}, f"Pose library '{new_library.name}' imported successfully.")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

classes = (
    AmarilloExpressionsPreferences,
    PoseItem,
    PoseLibraryItem,
    PoseLibraryUIList,
    PoseLibrariesUIList,
    PoseLibraryPanel,
    AddPoseLibraryOperator,
    RemovePoseLibraryOperator,
    RenamePoseLibraryOperator,
    SavePoseOperator,
    LoadPoseOperator,
    DeletePoseOperator,
    LoadPoseDirectOperator,
    MovePoseOperator,
    ExportPoseLibraryOperator,
    ImportPoseLibraryOperator,
)

@persistent
def migrate_old_poses(dummy):
    scene = bpy.context.scene
    if not hasattr(scene, 'pose_libraries'):
        return

    if getattr(scene, 'pose_library_migrated', False):
        return

    if hasattr(scene, 'expression_library') and scene.expression_library:
        if not scene.pose_libraries:
            default_lib = scene.pose_libraries.add()
            default_lib.name = "Default Library"
            for item in scene.expression_library:
                new_item = default_lib.poses.add()
                new_item.name = item.name
                new_item.data = item.data
            scene.active_pose_library_index = 0

        del scene.expression_library[:]
        scene.expression_library_index = 0
        scene.pose_library_migrated = True

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.expression_library = bpy.props.CollectionProperty(type=PoseItem)
    bpy.types.Scene.expression_library_index = bpy.props.IntProperty(name="Index for expression_library", default=0)
    bpy.types.Scene.pose_libraries = bpy.props.CollectionProperty(type=PoseLibraryItem)
    bpy.types.Scene.active_pose_library_index = bpy.props.IntProperty(name="Active Pose Library Index", default=0)
    bpy.types.Scene.pose_library_migrated = bpy.props.BoolProperty(default=False)

    bpy.app.handlers.load_post.append(migrate_old_poses)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.pose_libraries
    del bpy.types.Scene.active_pose_library_index
    del bpy.types.Scene.pose_library_migrated

    if hasattr(bpy.types.Scene, 'expression_library'):
        del bpy.types.Scene.expression_library
    if hasattr(bpy.types.Scene, 'expression_library_index'):
        del bpy.types.Scene.expression_library_index

    if migrate_old_poses in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(migrate_old_poses)

if __name__ == "__main__":
    register()
