@tool
extends EditorPlugin
# TASK-115 H7 probe. Deliberately does nothing: its only job is to exist in
# ProjectSettings' `editor_plugins/enabled`, which is the list
# editor_reload_plugin disables and enables again. It must not touch the editor
# state, or the probe would be measuring itself instead of the tool.

func _enter_tree() -> void:
	pass


func _exit_tree() -> void:
	pass
