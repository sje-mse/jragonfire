import json
import os
import sys

LINE_PATH = os.path.join("..", "lines")

def verify_lines(charpath, audiopath):
    path = os.path.join(charpath, "en_us.json")
    all_keys = set()
    data = dict()
    with open(path, 'r') as file:
        data = json.load(file)
        if not type(data) is dict:
            print("not a dict!")
            return False

        for key in data.keys():
            all_keys.add(key)

    # sanitize file
    if data:
        with open(path, "w") as file:
            json.dump(data, file, indent=4, sort_keys=True)

    if not os.path.isdir(audiopath):
        print("{} does not exist!".format(audiopath))
    all_audio = set()
    for p in os.listdir(audiopath):
        if not os.path.isfile(os.path.join(audiopath, p)):
            continue
        name, ext = os.path.splitext(p)
        if name.startswith("aud_"):
            continue
        all_audio.add(name)
        if not ext == ".wav":
            print("invalid audio file: {} is not a .wav".format(p))
            return False
    for k in all_audio:
        if not k in all_keys:
            print("audio file {} not found in keys!".format(k))
            return False
    for k in all_keys:
        if not k in all_audio:
            print("key {} not found in audio files!".format(k))
            return False
    return all_audio == all_keys


def verify_characters(audioroot):
    for p in os.listdir(LINE_PATH):
        charpath = os.path.join(LINE_PATH, p)
        audiopath = os.path.join(audioroot, p)
        print("{}...".format(p))
        if os.path.isdir(charpath) and os.path.isdir(audiopath):
            if (verify_lines(charpath, audiopath)):
                print("...all good!")
            else:
                print("...INVALID")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audioroot = sys.argv[1]
        if os.path.isdir(audioroot):
            verify_characters(audioroot)
        else:
            print("invalid audio path provided: {}".format(audioroot))
    else:
        print("usage: {} <audio root>".format(sys.argv[0]))
