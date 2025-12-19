import json
import os
import sys

sys.path.append(".")

from verify_dialogs import (
	ACTIONS_KEY,
	read_all_dialogs,
	read_all_lines,
	verify_dialog,
)

SOMETHING_ELSE = "Something else"

def export_action(action_list):
	for action in action_list:
		print("TODO: export action {}".format(action))

def export_line(speaker_key, line_key, lines):
	line = lines[speaker_key][line_key]
	print("{} : {}".format(speaker_key, line))

def export_response(response, lines):
	for speaker_key, line_key in response.items():
		if speaker_key == ACTIONS_KEY:
			export_action(line_key)
		else:
			export_line(speaker_key, line_key, lines)

def export_cycle(cycle_list, lines):
	print("TODO: cycle")
	for response in cycle_list:
		for speaker_key, line_key in response.items():
			print("{} : {}".format(speaker_key, lines[speaker_key][line_key]))

def export_prompt(prompt, lines):
	ego_line = lines["ego"][prompt["ego"]]
	print("ego: {}".format(ego_line))

	if "cycle" in prompt:
		export_cycle(prompt["cycle"], lines)
	elif "response" in prompt:
		for response in prompt["response"]:
			export_response(response, lines)

	# actions
	if ACTIONS_KEY in prompt:
		export_action(prompt[ACTIONS_KEY])

	# single lines
	for key, value in prompt.items():
		if key in lines and key != "ego":
			export_line(key, value, lines)

	# recurse
	if "prompts" in prompt:
		dialog_dict = { "prompts" : prompt["prompts"] }
		dialog_dict["prompts"].append( { "ego" : SOMETHING_ELSE } )
		export_dialog(prompt["ego"], dialog_dict, lines)

def export_dialog(name, dialog, lines):
	print("exporting dialog {}".format(name))
	if not verify_dialog(dialog, lines):
		return False

	if "intro" in dialog:
		for response in dialog["intro"]:
			export_response(response, lines)

	for prompt in dialog.get("prompts", []):
		export_prompt(prompt, lines)

	return True


if __name__ == "__main__":
	lines = read_all_lines()
	dialogs = read_all_dialogs()
	num_ok = 0
	num_bad = 0
	for key, dialog in dialogs.items():
		success = export_dialog(key, dialog, lines)
		if success:
			print("successfully exported {}".format(key))
			num_ok += 1
		else:
			print("failed to port {}".format(key))
			num_bad += 1
	print("{} OK, {} FAILED".format(num_ok, num_bad))

