class_name ClipRetarget
extends RefCounted
## Brings an animation from another model with the same bone names (a Mixamo download) onto a
## model's own AnimationPlayer.
##
## Mixamo and Tripo name the bones alike (`mixamorig_Hips`) but build them differently: the bones'
## local axes differ (up to 180 degrees) and the rest poses differ (Mixamo is a T-pose, Tripo
## an A-pose), so the clip's rotations cannot be copied. The clip is retargeted instead: for
## every frame the source skeleton is posed, and each target bone is turned to point where the
## source bone points (model space), keeping the source's twist around the bone. The hips'
## position is scaled to the target's size.

const FPS := 30.0


## Copies the first animation of `source` (a scene with an AnimationPlayer and a Skeleton3D,
## e.g. a Mixamo `.fbx`) into `player`'s default library as `clip_name`, retargeted to the
## `Skeleton3D` of `target_model`, and returns it (null if either side has no skeleton or
## animation).
static func add_clip(player: AnimationPlayer, target_model: Node, source: PackedScene,
		clip_name: StringName, loop := true) -> Animation:
	var existing := player.get_animation_library(&"")
	if existing and existing.has_animation(clip_name):
		# The library is shared by every instance of the model: a clip added before is reused. A
		# clip of the model's own with this name is a mistake (it would be used instead of the file).
		if not existing.get_animation(clip_name).has_meta(&"retargeted_from"):
			push_error("ClipRetarget: the model already has its own clip '%s'; give the new one another name" % clip_name)
			return null
		return existing.get_animation(clip_name)
	var source_root: Node = source.instantiate()
	var source_player := _first(source_root, "AnimationPlayer") as AnimationPlayer
	var source_skeleton := _first(source_root, "Skeleton3D") as Skeleton3D
	var target_skeleton := _first(target_model, "Skeleton3D") as Skeleton3D
	if source_player == null or source_skeleton == null or target_skeleton == null \
			or source_player.get_animation_list().is_empty():
		source_root.queue_free()
		return null
	var source_clip := source_player.get_animation(source_player.get_animation_list()[0])
	var source_path := String(source_player.get_node(source_player.root_node).get_path_to(source_skeleton))
	var target_path := String(player.get_node(player.root_node).get_path_to(target_skeleton))
	var clip := _retarget(source_clip, source_skeleton, source_path, target_skeleton, target_path)
	clip.set_meta(&"retargeted_from", source.resource_path)
	clip.loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
	var library := player.get_animation_library(&"")
	if library == null:
		library = AnimationLibrary.new()
		player.add_animation_library(&"", library)
	library.add_animation(clip_name, clip)
	source_root.queue_free()
	return clip


static func _retarget(source_clip: Animation, source: Skeleton3D, source_path: String,
		target: Skeleton3D, target_path: String) -> Animation:
	var source_order := _parents_first(source)
	var target_order := _parents_first(target)
	var source_rest := _model_rotations(source)
	var target_rest := _model_rotations(target)
	# For each target bone: the source bone it follows and the direction (to the bone's guide
	# child, model space, at rest) on each side; guide < 0: no direction, the bone keeps its rest.
	var follows := PackedInt32Array()
	var source_dir: Array[Vector3] = []
	var target_dir: Array[Vector3] = []
	follows.resize(target.get_bone_count())
	for bone in target.get_bone_count():
		follows[bone] = -1
		source_dir.append(Vector3.ZERO)
		target_dir.append(Vector3.ZERO)
		var from_bone := source.find_bone(target.get_bone_name(bone))
		if from_bone < 0:
			continue
		var guide := _guide_child(source, from_bone)
		var target_guide := target.find_bone(source.get_bone_name(guide)) if guide >= 0 else -1
		if target_guide < 0 or target.get_bone_parent(target_guide) != bone:
			continue
		follows[bone] = from_bone
		source_dir[bone] = _rest_offset(source, from_bone, guide).normalized()
		target_dir[bone] = _rest_offset(target, bone, target_guide).normalized()

	var clip := Animation.new()
	clip.length = source_clip.length
	var rotation_tracks := {}
	for bone in target.get_bone_count():
		if follows[bone] >= 0:
			var track := clip.add_track(Animation.TYPE_ROTATION_3D)
			clip.track_set_path(track, NodePath("%s:%s" % [target_path, target.get_bone_name(bone)]))
			rotation_tracks[bone] = track
	var position_tracks := {}
	var position_scale := {}
	for bone in target.get_bone_count():
		var from_bone := source.find_bone(target.get_bone_name(bone))
		if target.get_bone_parent(bone) >= 0 or from_bone < 0:
			continue
		var source_track := source_clip.find_track(
				NodePath("%s:%s" % [source_path, source.get_bone_name(from_bone)]), Animation.TYPE_POSITION_3D)
		if source_track < 0:
			continue
		var track := clip.add_track(Animation.TYPE_POSITION_3D)
		clip.track_set_path(track, NodePath("%s:%s" % [target_path, target.get_bone_name(bone)]))
		position_tracks[bone] = [track, source_track, from_bone]
		position_scale[bone] = target.get_bone_rest(bone).origin.y / source.get_bone_rest(from_bone).origin.y

	var source_local_tracks: Array[int] = []
	for bone in source.get_bone_count():
		source_local_tracks.append(source_clip.find_track(
				NodePath("%s:%s" % [source_path, source.get_bone_name(bone)]), Animation.TYPE_ROTATION_3D))
	var frames := int(round(source_clip.length * FPS))
	for frame in frames + 1:
		var time := minf(frame / FPS, source_clip.length)
		var source_pose: Array[Quaternion] = []
		source_pose.resize(source.get_bone_count())
		for bone in source_order:
			var local := source.get_bone_rest(bone).basis.orthonormalized().get_rotation_quaternion()
			if source_local_tracks[bone] >= 0:
				local = source_clip.rotation_track_interpolate(source_local_tracks[bone], time)
			var parent := source.get_bone_parent(bone)
			source_pose[bone] = local if parent < 0 else source_pose[parent] * local
		var target_pose: Array[Quaternion] = []
		target_pose.resize(target.get_bone_count())
		for bone in target_order:
			var parent := target.get_bone_parent(bone)
			var pose: Quaternion
			if follows[bone] < 0:
				var rest_local := target.get_bone_rest(bone).basis.orthonormalized().get_rotation_quaternion()
				pose = rest_local if parent < 0 else target_pose[parent] * rest_local
			else:
				pose = _follow(source_pose[follows[bone]], source_rest[follows[bone]],
						source_dir[bone], target_dir[bone], target_rest[bone])
			target_pose[bone] = pose
			if rotation_tracks.has(bone):
				var local_pose := pose if parent < 0 else target_pose[parent].inverse() * pose
				clip.rotation_track_insert_key(rotation_tracks[bone], time, local_pose)
		for bone in position_tracks:
			var tracks: Array = position_tracks[bone]
			var value := source_clip.position_track_interpolate(tracks[1], time)
			clip.position_track_insert_key(tracks[0], time, value * position_scale[bone])
	return clip


## The target bone's model-space rotation when the source bone is in `source_pose`: its guide
## direction turned to where the source's points, then the source's twist around that bone.
static func _follow(source_pose: Quaternion, source_rest: Quaternion, source_dir: Vector3,
		target_dir: Vector3, target_rest: Quaternion) -> Quaternion:
	var moved := source_pose * source_rest.inverse()  # rest -> pose, model space
	var posed_dir := moved * source_dir
	var twist := Vector3(moved.x, moved.y, moved.z).dot(source_dir)
	var twist_angle := 2.0 * atan2(twist, moved.w)
	var swing := Quaternion(target_dir, posed_dir)
	return swing * Quaternion(target_dir, twist_angle) * target_rest


## The rest rotation of every bone in model space.
static func _model_rotations(skeleton: Skeleton3D) -> Array[Quaternion]:
	var rotations: Array[Quaternion] = []
	for bone in skeleton.get_bone_count():
		rotations.append(skeleton.get_bone_global_rest(bone).basis.orthonormalized().get_rotation_quaternion())
	return rotations


static func _rest_offset(skeleton: Skeleton3D, bone: int, child: int) -> Vector3:
	return skeleton.get_bone_global_rest(child).origin - skeleton.get_bone_global_rest(bone).origin


## The child a bone points at: the longest one, skipping left and right ones when there is a
## centre one (the hips point at the spine, not a leg). -1 for a bone with no children.
static func _guide_child(skeleton: Skeleton3D, bone: int) -> int:
	var children := skeleton.get_bone_children(bone)
	var centre: Array[int] = []
	for child in children:
		var child_name := skeleton.get_bone_name(child)
		if not (child_name.contains("Left") or child_name.contains("Right")):
			centre.append(child)
	var candidates: Array = centre if not centre.is_empty() else Array(children)
	var best := -1
	var best_length := 0.0
	for child: int in candidates:
		var length := skeleton.get_bone_rest(child).origin.length()
		if best < 0 or length > best_length:
			best = child
			best_length = length
	return best


static func _parents_first(skeleton: Skeleton3D) -> Array[int]:
	var order: Array[int] = []
	for root in skeleton.get_parentless_bones():
		order.append(root)
	var next := 0
	while next < order.size():
		for child in skeleton.get_bone_children(order[next]):
			order.append(child)
		next += 1
	return order


static func _first(root: Node, type: String) -> Node:
	var found := root.find_children("*", type, true, false)
	return found[0] if found else null
