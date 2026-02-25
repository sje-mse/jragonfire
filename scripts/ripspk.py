import sys
import os

sys.path.append(".")

from env_paths import (SPK_PATH, ZIP_PATH)

SPK_FILENAMES = ['CDA', 'CDN', 'HDN', 'HDNW']

EOCD_SIZE = 22 # from zip spec, observed empirically
LOCAL_HEADER_SIZE = 66 # observed empirically

def zipify(fn):
    srcpath = os.path.join(SPK_PATH, "{}.SPK".format(fn))
    dstpath = os.path.join(ZIP_PATH, "{}.zip",format(fn))

    with open(srcpath, 'rb') as f:
        spk_len = f.seek(0, 2)

        f.seek(-EOCD_SIZE, 1)
        magic = f.read(4)
        print("magic: {}".format(magic.hex()))
        skip = f.read(4)
        num_files = int.from_bytes(f.read(2), 'little')
        num_files_dup = int.from_bytes(f.read(2), 'little')
        print("{} == {}".format(num_files, num_files_dup))
        cd_size = int.from_bytes(f.read(4), 'little')
        cd_offset = int.from_bytes(f.read(4), 'little')

        print("cd size: {}".format(cd_size))
        print("cd offset: {}".format(cd_offset))
        comment_length = int.from_bytes(f.read(2), 'little')
        print("comment length: {}".format(comment_length))
        print("======\n")

        cd_start = spk_len - EOCD_SIZE - cd_size
        local_file_start = cd_start - cd_offset

        records = []
        f.seek(cd_start, 0)
        for i in range(num_files):
            magic = f.read(4)
            f.read(6) # skip
            comp_method = int.from_bytes(f.read(2), 'little')
            f.read(4) # skip
            crc32 = int.from_bytes(f.read(4), 'little')
            comp_size = int.from_bytes(f.read(4), 'little')
            uncomp_size = int.from_bytes(f.read(4), 'little')
            n = int.from_bytes(f.read(2), 'little')
            m = int.from_bytes(f.read(2), 'little')
            k = int.from_bytes(f.read(2), 'little')
            disk_number = int.from_bytes(f.read(2), 'little')
            internal_attr = int.from_bytes(f.read(2), 'little')
            external_attr = int.from_bytes(f.read(4), 'little')
            local_header_offset = int.from_bytes(f.read(4), 'little')
            filename = f.read(n).decode('utf-8')
            f.read(m + k) # skip
            records.append((filename, local_file_start + local_header_offset + LOCAL_HEADER_SIZE, uncomp_size))

        for filename, offset, size in records:
            print("{} {} {}".format(filename, offset, size))

if __name__ == "__main__":
    print(os.listdir(SPK_PATH))
    zipify('CDN')

