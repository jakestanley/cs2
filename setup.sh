#!/usr/bin/env bash
METAMOD_RELEASE_URL="https://mms.alliedmods.net/mmsdrop/2.0/mmsource-2.0.0-git1284-linux.tar.gz "
CSSWR_RELEASE_URL="https://github.com/roflmuffin/CounterStrikeSharp/releases/download/v193/counterstrikesharp-with-runtime-build-193-linux-36a97bf.zip"


echo -e "Downloading and installing metamod. Latest releases here: https://www.sourcemm.net/downloads.php?branch=dev"
wget -q -O mm.tar.gz $METAMOD_RELEASE_URL
echo -e "Extracting metamod to csgo\n"
tar -zxvf mm.tar.gz -C ~/games/game/csgo/ > /dev/null 2>&1

echo -e "Downloading and installing CounterStrikeSharp with Runtime. Latest releases here: https://github.com/roflmuffin/CounterStrikeSharp/releases"
wget -q -O csswr.zip $CSSWR_RELEASE_URL
unzip csswr.zip -d ~/games/game/csgo/


echo "Ensure that ~/games/game/csgo/gameinfo.gi has the line"
echo -e "\tGame    csgo/addons/metamod"
echo "directly underneath"
echo -e "\tGame_LowViolence    csgo_lv"
echo "If this is set up correctly, the server command 'meta list' should work"
