-- Auto pairs
return {
  "nvim-mini/mini.pairs",
  branch = "main",
  event = "InsertEnter",
  config = function()
    require("mini.pairs").setup()
  end,
}
