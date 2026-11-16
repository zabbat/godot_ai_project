# Measures how a spring-bone chain hangs and swings, standing and walking, in numbers.
#
#   godot --headless --path <project> -s <absolute path>/spring_measure.gd -- \
#       <visual.tscn> <chain root bone> <chain last bone> <reference bone> [tip_length] [speed]
#
# e.g. `-- res://entities/defender/defender_visual.tscn ponytail_a_0 ponytail_a_3 mixamorig_Head`.
# The visual scene's root must have `set_moving(bool)` (it plays the walk and tells the spring
# bones). Four copies run side by side: standing, walking in place, walking while the copy moves
# through the world at `speed` (default 9 m/s), and the same turned 90 degrees. For each it prints
# the chain (root joint -> tip; the tip is the last joint plus `tip_length` along it, default 0.05)
# against its rest direction, after the reference bone's own turn is taken out (the head's turn for
# a ponytail, Spine2's for a cloak): the lean toward the back (+) in degrees and the side swing
# (+ = the model's +x), min, mean and max over 2.5 s. Axes are the skeleton's (the model file's: +y
# up, +z the model's front, the glTF convention).
#
# What the numbers say: walking in place, moving and turned should match when the simulation is
# centred on the skeleton (else the unit's own travel whips the chain); standing should be near 0
# (the modelled pose); walking shows the swing and any push.
#
# Spring-bone results are only readable inside `Skeleton3D.skeleton_updated`: after the frame the
# bones are back to the animation pose, and a measurement there shows nothing.
extends SceneTree

const CASES := ["stand", "walk", "walk_move", "walk_move_turned"]
const SETTLE_SECONDS := 1.5
const RUN_SECONDS := 4.0

var _args: PackedStringArray
var _tip_length := 0.05
var _speed := 9.0
var _time := 0.0
var _data := {}


func _initialize() -> void:
	_args = OS.get_cmdline_user_args()
	if _args.size() < 4:
		print("usage: -- <visual.tscn> <chain root bone> <chain last bone> <reference bone> [tip_length] [speed]")
		quit(1)
		return
	if _args.size() > 4:
		_tip_length = float(_args[4])
	if _args.size() > 5:
		_speed = float(_args[5])
	_run()


func _run() -> void:
	var scene: PackedScene = load(_args[0])
	for c in CASES:
		var root := Node3D.new()
		get_root().add_child(root)
		if c.ends_with("_turned"):
			root.rotation.y = PI / 2.0
		var visual := scene.instantiate() as Node3D
		root.add_child(visual)
		var skeletons := visual.find_children("*", "Skeleton3D", true, false)
		if skeletons.is_empty():
			print("no Skeleton3D in ", _args[0])
			quit(1)
			return
		var skeleton: Skeleton3D = skeletons[0]
		for bone_name in [_args[1], _args[2], _args[3]]:
			if skeleton.find_bone(bone_name) == -1:
				print("no bone '%s'" % bone_name)
				quit(1)
				return
		_data[c] = {"root": root, "visual": visual, "skeleton": skeleton, "lean": [], "side": []}
		skeleton.skeleton_updated.connect(_sample.bind(c))
	for _f in 3:
		await process_frame
	for c in CASES:
		if c != "stand":
			_data[c]["visual"].call("set_moving", true)
	while _time < RUN_SECONDS:
		await process_frame
		var delta := 1.0 / 60.0
		_time += delta
		for c in CASES:
			if c.contains("move"):
				var root: Node3D = _data[c]["root"]
				root.position += root.global_basis * Vector3.FORWARD * _speed * delta
	print("chain %s -> %s (+%.3f), against %s" % [_args[1], _args[2], _tip_length, _args[3]])
	for c in CASES:
		var lean: Array = _data[c]["lean"]
		var side: Array = _data[c]["side"]
		print("RESULT %-17s lean back min %6.1f mean %6.1f max %6.1f | side min %6.1f mean %6.1f max %6.1f" % [
			c, lean.min(), _mean(lean), lean.max(), side.min(), _mean(side), side.max()])
	quit()


func _sample(c: String) -> void:
	if _time < SETTLE_SECONDS:
		return
	var skeleton: Skeleton3D = _data[c]["skeleton"]
	var root_bone := skeleton.find_bone(_args[1])
	var last_bone := skeleton.find_bone(_args[2])
	var reference := skeleton.find_bone(_args[3])
	var before_last := skeleton.get_bone_parent(last_bone)
	# The chain now, with the reference bone's turn since its rest taken out.
	var turn := skeleton.get_bone_global_pose(reference).basis.orthonormalized() \
		* skeleton.get_bone_global_rest(reference).basis.orthonormalized().inverse()
	var now := turn.inverse() * (_tip(skeleton.get_bone_global_pose(before_last).origin,
		skeleton.get_bone_global_pose(last_bone).origin) - skeleton.get_bone_global_pose(root_bone).origin)
	var rest := _tip(skeleton.get_bone_global_rest(before_last).origin,
		skeleton.get_bone_global_rest(last_bone).origin) - skeleton.get_bone_global_rest(root_bone).origin
	_data[c]["lean"].append(rad_to_deg(atan2(-now.z, -now.y) - atan2(-rest.z, -rest.y)))
	_data[c]["side"].append(rad_to_deg(atan2(now.x, -now.y) - atan2(rest.x, -rest.y)))


func _tip(before_last: Vector3, last: Vector3) -> Vector3:
	return last + (last - before_last).normalized() * _tip_length


func _mean(values: Array) -> float:
	var total := 0.0
	for v in values:
		total += v
	return total / maxf(1.0, values.size())
