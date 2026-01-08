-- Motion plugin
return {
  "https://codeberg.org/andyg/leap.nvim.git",
  dependencies = { "tpope/vim-repeat" },
  keys = {
    { "s", "<Plug>(leap)", mode = { "n", "x", "o" }, desc = "Leap forward" },
    { "S", "<Plug>(leap-from-window)", mode = "n", desc = "Leap from window" },
  },
  init = function()
    -- Set up autocmd before plugin loads (for colorscheme changes)
    vim.api.nvim_create_autocmd("ColorScheme", {
      group = vim.api.nvim_create_augroup("LeapColorTweaks", {}),
      callback = function()
        -- Only run if leap is loaded
        local ok, leap = pcall(require, "leap")
        if not ok then return end
        if vim.g.colors_name == "selenized" then
          vim.cmd("hi! LeapLabel guifg=#000000 guibg=#ffff00")
        end
        vim.cmd("hi! link LeapMatch None")
        leap.init_hl()
      end,
    })
  end,
  config = function()
    -- Apply highlights immediately when plugin loads
    if vim.g.colors_name == "selenized" then
      vim.cmd("hi! LeapLabel guifg=#000000 guibg=#ffff00")
    end
    vim.cmd("hi! link LeapMatch None")
    require("leap").init_hl()
  end,
}
