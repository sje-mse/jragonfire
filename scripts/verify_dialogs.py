import json
import os
import sys

DIALOG_PATH = os.path.join("..", "dialogs")
LINE_PATH = os.path.join("..", "lines")

ACTIONS_KEY = "actions"
TOP_LEVEL_KEYS = set(["intro", "prompts"])
PROMPT_KEYS = set(["ego", "response", "cycle", "prompts", "actions"])

def read_all_lines():
	lines = dict()
	for p in os.listdir(LINE_PATH):
		linepath = os.path.join(LINE_PATH, p, "en_us.json")
		with open(linepath, 'r') as file:
			lines[p] = json.load(file)
	return lines

# Is the json dictionary provided a dialog line?
# A dialog only has keys that are the names of valid speakers.
def is_response(data, lines):
	for key in data.keys():
		if key == ACTIONS_KEY:
			continue
		if not key in lines:
			return False
	return True

def is_dialog(data):
	return len(TOP_LEVEL_KEYS.intersection(set(data.keys()))) > 0

def is_prompt(data):
	return len(PROMPT_KEYS.intersection(set(data.keys()))) > 0

def read_all_dialogs():
	dialogs = dict()
	for p in os.listdir(DIALOG_PATH):
		dpath = os.path.join(DIALOG_PATH, p)
		with open(dpath, 'r') as file:
			dialogs[p] = json.load(file)
	return dialogs

def verify_line(speaker, key, lines):
	if not speaker in lines:
		print("invalid speaker {}".format(speaker))
		return False
	if not key in lines[speaker]:
		print("line {} not found in lines for {}".format(key, speaker))
		return False
	# print("{} : {} : OK!".format(speaker, key))
	return True

def verify_response(response, lines):
	for speaker_key, line_key in response.items():
		if speaker_key == ACTIONS_KEY:
			print("actions detected: {}".format(line_key))
		elif not verify_line(speaker_key, line_key, lines):
			return False
	return True

def verify_prompt(prompt, lines):
	for key, value in prompt.items():
		if key not in PROMPT_KEYS and key not in lines:
			print("invalid prompt key {}".format(key))
			return False

		if key == "ego":
			if value in lines["ego"]:
				pass
				# print("ego : {} OK!".format(value))
			else:
				print("invalid prompt {}".format(value))
				return False

		# verify multi-line responses
		if key == "response" or key == "cycle":
			if not type(value) == list:
				print("invalid {} value: {}", key, value)
				return False
			for response in value:
				if not verify_response(response, lines):
					return False

		# verify single lines
		if key in lines:
			if not verify_line(key, value, lines):
				return False

		if key == ACTIONS_KEY:
			print("actions detected: {}".format(value))

		if key == "prompts":
			if not type(value) == list:
				print("invalid {} value: {}", key, value)
				return False
			for subprompt in value:
				if not verify_prompt(subprompt, lines):
					return False
	return True

def verify_dialog(dialog, lines):
	for key in dialog.keys():
		if key not in TOP_LEVEL_KEYS:
			print("invalid key {}".format(key))
			return False

	if "intro" in dialog:
		for response in dialog["intro"]:
			if not verify_response(response, lines):
				return False

	for prompt in dialog.get("prompts", []):
		if not verify_prompt(prompt, lines):
			return False

	return True

if __name__ == "__main__":
	lines = read_all_lines()
	dialogs = read_all_dialogs()
	num_ok = 0
	num_bad = 0
	for key, dialog in dialogs.items():
		valid = verify_dialog(dialog, lines)
		if (valid):
			num_ok += 1
			# print("{} OK!".format(key))
		else:
			num_bad += 1
			print("{} INVALID!!!".format(key))
	print("{} OK, {} INVALID".format(num_ok, num_bad))
