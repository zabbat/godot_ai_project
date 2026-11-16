class_name SpringChains
extends SpringBoneSimulator3D
## Base for spring bones that swing a model's own bone chains: bones `<prefix>_<chain>_<n>`, added
## to the model's `.glb` by `add_bone_chains.py` (a cloak, a ponytail; the script is bundled with
## the godot-3d-models-and-animations skill). The
## subclass finds its chains (`chain_roots`), sets them up (`setup_chains`) and adds collision
## shapes on the body (`add_segment`, `add_capsule`, `add_sphere`).
##
## The simulation is centred on the skeleton: only the animation swings the chains, not the unit
## walking through the world or turning (else they whip about like in a storm). Sizes are in the
## skeleton's space (the model's own units: Tripo models are 1.0 tall).


## The first bone of each chain whose bones start with `prefix` + "_" (`<prefix>_a_0`, ...).
static func chain_roots(skeleton: Skeleton3D, prefix: String) -> Array[String]:
	var roots: Array[String] = []
	for bone in skeleton.get_bone_count():
		var bone_name := skeleton.get_bone_name(bone)
		if bone_name.begins_with(prefix + "_") and bone_name.ends_with("_0"):
			roots.append(bone_name)
	return roots


## One setting per chain in `roots` (each runs to its last bone, extended by `tip_length`), all
## colliding with every shape under this node.
func setup_chains(skeleton: Skeleton3D, roots: Array[String], stiffness: float, drag: float,
		gravity: float, joint_radius: float, tip_length: float) -> void:
	set_setting_count(roots.size())
	for i in roots.size():
		var root := roots[i]
		var chain := root.trim_suffix("_0")
		var n := 0
		while skeleton.find_bone("%s_%d" % [chain, n + 1]) != -1:
			n += 1
		set_root_bone_name(i, root)
		set_end_bone_name(i, "%s_%d" % [chain, n])
		set_extend_end_bone(i, true)
		set_end_bone_direction(i, BONE_DIRECTION_FROM_PARENT)
		set_end_bone_length(i, tip_length)
		set_radius(i, joint_radius)
		set_stiffness(i, stiffness)
		set_drag(i, drag)
		set_gravity(i, gravity)
		set_gravity_direction(i, Vector3.DOWN)
		set_enable_all_child_collisions(i, true)
		set_center_from(i, CENTER_FROM_NODE)
		set_center_node(i, get_path_to(skeleton))


## A capsule from bone `from`'s head to bone `to`'s head (in the rest pose), carried by `from`.
func add_segment(skeleton: Skeleton3D, from: String, to: String, radius: float, label: StringName) -> void:
	var a := skeleton.find_bone(from)
	var b := skeleton.find_bone(to)
	if a == -1 or b == -1:
		push_warning("%s: no bone '%s' or '%s'" % [name, from, to])
		return
	var head := skeleton.get_bone_global_rest(a).origin
	var tail := skeleton.get_bone_global_rest(b).origin
	var along := (tail - head).normalized()
	var basis := Basis(Quaternion(Vector3.UP, along))
	add_capsule(skeleton, a, Transform3D(basis, (head + tail) / 2.0), radius, head.distance_to(tail), label)


## A capsule carried by `bone`, placed at `shape` (skeleton space, in the rest pose; its axis is the
## transform's y), with a straight part `length` long.
func add_capsule(skeleton: Skeleton3D, bone: int, shape: Transform3D, radius: float, length: float,
		label: StringName) -> void:
	var capsule := SpringBoneCollisionCapsule3D.new()
	capsule.name = label
	_place(capsule, skeleton, bone, shape)
	capsule.radius = radius
	capsule.height = length + radius * 2.0
	add_child(capsule)


## A sphere carried by `bone`, its centre at `center` (skeleton space, in the rest pose).
func add_sphere(skeleton: Skeleton3D, bone: int, center: Vector3, radius: float, label: StringName) -> void:
	var sphere := SpringBoneCollisionSphere3D.new()
	sphere.name = label
	_place(sphere, skeleton, bone, Transform3D(Basis.IDENTITY, center))
	sphere.radius = radius
	add_child(sphere)


func _place(collision: SpringBoneCollision3D, skeleton: Skeleton3D, bone: int, shape: Transform3D) -> void:
	collision.bone = bone
	var offset := skeleton.get_bone_global_rest(bone).affine_inverse() * shape
	collision.position_offset = offset.origin
	collision.rotation_offset = offset.basis.get_rotation_quaternion()
