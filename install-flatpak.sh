#!/usr/bin/env bash

SCRIPT_PATH="$(dirname "$0")"
APP_ID=$1
APP_NAME=$2

if flatpak install flathub -y "$APP_ID" >/dev/null; then
    choice=$(notify-send -a "Flathub Search" \
      -i "$SCRIPT_PATH/images/icon.png" \
      "$APP_NAME was installed successfully" \
      -A launch=Launch)

    if [[ "$choice" == "launch" ]]; then
        flatpak run "$APP_ID" >/dev/null
    fi
else
    notify-send -a "Flathub Search" \
      -i "$SCRIPT_PATH/images/icon.png" \
      "Failed to install $APP_NAME"
fi
