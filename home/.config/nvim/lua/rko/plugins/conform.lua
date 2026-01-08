return {
  "stevearc/conform.nvim",
  config = function()
    require("conform").setup({
      formatters = {
        standard_clj = {
          command = "standard-clj",
          args = { "fix", "-" },
          stdin = true,
        },
      },
      formatters_by_ft = {
        clojure = { "standard_clj" },
        clojurescript = { "standard_clj" },
        clojurec = { "standard_clj" },
        edn = { "standard_clj" },
      },
      format_on_save = {
        timeout_ms = 3000,
        lsp_format = "never",
      },
    })
  end,
}
