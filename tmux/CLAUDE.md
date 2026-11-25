# tmux

- `.tmux.conf` → `~/.tmux.conf`; `.config/tmux/` → `~/.config/tmux/`.
- Prefix is `C-n`. Plugins via tpm (`~/.tmux/plugins`), catppuccin status bar at top.
- Reload after edits: `C-n r` (or `tmux source-file ~/.tmux.conf`).

## Projects
One session per project. `C-n f` = fzf/sesh project picker, `C-n L` = last project.

## Sidebar (`.config/tmux/sidebar.py`, stdlib Python + curses)
- `C-n e` toggles it in every window, `C-n o` jumps in/out (mirrors neo-tree `<leader>e` / `<leader>o`).
- Each window gets its own sidebar pane, flagged with pane option `@sidebar_pane=1`;
  global on/off state is `@sidebar`. Hooks in `.tmux.conf` add one to new windows/sessions.
- Panes wake on SIGWINCH as "redraw now"; hooks send it with `pkill -WINCH -f sidebar.py.run || true`
  (keep the `|| true`, or tmux shows "returned 1" when no sidebar runs). Hidden sidebars
  block until woken; the visible one also polls every 1s.
- Pins: `~/.local/share/tmux/sidebar-pins`, one path per line, not in this repo.
- Rows are `(text, attr, action)` built in `build()`; add features there plus a key in `ui()`.

Test changes on a throwaway server, never the user's live one:
`tmux -L sbtest -f ~/.tmux.conf new -d`, with `XDG_DATA_HOME` pointed at a scratch dir
so pins aren't touched. Attach a client from a second server (`tmux -L sbouter new -d
"tmux -L sbtest attach"`) to test clicks (send SGR mouse bytes with `send-keys -H`) and switch-client.
