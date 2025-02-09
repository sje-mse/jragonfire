import os
import speech_recognition as sr
r = sr.Recognizer()

def recog(filename):
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
        try:
            s = r.recognize_sphinx(audio)
            print("{}: {}".format(filename, s))
        except Exception as e:
            print("Exception: {}".format(str(e)))

for f in os.listdir("aud"):
    if not f.endswith("wav"):
        continue
    recog(f)
