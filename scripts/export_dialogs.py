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
		ofile.write('	doAction("{}")\n'.format(action))

def export_line(speaker_key, line_key, lines, ofile):
	line = lines[speaker_key][line_key]

	char_name = 'c{}'.format(speaker_key.title())

	# get cached id if it exists

	# TODO
	ofile.write('{}: {}\n'.format(char_name, line))

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

def export_dialog(id_count, name, dialog, lines, ofile):
	ofile.write('			  <Dialog>\n')
	ofile.write('			   <ID>{}</ID>\n'.format(id_count))
	ofile.write('			   <Name>d{}</Name>\n'.format(name))
	ofile.write('			   <ShowTextParser>False</ShowTextParser>\n')
	ofile.write('			   <Script><![CDDATA[// Dialog script file\n')

	if "intro" in dialog:
		ofile.write('@S  // Dialog startup entry point\n')
		for response in dialog["intro"]:
			export_response(response, lines, ofile)
		ofile.write('return\n')

		# responses

		# prompts

	ofile.write(']]></Script>\n')


	'''
	for prompt in dialog.get("prompts", []):
		export_prompt(prompt, lines, ofile)
	'''

	ofile.write('			  </Dialog>\n')

	return True

def update_stack(line, stack):
	if line.endswith("<Dialogs>"):
		stack.append(line)
	elif line.endswith("</Dialogs>"):
		stack.pop()

def write_dialogs(ipath):
	id_count = 0
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

			ofile.write('	  <DialogFolder Name="Main">\n')
			ofile.write('		<SubFolders>\n')

			for folder_name, char_dict in dialogs.items():
				print("exporting folder {}...".format(folder_name))
				ofile.write('		  <DialogFolder Name="{}">\n'.format(folder_name))
				ofile.write('			<SubFolders />\n')
				ofile.write('			<Dialogs>\n')

				for key, dialog in char_dict.items():
					if verify_dialog(dialog, lines):
						print("...exporting dialog {}".format(key))
						export_dialog(id_count, key, dialog, lines, ofile)
						id_count += 1
					else:
						print("...skipping invalid dialog {}".format(key))

				ofile.write('			</Dialogs>\n')
				ofile.write('		  </DialogFolder>\n')


			ofile.write('		</SubFolders>\n')
			ofile.write('		<Dialogs />\n')
			ofile.write('	  </DialogFolder>\n')

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

