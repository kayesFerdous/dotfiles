# dotfiles

Linux (Arch) configs managed with GNU Stow. Each top-level dir is a stow package
(`nvim`, `zsh`, `tmux`, `ghostty`) mirroring paths under `~`, so editing a file
here edits the live config.

- `.stowrc` ignores `CLAUDE.md`, so these notes never get symlinked into `~`.
  Run stow from this directory or that ignore doesn't apply.
- Don't commit machine-local or backup files (`*.bak*`) or generated caches (`__pycache__`).
- Work on a branch; `main` is the default branch.

How the pieces fit: Ghostty opens straight into tmux (`home` session), tmux is
the tab/project manager (one session per project via `sesh`), nvim runs inside it.
