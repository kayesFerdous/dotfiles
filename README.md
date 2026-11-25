# dotfiles

My config files for Linux, managed with GNU Stow.

## What's in here

- `nvim` — Neovim, based on AstroNvim
- `zsh` — shell config, aliases and PATH setup
- `tmux` — tmux config
- `ghostty` — Ghostty terminal config

## Install

Clone the repo into your home directory and stow whatever you want:

```sh
git clone https://github.com/kayesFerdous/dotfiles ~/dotfiles
cd ~/dotfiles
stow nvim zsh tmux ghostty
```

Stow makes symlinks from these folders into `~/.config`, so editing a file here
edits the real config.

To remove one:

```sh
stow -D nvim
```
