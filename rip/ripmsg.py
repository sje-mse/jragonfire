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
	return "".join([chr(b) for b in b13])

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
			block_id = (to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))
			block_meta = (to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)), to_short(file.read(2)))

			print("MSG BLOCK {}======".format(block_num))
			num_options = to_short(file.read(2))
			flags = to_short(file.read(2))
			# msg_num = to_short(file.read(2))
			# unknown_1 = to_short(file.read(2))
			# msg_len = to_short(file.read(2))
			# unknown_2 = to_short(file.read(2))
			# msg_lbl_present = to_short(file.read(2))
			# unknown_3 = to_short(file.read(2))
			msg_num = to_int(file.read(4))
			msg_len = to_int(file.read(4))
			msg_lbl_present = to_int(file.read(4))

			print("id: {}".format(block_id))
			print("char: {}".format(block_meta[0]))

			if msg_lbl_present > 0:
				msg_id = to_msg_id(file.read(13))
				print("msg id: {}".format(msg_id))

			if (num_options > 0):
				print("{} options:".format(num_options))
				for option_num in range(num_options):
					option_id = to_msg_id(file.read(13))
					print("---{}: {}".format(option_num, option_id))

			if (msg_len > 0):
				msg = file.read(msg_len)
				if flags & 0x04:
					decoded = decode(msg)
				else:
					decoded = "".join(msg)
				print("msg: {}".format(decoded))
			# print("options: {}".format(num_options))
			print("flags: {}".format(flags))
			print("msg_num: {}".format(msg_num))
			print("msg_len: {}".format(msg_len))
			# print("msg_lbl_present: {}".format(msg_lbl_present))
			# print("unknown: {} {} {}".format(unknown_1, unknown_2, unknown_3))

			footer = to_int(file.read(4))
			print("{}======\n".format(footer))


if __name__ == "__main__":
	fpath = "200.QGM"
	if len(sys.argv) > 1:
		fpath = sys.argv[1]
	print("hello {}".format(fpath))
	extract_blocks(fpath)
