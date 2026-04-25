## UTILITY FUNCTIONS

def read_int(f):
    return int.from_bytes(f.read(4), 'little')

def read_short(f):
    return int.from_bytes(f.read(2), 'little')

def read_byte(f):
    return int.from_bytes(f.read(1), 'little')

def read_rle(f, h):
    arr = []
    lines = 0
    while lines < h:
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
