import json
import os
import sys

sys.path.append(".")

from verify_dialogs import (
	is_response,
	is_prompt,
	is_dialog,
	read_all_lines,
	verify_prompt,
	verify_response,
	verify_dialog,
	verify_line
)

INTERACT_KEY = "interact"
LOOK_KEY = "look"
FLAGS_KEY = "flags"
PROPS_KEY = "props"

ROOM_PATH = os.path.join("..", "rooms")
TOP_LEVEL_KEYS = set([FLAGS_KEY, PROPS_KEY])
PROP_KEYS = set([LOOK_KEY, INTERACT_KEY])
CONDITION_KEYS = set(["condition", "then"])

def is_conditional(data):
	all_keys = set(data.keys())
	return len(all_keys) == 1 and "if" in all_keys

def verify_conditional(data):
	if not set(data.keys()) == CONDITION_KEYS:
		print("invalid condition keys")
		return False
	return True

def read_all_rooms():
	rooms = dict()
	for p in os.listdir(ROOM_PATH):
		if not p.endswith(".json"):
			continue
		print("loading room {}".format(p))
		rpath = os.path.join(ROOM_PATH, p)
		with open(rpath, 'r') as file:
			rooms[p] = json.load(file)
	return rooms

def verify_interaction(data, lines):
	if is_conditional(data):
		for conditional in data["if"]:
			if not verify_conditional(conditional):
				return False
			thenclause = conditional["then"]
			if not verify_interaction(thenclause, lines):
				return True
	else:
		if is_dialog(data):
			if not verify_dialog(data, lines):
				return False
		elif is_prompt(data):
			if not verify_prompt(data, lines):
				return False
		elif is_response(data, lines):
			if not verify_response(data, lines):
				return False
		else:
			print("malformed entry detected\n{}".format(json.dumps(data, indent=2)))
			return False
	return True

def verify_prop(data, lines):
	for key, value in data.items():
		if not key in PROP_KEYS:
			print("Invalid prop key {}".format(key))
			return False

		if not verify_interaction(value, lines):
			return False
	return True

def verify_room(data, lines):
	for top_level_key, top_level_value in data.items():
		if top_level_key not in TOP_LEVEL_KEYS:
			print("Invalid top-level key {} ".format(top_level_key))
			return False

		if top_level_key == PROPS_KEY:
			for prop_key, prop_value in top_level_value.items():
				print(prop_key)
				if not verify_prop(prop_value, lines):
					print("Prop {} invalid".format(prop_key))
					return False
	return True

if __name__ == "__main__":
	lines = read_all_lines()
	rooms = read_all_rooms()
	num_ok = 0
	num_bad = 0
	for key, room in rooms.items():
		valid = verify_room(room, lines)
		if (valid):
			num_ok += 1
			# print("{} OK!".format(key))
		else:
			num_bad += 1
			print("{} INVALID!!!".format(key))
	print("{} OK, {} INVALID".format(num_ok, num_bad))
