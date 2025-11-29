(local uu (require :dotfiles.util))

[(uu.tx :Olical/nfnl {:priority 9001 :ft ["fennel"]})
 (uu.tx :bakpakin/fennel.vim)
 ;; conflicts with nmap S
 ; (uu.tx :shortcuts/no-neck-pain.nvim)

 ; (uu.tx :loganswartz/selenized.nvim
 ;        {:dependencies [:rktjmp/lush.nvim]
 ;         :config (fn []
 ;                   (tset _G.vim.g :selenized_variant "normal")
 ;                   (tset _G.vim.o :background "light")
 ;                   (vim.cmd.colorscheme "selenized"))})
 (uu.tx :calind/selenized.nvim
        {:config (fn []
                   (vim.cmd "colorscheme selenized"))})

 ;; does not work by default for Lisp languages
 ; (uu.tx "windwp/nvim-autopairs" {:event "InsertEnter" :config true})
 (uu.tx "echasnovski/mini.pairs" {:version false
                                  :config (fn []
                                            (local MiniPairs (require "mini.pairs"))
                                            (MiniPairs.setup))})

 (uu.tx :nvim-telescope/telescope.nvim
        {:dependencies [:nvim-lua/plenary.nvim]
         :keys [["<C-p>" "<cmd>Telescope find_files<cr>"]]
         :tag "0.1.8"})
 
 (uu.tx :ggandor/leap.nvim
        {:dependencies [:tpope/vim-repeat]
         :keys [{1 "s" 2 "<Plug>(leap-forward)" :mode ["n" "x" "o"]}
                {1 "S" 2 "<Plug>(leap-backward)" :mode ["n" "x" "o"]}
                {1 "gs" 2 "<Plug>(leap-from-window)" :mode "n"}]})
 
 (uu.tx :nvim-lualine/lualine.nvim
        {:dependencies [:calind/selenized.nvim
                        :nvim-tree/nvim-web-devicons]
         :config (fn []
                   (local lualine (require "lualine"))
                   (lualine.setup {:theme "selenized"}))})
 ]


