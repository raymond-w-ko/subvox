-- make sure to setup `mapleader` and `maplocalleader` before loading lazy.nvim so that mappings are correct.
-- this is also a good place to setup other settings (vim.opt)
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

vim.o.termguicolors = true

vim.o.encoding = "utf-8"
vim.o.hidden = true

vim.o.wrap = true
vim.o.textwidth = 99
vim.o.tabstop = 2
vim.o.softtabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true

vim.o.modelines = 0
vim.o.number = true
vim.o.ruler = true
vim.o.laststatus = 2
vim.o.showmode = true
vim.o.showcmd = true
vim.o.listchars = "tab:▸\\ ,eol:¬"

vim.o.hlsearch = true
vim.o.incsearch = true
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.showmatch = true

vim.keymap.set({"n", "v"}, "/", "/\\v")

require("config.lazy")
