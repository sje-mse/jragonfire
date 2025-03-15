# jragonfire

A non-profit fan-based project to organize the data of QFG5: Dragonfire as an exercise in the study of game design.

The current phase of the project is to arrange the game data (extracted, demastered, or otherwise adapted) into such a form as:
- To be able to be automatically imported into a game engine (probably AGS) using python scripts.
- To be able to be validated using scripts.
- To be tested using a bare-bones engine (probably in python).

This repo is expected to be written in two languages:
- `json`, for the structured data.
- `python`, for the scripting.

Heavy assets will be hosted elsewhere.

This README will be updated with descriptions of the directory structures and `json` schema.

## Characters

Each character has a key - in most cases this will be their name in lowercase. Each key
corresponds to a file of the form `characters/key.json`, which will important data on that character.
Each character key also corresponds to a directory in `lines`, which will have all their dialog lines
in files organized by language. Here is of the file structure for a character.

```
characters/wolfie.json
lines/wolfie/en_us.json
audio/wolfie/
```

### Lines

Here is an example of `en_us.json`:
```
{
    "welcome_prince_of_shapier": "Welcome, Prince of Shapier. How may I serve you?"
}
```

If an audio for this line of dialog exists, it must have the same name as the `key` field, plus the `wav` extension.
For example, the audio file corresponding to this line of dialog should be found in:

```
audio/sarra/welcome_prince_of_shapier.wav
```

Git not was intended to store audio files, so these will be stored [elsewhere](https://1drv.ms/f/c/83c2e71ede7cabb9/EqVGGr-sod5PmNuVqu-7gQABAV3-F9Sae1LHLcKIVPM1kw?e=PqWkeQ).
