import sys
import json

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

def to_id_tuple(b):
	return (
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

def to_id_filename(char1, room, t):
	result = [char1]
	result.append(to_b36_str(room, 3))
	result.append(to_b36_str(t[0], 2))
	result.append(to_b36_str(t[1], 2))
	result.append('.')
	result.append(to_b36_str(t[2], 2))
	result.append(to_b36_str(t[3], 1))
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

def extract_blocks(fpath):
	with open(fpath, 'rb') as file:
		header = file.read(4)
		version = to_int(file.read(4))
		num_blocks = to_int(file.read(4))
		mystery = to_short(file.read(2))
		file_id = to_short(file.read(2))

		print("{} : v{} : {} ({})".format(header, version, file_id, mystery))
		print("{} blocks\n".format(num_blocks))

		for block_num in range(num_blocks):
			uks = [] # unknown codes
			block_id = (to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))
			character_id = to_short(file.read(2))
			uks.append(to_short(file.read(2)))
			uks.append(to_short(file.read(2)))
			# uks.append(to_short(file.read(2)))
			uks.append(to_byte(file.read(1)))
			uks.append(to_byte(file.read(1)))
			# print("{} {}".format(bin(ord(file.read(1))), bin(ord(file.read(1)))))

			print("MSG BLOCK {}======".format(block_num))
			num_options = to_short(file.read(2))
			flags = to_short(file.read(2))
			block_num = to_short(file.read(2))
			uks.append(to_short(file.read(2)))
			msg_len = to_short(file.read(2))
			uks.append(to_short(file.read(2)))
			msg_lbl_present = to_short(file.read(2))
			uks.append(to_short(file.read(2)))

			print("id: {}".format(block_id))
			print("character: {}".format(character_id))
			print("msg fn: {}".format(to_id_filename("A", file_id, block_id)))

			if msg_lbl_present != 0:
				msg_id = to_id_str(file.read(13))
				print("msg id: {}".format(to_id_tuple(msg_id)))

			if (num_options > 0):
				print("{} options:".format(num_options))
				for option_num in range(num_options):
					option_id = to_id_str(file.read(13))
					print("---{}: {}".format(option_num, to_id_tuple(option_id)))

			if (msg_len > 0):
				msg = file.read(msg_len)
				if flags & 0x04:
					decoded = decode(msg)
				else:
					decoded = "".join(msg)
				print("msg: {}".format(decoded))
			print("flags: {}".format(flags))
			print("block num: {}".format(block_num))

			footer = to_int(file.read(4))
			print("{} {}\n".format(footer, uks))


if __name__ == "__main__":
	fpath = "200.QGM"
	if len(sys.argv) > 1:
		fpath = sys.argv[1]
	print("hello {}".format(fpath))
	extract_blocks(fpath)
