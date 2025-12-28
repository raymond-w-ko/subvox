-- [nfnl] fnl/plugins/user.fnl
local uu = require("dotfiles.util")
local function _1_()
  return vim.cmd("colorscheme selenized")
end
local function _2_()
  local MiniPairs = require("mini.pairs")
  return MiniPairs.setup()
end
local function _3_()
  local telescope = require("telescope")
  return telescope.setup({defaults = {file_ignore_patterns = {"^.git/"}}})
end
local function _4_()
  local builtin = require("telescope.builtin")
  return builtin.find_files({hidden = true})
end
local function _5_()
  local builtin = require("telescope.builtin")
  return builtin.live_grep({additional_args = {"--hidden"}})
end
local function _6_()
  local lualine = require("lualine")
  return lualine.setup({theme = "selenized"})
end
return {uu.tx("Olical/nfnl", {priority = 9001, ft = {"fennel"}}), uu.tx("bakpakin/fennel.vim"), uu.tx("raymond-w-ko/selenized.nvim", {config = _1_}), uu.tx("echasnovski/mini.pairs", {config = _2_, version = false}), uu.tx("nvim-telescope/telescope.nvim", {dependencies = {"nvim-lua/plenary.nvim"}, config = _3_, keys = {{"<C-p>", _4_}, {"<leader>/", _5_}}, tag = "v0.2.0"}), uu.tx("https://codeberg.org/andyg/leap.nvim.git", {dependencies = {"tpope/vim-repeat"}, keys = {{"s", "<Plug>(leap-forward)", mode = {"n", "x", "o"}}, {"S", "<Plug>(leap-backward)", mode = {"n", "x", "o"}}, {"gs", "<Plug>(leap-from-window)", mode = "n"}}}), uu.tx("nvim-lualine/lualine.nvim", {dependencies = {"raymond-w-ko/selenized.nvim", "nvim-tree/nvim-web-devicons"}, config = _6_})}
