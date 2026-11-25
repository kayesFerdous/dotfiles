# ghostty

- `.config/ghostty/config` → `~/.config/ghostty/config`.
- Ghostty runs `tmux new-session -A -s home` on launch and hides its own tab bar:
  tabs/projects are tmux's job (see `../tmux/CLAUDE.md`). Don't add Ghostty tab or
  split keybinds that fight tmux's `C-n` prefix.
- Translucent background (`background-opacity`, blur); tmux and nvim configs use
  transparent backgrounds to match.
