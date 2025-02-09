from ffmpeg import FFmpeg
import os

def cvtfile(src, dst):
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(src)
        .output(
            dst,
        )
    )
    ffmpeg.execute()

for f in os.listdir("aud"):
    if not f.endswith("wav"):
        continue
    src = os.path.join("aud", f)
    dst = f
    print(src)
    cvtfile(src, dst)