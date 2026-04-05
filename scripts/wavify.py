from ffmpeg import FFmpeg
import os
import sys

def cvtaud(src, dst):
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(src)
        .output(
            dst,
        )
    )
    ffmpeg.execute()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        cvtaud(sys.argv[1], sys.argv[2])
    else:
        print("usage: python {} <src> <dst>".format(sys.argv[0]))
