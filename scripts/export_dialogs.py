import json
import os
import shutil
import sys
from pathlib import Path

sys.path.append(".")

from env_paths import (
    AGS_PATH,
    AGS_SPEECH_PATH,
    AGS_XML_PATH,
    BACKUP_AGS_XML_PATH,
    SPEECH_PATH,
)

from verify_dialogs import (
    ACTIONS_KEY,
    TOPIC_DELIMITER,
    read_all_dialogs,
    read_all_lines,
    verify_dialog,
)

GO_TO_PREVIOUS = "go_to_previous"
TMP_PATH = "tmp.xml"
ROOT_SUFFIX = "{}root".format(TOPIC_DELIMITER)
PREAMBLE_SUFFIX = "{}preamble".format(TOPIC_DELIMITER)
CYCLES_HEADER_PATH = os.path.join(AGS_PATH, "DialogCycles.ash")
CYCLES_SCRIPT_PATH = os.path.join(AGS_PATH, "DialogCycles.asc")

class LineCache:
    def __init__(self):
        self.count = 0
        self.cache = dict()

    def has(self, line_key):
        return line_key in self.cache

    def put(self, line_key):
        self.count += 1
        self.cache[line_key] = self.count
        return self.count

    # @return line number on hit, 0 on miss
    def get(self, line_key):
        return self.cache.get(line_key, 0)

class Cycle:
    def __init__(self, key, index):
        self.key = key
        self.index = index
        self.line_pairs = list()

class CycleCache:
    def __init__(self):
        self.max_cycles = 0
        self.index = 0
        self.cache = list() # [Cycle]

def encache(speaker_key, line_key, cache):
    src_path = os.path.join(SPEECH_PATH, speaker_key, '{}.wav'.format(line_key))
    if os.path.isfile(src_path):
        line_id = cache[speaker_key].put(line_key)
        dst_path = os.path.join(AGS_SPEECH_PATH, '{}.{}.wav'.format(speaker_key, line_id))
        print('copying {} to {}...'.format(src_path, dst_path))
        shutil.copy(src_path, dst_path)
    else:
        print("no line found for {}".format(src_path))

def export_action(action_list, ofile):
    for action in action_list:
        ofile.write('    doAction("{}")\n'.format(action))

def resolve_line(speaker_key, line_key, lines, cache):
    line = lines[speaker_key][line_key]

    # get cached id if it exists
    if speaker_key not in cache:
        cache[speaker_key] = LineCache()

    if not cache[speaker_key].has(line_key):
        encache(speaker_key, line_key, cache)

    line_id = cache[speaker_key].get(line_key)

    if line_id > 0:
        return '&{} {}'.format(line_id, line)
    else:
        return line

def export_line(speaker_key, line_key, lines, cache, ofile):
    line = resolve_line(speaker_key, line_key, lines, cache)
    ofile.write('{}: {}\n'.format(speaker_key, line))

def export_response(response, lines, cache, ofile):
    for speaker_key, line_key in response.items():
        if speaker_key in lines:
            export_line(speaker_key, line_key, lines, cache, ofile)

def count_cycles(dialog):
    count = 0
    for prompt in dialog.get("prompts", []):
        if "cycle" in prompt:
            count += 1
    return count

def export_cycle(dialog_name, ego_line, cycle_list, lines, cache, cycles, ofile):
    cycle = Cycle('cycle{}{}{}{}'.format(TOPIC_DELIMITER, dialog_name, TOPIC_DELIMITER, ego_line), cycles.index)
    for response in cycle_list:
        for speaker_key, line_key in response.items():
            if speaker_key in lines:
                cycle.line_pairs.append((speaker_key, resolve_line(speaker_key, line_key, lines, cache)))
    cycles.cache.append(cycle)
    cycles.index += 1
    ofile.write("    {}();\n".format(cycle.key))

def export_option(option_id, line, ofile):
    ofile.write('                  <DialogOption>\n')
    ofile.write('                    <ID>{}</ID>\n'.format(option_id))
    ofile.write('                    <Say>False</Say>\n')
    ofile.write('                    <Show>True</Show>\n')
    ofile.write('                    <Text xml:space="preserve">{}</Text>\n'.format(line))
    ofile.write('                  </DialogOption>\n')

def get_goto_cmd(dialog_name, target):
    return 'goto-dialog d{}{}{}\n'.format(dialog_name.split(TOPIC_DELIMITER)[0].title(), TOPIC_DELIMITER, target.title())

def export_dialog(id_count, name, dialog, lines, cache, cycles, ofile):
    ofile.write('              <Dialog>\n')
    ofile.write('               <ID>{}</ID>\n'.format(id_count))
    ofile.write('               <Name>d{}</Name>\n'.format(name.title()))
    ofile.write('               <ShowTextParser>False</ShowTextParser>\n')
    ofile.write('               <Script><![CDATA[// Dialog script file\n')

    num_cycles = count_cycles(dialog)
    cycles.max_cycles = max(num_cycles, cycles.max_cycles)
    cycles.index = 0

    # startup
    ofile.write('@S  // Dialog startup entry point\n')

    if num_cycles > 0:
        ofile.write('    reset_dialog_cycle_counters();\n')

    if "intro" in dialog:
        for response in dialog["intro"]:
            export_response(response, lines, cache, ofile)

    if name.endswith(PREAMBLE_SUFFIX):
        ofile.write(get_goto_cmd(name, "root"))
    else:
        ofile.write('return\n')

    # prompt responses
    is_root = name.endswith(ROOT_SUFFIX)
    option_id = 0 
    prompts = dialog.get("prompts", [])
    for i, prompt in enumerate(prompts):
        prompt = prompts[i]
        option_id += 1
        ofile.write('@{}\n'.format(option_id))

        if "response" in prompt:
            for response in prompt["response"]:
                export_response(response, lines, cache, ofile)
        elif "cycle" in prompt:
            export_cycle(name, prompt["ego"], prompt["cycle"], lines, cache, cycles, ofile)

        # single lines
        for key, value in prompt.items():
            if key in lines and key != "ego":
                export_line(key, value, lines, cache, ofile)

        # TODO: Actions

        if "goto" in prompt:
            ofile.write(get_goto_cmd(name, prompt["goto"]))
        elif is_root and i == (len(prompts) - 1):
            ofile.write('stop\n')
        else :
            ofile.write('return\n')

    if not is_root and option_id > 0:
        option_id += 1
        ofile.write('@{}\n'.format(option_id))
        ofile.write('goto-previous\n')

    ofile.write(']]></Script>\n')
    ofile.write('               <DialogOptions>\n')

    # prompt options
    option_id = 0 
    for prompt in prompts:
        option_id += 1
        export_option(option_id, lines["ego"][prompt["ego"]], ofile)

    if not is_root and option_id > 0:
        option_id += 1
        export_option(option_id, lines["ego"][GO_TO_PREVIOUS], ofile)

    ofile.write('               </DialogOptions>\n')
    ofile.write('              </Dialog>\n')

def update_stack(line, stack):
    if line.endswith("<Dialogs>"):
        stack.append(line)
    elif line.endswith("</Dialogs>"):
        stack.pop()

def write_dialogs(ipath):
    id_count = 0
    lines = read_all_lines()
    dialogs = read_all_dialogs()

    stack = []
    cache = dict() # { character_name, LineCache }
    cycles = CycleCache()

    with open(ipath, 'r') as ifile:
        with open(TMP_PATH, 'w') as ofile:
            # copy pre-dialog section.
            while line := ifile.readline():
                ofile.write(line)
                update_stack(line.strip(), stack)
                if stack:
                    break

            ofile.write('      <DialogFolder Name="Main">\n')
            ofile.write('        <SubFolders>\n')

            for folder_name, char_dict in dialogs.items():
                print("exporting folder {}...".format(folder_name))
                ofile.write('          <DialogFolder Name="{}">\n'.format(folder_name))
                ofile.write('            <SubFolders />\n')
                ofile.write('            <Dialogs>\n')

                for key, dialog in char_dict.items():
                    if verify_dialog(dialog, lines):
                        print("...exporting dialog {}".format(key))
                        export_dialog(id_count, key, dialog, lines, cache, cycles, ofile)
                        id_count += 1
                    else:
                        print("...skipping invalid dialog {}".format(key))

                ofile.write('            </Dialogs>\n')
                ofile.write('          </DialogFolder>\n')

            ofile.write('        </SubFolders>\n')
            ofile.write('        <Dialogs />\n')
            ofile.write('      </DialogFolder>\n')

            # copy post-dialog section.
            while line := ifile.readline():
                update_stack(line.strip(), stack)
                if not stack:
                    ofile.write(line)

    # write cycles
    with open(CYCLES_HEADER_PATH, 'w') as ofile:
        ofile.write('// Header file for Dialog Cycles\n')
        ofile.write('\n')
        ofile.write('import function reset_dialog_cycle_counters();\n')

        for cycle in cycles.cache:
            ofile.write('import function {}();\n'.format(cycle.key))

    with open(CYCLES_SCRIPT_PATH, 'w') as ofile:
        for i in range(cycles.max_cycles):
            ofile.write("int cycle_counter_{};\n".format(i))

        ofile.write('\n')
        ofile.write('function reset_dialog_cycle_counters()\n')
        ofile.write('{\n')
        for i in range(cycles.max_cycles):
            ofile.write("    cycle_counter_{} = 0;\n".format(i))
        ofile.write('}\n\n')

        for cycle in cycles.cache:
            ofile.write('function {}()\n'.format(cycle.key))
            ofile.write('{\n')
            ofile.write('    if (cycle_counter_{} >= {}) {{\n'.format(cycle.index, len(cycle.line_pairs)))
            ofile.write('        cycle_counter_{} = 0;\n'.format(cycle.index))
            ofile.write('    }\n')
            ofile.write('    switch(cycle_counter_{}) {{\n'.format(cycle.index))
            line_index = 0;
            for speaker_key, line in cycle.line_pairs:
                ofile.write('    case {}:\n'.format(line_index))
                ofile.write('        c{}.Say("{}");\n'.format(speaker_key.title(), line))
                ofile.write('        break;\n')
                line_index += 1

            ofile.write('    default:\n')
            ofile.write('        Display("I am error.");\n')
            ofile.write('        break;\n')
            ofile.write('    }\n')
            ofile.write('    cycle_counter_{} += 1;\n'.format(cycle.index))
            ofile.write('}\n\n')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
    else:
        xml_path = AGS_XML_PATH

    write_dialogs(xml_path)

    if len(sys.argv) == 1:
        # copy and back up
        print('backing up {} to {}'.format(AGS_XML_PATH, BACKUP_AGS_XML_PATH))
        shutil.copy(AGS_XML_PATH, BACKUP_AGS_XML_PATH)
        print('copying {} to {}'.format(TMP_PATH, AGS_XML_PATH))
        shutil.copy(TMP_PATH, AGS_XML_PATH)

