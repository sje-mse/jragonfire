import sys
import json
import re

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

to36 = [
    "0", "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "A", "B",
    "C", "D", "E", "F", "G", "H",
    "I", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z"]

def to_int(four_bytes):
    value = int(four_bytes[0]) << 0
    value |= int(four_bytes[1]) << 8
    value |= int(four_bytes[2]) << 16
    value |= int(four_bytes[3]) << 24
    return value

def to_short(two_bytes):
    value = int(two_bytes[0]) << 0
    value |= int(two_bytes[1]) << 8
    return value

def to_byte(one_byte):
    return int(one_byte[0])

def to_id_str(b13):
    return "".join([chr(b) for b in b13[:12]])

def to_id_tuple(room, b):
    return (
        room,
        (from36[b[4]] * 36) + from36[b[5]],
        (from36[b[6]] * 36) + from36[b[7]],
        (from36[b[9]] * 36) + from36[b[10]],
        from36[b[11]]
    )

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

def to_id_filename(char1, t):
    result = [char1]
    result.append(to_b36_str(t[0], 3))
    result.append(to_b36_str(t[1], 2))
    result.append(to_b36_str(t[2], 2))
    result.append('.')
    result.append(to_b36_str(t[3], 2))
    result.append(to_b36_str(t[4], 1))
    return "".join(result)

def msg_to_key(msg):
    plain = re.sub(r'[^a-zA-Z0-9 ]', '', msg)
    parts = [w for w in plain.lower().split(" ") if w]
    return "_".join(parts[:4])

def to_topic(block, msg):
    key = msg_to_key(msg)
    return "{}_{}_{}_{}".format(block.character_id, block.guid[0], block.index, key)

"""
1. split data into 4-byte chunks and tail 0-3 bytes long;
2. for each 4-byte chunk repeat steps 3-6:
3. read those bytes as 32-bit little-endian number;
4. exclusive-or the value with constant 0xf1acc1d;
5. rotate value cyclically left by 15 bits;
6. store 32-bit number back as four bytes;
7. invert bits in all bytes of the tail.
"""
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
                    block.msg = "".join(msg)

            block.uk.append(to_int(file.read(4)))
            blocks[block.guid] = block
    return blocks

def get_response(guid, blocks):
    is_cycle = False
    result = list()
    while guid in blocks:
        block = blocks[guid]
        result.append(to_topic(block, block.msg))
        if block.is_cycle():
            is_cycle = True
        guid = (guid[0], guid[1], guid[2], guid[3], guid[4] + 1)
    return result, is_cycle

def get_prompt(guid, blocks):
    block = blocks[guid]
    prompt = dict()
    prompt["ego"] = block.msg
    if block.has_options():
        o_guid = block.options[0]
        response, is_cycle = get_response(o_guid, blocks)
        if is_cycle:
            prompt["cycle"] = response
        else:
            prompt["response"] = response
        ob = blocks[o_guid]
        if ob.has_options():
            prompt["goto"] = to_topic(ob, block.msg)
    '''
    if len(block.options) > 1:
        for option in block.options[1:]:
            print(">>>>>><<<<<<<<")
            for line in get_series(option, blocks):
                print("{}".format(line))
            print(">>>>>><<<<<<<<")
    '''
    return prompt

def get_dialogs(dialogs, blocks):
    for guid, block in blocks.items():
        if (block.has_options()):
            # only care about trees with ego options.
            if (blocks[block.options[0]].character_id > 2):
                continue

            dialog = dict()

            # resolve options and responses
            dialog["prompts"] = list()
            for option_id in block.options:
                prompt = get_prompt(option_id, blocks)
                dialog["prompts"].append(prompt)

            # figure out the parent, if any
            if block.has_parent():
                parent = blocks[block.parent_guid]
                dialog["topic"] = to_topic(block, parent.msg)
            else:
                dialog["topic"] = to_topic(block, "root")
                # get "intro" message(s) only if not a subdialog
                if block.msg:
                    dialog["intro"], _ = get_response(guid, blocks)

            dialogs[dialog["topic"]] = dialog

def get_singles(dialogs, blocks):
    for guid, block in blocks.items():
        if not block.follows() and block.character_id > 2 and not block.has_parent() and not block.has_options():
            dialog = dict()
            key = to_topic(block, block.msg)
            dialog["intro"], _ = get_response(guid, blocks)
            dialog["topic"] = key
            dialogs[key] = dialog

def get_lines(blocks):
    result = dict()
    for guid, block in blocks.items():
        # only count lines from npcs
        if block.character_id <= 2:
            continue
        data = dict()
        data["msg"] = block.msg
        data["audiofile"] = to_id_filename("A", block.guid)
        data["lipsyncfile"] = to_id_filename("S", block.guid)
        data["guid"] = block.guid
        key = to_topic(block, block.msg)
        result[key] = data
    return result

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

def print_response(response, lines):
    for key in response:
        if key in lines:
            print("----{} : {}".format(key, lines[key]["msg"]))
        else:
            print("----{} NOT FOUND".format(key))

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

def print_dialogs(dialogs, lines):
    for key, line in lines.items():
        print("{} : {}".format(key, line["msg"]))

    for topic, dialog in dialogs.items():
        print("\n=========================")
        print("topic: {}".format(topic))
        if "intro" in dialog:
            print("intro:")
            print_response(dialog["intro"], lines)

        if "prompts" in dialog:
            print("prompts:")
            for prompt in dialog["prompts"]:
                print_prompt(prompt, lines)

if __name__ == "__main__":
    fpath = "200.QGM"
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    print("Extracting messages from {}...".format(fpath))
    blocks = extract_blocks(fpath)

    lines = get_lines(blocks)

    dialogs = dict()
    get_dialogs(dialogs, blocks)
    get_singles(dialogs, blocks)

    print_dialogs(dialogs, lines)

    with open("dialogs.json", "w") as file:
        json.dump(dialogs, file, indent=4, sort_keys=True)
