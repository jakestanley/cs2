#!/usr/bin/env bash
# https://github.com/NockyCZ/CS2-Deathmatch/releases
CS2_ROOT=$HOME/games/game
CS2_DM_MOD="https://github.com/NockyCZ/CS2-Deathmatch/releases/download/v1.0.9/Deathmatch.zip"
wget -q -O Deathmatch.zip $CS2_DM_MOD
unzip Deathmatch.zip -d $CS2_ROOT/

