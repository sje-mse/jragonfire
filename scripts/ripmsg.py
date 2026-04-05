import sys
import os
import json
import re

from pathlib import Path
from ffmpeg import FFmpeg

sys.path.append(".")

from env_paths import (
    MSG_PATH,
    AGS_SPEECH_PATH,
)

from export_dialogs import write_ags_dialogs
from riputils import (
    CHARACTER_IDS,
    NPC_ROOMS,
    ROOM_IDS,
)
from wavify import cvtaud

###############################################################################
## Rip Msgs
##
## A Script whose purpose is to dig into the QGM files (previously unpacked
## using ripspk.py) and:
## 1. decode all msg blocks
## 2. collate all lines by speaker
## 3. associate msg blocks into dialog/interaction trees and singles.
## 4. export all decoded dialogs, interactions, and singles in AGS.
## 5. export all speech performance files into AGS.
##
## USAGE:
##
## python ripmsgs.py [--speech] [--dialogs]
##
## arguments:
##
## --speech: copies audio files to AGS
## --dialogs: exports dialog information to AGS.
##
## if run without arguments, the data is extracted without exporting to AGS.
##
###############################################################################

# Lookup table to help decode audio/lipsync filenames,
# which are composed of base 36 strings.
from36 = {
    "0" : 0, "1" : 1, "2" : 2, "3" : 3,
    "4" : 4, "5" : 5, "6" : 6, "7" : 7,
    "8" : 8, "9" : 9, "A" : 10, "B" : 11,
    "C" : 12, "D" : 13, "E" : 14, "F" : 15,
    "G" : 16, "H" : 17, "I" : 18, "J" : 19,
    "K" : 20, "L" : 21, "M" : 22, "N" : 23,
    "O" : 24, "P" : 25, "Q" : 26, "R" : 27,
    "S" : 28, "T" : 29, "U" : 30, "V" : 31,
    "W" : 32, "X" : 33, "Y" : 34, "Z" : 35
}

# Lookup table to help re-encode audio/lipsync filenames.
to36 = [
    "0", "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "A", "B",
    "C", "D", "E", "F", "G", "H",
    "I", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z"]


def to_int(four_bytes):
    return int.from_bytes(four_bytes, 'little')

def to_short(two_bytes):
    return int.from_bytes(two_bytes, 'little')

def to_byte(one_byte):
    return int.from_bytes(one_byte, 'little')

def to_id_str(b13):
    return "".join([chr(b) for b in b13[:12]])

# Uses the room number and the base-36 id to create a more legible guid.
def to_id_tuple(room, b):
    return (
        room,
        (from36[b[4]] * 36) + from36[b[5]],
        (from36[b[6]] * 36) + from36[b[7]],
        (from36[b[9]] * 36) + from36[b[10]],
        from36[b[11]]
    )

# converts the number "num" into a base-36 string of length "l"
def to_b36_str(num, l):
    hundreds = 36 * 36
    tens = 36
    result = []
    if (l >= 3):
        if num >= hundreds:
            digit = num // hundreds
            result.append(to36[digit])
            num -= (hundreds * digit)
        else:
            result.append("0")
    if (l >= 2):
        if num >= tens:
            digit = num // tens
            result.append(to36[digit])
            num -= (tens * digit)
        else:
            result.append("0")
    if (l >= 1):
        result.append(to36[num])

    return "".join(result)

# converts the guid tuple "t" to the filename of representing either:
# char1 == "A" - audio
# char1 == "S" - lipsync
def to_id_filename(char1, t):
    result = [char1]
    result.append(to_b36_str(t[0], 3))
    result.append(to_b36_str(t[1], 2))
    result.append(to_b36_str(t[2], 2))
    result.append('.')
    result.append(to_b36_str(t[3], 2))
    result.append(to_b36_str(t[4], 1))
    return "".join(result)

# creates a reasonably human-readable key from a block's message content.
def msg_to_key(msg):
    plain = re.sub(r'[^a-zA-Z0-9 ]', '', msg)
    parts = [w for w in plain.lower().split(" ") if w]
    return "_".join(parts[:4])

# creates a reasonably human-readable and unique line id.
def to_line_id(block):
    key = msg_to_key(block.msg)
    return "{}_{}_{}__{}".format(block.character_id, block.guid[0], block.index, key)

# creates a reasonably human-readable and unique dialog id.
def to_dialog_id(block, msg):
    key = msg_to_key(msg)
    return "{}_{}__{}".format(block.guid[0], block.index, key)

# create a reasonably human-readable nickname for a response.
def get_response_hint(response):
    for line_key in response:
        return '{}__root'.format(line_key.split('__')[1])
    return "root"

# create a reasonably human-readable key for a dialog.
# helps create a key for this dialog in AGS.
def get_dialog_hint(dialog):
    if "intro" in dialog:
        return get_response_hint(dialog["intro"])
    elif "cycle" in dialog:
        return get_response_hint(dialog["cycle"])

    for prompt in dialog["prompts"]:
        if "response" in prompt:
            return get_response_hint(prompt["response"])
        else:
            return "{}__root".format(msg_to_key(prompt["ego"]))

    return "root"

# create a reasonably human-readable id for a root dialog in AGS.
def to_root_dialog_id(block, dialog):
    return "{}_{}__{}".format(block.guid[0], block.index, get_dialog_hint(dialog))


# msg content is obfuscated within the QGM files.
# this function decodes it using the following algorithm:
#
# 1. split data into 4-byte chunks and tail 0-3 bytes long;
# 2. for each 4-byte chunk repeat steps 3-6:
# 3. read those bytes as 32-bit little-endian number
# 4. exclusive-or the value with constant 0xf1acc1d
# 5. rotate value cyclically right by 15 bits
# 6. store 32-bit number back as four bytes
# 7. invert bits in all bytes of the tail.
def decode(msg):
    deffed = list()
    tailstart = len(msg) - (len(msg) % 4)
    for i in range(0, tailstart, 4):
        step2 = msg[i:i+4]
        step3 = to_int(step2)

        step4 = (step3 ^ 0xf1acc1d) & 0xffffffff

        step5 = ((step4 >> 15) | (step4 << 17)) & 0xffffffff

        deffed.append(chr(0xff & (step5 >> 0)))
        deffed.append(chr(0xff & (step5 >> 8)))
        deffed.append(chr(0xff & (step5 >> 16)))
        deffed.append(chr(0xff & (step5 >> 24)))

    for i in range(tailstart, len(msg)):
        deffed.append(chr(msg[i] ^ 0xff))

    return "".join(deffed)

# A utility class to assist in parsing msg block data.
class MsgBlock:
    def __init__(self):
        self.character_id = 0
        self.guid = tuple()
        self.filename = ""
        self.num = 0
        self.uk = list() # unknown codes
        self.flags = 0
        self.options = list()
        self.msg = ""
        self.parent_guid = tuple()
        self.index = 0

    def has_options(self):
        return len(self.options) > 0

    def is_cycle(self):
        return (self.uk[1] & 0x01) == 0x01

    def juid(self):
        return (self.character_id, self.guid[0], self.num)

    def has_parent(self):
        return len(self.parent_guid) > 0

    def room(self):
        return self.guid[0]

    def follows(self):
        return self.guid[-1] > 1

# Extract a dictionary of the form { block guid : MsgBlock } from the file at "fpath".
def extract_blocks(fpath):
    blocks = dict()
    with open(fpath, 'rb') as file:
        header = file.read(4)
        version = to_int(file.read(4))
        num_blocks = to_int(file.read(4))
        mystery = to_short(file.read(2))
        file_id = to_short(file.read(2))

        print("{} : v{} : {} ({})".format(header, version, file_id, mystery))
        print("{} blocks\n".format(num_blocks))

        for block_num in range(num_blocks):
            block = MsgBlock()
            block.guid = (file_id, to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))
            block.character_id = to_short(file.read(2))
            block.uk.append(to_short(file.read(2)))
            block.uk.append(to_short(file.read(2)))
            block.uk.append(to_short(file.read(2)))

            num_options = to_short(file.read(2))
            block.flags = to_short(file.read(2))
            block.num = to_short(file.read(2))
            block.uk.append(to_short(file.read(2)))
            msg_len = to_short(file.read(2))
            block.uk.append(to_short(file.read(2)))
            parent_lbl_present = to_short(file.read(2))
            block.uk.append(to_short(file.read(2)))
            block.filename = to_id_filename("A", block.guid)
            block.index = block_num

            if parent_lbl_present != 0:
                parent_id_str = to_id_str(file.read(13))
                block.parent_guid = to_id_tuple(file_id, parent_id_str)

            if (num_options > 0):
                for option_num in range(num_options):
                    option_str = to_id_str(file.read(13))
                    option_id = to_id_tuple(file_id, option_str)
                    block.options.append(option_id)

            if (msg_len > 0):
                msg = file.read(msg_len)
                if block.flags & 0x04:
                    block.msg = decode(msg)
                else:
                    block.msg = str(msg)

            block.uk.append(to_int(file.read(4)))
            blocks[block.guid] = block
    return blocks

# given a "guid" to start with, gather a list of line_ids that constitute
# an entire response.
# returns the list of line ids,
#         whether or not the response is a cycle,
#         and a set of all block guids that were gathered.
def get_response(guid, blocks):
    all_guids = set()
    is_cycle = False
    result = list()
    while guid in blocks:
        all_guids.add(guid)
        block = blocks[guid]
        if block.msg:
            result.append(to_line_id(block))
        if block.is_cycle():
            is_cycle = True
        guid = (guid[0], guid[1], guid[2], guid[3], guid[4] + 1)
    return result, is_cycle, all_guids

# return a dictionary representing the prompt data encoded in a block "option" guid.
def get_prompt(guid, blocks):
    block = blocks[guid]
    prompt = dict()

    if block.msg:
        prompt["ego"] = clean_msg(block.msg)
    else:
        prompt["ego"] = "TODO"

    if block.has_options():
        o_guid = block.options[0]
        response, is_cycle, _ = get_response(o_guid, blocks)
        if response:
            if is_cycle:
                prompt["cycle"] = response
            else:
                prompt["response"] = response
        else:
            prompt["action"] = "TODO"
        ob = blocks[o_guid]
        if ob.has_options():
            prompt["goto"] = to_dialog_id(ob, block.msg)

    if len(block.options) > 1:
        xtra = 1
        for o_guid in block.options[1:]:
            response, is_cycle, _ = get_response(o_guid, blocks)
            if response:
                if is_cycle:
                    prompt["xtra_cycle_{}".format(xtra)] = response
                else:
                    prompt["xtra_response_{}".format(xtra)] = response
            else:
                prompt["xtra_action_{}".format(xtra)] = "TODO"
            xtra += 1
    return prompt

# associate MsgBlocks into json-ready dialog dictionaries, keyed by unique AGS-friendly keys.
def get_dialogs(dialogs, blocks):
    for guid, block in blocks.items():
        if (block.has_options()):
            # only care about trees with ego options.
            if blocks[block.options[0]].character_id > 2:
                continue

            dialog = dict()
            dialog["room"] = ROOM_IDS[block.room()]

            # resolve options and responses
            dialog["prompts"] = list()
            for option_id in block.options:
                prompt = get_prompt(option_id, blocks)
                dialog["prompts"].append(prompt)

            # figure out the parent, if any
            if block.has_parent():
                parent = blocks[block.parent_guid]
                if not parent.msg:
                    continue
                dialog["topic"] = to_dialog_id(block, parent.msg)
            else:
                # get "intro" message(s) only if not a subdialog
                if block.msg:
                    intro, is_cycle, _ = get_response(guid, blocks)
                    if is_cycle:
                        dialog["cycle"] = intro
                    else:
                        dialog["intro"] = intro
                # only safe to use because we never goto a root dialog!!!
                dialog["topic"] = to_root_dialog_id(block, dialog)

            dialogs[dialog["topic"]] = dialog

# get the single "responses" (may be multi-line) that are
# not associated directly with dialog or interaction trees.
def get_singles(singles, blocks):
    handled = set()
    for guid, block in blocks.items():
        if not guid in handled and not block.follows() and not block.has_parent() and not block.has_options():
            dialog = dict()
            key = to_dialog_id(block, block.msg)
            intro, is_cycle, guids = get_response(guid, blocks)
            handled.update(guids)
            if is_cycle:
                dialog["cycle"] = intro
            else:
                dialog["intro"] = intro
            dialog["topic"] = key
            dialog["room"] = ROOM_IDS[block.room()]
            singles[key] = dialog

# remove quotation marks and illegal characters from block msgs.
def clean_msg(msg):
    s = msg.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:len(s)-1]
    s = s.replace("\x92", "'")
    s = s.replace('\r\n', '\\n')
    return s

# extract useful json-ready line information dicts from MsgBlock.
def get_lines(lines, blocks, counts):
    for guid, block in blocks.items():
        if not block.msg:
            continue

        data = dict()
        data["msg"] = clean_msg(block.msg)
        if block.character_id > 10:
            data["audiofile"] = to_id_filename("A", block.guid)
            data["lipsyncfile"] = to_id_filename("S", block.guid)
        data["character"] = CHARACTER_IDS.get(block.character_id, "I AM ERROR {}".format(block.character_id))
        data["character_id"] = block.character_id
        # line number, for audio file exporting
        count = counts.get(block.character_id, 0)
        count += 1
        data["num"] = count
        counts[block.character_id] = count
        key = to_line_id(block)
        lines[key] = data

# Debug method: print block data.
def print_blocks(blocks):
    for guid, block in blocks.items():
        print("{} ({}) {} ========".format(block.juid(), guid, block.filename))
        if block.msg:
            print("{}: {}".format(block.character_id, block.msg))
        for o in block.options:
            ob = blocks[o]
            print("----{}: {}: {}".format(o, ob.character_id, ob.msg))
        if block.parent_guid:
            mb = blocks[block.parent_guid]
            print("<<<<{}: {}: {}".format(block.parent_guid, mb.character_id, mb.msg))
        print("{}==========\n".format(block.uk))

# Debug method: print response data.
def print_response(response, lines):
    for key in response:
        if key in lines:
            print("----{} : {}".format(lines[key]["character"], lines[key]["msg"]))
        else:
            print("----{} NOT FOUND".format(key))

# Debug method: print prompt data.
def print_prompt(prompt, lines):
    print("--ego: {}".format(prompt["ego"]))
    if "cycle" in prompt:
        print("cycle:")
        print_response(prompt["cycle"], lines)
    elif "response" in prompt:
        print_response(prompt["response"], lines)
    if "goto" in prompt:
        print("goto: {}".format(prompt["goto"]))
    print("\n")

# Debug method: print dialogs.
def print_dialogs(dialogs, lines):
    for topic, dialog in dialogs.items():
        print("\n=========================")
        print("topic: {}".format(topic))
        if "intro" in dialog:
            print("intro:")
            print_response(dialog["intro"], lines)
        elif "cycle" in dialog:
            print("intro(cycle):")
            print_response(dialog["cycle"], lines)

        if "prompts" in dialog:
            print("prompts:")
            for prompt in dialog["prompts"]:
                print_prompt(prompt, lines)

# determine if the line with key "key" is spoken by an NPC or not.
def is_npc_line(key, lines):
    if key not in lines:
        return False
    return lines[key]["character_id"] > 5

# determine if a dialog tree is an NPC dialog or something else,
# (eg an interaction tree.)
def is_npc_dialog(dialog, lines):
    for key in dialog.get("intro", dialog.get("cycle", list())):
        if is_npc_line(key, lines):
            return True

    for prompt in dialog.get("prompts", list()):
        for key in prompt.get("cycle", prompt.get("response", list())):
            if is_npc_line(key, lines):
                return True
    return False

# collate dialogs by room and folder, for AGS
def collate_dialogs(collated, dialogs, folder):
    for dialog in dialogs.values():
        room = dialog["room"]
        if room not in collated:
            collated[room] = dict()
        rdict = collated[room]
        if folder not in rdict:
            rdict[folder] = list()
        rdict[folder].append(dialog)

# collate and dump line data to json.
def write_lines_json(lines):
    collated = dict()
    for key, line in lines.items():
        char_id = line["character_id"]
        if char_id < 10:
            continue
        char_name = CHARACTER_IDS[char_id]
        if char_name not in collated:
            collated[char_name] = dict()
        # collated[char_name][key] = line
        count_key = "{}_{}".format(line["num"], msg_to_key(line["msg"]))
        collated[char_name][count_key] = line["msg"]

        # print("{} {}: {}".format(char_name, line["num"], line["msg"]))
    for char_name, cdict in collated.items():
        path = os.path.join("..", "lines", "{}.json".format(char_name))
        with open(path, "w") as file:
            json.dump(cdict, file, indent=4, sort_keys=True)

# dump collated dialogs to json.
def write_dialogs_json(collated):
    for room, rdict in collated.items():
        for category, dlist in rdict.items():
            path = os.path.join("..", "dialogs", room, "{}.json".format(category))
            Path(path).parent.mkdir(exist_ok=True, parents=True)
            with open(path, "w") as file:
                json.dump(dlist, file, indent=4, sort_keys = True)

# use the line dictionary to locate audio files, convert to AGS-friendly wav format,
# and copy them to the expected file location.
def export_audio(lines):
    for key, line in lines.items():
        char_id = line["character_id"]
        if char_id < 10:
            continue
        char_name = CHARACTER_IDS[char_id]
        src = os.path.join("..", "rip", "CDA", "aud", line["audiofile"])
        if not os.path.isfile(src):
            print("skipping unfound audio file {}".format(src))
            continue
        dst = os.path.join(AGS_SPEECH_PATH, "{}.{}.wav".format(char_name, line["num"]))
        print("exporting {} to {}...".format(src, dst))
        cvtaud(src, dst)

# rip all messages from all QGM files.
# return dialogs, singles, and lines dictionaries.
def rip_msgs():
    singles = dict()
    dialogs = dict()
    lines = dict()
    counts = dict()

    for room_num in ROOM_IDS.keys():
    # for room_num in [385]:
        fpath = os.path.join(MSG_PATH, "{}.QGM".format(room_num))
        print("Extracting messages from {}...".format(fpath))
        blocks = extract_blocks(fpath)
        get_lines(lines, blocks, counts)
        get_dialogs(dialogs, blocks)
        get_singles(singles, blocks)
        # print_blocks(blocks)
    return dialogs, singles, lines

# locate Lipsync files. TODO: Probably not to be used.
def gather_lips(lines):
    lips = set()
    for guid, line in lines.items():
        if "lipsyncfile" not in line:
            continue
        src = os.path.join("..", "rip", "CDA", "snc", line["lipsyncfile"])
        if not os.path.isfile(src):
            print("{} 404".format(src))
            continue
        with open(src, "rb") as file:
            file.read(2)
            fn = to_short(file.read(2))
            lips.add(fn)
    return lips


if __name__ == "__main__":
    argset = set(sys.argv[1:])
    export_speech = "--speech" in argset
    export_dialogs = "--dialogs" in argset
    lips = "--lips" in argset

    dialogs, singles, lines = rip_msgs()

    npc_trees = dict()
    narrator_trees = dict()
    for topic, dialog in dialogs.items():
        if is_npc_dialog(dialog, lines):
            npc_trees[topic] = dialog
        else:
            narrator_trees[topic] = dialog

    npc_singles = dict()
    narrator_singles = dict()
    for topic, single in singles.items():
        if is_npc_dialog(single, lines):
            npc_singles[topic] = single
        else:
            narrator_singles[topic] = single

    print("{} npc dialog trees detected".format(len(npc_trees.keys())))
    print("{} npc singles detected".format(len(npc_singles.keys())))
    print("{} interaction trees detected".format(len(narrator_trees.keys())))
    print("{} interaction singles detected".format(len(narrator_singles.keys())))

    collated = dict()
    collate_dialogs(collated, npc_trees, "npc_trees")
    collate_dialogs(collated, npc_singles, "npc_singles")
    collate_dialogs(collated, narrator_trees, "action_trees")
    collate_dialogs(collated, narrator_singles, "action_singles")
    write_dialogs_json(collated)

    with open("dialogs.json", "w") as file:
        json.dump(npc_trees, file, indent=4, sort_keys=True)

    with open("interactions.json", "w") as file:
        json.dump(narrator_trees, file, indent=4, sort_keys=True)

    with open("interaction_singles.json", "w") as file:
        json.dump(narrator_singles, file, indent=4, sort_keys=True)

    with open("npc_singles.json", "w") as file:
        json.dump(npc_singles, file, indent=4, sort_keys=True)

    with open("lines.json", "w") as file:
        json.dump(lines, file, indent=4, sort_keys = True)
    write_lines_json(lines)

    if export_speech:
        export_audio(lines)

    if export_dialogs:
        write_ags_dialogs(collated, lines)

    if lips:
        print(gather_lips(lines))

