import os

# the location of the audio files for lines of recorded dialog
SPEECH_PATH = os.path.expanduser('~/OneDrive/qfg5/speech')

# the root location of the AGS project
AGS_PATH = os.path.expanduser('~/OneDrive/qfg5/qfg5vga')

# the target location for exported recorded speech files.
AGS_SPEECH_PATH = os.path.join(AGS_PATH, 'Speech')

# the location of the xml-like master file for the AGS project.
AGS_XML_PATH = os.path.join(AGS_PATH, 'Game.agf')

# backup path for when we do some kind of bulk operation on the AGS project.
BACKUP_AGS_XML_PATH = os.path.join(AGS_PATH, 'Game.agf.bak2')
