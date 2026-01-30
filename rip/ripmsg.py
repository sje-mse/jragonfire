import sys
import json

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

def to_msg_id(b13):
	return "".join([char(b) for b in b13])

"""
1. split data into 4-byte chunks and tail 0-3 bytes long;
2. for each 4-byte chunk repeat steps 3-6:
3. read those bytes as 32-bit little-endian number;
4. exclusive-or the value with constant 0xf1acc1d;
5. rotate value cyclically left by 15 bits;
6. store 32-bit number back as four bytes;
7. invert bits in all bytes of the tail.
"""
def decode(file, msg_len):
	deffed = list()
	tail = 4 & msg_len
	for i in range(0, msg_len, 4):
		step2 = file.read(4)
		step3 = int(step2[0]) << 24
		step3 |= int(step2[1]) << 16
		step3 |= int(step2[2]) << 8
		step3 |= int(step2[3]) << 0

		step4 = step3 ^ 0xf1acc1d;
		step5 = (step4 >> 17) | (step4 << 15) & 0xffffffff

		deffed.append(chr(0xff & (step5 >> 24)))
		deffed.append(chr(0xff & (step5 >> 16)))
		deffed.append(chr(0xff & (step5 >> 8)))
		deffed.append(chr(0xff & (step5 >> 0)))
		print(i)

	print(deffed)

	'''
	for i in range(msg_len - tail, msg_len):
		deffed.append(~file.read(1))
	'''
	file.read(tail)
	return "{}".format(deffed)

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
			block_id = (to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))
			block_meta = (to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))

			print("MSG BLOCK {}======".format(block_num))
			num_options = to_short(file.read(2))
			flags = to_short(file.read(2))
			unknown_1 = to_short(file.read(2))
			msg_num = to_short(file.read(2))
			msg_len = to_short(file.read(2))
			unknown_2 = to_short(file.read(2))
			msg_lbl_present = to_short(file.read(2))
			unknown_3 = to_short(file.read(2))
			print("id: {}".format(block_id))
			print("char: {}".format(block_meta[0]))
			print("options: {}".format(num_options))
			print("flags: {}".format(flags))
			print("msg_num: {}".format(msg_num))
			print("msg_len: {}".format(msg_len))
			print("msg_lbl_present: {}".format(msg_lbl_present))
			print("unknown: {} {} {}".format(unknown_1, unknown_2, unknown_3))

			if msg_lbl_present > 0:
				msg_id = file.read(13)
				print("msg id: {}".format(msg_id))

			for option_num in range(num_options):
				option_id = file.read(13)
				print("option_id: {}".format(option_id))

			"""
			if flags & 0x04:
				msg = decode(file, msg_len)
			else:
				msg = file.read(msg_len)
			print("{}".format(msg))
			"""

			file.read(msg_len)

			footer = file.read(4)
			print("{}\n".format(to_int(footer)))


if __name__ == "__main__":
	fpath = "200.QGM"
	if len(sys.argv) > 1:
		fpath = sys.argv[1]
	print("hello {}".format(fpath))
	extract_blocks(fpath)
