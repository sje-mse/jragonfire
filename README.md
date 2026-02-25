# jragonfire

A non-profit fan-based project to organize the data of QFG5: Dragonfire as an exercise in the study of game design.

The current phase of the project is to arrange the game data (extracted, demastered, or otherwise adapted) into such a form as:
- To be able to be automatically imported into a game engine (probably AGS) using python scripts.
- To be able to be validated using scripts.

This repo is expected to be written in two languages:
- `json`, for the structured data.
- `python`, for the scripting.

Heavy assets will be hosted elsewhere.

This README will be updated with descriptions of the directory structures and `json` schema.

## Extraction
Most of the data from the OG game is extracted programmatically from the original game files.
This is done using scripts in the `scripts` folder, usually that start with `rip`.


## Special thanks to:
- [qhmu](https://github.com/zhmu/qfg5-reenigne/tree/main)
- [Kostya](https://codecs.multimedia.cx/2023/11/qfg-spk-format/)

These two projects have been essential to the ripping efforts. Thanks so much <3
