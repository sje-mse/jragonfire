import sys
import json

character_ids = {
    0 : "narr_interact",
    1 : "narr_look",
    2 : "ego",
    37 : "marrak"
}

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
        self.msg_guid = tuple()

    def has_options(self):
        return len(self.options) > 0

    def is_cycle(self):
        return (self.uk[1] & 0x01) == 0x01

class MsgTree:
    def __init__(self, guid, character_id):
        self.character_id = character_id
        self.guid = guid
        self.msgs = list()
        self.prompts = list()

class MsgPrompt:
    def __init__(self, guid):
        self.guid = guid
        self.ego = ""
        self.msgs = list()

    def __str__(self):
        return "--ego: {}\n{}".format(self.ego, "\n".join([str(s) for s in self.msgs]))

class MsgLine:
    def __init__(self, guid, character_id, msg):
        self.guid = guid
        self.character_id = character_id
        self.msg = msg

    def __str__(self):
        return "----{}: {}".format(self.character_id, self.msg)

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
            msg_lbl_present = to_short(file.read(2))
            block.uk.append(to_short(file.read(2)))
            block.filename = to_id_filename("A", block.guid)

            if msg_lbl_present != 0:
                msg_id_str = to_id_str(file.read(13))
                block.msg_guid = to_id_tuple(file_id, msg_id_str)

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

def get_series(guid, blocks):
    result = list()
    while guid in blocks:
        block = blocks[guid]
        if block.is_cycle():
            print("cycle!")
        line = MsgLine(block.guid, block.character_id, block.msg)
        guid = (guid[0], guid[1], guid[2], guid[3], guid[4] + 1)
        result.append(line)
    return result

def get_prompt(guid, blocks):
    block = blocks[guid]
    prompt = MsgPrompt(guid)
    if len(block.options) > 0:
        prompt.ego = block.msg
        prompt.msgs = get_series(block.options[0], blocks)
    if len(block.options) > 1:
        for option in block.options[1:]:
            print(">>>>>><<<<<<<<")
            for line in get_series(option, blocks):
                print("{}".format(line))
            print(">>>>>><<<<<<<<")
    return prompt

def get_trees(blocks):
    trees = dict()
    for guid, block in blocks.items():
        if (block.has_options()):
            # only care about trees with ego options.
            if (blocks[block.options[0]].character_id > 2):
                continue

            tree = MsgTree(guid, block.character_id)
            print("Tree {}".format(tree.guid))
            if (block.msg):
                tree.msgs.append(block.msg)
                print('{}: {}'.format(tree.character_id, block.msg))

            for option_id in block.options:
                o_block = blocks[option_id]
                prompt = get_prompt(option_id, blocks)
                tree.prompts.append(prompt)
                print("{}\n".format(prompt))
            trees[tree.guid] = tree
            print("========\n")
    return trees

def print_blocks(blocks):
    for guid, block in blocks.items():
        print("{} ({}) ========".format(guid, block.character_id))
        if block.msg:
            print("{}: {}".format(block.character_id, block.msg))
        for o in block.options:
            ob = blocks[o]
            print("----{}: {}".format(ob.character_id, ob.msg))
        if block.msg_guid:
            mb = blocks[block.msg_guid]
            print("\n{}: {}: {}".format(block.msg_guid, mb.character_id, mb.msg))
        print("{}==========\n".format(block.uk))


if __name__ == "__main__":
    fpath = "200.QGM"
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    print("Extracting messages from {}...".format(fpath))
    blocks = extract_blocks(fpath)
    trees = get_trees(blocks)

    print_blocks(blocks)
