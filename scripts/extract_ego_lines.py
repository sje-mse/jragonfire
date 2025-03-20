import json
import os
import sys

LINE_PATH = os.path.join("..", "lines")


def line_to_key(line):
    key = line
    key = key.replace("'", "")
    key = key.replace(".", "")
    key = key.replace(" ", "_")
    key = key.replace("-", "_")
    key = key.replace("&", "")
    key = key.replace("\n", "")
    key = key.lower()
    return key

def extract_ego():
    txtpath = os.path.join(LINE_PATH, "ego", "all.txt")
    if not os.path.isfile(txtpath):
        print("ERROR: not a real file {}".format(txtpath))
        return
    lines = list()
    with open(txtpath, "r") as file:
        lines = file.readlines()

    data = dict()

    for l in lines:
        key = line_to_key(l)
        newl = l.replace("\n", "")
        data[line_to_key(l)] = newl
    
    outpath = os.path.join(LINE_PATH, "ego", "en_us.json")
    with open(outpath, "w") as file:
        json.dump(data, file, indent=4, sort_keys=True)

if __name__ == "__main__":
    extract_ego()
