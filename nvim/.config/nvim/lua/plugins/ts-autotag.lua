-- AstroNvim v4 pins this to a Feb 2025 commit that crashes on Neovim 0.12
-- (get_parser() now returns nil instead of erroring). Unpin to get the fix.
---@type LazySpec
return { "windwp/nvim-ts-autotag", commit = false, version = false }
