import os
import sys
from PIL import Image
sys.path.append(".")

from riputils import *

LEN_RPAL = 72

###############################################################################
## RIP VIEWS
##
## Extract animated sprite information from .GRA files
## (previously unpacked from spk files using ripspk.py)
## and dump them to PNG, preparing for the possibility
## of exporting them to AGS.
##
## USAGE:
##
## python ripviews.py [--remap]
##
## if argument "--remap" is provided, makes an attempt to remap original color
## data to the sprite portion of the universal palette.
##
###############################################################################


# convert palette information from RGB555 to the flat 256 * 3 entry table
# expected by the PIL library.
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

# raw pixel data
def read_mode_0(f, h, w):
    arr = []
    while (len(arr) < w * h):
        arr.append(read_byte(f))
    return arr

# pixel data interlaced with depth data.
def read_mode_1(f, h, w):
    dep = []
    arr = []
    while (len(arr) < w * h):
        arr.append(read_byte(f))
        dep.append(read_byte(f))
    return arr

# given the indexed image encoded in arr,
# return a PIL image.
# optionally, use the mapping provided in "pmap"
# to replace the indexes in "arr" with their mapped index in "rpal".
def create_img(w, h, arr, palette, rpal, pmap):
    img = Image.new('P', (w, h))
    if pmap:
        img.putpalette(rpal, 'RGB')
    else:
        img.putpalette(palette, 'RGB')

    for x in range(w):
        for y in range(h):
            index = (y * w) + x
            if index >= len(arr):
                print("invalid index attempted: {} >= {}".format(index, len(arr)))
                return img
            if pmap:
                pixel = pmap[arr[index]]
            else:
                pixel = arr[index]
            img.putpixel((x, y), pixel)
    return img

def read_collection(f, collection_offset, palette, mode, pmap):
    f.seek(collection_offset, 0)
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
    frame_offsets = [read_int(f) for _ in range(n)]

    frames = list()
    for frame_num, frame_offset in enumerate(frame_offsets):
        f.seek(collection_offset + frame_offset, 0)
        if mode == 0:
            arr = read_mode_0(f, h, w)
        elif mode == 1:
            arr = read_mode_1(f, h, w)
        elif mode <= 4:
            arr = read_rle(f, h)
        else:
            print("unknown mode {} detected, corruption suspected. aborting.".format(mode))
            return frames
        frames.append(create_img(w, h, arr, palette, rpal, pmap))
    
    return frames

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
        collection_offsets = [read_int(f) for _ in range(num_collections)]

        for c, offset in enumerate(collection_offsets):
            imgs = read_collection(f, offset, palette, mode, pmap)
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

# attempt to create a mapping from indexes from the extracted palette "pal"
# to the sprite palette "rpal". Uses a fairly naive algorithm.
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
    if "--remap" in sys.argv:
        rpal = get_rpal()

    folder = os.path.join('..', 'rip', 'CDN', 'GRA')
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if os.path.isfile(path):
            process_file(path, rpal)
        else:
            print("404 {}".format(path))

    '''
    for headnum in range(1000):
        filename = "{}.GRA".format(100000 + headnum)
        path = os.path.join('..', 'rip', 'CDN', 'GRA', "{}.GRA".format(100000 + headnum))
        if os.path.isfile(path):
            process_file(path, rpal)
        else:
            print("404 {}".format(path))
    '''
