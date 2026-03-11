-- Motion plugin
local function set_hl()
  vim.api.nvim_set_hl(0, "LeapLabel", { fg = "#000000", bg = "#ffff00", ctermfg = 14 })
  vim.api.nvim_set_hl(0, "LeapMatch", {})
  vim.api.nvim_set_hl(0, "LeapBackdropDim", { fg = "#6c6c6c", ctermfg = 242, nocombine = true })
end

local function apply_colors()
  local ok, leap = pcall(require, "leap")
  if not ok then return end

  set_hl()
  leap.init_hl()
  require("leap.user").set_backdrop_highlight("LeapBackdropDim")
end

return {
  "https://codeberg.org/andyg/leap.nvim.git",
  dependencies = { "tpope/vim-repeat" },
  keys = {
    { "s", "<Plug>(leap)", mode = { "n", "x", "o" }, desc = "Leap forward" },
    { "S", "<Plug>(leap-from-window)", mode = "n", desc = "Leap from window" },
  },
  init = function()
    vim.api.nvim_create_autocmd("ColorScheme", {
      group = vim.api.nvim_create_augroup("LeapColorTweaks", {}),
      callback = function()
        apply_colors()
      end,
    })
  end,
  config = function()
    apply_colors()
  end,
}
