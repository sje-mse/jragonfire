import os
import sys
from PIL import Image
sys.path.append(".")
from riputils import NPC_HEADS

LEN_RPAL = 72

def read_int(f):
    return int.from_bytes(f.read(4), 'little')

def read_short(f):
    return int.from_bytes(f.read(2), 'little')

def read_byte(f):
    return int.from_bytes(f.read(1), 'little')

def read_palette(f):
    palette = []
    for i in range(256):
        rgb555 = read_short(f)
        b = (0x1F & (rgb555 >> 0)) << 3
        g = (0x1F & (rgb555 >> 5)) << 3
        r = (0x1F & (rgb555 >> 10)) << 3
        palette.append(r)
        palette.append(g)
        palette.append(b)
    return palette

def read_mode_2(f, h, n):
    arr = []
    lines = 0
    while lines < h * n:
        code = int.from_bytes(f.read(1), 'little', signed=True)
        if (code == 0):
            lines += 1
        elif (code < 0):
            for _ in range(abs(code)):
                arr.append(read_byte(f))
        else:
            b = read_byte(f)
            for _ in range(code):
                arr.append(b)
    return arr

def read_mode_0(f, h, w, n):
    arr = []
    while (len(arr) < w * h * n):
        arr.append(read_byte(f))
    return arr

def read_mode_1(f, h, w, n):
    dep = []
    arr = []
    while (len(arr) < w * h * n):
        arr.append(read_byte(f))
        dep.append(read_byte(f))
    return arr

def create_img(num, w, h, arr, palette, rpal, pmap):
    img = Image.new('P', (w, h))
    if pmap:
        img.putpalette(rpal, 'RGB')
    else:
        img.putpalette(palette, 'RGB')

    for x in range(w):
        for y in range(h):
            index = (num * h * w) + (y * w) + x
            if index >= len(arr):
                print("invalid index attempted: {} > {}".format(index, len(arr)))
                return img
            if pmap:
                pixel = pmap[arr[index]]
            else:
                pixel = arr[index]
            img.putpixel((x, y), pixel)
    return img

def read_collection(f, palette, mode, pmap):
    x = read_int(f)
    y = read_int(f)
    w = read_int(f)
    h = read_int(f)
    n = read_int(f)
    delay = read_int(f)
    flags = read_int(f)

    print("...{} {}x{} frames detected with delay {}".format(n, w, h, delay))
    if (n > 256 or w == 0 or h == 0 or n == 0):
        print("...corruption suspected. aborting.")
        return []

    # offsets
    for i in range(n):
        read_int(f)

    if mode == 0:
        arr = read_mode_0(f, h, w, n)
    elif mode == 1:
        arr = read_mode_1(f, h, w, n)
    elif mode <= 4:
        arr = read_mode_2(f, h, n)
    else:
        print("unknown mode {} detected, corruption suspected. aborting.".format(mode))
        return []
    
    imgs = []
    for k in range(n):
        imgs.append(create_img(k, w, h, arr, palette, rpal, pmap))
    return imgs

def process_file(filename, rpal):
    outdir = os.path.join('..', 'rip', 'views', os.path.basename(filename).split('.')[0])
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    with open(filename, "rb") as f:
        mode = read_int(f)
        num_collections = read_int(f)
        print("{}: {} collections encoded with mode {}".format(filename, num_collections, mode))
        palette = read_palette(f)
        pmap = get_pmap(palette, rpal)

        # offsets
        for _ in range(num_collections):
            read_int(f)

        for c in range(num_collections):
            imgs = read_collection(f, palette, mode, pmap)
            i = 0
            for img in imgs:
                if rpal:
                    outpath = os.path.join(outdir, "r{}v{}.png".format(c, i))
                else:
                    outpath = os.path.join(outdir, "{}v{}.png".format(c, i))
                img.save(outpath)
                i += 1

def get_rpal():
    path = os.path.join('..', 'rip', 'views', '999.bmp')
    if not os.path.isfile(path):
        print('invalid remap palette location: {}'.format(path))
        return []
    rpal = Image.open(path).getpalette()
    for i in range(LEN_RPAL * 3, len(rpal)):
        rpal[i] = 0
    return rpal

def get_pmap(pal, rpal):
    if not rpal:
        return dict()

    pmap = dict()
    for i in range(256):
        best = 256 * 256 * 3
        best_index = 0
        for j in range(LEN_RPAL):
            dist = (pal[i * 3] - rpal[j * 3]) ** 2 + (pal[i * 3 + 1] - rpal[j * 3 + 1]) ** 2 + (pal[i * 3 + 2] - rpal[j * 3 + 2]) ** 2
            if dist < best:
                best_index = j
                best = dist
        pmap[i] = best_index
    pmap[255] = 255
    return pmap

if __name__ == "__main__":
    rpal = []
    if "remap" in sys.argv:
        rpal = get_rpal()

    for headnum in range(5, 73):
        filename = "{}.GRA".format(100000 + headnum)
        path = os.path.join('..', 'rip', 'CDN', 'GRA', "{}.GRA".format(100000 + headnum))
        if os.path.isfile(path):
            process_file(path, rpal)
        else:
            print("404 {}".format(path))
