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

      # Overlay for custom packages
      customOverlay = final: prev: {
        mactop = prev.callPackage ./pkgs/mactop/package.nix { };
        raycast = prev.callPackage ./pkgs/raycast/package.nix { };
        claude-code = prev.callPackage ./pkgs/claude-code/package.nix { };
        codex = prev.callPackage ./pkgs/codex/package.nix { };
      };

      # Unfree packages we allow
      allowedUnfree = [
        "claude-code"
        "raycast"
      ];

      # Create pkgs for a given system with our overlays
      mkPkgs =
        system:
        import nixpkgs {
          inherit system;
          overlays = [ customOverlay ];
          config.allowUnfreePredicate = pkg: builtins.elem (nixpkgs.lib.getName pkg) allowedUnfree;
        };

      # Shared nix settings
      nixSettings = {
        nix.settings.experimental-features = [
          "nix-command"
          "flakes"
        ];
        nix.gc = {
          automatic = true;
          options = "--delete-older-than 30d";
        };
      };

      # Shared nixpkgs config (for NixOS/darwin modules)
      nixpkgsConfig =
        { lib, ... }:
        {
          nixpkgs.overlays = [ customOverlay ];
          nixpkgs.config.allowUnfreePredicate = pkg: builtins.elem (lib.getName pkg) allowedUnfree;
        };

      # Font configuration (system-level)
      fontConfig =
        { pkgs, ... }:
        let
          myPkgs = import ./packages.nix { inherit pkgs; };
        in
        {
          fonts.packages = myPkgs.fonts;
        };

      # Core home-manager config (shared across all platforms)
      homeManagerConfig =
        { pkgs, config, ... }:
        let
          dotfilesDir = "${config.home.homeDirectory}/subvox/home";
          myPkgs = import ./packages.nix { inherit pkgs; };
        in
        {
          # Install packages via home-manager
          home.packages = myPkgs.forHome;

          # Disable manual generation to avoid builtins.toFile warning
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

          programs.bash = {
            enable = true;
          };
          programs.fish = {
            enable = true;
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

              test -f $HOME/.config/secrets.fish && source $HOME/.config/secrets.fish
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
              gm = "git merge";
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
              yc = "claude --dangerously-skip-permissions";
              yx = "codex --yolo";

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
                  set -ag status-right "#{E:@catppuccin_status_session}"
                  set -ag status-right "#{E:@catppuccin_status_uptime}"
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

          programs.gpg = {
            enable = true;
          };
        };

      # Linux-specific home-manager additions
      linuxHomeManagerConfig =
        { pkgs, config, ... }:
        {
          home.packages = [ pkgs.dconf ];

          dconf = {
            enable = true;
            settings = {
              "org/gnome/desktop/interface" = {
                enable-animations = false;
              };
            };
          };
        };

      # NixOS/darwin shared system config
      systemConfig =
        { lib, pkgs, ... }:
        {
          time.timeZone = "America/New_York";
          security.sudo.keepTerminfo = true;
          programs.fish.enable = true;
          users.users."${user}".shell = pkgs.fish;
        };

      # Linux-specific system config
      linuxSystemConfig =
        { pkgs, ... }:
        {
          nix.settings.trusted-users = [ "${user}" ];
          nix.gc.dates = "weekly";
          environment.localBinInPath = true;
          programs.nix-ld.enable = true;
          users.users."${user}".isNormalUser = true;

          fonts = {
            fontDir.enable = true;
            fontconfig.useEmbeddedBitmaps = true;
            enableDefaultPackages = true;
          };

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = {
            imports = [
              homeManagerConfig
              linuxHomeManagerConfig
            ];
          };
        };

      # WSL2-specific config
      wsl2Config =
        { pkgs, ... }:
        {
          wsl.enable = true;
          wsl.defaultUser = user;
          wsl.useWindowsDriver = true;
          system.stateVersion = "25.05";

          hardware.graphics.enable = true;
          hardware.graphics.enable32Bit = true;
          environment.systemPackages = with pkgs; [
            mesa
            mesa-demos
            glmark2
            gst_all_1.gstreamer
            gst_all_1.gst-plugins-base
            gst_all_1.gst-plugins-good
            gst_all_1.gst-plugins-bad
            gst_all_1.gst-plugins-ugly
            gst_all_1.gst-libav
            gst_all_1.gst-vaapi
          ];
          environment.sessionVariables.GST_PLUGIN_PATH = with pkgs.gst_all_1; [
            "${gst-plugins-base}/lib/gstreamer-1.0"
            "${gst-plugins-good}/lib/gstreamer-1.0"
            "${gst-plugins-bad}/lib/gstreamer-1.0"
            "${gst-plugins-ugly}/lib/gstreamer-1.0"
            "${gst-libav}/lib/gstreamer-1.0"
            "${gst-vaapi}/lib/gstreamer-1.0"
          ];
          environment.sessionVariables.LD_LIBRARY_PATH = [ "/run/opengl-driver/lib/" ];
          environment.sessionVariables.GALLIUM_DRIVER = "d3d12";
          environment.sessionVariables.MESA_D3D12_DEFAULT_ADAPTER_NAME = "Nvidia";
          environment.sessionVariables.GDK_BACKEND = "x11";
        };

      # macOS-specific system config
      macosSystemConfig =
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

          environment.shells = with pkgs; [
            bash
            fish
            zsh
          ];

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = homeManagerConfig;
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
            nixpkgsConfig
            nixSettings
            systemConfig
            fontConfig
            linuxSystemConfig
            wsl2Config
            { home-manager.users."${user}".home.stateVersion = "26.05"; }
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
            nixpkgsConfig
            nixSettings
            systemConfig
            fontConfig
            macosSystemConfig
            {
              users.users.${user}.home = "/Users/${user}";
              home-manager.users.${user}.home.stateVersion = "26.05";
            }
          ];
        };
      };

      ########################
      # standalone home-manager
      ########################
      homeConfigurations = {
        # Generic Linux (non-NixOS)
        "${user}@linux" = home-manager.lib.homeManagerConfiguration {
          pkgs = mkPkgs "x86_64-linux";
          modules = [
            homeManagerConfig
            linuxHomeManagerConfig
            {
              home.username = user;
              home.homeDirectory = "/home/${user}";
              home.stateVersion = "26.05";
            }
          ];
        };

        # Generic macOS (without nix-darwin)
        "${user}@macos" = home-manager.lib.homeManagerConfiguration {
          pkgs = mkPkgs "aarch64-darwin";
          modules = [
            homeManagerConfig
            {
              home.username = user;
              home.homeDirectory = "/Users/${user}";
              home.stateVersion = "26.05";
            }
          ];
        };

        # ARM Linux (e.g., Raspberry Pi, ARM server)
        "${user}@linux-arm" = home-manager.lib.homeManagerConfiguration {
          pkgs = mkPkgs "aarch64-linux";
          modules = [
            homeManagerConfig
            linuxHomeManagerConfig
            {
              home.username = user;
              home.homeDirectory = "/home/${user}";
              home.stateVersion = "26.05";
            }
          ];
        };
      };
    };
}
# vim: ts=2 sts=2 sw=2 et
