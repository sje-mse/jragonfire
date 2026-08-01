import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.append(".")

from env_paths import (
	AGS_PATH,
	AGS_SPEECH_PATH,
	AGS_XML_PATH,
	BACKUP_AGS_XML_PATH,
	SPEECH_PATH,
)

TOPIC_DELIMITER = '__'
GO_TO_PREVIOUS = "go_to_previous"
TMP_PATH = "tmp.xml"
ROOT_SUFFIX = "{}root".format(TOPIC_DELIMITER)
PREAMBLE_SUFFIX = "{}preamble".format(TOPIC_DELIMITER)
CYCLES_HEADER_PATH = os.path.join(AGS_PATH, "DialogCycles.ash")
CYCLES_SCRIPT_PATH = os.path.join(AGS_PATH, "DialogCycles.asc")
OPTIONS_HEADER_PATH = os.path.join(AGS_PATH, "DialogOptions.ash")
OPTIONS_SCRIPT_PATH = os.path.join(AGS_PATH, "DialogOptions.asc")

class Cycle:
	def __init__(self, key):
		self.key = key
		self.line_pairs = list()

def export_action(action_list, ofile):
	for action in action_list:
		ofile.write('	doAction("{}")\n'.format(action))

def resolve_line(line_key, lines):
	if line_key in lines:
		line = lines[line_key]
		if "audiofile" in line:
			return '&{} {}'.format(line["num"], line["msg"])
		else:
			return line["msg"]
	else:
		return "I AM ERROR"

def export_line(line_key, lines, ofile):
	msg = resolve_line(line_key, lines)
	speaker = lines[line_key]["character"]
	ofile.write('{}: {}\n'.format(speaker, msg))

def export_response(response, lines, ofile):
	for line_key in response:
		export_line(line_key, lines, ofile)

def msg_to_key(msg):
	plain = re.sub(r'[^a-zA-Z0-9 ]', '', msg)
	parts = [w for w in plain.lower().split(" ") if w]
	return "_".join(parts[:4])

def export_cycle(dialog_name, ego_line, cycle_list, lines, cycles, ofile):
	cycle = Cycle('cycle{}{}{}{}'.format(TOPIC_DELIMITER, dialog_name, TOPIC_DELIMITER, msg_to_key(ego_line)))
	for line_key in cycle_list:
		if line_key in lines:
			speaker = lines[line_key]["character"]
			cycle.line_pairs.append((speaker, resolve_line(line_key, lines)))
	cycles.append(cycle)
	ofile.write("	{}();\n".format(cycle.key))

def export_option(option_id, line, ofile):
	ofile.write('				  <DialogOption>\n')
	ofile.write('					<ID>{}</ID>\n'.format(option_id))
	ofile.write('					<Say>False</Say>\n')
	ofile.write('					<Show>True</Show>\n')
	ofile.write('					<Text xml:space="preserve">{}</Text>\n'.format(line))
	ofile.write('				  </DialogOption>\n')

def get_goto_cmd(dialog_name, target):
	return 'goto-dialog d{}\n'.format(target)

# id_count: unique integer id
# dialog: dictionary, created by ripmsg
# line: dictionary of all lines in the game. created by ripmsg.
# cycles: list of Cycles for this room. Populated by this function.
# options: set of trees that should have option functions. Populated by this function.
# ofile: output file
def export_dialog(id_count, dialog, lines, cycles, options, ofile):
	name = dialog["topic"]
	ofile.write('			  <Dialog>\n')
	ofile.write('			   <ID>{}</ID>\n'.format(id_count))
	ofile.write('			   <Name>d{}</Name>\n'.format(name))
	ofile.write('			   <ShowTextParser>False</ShowTextParser>\n')
	ofile.write('			   <Script><![CDATA[// Dialog script file\n')

	# startup
	ofile.write('@S  // Dialog startup entry point\n')

	if "intro" in dialog:
		export_response(dialog["intro"], lines, ofile)
	elif "cycle" in dialog:
		export_cycle(name, "intro", dialog["cycle"], lines, cycles, ofile)

	if name.endswith(PREAMBLE_SUFFIX):
		ofile.write(get_goto_cmd(name, "root"))
	else:
		ofile.write('return\n')

	# prompt responses
	is_root = name.endswith(ROOT_SUFFIX)
	option_id = 0
	prompts = dialog.get("prompts", [])
	for i, prompt in enumerate(prompts):
		option_func = "on_{}_option".format(name)
		options.add(option_func)

		prompt = prompts[i]
		option_id += 1
		ofile.write('@{}\n'.format(option_id))

		if "response" in prompt:
			export_response(prompt["response"], lines, ofile)
			ofile.write("	{}({});\n".format(option_func, option_id))
		elif "cycle" in prompt:
			export_cycle(name, prompt["ego"], prompt["cycle"], lines, cycles, ofile)
			ofile.write("	{}({});\n".format(option_func, option_id))

		# TODO: Actions

		if "goto" in prompt:
			ofile.write(get_goto_cmd(name, prompt["goto"]))
		elif is_root and i == (len(prompts) - 1):
			ofile.write('stop\n')
		else :
			ofile.write('return\n')

	if not is_root and option_id > 0:
		option_id += 1
		ofile.write('@{}\n'.format(option_id))
		ofile.write('goto-previous\n')

	ofile.write(']]></Script>\n')
	ofile.write('			   <DialogOptions>\n')

	# prompt options
	option_id = 0
	for prompt in prompts:
		option_id += 1
		export_option(option_id, prompt["ego"], ofile)

	if not is_root and option_id > 0:
		option_id += 1
		export_option(option_id, "Something Else", ofile)

	ofile.write('			   </DialogOptions>\n')
	ofile.write('			  </Dialog>\n')

def update_stack(line, stack):
	if line.endswith("<Dialogs>"):
		stack.append(line)
	elif line.endswith("</Dialogs>"):
		stack.pop()

def write_ags_dialogs(dialogs, lines):
	write_dialogs(AGS_XML_PATH, dialogs, lines)

	# copy and back up
	print('backing up {} to {}'.format(AGS_XML_PATH, BACKUP_AGS_XML_PATH))
	shutil.copy(AGS_XML_PATH, BACKUP_AGS_XML_PATH)
	print('copying {} to {}'.format(TMP_PATH, AGS_XML_PATH))
	shutil.copy(TMP_PATH, AGS_XML_PATH)

def escape_string(s):
	s = s.replace('"', '\\"')
	s = s.replace("'", "\\'")
	return s

def write_dialogs(ipath, dialogs, lines):
	id_count = 0

	stack = list()
	cycles = dict() # { room_name :  [Cycles] }
	options = set()

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

			for room_name in sorted(dialogs.keys()):
				room_dict = dialogs[room_name]
				if room_name not in cycles:
					cycles[room_name] = list()
				cycle_list = cycles[room_name]
				print("exporting room {}...".format(room_name))
				ofile.write('		  <DialogFolder Name="{}">\n'.format(room_name))
				ofile.write('			<SubFolders>\n')
				for category, dialog_list in room_dict.items():
					print("--exporting category {}...".format(category))
					ofile.write('			<DialogFolder Name="{}">\n'.format(category))

					ofile.write('			  <SubFolders />\n')
					ofile.write('				<Dialogs>\n')

					for dialog in dialog_list:
						export_dialog(id_count, dialog, lines, cycle_list, options, ofile)
						id_count += 1
					ofile.write('				</Dialogs>\n')
					ofile.write('			  </DialogFolder>\n')
				ofile.write('			</SubFolders>\n')
				ofile.write('			<Dialogs />\n')
				ofile.write('		  </DialogFolder>\n')

			ofile.write('		</SubFolders>\n')
			ofile.write('		<Dialogs />\n')
			ofile.write('	  </DialogFolder>\n')

			# copy post-dialog section.
			while line := ifile.readline():
				update_stack(line.strip(), stack)
				if not stack:
					ofile.write(line)

	# write cycles
	# calculate maximum cycles
	max_cycles = max([len(cycle_list) for cycle_list in cycles.values()])

	with open(CYCLES_HEADER_PATH, 'w') as ofile:
		ofile.write('// Header file for Dialog Cycles\n')
		ofile.write('\n')
		ofile.write('import function reset_dialog_cycle_counters();\n')

		for room_key, cycle_list in cycles.items():
			for cycle in cycle_list:
				ofile.write('import function {}();\n'.format(cycle.key))

	with open(CYCLES_SCRIPT_PATH, 'w') as ofile:
		for i in range(max_cycles):
			ofile.write("int cycle_counter_{};\n".format(i))

		ofile.write('\n')
		ofile.write('function reset_dialog_cycle_counters()\n')
		ofile.write('{\n')
		for i in range(max_cycles):
			ofile.write("	cycle_counter_{} = 0;\n".format(i))
		ofile.write('}\n\n')

		for room_key, cycle_list in cycles.items():
			for index, cycle in enumerate(cycle_list):
				ofile.write('function {}()\n'.format(cycle.key))
				ofile.write('{\n')
				ofile.write('	if (cycle_counter_{} >= {}) {{\n'.format(index, len(cycle.line_pairs)))
				ofile.write('		cycle_counter_{} = 0;\n'.format(index))
				ofile.write('	}\n')
				ofile.write('	switch(cycle_counter_{}) {{\n'.format(index))
				line_index = 0;
				for speaker_key, line in cycle.line_pairs:
					ofile.write('	case {}:\n'.format(line_index))
					if speaker_key == "narrator":
						ofile.write('		Display("{}");\n'.format(escape_string(line)))
					else:
						ofile.write('		c{}.Say("{}");\n'.format(speaker_key.title(), escape_string(line)))
					ofile.write('		break;\n')
					line_index += 1

				ofile.write('	default:\n')
				ofile.write('		Display("I am error.");\n')
				ofile.write('		break;\n')
				ofile.write('	}\n')
				ofile.write('	cycle_counter_{} += 1;\n'.format(index))
				ofile.write('}\n\n')

	# write option functions
	funcs = sorted(options)
	with open(OPTIONS_HEADER_PATH, 'w') as ofile:
		ofile.write('// Header file for Dialog Option Codes\n')
		ofile.write('\n')
		for func in funcs:
			ofile.write('import function {}(int option);\n'.format(func))
	
	with open(OPTIONS_SCRIPT_PATH, 'w') as ofile:
		for func in funcs:
			ofile.write('function {}(int option)\n'.format(func))
			ofile.write('{}\n')


if __name__ == "__main__":
	print("No direct usage. Use from ripmsg.")
