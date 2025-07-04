import json
import os
import sys

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
	# for now, all responses are a single item: { <speaker_key> : <line_key> }.
	if len(response) != 1:
		print("invalid number of entries in response: {}".format(response))
		return False
	for speaker_key, line_key in response.items():
		return verify_line(speaker_key, line_key, lines)

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

		if key == "prompts":
			if not type(value) == list:
				print("invalid {} value: {}", key, value)
				return False
			for subprompt in value:
				if not verify_prompt(subprompt, lines):
					return False
	return True

def verify(dialog, lines):
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
	for key, dialog in dialogs.items():
		valid = verify(dialog, lines)
		if (valid):
			print("{} OK!".format(key))
		else:
			print("{} INVALID!!!".format(key))
