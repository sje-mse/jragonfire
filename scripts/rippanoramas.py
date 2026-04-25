import os
import sys
from PIL import Image
sys.path.append(".")

from riputils import *

###############################################################################
## RIP PANORAMAS
##
## Extract background panoramas from resource files.
## (previously unpacked from spk files using ripspk.py)
## and dump them to PNG.
## Slice, downsample, and collate them into AGS-friendly room backgrounds.
##
## USAGE:
##
## python rippanoramas.py
##
###############################################################################

PALETTE_DIR = os.path.join('..', 'rip', 'CDN', 'NOD')
PANORAMA_DIR = os.path.join('..', 'rip', 'CDN', 'IMG')

def read_palette(path):
    pal = list()
    with open(path, "rb") as f:
        f.seek(0xA8)
        for _ in range(256):
            pal.append(read_byte(f)) # red
            pal.append(read_byte(f)) # green
            pal.append(read_byte(f)) # blue
            read_byte(f) # skip alpha
    return pal

def read_panorama(path):
    with open(path, "rb") as f:
        f.read(32) # skip big-endian header
        w = read_int(f)
        h = read_int(f)
        f.read(24)
        return read_rle(f, h), w, h 

# given the indexed image encoded in arr
# return a PIL image.
# Note: Images are stored on their side, so this method rotates it back.
def create_img(w, h, arr, palette):
    img = Image.new('P', (h, w))
    img.putpalette(palette, 'RGB')

    for x in range(w):
        for y in range(h):
            index = (y * w) + x
            if index >= len(arr):
                print("invalid index attempted: {} >= {}".format(index, len(arr)))
                return img
            pixel = arr[index]
            img.putpixel((h - 1 - y, x), pixel)
    return img

def rip_panoramas():
    outdir = os.path.join('..', 'rip', 'panoramas')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    for basename in os.listdir(PANORAMA_DIR):
        filestem = os.path.splitext(basename)[0]
        panorama_path = os.path.join(PANORAMA_DIR, basename)
        palette_path = os.path.join(PALETTE_DIR, "{}.NOD".format(filestem))
        if not os.path.isfile(panorama_path):
            print("panorama 404: {}".format(panorama_path))
            continue
        if not os.path.isfile(palette_path):
            print("palette 404: {}".format(palette_path))
            continue

        palette = read_palette(palette_path)
        panorama, w, h = read_panorama(panorama_path)
        img = create_img(w, h, panorama, palette)
        print("{}: {}x{}...".format(filestem, h, w))
        img.save(os.path.join(outdir, "{}.png".format(filestem)))


if __name__ == "__main__":
    rip_panoramas()
