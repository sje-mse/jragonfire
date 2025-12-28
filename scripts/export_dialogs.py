import json
import os
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

from verify_dialogs import (
	ACTIONS_KEY,
	read_all_dialogs,
	read_all_lines,
	verify_dialog,
)

SOMETHING_ELSE = "Something else"
TMP_PATH = "tmp.xml"

class LineCache:
	def __init__(self):
		self.count = 0
		self.cache = dict()

	def has(self, line_key):
		return line_key in self.cache

	def put(self, line_key):
		self.count += 1
		self.cache[line_key] = self.count
		return self.count

	# @return line number on hit, 0 on miss
	def get(self, line_key):
		return self.cache.get(line_key, 0)

def encache(speaker_key, line_key, cache):
	src_path = os.path.join(SPEECH_PATH, speaker_key, '{}.wav'.format(line_key))
	if os.path.isfile(src_path):
		line_id = cache[speaker_key].put(line_key)
		dst_path = os.path.join(AGS_SPEECH_PATH, '{}.{}.wav'.format(speaker_key, line_id))
		print('copying {} to {}...'.format(src_path, dst_path))
		shutil.copy(src_path, dst_path)
	else:
		print("no line found for {}".format(src_path))

def export_action(action_list, ofile):
	for action in action_list:
		ofile.write('	doAction("{}")\n'.format(action))

def export_line(speaker_key, line_key, lines, cache, ofile):
	line = lines[speaker_key][line_key]

	# get cached id if it exists
	if speaker_key not in cache:
		cache[speaker_key] = LineCache()

	if not cache[speaker_key].has(line_key):
		encache(speaker_key, line_key, cache)

	line_id = cache[speaker_key].get(line_key)

	if line_id > 0:
		ofile.write('{}: &{} {}\n'.format(speaker_key, line_id, line))
	else:
		ofile.write('{}: {}\n'.format(speaker_key, line))

def export_response(response, lines, cache, ofile):
	for speaker_key, line_key in response.items():
		if speaker_key == ACTIONS_KEY:
			export_action(line_key, ofile)
		else:
			export_line(speaker_key, line_key, lines, cache, ofile)

def export_cycle(cycle_list, lines, cache, ofile):
	print("TODO: cycle")
	for response in cycle_list:
		for speaker_key, line_key in response.items():
			pass
			# print("{} : {}".format(speaker_key, lines[speaker_key][line_key]))

def export_prompt(prompt, lines, cache, ofile):
	ego_line = lines["ego"][prompt["ego"]]
	# print("ego: {}".format(ego_line))

	if "cycle" in prompt:
		export_cycle(prompt["cycle"], lines, cache, ofile)
	elif "response" in prompt:
		for response in prompt["response"]:
			export_response(response, lines, cache, ofile)

	# actions
	if ACTIONS_KEY in prompt:
		export_action(prompt[ACTIONS_KEY], ofile)

	# single lines
	for key, value in prompt.items():
		if key in lines and key != "ego":
			export_line(key, value, lines, cache, ofile)

def export_dialog(id_count, name, dialog, lines, cache, ofile):
	ofile.write('			  <Dialog>\n')
	ofile.write('			   <ID>{}</ID>\n'.format(id_count))
	ofile.write('			   <Name>d{}</Name>\n'.format(name.title()))
	ofile.write('			   <ShowTextParser>False</ShowTextParser>\n')
	ofile.write('			   <Script><![CDATA[// Dialog script file\n')

	if "intro" in dialog:
		ofile.write('@S  // Dialog startup entry point\n')
		for response in dialog["intro"]:
			export_response(response, lines, cache, ofile)
		ofile.write('return\n')

		# responses

		# prompts

	ofile.write(']]></Script>\n')


	'''
	for prompt in dialog.get("prompts", []):
		export_prompt(prompt, lines, cache, ofile)
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
	cache = dict() # { character_name, LineCache }

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
						export_dialog(id_count, key, dialog, lines, cache, ofile)
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
	else:
		xml_path = AGS_XML_PATH

	write_dialogs(xml_path)

	if len(sys.argv) == 1:
		# copy and back up
		print('backing up {} to {}'.format(AGS_XML_PATH, BACKUP_AGS_XML_PATH))
		shutil.copy(AGS_XML_PATH, BACKUP_AGS_XML_PATH)
		print('copying {} to {}'.format(TMP_PATH, AGS_XML_PATH))
		shutil.copy(TMP_PATH, AGS_XML_PATH)

