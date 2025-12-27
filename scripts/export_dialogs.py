import json
import os
import sys
from pathlib import Path

sys.path.append(".")

from verify_dialogs import (
	ACTIONS_KEY,
	read_all_dialogs,
	read_all_lines,
	verify_dialog,
)

SOMETHING_ELSE = "Something else"
TMP_PATH = "tmp.xml"

def export_action(action_list, ofile):
	for action in action_list:
		pass
		#print("TODO: export action {}".format(action))

def export_line(speaker_key, line_key, lines, ofile):
	line = lines[speaker_key][line_key]
	# print("{} : {}".format(speaker_key, line))

def export_response(response, lines, ofile):
	for speaker_key, line_key in response.items():
		if speaker_key == ACTIONS_KEY:
			export_action(line_key, ofile)
		else:
			export_line(speaker_key, line_key, lines, ofile)

def export_cycle(cycle_list, lines, ofile):
	print("TODO: cycle")
	for response in cycle_list:
		for speaker_key, line_key in response.items():
			pass
			# print("{} : {}".format(speaker_key, lines[speaker_key][line_key]))

def export_prompt(prompt, lines, ofile):
	ego_line = lines["ego"][prompt["ego"]]
	# print("ego: {}".format(ego_line))

	if "cycle" in prompt:
		export_cycle(prompt["cycle"], lines, ofile)
	elif "response" in prompt:
		for response in prompt["response"]:
			export_response(response, lines, ofile)

	# actions
	if ACTIONS_KEY in prompt:
		export_action(prompt[ACTIONS_KEY], ofile)

	# single lines
	for key, value in prompt.items():
		if key in lines and key != "ego":
			export_line(key, value, lines, ofile)

def export_dialog(name, dialog, lines, ofile):
	print("...exporting dialog {}".format(name))
	if not verify_dialog(dialog, lines):
		return False

	if "intro" in dialog:
		for response in dialog["intro"]:
			export_response(response, lines, ofile)

	for prompt in dialog.get("prompts", []):
		export_prompt(prompt, lines, ofile)

	return True

def export_folder(name, dialogs, lines, ofile):
	print("exporting character {}...".format(name))
	for key, dialog in dialogs.items():
		export_dialog(key, dialog, lines, ofile)

def update_stack(line, stack):
	if line.endswith("<Dialogs>"):
		stack.append(line)
	elif line.endswith("</Dialogs>"):
		stack.pop()

def write_dialogs(ipath):
	lines = read_all_lines()
	dialogs = read_all_dialogs()
	stack = []
	with open(ipath, 'r') as ifile:
		with open(TMP_PATH, 'w') as ofile:
			# copy pre-dialog section.
			while line := ifile.readline():
				ofile.write(line)
				update_stack(line.strip(), stack)
				if stack:
					break

			for char_key, char_dict in dialogs.items():
				export_folder(char_key, char_dict, lines, ofile)

			# write exported stuff.
			ofile.write("	<!------- DIALOGS GO HERE-------->\n")

			# copy post-dialog section.
			while line := ifile.readline():
				update_stack(line.strip(), stack)
				if not stack:
					ofile.write(line)


if __name__ == "__main__":
	if len(sys.argv) > 1:
		xml_path = sys.argv[1]
		write_dialogs(xml_path)
	else:
		print("usage: {} <xml path>".format(sys.argv[0]))

