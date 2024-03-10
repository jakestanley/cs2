#!/usr/bin/env bash
# https://github.com/NockyCZ/CS2-Deathmatch/releases
CS2_ROOT=$HOME/games/game
CS2_DM_MOD="https://github.com/NockyCZ/CS2-Deathmatch/releases/download/v1.0.9/Deathmatch.zip"
wget -q -O Deathmatch.zip $CS2_DM_MOD
unzip Deathmatch.zip -d $CS2_ROOT/

# https://github.com/ssypchenko/cs2-gungame/releases/tag/V1.0.8
# edit weapons here: $CS2_ROOT/csgo/cfg/gungame/gungame_weapons.json
# edit general options here: $CS2_ROOT/csgo/addons/counterstrikesharp/configs/plugins/GG2/GG2.json
CS2_GG_MOD="https://github.com/ssypchenko/cs2-gungame/releases/download/V1.0.8/GG2.plugin.1.0.8.zip"
wget -q -O GG2.zip $CS2_GG_MOD
unzip GG2.zip -d $CS2_ROOT/
