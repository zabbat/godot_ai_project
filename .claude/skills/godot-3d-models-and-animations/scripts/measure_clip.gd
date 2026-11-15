extends SceneTree
## Measures an animation clip on a model: its length, how far the root bone travels, and how fast
## the feet move while they touch the ground, so the playback speed can be set to match the
## unit's movement speed (no foot sliding). Also prints the root bone's height.
##
## Run (windowless is fine; no project autoloads are needed):
##   godot --headless --path <project> -s <this file> -- <model.glb> <clip> [model_scale] [foot_bone] [root_bone]
## <clip> is either "own:<clip name>" (a clip inside the model) or the res:// path of another file
## (a Mixamo .fbx: it is retargeted onto the model first, with the project's ClipRetarget, see
## references/retargeting.md; without that script the clip is measured on its own skeleton).
## model_scale: the scale the model has in the game (default 1): speeds are printed in metres
## per second at that scale and at playback speed x1. Bones default to Mixamo's names.

const RETARGET_PATH := "res://common/visuals/clip_retarget.gd"


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		print("usage: -- <model.glb> <own:clip | clip.fbx> [model_scale] [foot_bone] [root_bone]")
		quit()
		return
	var model_scale := float(args[2]) if args.size() > 2 else 1.0
	var foot_name := args[3] if args.size() > 3 else "mixamorig_LeftFoot"
	var root_name := args[4] if args.size() > 4 else "mixamorig_Hips"
	var model: Node3D = (load(args[0]) as PackedScene).instantiate()
	root.add_child(model)
	await process_frame  # the model must be in the tree for a frame before its pose follows the player
	var player := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	var skeleton := model.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	var clip_name: StringName
	if args[1].begins_with("own:"):
		clip_name = StringName(args[1].trim_prefix("own:"))
	else:
		clip_name = &"_measured"
		if ResourceLoader.exists(RETARGET_PATH):
			load(RETARGET_PATH).call("add_clip", player, model, load(args[1]), clip_name, false)
		else:
			print("no ", RETARGET_PATH, ": measuring the clip on its own skeleton")
			var source: Node3D = (load(args[1]) as PackedScene).instantiate()
			root.add_child(source)
			await process_frame
			player = source.find_children("*", "AnimationPlayer", true, false)[0]
			skeleton = source.find_children("*", "Skeleton3D", true, false)[0]
			clip_name = player.get_animation_list()[0]
	var clip := player.get_animation(clip_name)
	var foot := skeleton.find_bone(foot_name)
	var root_bone := skeleton.find_bone(root_name)
	if foot < 0 or root_bone < 0:
		print("bone not found: ", foot_name, " / ", root_name)
		quit()
		return
	player.play(clip_name)
	var frames := int(clip.length * 30.0)
	var rows := []
	var lowest := INF
	for i in frames:
		player.seek(i / 30.0, true)
		var foot_pos := skeleton.get_bone_global_pose(foot).origin
		var root_pos := skeleton.get_bone_global_pose(root_bone).origin
		rows.append([foot_pos.y, foot_pos.z - root_pos.z])
		lowest = minf(lowest, foot_pos.y)
	var speeds := []
	for i in range(1, rows.size()):
		if rows[i][0] < lowest + 0.03 and rows[i - 1][0] < lowest + 0.03:
			speeds.append(absf(rows[i][1] - rows[i - 1][1]) * 30.0)
	speeds.sort()
	player.seek(0.0, true)
	var start := skeleton.get_bone_global_pose(root_bone).origin
	player.seek(clip.length, true)
	var end := skeleton.get_bone_global_pose(root_bone).origin
	print("clip ", clip_name, ": length ", snappedf(clip.length, 0.01), " s, loop mode ", clip.loop_mode)
	print("root bone ", root_name, ": height ", snappedf(start.y * model_scale, 0.01), " m, travel over the clip x/z ",
			snappedf((end.x - start.x) * model_scale, 0.01), " / ", snappedf((end.z - start.z) * model_scale, 0.01), " m")
	if speeds.is_empty():
		print("feet: no ground contact found (a clip that stands still, or another foot bone is needed)")
	else:
		var median: float = speeds[speeds.size() / 2] * model_scale
		print("feet on the ground (", speeds.size(), " frames): ", snappedf(median, 0.01),
				" m/s at playback x1 -> playback speed for a move speed of V m/s = V / ", snappedf(median, 0.01))
	quit()
