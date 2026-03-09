import os
import sys
from PIL import Image
sys.path.append(".")
from riputils import NPC_HEADS

def read_int(f):
    return int.from_bytes(f.read(4), 'little')

def read_short(f):
    return int.from_bytes(f.read(2), 'little')

def read_pallet(f):
    pallet = []
    for i in range(256):
        pallet.append(int.from_bytes(f.read(2), 'little'))
    return pallet

def read_mode_3(f, h, n):
    arr = []
    lines = 0
    while lines < h * n:
        code = int.from_bytes(f.read(1), 'little', signed=True)
        if (code == 0):
            lines += 1
        elif (code < 0):
            for _ in range(abs(code)):
                arr.append(int.from_bytes(f.read(1)))
        else:
            b = int.from_bytes(f.read(1))
            for _ in range(code):
                arr.append(b)
    return arr

def read_mode_0(f, h, w, n):
    arr = []
    while (len(arr) < w * h * n):
        arr.append(int.from_bytes(f.read(1)))
    return arr

def read_collection(f, pallet, mode):
    x = read_int(f)
    y = read_int(f)
    w = read_int(f)
    h = read_int(f)
    n = read_int(f)
    delay = read_int(f)
    flags = read_int(f)

    print("...{} {}x{} frames detected with delay {}".format(n, w, h, delay))
    if (n > 4192 or w == 0 or h == 0 or n == 0):
        print("...corruption suspected. aborting.")
        return []

    # offsets
    for i in range(n):
        read_int(f)

    if (mode >= 2):
        arr = read_mode_3(f, h, n)
    elif (mode == 0):
        arr = read_mode_0(f, h, w, n)
    else:
        print("...mode {} not yet implemented".format(mode))
        return []
    
    imgs = []
    for k in range(n):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(w):
            for j in range(h):
                index = (k * h * w) + (j * w) + i
                if index >= len(arr):
                    print("invalid index attempted: {} > {}".format(index, len(arr)))
                    return imgs
                rgb555 = pallet[arr[index]]
                img[j, i, 0] = (0b0000000000011111 & rgb555) << 3
                img[j, i, 1] = (0b0000000000011111 & (rgb555 >> 5)) << 3
                img[j, i, 2] = (0b0000000000011111 & (rgb555 >> 10)) << 3
        imgs.append(img)
    return imgs

def process_file(filename):
    outdir = os.path.join('..', 'rip', 'sprites', os.path.basename(filename).split('.')[0])
    if (not os.path.isdir(outdir)):
        os.mkdir(outdir)

    with open(filename, "rb") as f:
        mode = read_int(f)
        num_collections = read_int(f)
        print("{}: {} collections encoded with mode {}".format(filename, num_collections, mode))
        pallet = read_pallet(f)

        # offsets
        for _ in range(num_collections):
            read_int(f)

        for c in range(num_collections):
            imgs = read_collection(f, pallet, mode)
            i = 0
            for img in imgs:
                outfile = os.path.join(outdir, "frame_{}_{}.bmp".format(i, c))
                cv.imwrite(outfile, img)
                i += 1

if __name__ == "__main__":
    for headnum in range(5, 73):
        filename = "{}.GRA".format(100000 + headnum)
        path = os.path.join('..', 'rip', 'CDN', 'GRA', "{}.GRA".format(100000 + headnum))
        if os.path.isfile(path):
            process_file(path)
        else:
            print("404 {}".format(path))
