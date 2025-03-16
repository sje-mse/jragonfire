import json
import os
import sys

ITEMS_PATH = os.path.join("..", "items")

def verify_items():
    allpath = os.path.join(ITEMS_PATH, "all.json")
    if not os.path.isfile(allpath):
        print("ERROR: not a real file {}".format(allpath))
        return

    data = list()
    with open(allpath, 'r') as file:
        data = json.load(file)
        if not type(data) is list:
            print("ERROR: not a list!")
            return

    good_fields = set(["name", "description"])

    good = True
    num_good = 0
    num_bad = 0
    for item in data:
        good = True
        for key, value in item.items():
            if not key in good_fields:
                good = False
        if good:
            num_good += 1
        else:
            num_bad += 1
            continue
        key = item["name"]
        key = key.replace("'", "")
        key = key.replace(".", "")
        key = key.replace(" ", "_")
        key = key.replace("-", "_")
        key = key.replace("&", "")
        key = key.lower()
        print(key)

        folder = os.path.join(ITEMS_PATH, key)
        if not os.path.exists(folder):
            os.mkdir(folder)
        jpath = os.path.join(folder, "en_us.json")
        with open(jpath, "w") as file:
            json.dump(item, file, indent=4, sort_keys=True)

    print("good items: {}".format(num_good))
    print("bad items: {}".format(num_bad))

if __name__ == "__main__":
    verify_items()
