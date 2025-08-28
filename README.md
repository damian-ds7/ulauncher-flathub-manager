# Ulauncher Flathub Manager

## Features

- Search Flathub apps directly from Ulauncher
- Install, update, and remove Flatpak applications
- Receive desktop notifications for each operation

## Requirements

This extension requires [libnotify](https://gitlab.gnome.org/GNOME/libnotify), as it uses the `notify-send` command to display desktop notifications and [fzf](https://junegunn.github.io/fzf/) to filter installed flatpaks

## Demo

<p align="center">
  <img src="images/search-results.png" alt="Search Results" />
  <br/>
  <sub><em>Search results from Flathub</em></sub>
</p>

<p align="center">
  <img src="images/installed.png" alt="Installed Application" />
  <br/>
  <sub><em>Application is already installed</em></sub>
</p>

<p align="center">
  <img src="images/not-installed.png" alt="Not Installed Application" />
  <br/>
  <sub><em>Application is not yet installed</em></sub>
</p>

## Notifications

Notifications indicate whether an operation completed successfully or failed.

<p align="center">
  <img src="images/install-notif.png" alt="Install Notification" />
  <br/>
  <sub><em>Install notification</em></sub>
</p>

<p align="center">
  <img src="images/update-notif.png" alt="Update Notification" />
  <br/>
  <sub><em>Update notification</em></sub>
</p>

<p align="center">
  <img src="images/remove-notif.png" alt="Remove Notification" />
  <br/>
  <sub><em>Remove notification</em></sub>
</p>
