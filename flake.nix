{
  description = "declarative linux/unix os config for rko";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nix-darwin.url = "github:nix-darwin/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    nixos-wsl.url = "github:nix-community/NixOS-WSL";
    nixos-wsl.inputs.nixpkgs.follows = "nixpkgs";

    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixos-wsl,
      nix-darwin,
      home-manager,
      ...
    }:
    let
      user = "rko";

      myPackages =
        pkgs: with pkgs; [
          nixpkgs-review
          nix-update

          git
          gh
          lazygit
          neovim
          htop
          curl
          wget
          ripgrep
          fzf
          fd
          jq
          bash
          zsh
          fish
          zoxide
          eza
          tmux
          ncdu

          nodejs_24
          bun

          python314
          uv

          javaPackages.compiler.openjdk25
          babashka

          go

          perl

          codex
          claude-code
        ];
      myFontPackages =
        pkgs: with pkgs; [
          noto-fonts
          noto-fonts-cjk-sans
          noto-fonts-color-emoji
          liberation_ttf
          fira-code
          fira-code-symbols
          mplus-outline-fonts.githubRelease
          dina-font
          iosevka
          aporetic
          jetbrains-mono
        ];
      myLinuxPackages =
        pkgs: with pkgs; [
          perf
          adwaita-icon-theme
          ghostty
          # one of these is needed for ghostty playing bell
          gst_all_1.gstreamer
          gst_all_1.gst-plugins-base
          gst_all_1.gst-plugins-good
          gst_all_1.gst-plugins-ugly
          gst_all_1.gst-plugins-bad
          gst_all_1.gst-libav
          gst_all_1.gst-vaapi
        ];
      myMacosPackages =
        pkgs: with pkgs; [
          kanata
          aerospace
          sketchybar
          raycast
        ];

      globalConfig =
        { lib, pkgs, ... }:
        {
          nixpkgs.overlays = [
            (final: prev: {
              raycast = prev.callPackage ./pkgs/raycast/default.nix { };
              claude-code = prev.callPackage ./pkgs/claude-code/default.nix { };
            })
          ];
          nixpkgs.config.allowUnfreePredicate =
            pkg:
            builtins.elem (lib.getName pkg) [
              "claude-code"
              "raycast"
            ];
          nix.settings.experimental-features = [
            "nix-command"
            "flakes"
          ];

          nix.gc = {
            automatic = true;
            options = "--delete-older-than 30d";
          };

          time.timeZone = "America/New_York";

          environment.systemPackages = myPackages pkgs;
          # this pulls in termbench-pro, which does not compile
          # environment.enableAllTerminfo = true;
          security.sudo.keepTerminfo = true;
          fonts = {
            packages = myFontPackages pkgs;
          };

          programs.fish.enable = true;

          users.users."${user}" = {
            shell = pkgs.fish;
          };
          home-manager.users."${user}" = homeManagerConfig;
        };
      linuxConfig =
        { pkgs, ... }:
        {
          nix.settings.trusted-users = [ "${user}" ];
          nix.gc.dates = "weekly";
          environment.localBinInPath = true;

          programs.nix-ld.enable = true;

          # services.openssh.enable = true;

          users.users."${user}".isNormalUser = true;

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = linuxHomeManagerConfig;
        };
      wsl2Config =
        { pkgs, ... }:
        {
          wsl.enable = true;
          wsl.defaultUser = user;
          wsl.useWindowsDriver = true;

          # This value determines the NixOS release from which the default
          # settings for stateful data, like file locations and database versions
          # on your system were taken. It's perfectly fine and recommended to leave
          # this value at the release version of the first install of this system.
          # Before changing this value read the documentation for this option
          # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
          system.stateVersion = "25.05"; # Did you read the comment?

          hardware.graphics.enable = true;
          hardware.graphics.enable32Bit = true;
          environment.systemPackages = with pkgs; [
            mesa
            mesa-demos
            glmark2
          ];
          environment.sessionVariables.LD_LIBRARY_PATH = [ "/run/opengl-driver/lib/" ];
          environment.sessionVariables.GALLIUM_DRIVER = "d3d12";
          environment.sessionVariables.MESA_D3D12_DEFAULT_ADAPTER_NAME = "Nvidia";
          environment.sessionVariables.GDK_BACKEND = "x11";
        };
      macosConfig =
        { pkgs, ... }:
        {
          nix.gc.interval = {
            Weekday = 0;
            Hour = 0;
            Minute = 0;
          };
          system.configurationRevision = self.rev or self.dirtyRev or null;
          system.stateVersion = 6;
          nixpkgs.hostPlatform = "aarch64-darwin";
          nix.enable = true;

          system.primaryUser = "${user}";
          system.defaults.NSGlobalDomain.NSWindowShouldDragOnGesture = true;

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
        };
      linuxOnlyPackages =
        { pkgs, ... }:
        {
          environment.systemPackages = myLinuxPackages pkgs;

          fonts = {
            fontDir.enable = true;
            fontconfig.useEmbeddedBitmaps = true;
            enableDefaultPackages = true;
          };

          # environment.variables = {
          #   GST_PLUGIN_SYSTEM_PATH_1_0 = "/run/current-system/sw/lib/gstreamer-1.0/";
          #   GST_PLUGIN_SYSTEM_PATH = "/run/current-system/sw/lib/gstreamer-1.0/";
          #   GST_PLUGIN_PATH = "/run/current-system/sw/lib/gstreamer-1.0/";
          # };
        };
      macosOnlyPackages =
        { pkgs, ... }:
        {
          environment.systemPackages = myMacosPackages pkgs;
          environment.shells = with pkgs; [
            bash
            fish
            zsh
          ];
        };

      homeManagerConfig =
        { pkgs, config, ... }:
        let
          dotfilesDir = "${config.home.homeDirectory}/subvox/home";
        in
        {
          # Disable manual generation to avoid builtins.toFile warning
          # See: https://github.com/nix-community/home-manager/issues/7935
          manual.manpages.enable = false;

          xdg.enable = true;

          home.file.".config/nvim/".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/nvim";
          home.file.".config/ghostty/".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/ghostty";

          home.file.".codex/config.template.toml".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.codex/config.template.toml";
          home.file.".codex/AGENTS.md".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/ai/AGENTS.md";
          home.file.".pi/".source = config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.pi";

          programs.direnv = {
            enable = true;
            nix-direnv.enable = true;
            enableBashIntegration = true;
            enableZshIntegration = true;
            # enableFishIntegration = true;
          };

          programs.zoxide = {
            enable = true;
            enableBashIntegration = true;
            enableZshIntegration = true;
            enableFishIntegration = true;
            options = [
              "--cmd"
              "j"
            ];
          };

          programs.fzf = {
            enable = true;
            enableBashIntegration = true;
            enableZshIntegration = true;
            enableFishIntegration = true;
          };
          programs.fish = {
            enable = true;
            binds = { };
            interactiveShellInit = ''
              set fish_greeting
              set -gx fish_prompt_pwd_dir_length 3
              set -gx fish_prompt_pwd_full_dirs 3

              fish_add_path $HOME/subvox/bin
              fish_add_path $HOME/bin

              set -l newpath (for p in $PATH
                if not string match -rq '^/mnt/c/' -- $p
                  echo $p
                end
              end)
              set -gx PATH (string join ":" $newpath)

              test -f $HOME/.config/secrets && source $HOME/.config/secrets
            '';
            shellAbbrs = {
              e = "eza -l";
              ee = "eza -la";
              l = "eza -l";
              ll = "eza -la";
              v = "nvim";
              cd = "__zoxide_z";

              g = "git";
              gs = "git status";
              gsw = "git switch";
              gcfxd = "git clean -fxd";
              gd = "git diff";

              ga = "git add";
              gf = "git fetch";
              gl = "git pull";
              gc = "git commit";
              gca = "git commit -a";
              gcam = "git commit -a -m";
              gcav = "git commit -a -v";
              gp = "git push";
              gpfnv = "git push --force-with-lease --no-verify";

              ts = "tmux new -s";
              ta = "tmux attach -d -t";
              tl = "tmux list-sessions";

              oc = "opencode";
              cx = "codex";

              ".." = "__zoxide_z ..";
              "..." = "__zoxide_z ../..";
              "...." = "__zoxide_z ../../..";
              "....." = "__zoxide_z ../../../..";
            };
          };
          programs.tmux = {
            enable = true;
            terminal = "tmux-256color";
            prefix = "f4";
            keyMode = "emacs";
            mouse = true;
            focusEvents = true;
            clock24 = true;
            newSession = false;
            baseIndex = 1;
            historyLimit = 10000;
            extraConfig = ''
              set -g default-shell ${pkgs.fish}/bin/fish
              set -g status-justify centre
              set -g status-position top
              setw -g monitor-activity on
            '';
            plugins = with pkgs; [
              {
                plugin = tmuxPlugins.sensible;
              }
              {
                plugin = tmuxPlugins.catppuccin;
                extraConfig = ''
                  set -g @catppuccin_flavor "latte"
                  set -g @catppuccin_window_status_style "rounded"
                  set -g status-right-length 100
                  set -g status-left-length 100
                  set -g status-left ""
                  set -g status-right "#{E:@catppuccin_status_application}"
                  # set -agF status-right "#{E:@catppuccin_status_cpu}"
                  set -ag status-right "#{E:@catppuccin_status_session}"
                  set -ag status-right "#{E:@catppuccin_status_uptime}"
                  # set -agF status-right "#{E:@catppuccin_status_battery}"
                '';
              }
            ];
          };
          programs.git = {
            enable = true;
            lfs.enable = true;
            settings = {
              user.name = "Raymond W. Ko";
              user.email = "raymond.w.ko@gmail.com";
              pull.rebase = true;
              init.defaultBranch = "master";
              alias = {
                co = "checkout";
                br = "branch";
                cp = "cherry-pick";
                undo = "reset --soft HEAD^";
                lg = "log --graph --full-history --pretty=format:\"%h%x09%ar%x09%d%x20%s\"";
              };
            };
          };
          programs.lazygit = {
            enable = true;
            enableBashIntegration = true;
            enableZshIntegration = true;
            enableFishIntegration = true;
            shellWrapperName = "lg";
            settings = {
              gui.theme = {
                lightTheme = true;
                activeBorderColor = [
                  "#40a02b"
                  "bold"
                ];
                inactiveBorderColor = [ "#6c6f85" ];
                optionsTextColor = [ "#1e66f5" ];
                selectedLineBgColor = [ "#ccd0da" ];
                cherryPickedCommitBgColor = [ "#bcc0cc" ];
                cherryPickedCommitFgColor = [ "#40a02b" ];
                unstagedChangesColor = [ "#d20f39" ];
                defaultFgColor = [ "#4c4f69" ];
                searchingActiveBorderColor = [ "#df8e1d" ];
              };
              gui.authorColors = {
                "*" = "#7287fd";
              };
            };
          };
          programs.neovim = {
            enable = true;
            defaultEditor = true;
            vimAlias = true;
          };
          programs.bun = {
            enable = true;
          };
          programs.uv = {
            enable = true;
          };
        };
      linuxHomeManagerConfig =
        { pkgs, config, ... }:
        let
          dotfilesDir = "${config.home.homeDirectory}/subvox/home";
        in
        {
          home.packages = [
            pkgs.dconf
          ];

          dconf = {
            enable = true;
            settings = {
              "org/gnome/desktop/interface" = {
                enable-animations = false;
              };
            };
          };
        };
    in
    {
      ########################
      # formatter
      ########################
      formatter.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.nixfmt-tree;
      formatter.aarch64-darwin = nixpkgs.legacyPackages.aarch64-darwin.nixfmt-tree;

      ########################
      # nixos
      ########################
      nixosConfigurations = {
        wsl2 = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          modules = [
            nixos-wsl.nixosModules.default
            home-manager.nixosModules.home-manager
            globalConfig
            linuxOnlyPackages
            linuxConfig
            wsl2Config
            {
              home-manager.users."${user}".home.stateVersion = "26.05";
            }
          ];
        };
      };

      ########################
      # darwin
      ########################
      darwinConfigurations = {
        macos = nix-darwin.lib.darwinSystem {
          modules = [
            home-manager.darwinModules.home-manager
            globalConfig
            macosOnlyPackages
            macosConfig
            {
              users.users.${user}.home = "/Users/${user}";
              home-manager.users.${user}.home = {
                stateVersion = "26.05";
              };
            }
          ];
        };
      };
    };
}
# vim: ts=2 sts=2 sw=2 et
