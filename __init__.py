# This script creates two kinds of isometric cameras.
#The one, TrueIsocam called camera, is the mathematical correct isometric camera with the 54.736 rotation to get the 30 degrees angles at the sides of the rhombus.
#The other, GameIsocam called camera, is a camera with which you can render isometric tiles for a 2d game. Here we need a 60 degrees angle instedad of the 54.736 one to get a proper stairs effect and a ratio of 2:1
# Then there is the special case with a 4:3 ratio, which is button 3. You can also make 2D games with that one. The view is more topdown though as with a 2:1 ratio of the traditional game iso view.
# The fourth button creates a simple groundplane where you can place your stuff at.

# You can of course set up everything by hand. This script is a convenient solution so that you don't have to setup it again and again.

# The script is under Apache license

bl_info = {
    "name": "Create IsoCam",
    "description": "Creates a true isometric camera or a isometric camera for game needs",
    "author": "Reiner 'Tiles' Prokein",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "location": "Toolshelf",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Create_IsoCam",
    "category": "Create"}


import bpy
from bpy.types import Panel,Operator,PropertyGroup
from bpy.props import EnumProperty, FloatProperty
from mathutils import Vector

# Third party application
from . import addon_updater_ops


def _selection_bounds_in_view(camera, objects):
    """Return (center, width, height, depth, forward) of objects' combined
    bounding box, expressed along the camera's right/up/forward axes."""
    corners = []
    for obj in objects:
        if obj.type in {'CAMERA', 'LIGHT'} or not hasattr(obj, "bound_box"):
            continue
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not corners:
        return None

    basis = camera.matrix_world.to_3x3()
    right = (basis @ Vector((1, 0, 0))).normalized()
    up = (basis @ Vector((0, 1, 0))).normalized()
    forward = (basis @ Vector((0, 0, -1))).normalized()

    xs = [c.dot(right) for c in corners]
    ys = [c.dot(up) for c in corners]
    zs = [c.dot(forward) for c in corners]

    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    depth = max(zs) - min(zs)
    center = (right * (max(xs) + min(xs)) / 2
              + up * (max(ys) + min(ys)) / 2
              + forward * (max(zs) + min(zs)) / 2)
    return center, width, height, depth, forward


def frame_camera_on_objects(camera, objects, units_per_pixel, margin=1.05):
    """Center camera on objects and set render resolution so that
    units_per_pixel Blender units always equal one output pixel."""
    bounds = _selection_bounds_in_view(camera, objects)
    if bounds is None:
        return False
    center, width, height, depth, forward = bounds

    width *= margin
    height *= margin

    distance = depth / 2 + max(width, height, 1.0)
    camera.location = center - forward * distance
    camera.data.clip_end = max(camera.data.clip_end, distance + depth + max(width, height))

    camera.data.sensor_fit = 'AUTO'
    camera.data.ortho_scale = max(width, height)

    render = bpy.context.scene.render
    render.resolution_x = max(1, round(width / units_per_pixel))
    render.resolution_y = max(1, round(height / units_per_pixel))
    render.pixel_aspect_x = 1.0
    render.pixel_aspect_y = 1.0
    return True


class PR_GT_listofisocam(PropertyGroup):
    list_isocam: EnumProperty (
        name = "",
        description = "",
        items = [
        ("ITEM_1", "TrueIsoCam",""),
        ("ITEM_2", "GameIsoCam",""),
        ("ITEM_3", "GameIsoTo3Cam",""),
        ("ITEM_4", "GroundPlane", "")
        ])
    pixel_density: FloatProperty(
        name="Units per Pixel",
        description="Blender units represented by one output pixel when framing a selection",
        default=0.01,
        min=0.0001,
        subtype='DISTANCE',
        unit='LENGTH',
        )

class PR_OT_createisocams(Operator):
    """Creates a camera on 4 different isometric views"""
    bl_label = "GENERATE"
    bl_idname = "scene.create_isocams"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self,context):
        scene = context.scene
        custom_isocam_property = scene.custom_isocam
        # Captured before any camera-add operator runs, since those change selection.
        target_objects = [obj for obj in context.selected_objects
                           if obj.type not in {'CAMERA', 'LIGHT'}]

        if custom_isocam_property.list_isocam == "ITEM_1":
            # ----------------------------Create Camera with correct position and rotation
            bpy.ops.object.camera_add(location=(30.60861, -30.60861, 30.60861)) # Create Camera. I would love to set the rotation here too. Blender not. Not that there are no tutorials around which shows that it should work ... .

            #So that's what the next two lines are good for. Setting the rotation of the camera ...

            object = bpy.context.active_object
            object.rotation_euler = (0.955324, 0, 0.785398) #Attention, these are radians. Euler angles are (54.736,0,45) Here we set the rotation for a mathematical correct isometric view. Not to mix with the Isoview for a 2D game!

            # ------------------------------Here we adjust some settings ---------------------------------
            object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
            object.data.ortho_scale = 14.123 # Let's fit the camera to a basetile in size of 10
            object.name = "TrueIsoCam" # let's rename the cam so that it cannot be confused with other cameras.
            bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through
            if target_objects:
                frame_camera_on_objects(object, target_objects, custom_isocam_property.pixel_density)
        elif custom_isocam_property.list_isocam == "ITEM_2":
            view_layer = bpy.context.view_layer
            # ----------------------------Create Camera with correct position and rotation
            cam1 =  bpy.data.cameras.new(name="Camera Iso Test")
            # ------------------------------Here we adjust some settings ---------------------------------

            cam1.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
            cam1.ortho_scale=14.123 # Let's fit the camera to our basetile in size of 10
            camera = bpy.data.objects.new(name="Camera Iso", object_data =cam1)
            view_layer.active_layer_collection.collection.objects.link(camera)
            camera.location = (30.60861, -30.60861, 25.00000)
            camera.rotation_euler=(1.047198, 0, 0.785398) #Attention, these are radians. Euler angles are (60,0,45) Here we set the rotation for a isometric view that is used in 2D games. Not to mix with the mathematical correct Isoview!

            # object_as_camera() acts on the active object, which linking alone does not set.
            for obj in view_layer.objects:
                obj.select_set(False)
            camera.select_set(True)
            view_layer.objects.active = camera
            bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through
            if target_objects:
                frame_camera_on_objects(camera, target_objects, custom_isocam_property.pixel_density)
        elif custom_isocam_property.list_isocam == "ITEM_3":
            # ----------------------------Create Camera with correct position and rotation
            bpy.ops.object.camera_add(location=(23.42714, -23.42714, 37.4478)) # Create Camera. I would love to set the rotation here too. Blender not. Not that there are no tutorials around which shows that it should work ... .

            #So that's what the next two lines are good for. Setting the rotation of the camera ...

            object = bpy.context.active_object
            object.rotation_euler = (0.724312, 0, 0.785398)#Attention, these are radians. Euler angles are (41.5,0,45) Here we set the rotation for a isometric view that is used in 2D games. Not to mix with the mathematical correct Isoview!

            # ------------------------------Here we adjust some settings ---------------------------------
            object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
            object.data.ortho_scale = 14.123  # Let's fit the camera to our basetile in size of 10
            object.name = "GameIso4to3Cam" # let's rename the cam so that it cannot be confused with other cameras.
            bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through
            if target_objects:
                frame_camera_on_objects(object, target_objects, custom_isocam_property.pixel_density)

        elif custom_isocam_property.list_isocam == "ITEM_4":
            bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0)) # Create Camera. I would love to set the scale here too. Blender not. So let's do it in an extra step
            object = bpy.context.active_object
            object.scale = (5, 5, 0)#The plane object is created with a size of 2. Scaling it to 10 means to scale it by factor 5
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)# apply scale

        return {"FINISHED"}

class PR_OT_frameisocamselection(Operator):
    """Recenter the scene camera on the current selection and set the render resolution to match the Units per Pixel setting"""
    bl_label = "Frame Selection"
    bl_idname = "scene.frame_isocam_selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT' or context.scene.camera is None:
            return False
        return any(obj.type not in {'CAMERA', 'LIGHT'} for obj in context.selected_objects)

    def execute(self, context):
        custom_isocam_property = context.scene.custom_isocam
        target_objects = [obj for obj in context.selected_objects
                           if obj.type not in {'CAMERA', 'LIGHT'}]
        camera = context.scene.camera
        if not frame_camera_on_objects(camera, target_objects, custom_isocam_property.pixel_density):
            self.report({'WARNING'}, "Selected objects have no bounding box to frame")
            return {'CANCELLED'}
        return {"FINISHED"}

class PR_PT_createisocampanel(Panel):
    bl_label = "Create IsoCam"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PR Isocam"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        custom_pg = context.scene.custom_isocam

        col = layout.row(align=False)
        col.scale_x = 2.0
        col.scale_y = 2.0
        col.operator("scene.create_isocams", icon="RESTRICT_VIEW_OFF")

        col = layout.row(align=False)
        col.scale_x = 1.6
        col.scale_y = 1.6
        col.prop(custom_pg, "list_isocam")

        col = layout.column(align=False)
        col.prop(custom_pg, "pixel_density")
        col.operator("scene.frame_isocam_selection")

        col = layout.column(align=False)
        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready:
            col.label(text="Create IsoCam Successfuly Update", icon="INFO")
        addon_updater_ops.update_notice_box_ui(self, context)

@addon_updater_ops.make_annotations
class CreateIsocamPreferences(bpy.types.AddonPreferences):
	"""Demo bare-bones preferences"""
	bl_idname = __package__

	# Addon updater preferences.

	auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

	updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

	updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

	updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

	updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

	def draw(self, context):
		layout = self.layout

		# Works best if a column, or even just self.layout.
		mainrow = layout.row()
		col = mainrow.column()

		# Updater draw function, could also pass in col as third arg.
		addon_updater_ops.update_settings_ui(self, context)

		# Alternate draw function, which is more condensed and can be
		# placed within an existing draw function. Only contains:
		#   1) check for update/update now buttons
		#   2) toggle for auto-check (interval will be equal to what is set above)
		# addon_updater_ops.update_settings_ui_condensed(self, context, col)

		# Adding another column to help show the above condensed ui as one column
		# col = mainrow.column()
		# col.scale_y = 2
		# ops = col.operator("wm.url_open","Open webpage ")
		# ops.url=addon_updater_ops.updater.website




classes = (PR_GT_listofisocam, PR_OT_createisocams, PR_OT_frameisocamselection, PR_PT_createisocampanel, CreateIsocamPreferences)

def register():
    addon_updater_ops.register(bl_info)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.custom_isocam = bpy.props.PointerProperty(type= PR_GT_listofisocam)

def unregister():
    addon_updater_ops.unregister()
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.custom_isocam

if __name__ == "__main__":
    register()
