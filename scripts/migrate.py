import json
import os
import sys

CHARACTER_PATH = os.path.join("..", "characters")
LINES_PATH = os.path.join("..", "lines")

def mkdict(old_data):
    new_data = dict()
    for item in old_data:
        if not "key" in item:
            print("no key")
            continue
        if not "en_us" in item:
            print("no value")
            continue
        new_data[item["key"]] = item["en_us"]
    return new_data

def migrate(character):
    dstdir = os.path.join(LINES_PATH, character)
    os.makedirs(dstdir, exist_ok=True)
    dstpath = os.path.join(dstdir, "en_us.json")
    srcpath = os.path.join(CHARACTER_PATH, character, "lines.json")
    with open(srcpath, 'r') as file:
        old_data = json.load(file)
        if not type(old_data) is list:
            print("invalid input data for {}", srcpath)
            return False
    new_data = mkdict(old_data)
    print(new_data)
    with open(dstpath, 'w') as file:
        json.dump(new_data, file, indent=4)

if __name__ == "__main__":
    for p in os.listdir(CHARACTER_PATH):
        migrate(p)
