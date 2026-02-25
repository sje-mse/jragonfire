import sys
import os
from pathlib import Path

sys.path.append(".")

from env_paths import SPK_PATH

SPK_FILENAMES = ['CDA', 'CDN', 'HDN', 'HDNW']

EOCD_SIZE = 22 # from zip spec, observed empirically

def unpack(spk_name):
    srcpath = os.path.join(SPK_PATH, "{}.SPK".format(spk_name))

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
            records.append((filename, local_file_start + local_header_offset, uncomp_size))

        for filename, offset, size in records:
            f.seek(offset, 0)
            magic = f.read(4)
            f.read(14) # skip
            comp_size = int.from_bytes(f.read(4), 'little')
            uncomp_size = int.from_bytes(f.read(4), 'little')
            n = int.from_bytes(f.read(2), 'little')
            m = int.from_bytes(f.read(2), 'little')
            fn = f.read(n).decode('utf-8')
            f.read(m) # skip
            content = f.read(size)
            if filename != fn:
                print("skipping {}: filename mismatch {}".format(filename, fn))
                continue
            if size != comp_size:
                print("skpping {}: size mismatch {} {} {}".format(filename, size, comp_size, uncomp_size))
                continue
            opath = os.path.join('..', 'rip', spk_name, filename)
            Path(opath).parent.mkdir(exist_ok=True, parents=True)
            print("unpacking {} ({} bytes)...".format(opath, size))
            with open(opath, 'wb') as ofile:
                ofile.write(content)

if __name__ == "__main__":
    for spk in SPK_FILENAMES:
        unpack(spk)

