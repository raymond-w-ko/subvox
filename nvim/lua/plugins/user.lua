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
  local lualine = require("lualine")
  return lualine.setup({theme = "selenized"})
end
return {uu.tx("Olical/nfnl", {priority = 9001, ft = {"fennel"}}), uu.tx("bakpakin/fennel.vim"), uu.tx("calind/selenized.nvim", {config = _1_}), uu.tx("echasnovski/mini.pairs", {config = _2_, version = false}), uu.tx("nvim-telescope/telescope.nvim", {dependencies = {"nvim-lua/plenary.nvim"}, keys = {{"<C-p>", "<cmd>Telescope find_files<cr>"}}, tag = "0.1.8"}), uu.tx("ggandor/leap.nvim", {dependencies = {"tpope/vim-repeat"}, keys = {{"s", "<Plug>(leap-forward)", mode = {"n", "x", "o"}}, {"S", "<Plug>(leap-backward)", mode = {"n", "x", "o"}}, {"gs", "<Plug>(leap-from-window)", mode = "n"}}}), uu.tx("nvim-lualine/lualine.nvim", {dependencies = {"calind/selenized.nvim", "nvim-tree/nvim-web-devicons"}, config = _3_})}
