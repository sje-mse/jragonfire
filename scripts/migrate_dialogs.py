import json
import os
import sys

MIGRATED_PATH = os.path.join("..", "migrated_dialogs")
DIALOG_PATH = os.path.join("..", "dialogs")
LINE_PATH = os.path.join("..", "lines")

TOP_LEVEL_KEYS = set(["intro", "prompts"])
PROMPT_KEYS = set(["ego", "response", "cycle", "prompts"])

def read_all_lines():
	lines = dict()
	for p in os.listdir(LINE_PATH):
		linepath = os.path.join(LINE_PATH, p, "en_us.json")
		with open(linepath, 'r') as file:
			lines[p] = json.load(file)
	return lines

def read_all_dialogs():
	dialogs = dict()
	for p in os.listdir(DIALOG_PATH):
		dpath = os.path.join(DIALOG_PATH, p)
		with open(dpath, 'r') as file:
			dialogs[p] = json.load(file)
	return dialogs

def migrate_prompt(prompt, lines):
	new_prompt = {}
	for key, value in prompt.items():
		if key == "ego":
			new_prompt["ego"] = value
			continue

		if key == "response" or key == "cycle":
			if len(value) == 1:
				entry = value[0]
				for speaker_key, line_key in entry.items():
					new_prompt[speaker_key] = line_key
			else:
				new_prompt[key] = value

		if key == "prompts":
			subprompts = []
			for subprompt in value:
				subprompts.append(migrate_prompt(subprompt, lines))
			new_prompt[key] = subprompts
	return new_prompt

def migrate(dialog, lines):
	migrated = {}
	for key in dialog.keys():
		if key not in TOP_LEVEL_KEYS:
			print("invalid key {}".format(key))
			return False

	if "intro" in dialog:
		migrated["intro"] = dialog["intro"]

	if "prompts" in dialog:
		prompts = []
		for prompt in dialog["prompts"]:
			prompts.append(migrate_prompt(prompt, lines))
		migrated["prompts"] = prompts

	return migrated

if __name__ == "__main__":
	lines = read_all_lines()
	dialogs = read_all_dialogs()
	for key, dialog in dialogs.items():
		migrated = migrate(dialog, lines)
		with open(os.path.join(MIGRATED_PATH, key), "w") as file:
			json.dump(migrated, file, indent="\t")

