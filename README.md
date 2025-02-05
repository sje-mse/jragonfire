# dragon-fire-demake
A VGA Demake of Quest for Glory V: Dragon Fire

The goal of this project is to demaster the 1999 adventure game Quest for Glory V: Dragon Fire into a VGA style, similar to that of Quest for Glory III and IV.

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

All character data is stored in a subdirectory of the `characters` directory by their key.
This will include:
- `info.json` - metadata on the character.
- `lines.json` - a list of all their dialog lines. Translations can go here.
- `views` - a directory containing all the character's sprites.
- `audio` - a directory containing the audio files corresponding entries in `lines.json`.

### `lines.json`


Each line of dialog will be stored as an array entry of the following schema:

`
{
    "key": "welcome_prince_of_shapier",
    "en_us": "Welcome, Prince of Shapier. How may I serve you?"
}
`
If an audio for this line of dialog exists, it must have the same name as the `key` field, plus the `wav` extension.
For example, the audio file corresponding to this line of dialog should be found in:
```
characters/sarra/audio/welcome_prince_of_shapier.wav
```
Git not was intended to store audio files, so these will be stored elsewhere.
