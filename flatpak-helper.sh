ctr#!/usr/bin/env bash

SCRIPT_PATH="$(dirname "$0")"
ACTION=$1   # install | uninstall | update
APP_ID=$2
APP_NAME=$3

ICON="$SCRIPT_PATH/images/icon.png"

if flatpak "$ACTION" -y "$APP_ID" >/dev/null; then
    MSG="$APP_NAME was ${ACTION}ed successfully"

    if [[ "$ACTION" == "install" || "$ACTION" == "update" ]]; then
        choice=$(notify-send -a "Flathub Search" -i "$ICON" \
            "$MSG" -A launch=Launch)

        if [[ "$choice" == "launch" ]]; then
            flatpak run "$APP_ID" >/dev/null
        fi
    else
        notify-send -a "Flathub Search" -i "$ICON" "$MSG"
    fi
else
    notify-send -a "Flathub Search" -i "$ICON" \
        "Failed to $ACTION $APP_NAME"
fi
