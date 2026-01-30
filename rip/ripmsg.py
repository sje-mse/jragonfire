import sys
import json

def to_int(four_bytes):
	value = (int(four_bytes[0]) << 0)
	value |= (int(four_bytes[1]) << 8)
	value |= (int(four_bytes[2]) << 16)
	value |= (int(four_bytes[3]) << 24)
	return value

def to_short(two_bytes):
	value = (int(two_bytes[0]) << 0)
	value |= (int(two_bytes[1]) << 8)
	return value

def to_msg_id(b13):
	return "".join([char(b) for b in b13])

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

			obf_msg = file.read(msg_len)

			footer = file.read(4)
			print("{}\n".format(to_int(footer)))


if __name__ == "__main__":
	fpath = "200.QGM"
	if len(sys.argv) > 1:
		fpath = sys.argv[1]
	print("hello {}".format(fpath))
	extract_blocks(fpath)
