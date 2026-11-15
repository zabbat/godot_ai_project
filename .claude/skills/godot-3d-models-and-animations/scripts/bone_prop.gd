class_name BoneProp
extends RefCounted
## Attaches a prop (a weapon) to a bone of a skeleton, so it follows the bone through every clip.


## Adds `prop` under a new BoneAttachment3D on `bone` and returns the attachment (null if the
## skeleton has no such bone, or there is no prop). `offset` moves the prop from the bone (the
## bone's own axes), on top of the prop scene's own transform.
static func attach(skeleton: Skeleton3D, bone: StringName, prop: PackedScene,
		offset: Transform3D = Transform3D.IDENTITY) -> BoneAttachment3D:
	if prop == null or skeleton == null:
		return null
	if skeleton.find_bone(bone) < 0:
		push_warning("BoneProp: no bone '%s' in the skeleton" % bone)
		return null
	var attachment := BoneAttachment3D.new()
	attachment.bone_name = bone
	skeleton.add_child(attachment)
	var instance: Node3D = prop.instantiate()
	instance.transform = offset * instance.transform  # keep the prop scene's own scale
	attachment.add_child(instance)
	return attachment
