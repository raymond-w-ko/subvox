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

      globalConfig =
        { lib, pkgs, ... }:
        {
          nixpkgs.overlays = [
            (final: prev: {
              raycast = prev.callPackage ./pkgs/raycast/default.nix { };
            })
          ];
          nixpkgs.config.allowUnfreePredicate =
            pkg:
            builtins.elem (lib.getName pkg) [
              "claude-code"
              "raycast"
            ];
        };
      linuxConfig =
        { pkgs, ... }:
        {
          programs.nix-ld.enable = true;

          # services.openssh.enable = true;

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = homeManagerConfig;
        };
      wslConfig =
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
          ];
          environment.sessionVariables.LD_LIBRARY_PATH = [ "/run/opengl-driver/lib/" ];
          environment.sessionVariables.GALLIUM_DRIVER = "d3d12";
          environment.sessionVariables.MESA_D3D12_DEFAULT_ADAPTER_NAME = "Nvidia";
        };
      macosConfig =
        { pkgs, ... }:
        {
          system.configurationRevision = self.rev or self.dirtyRev or null;
          system.stateVersion = 6;
          nixpkgs.hostPlatform = "aarch64-darwin";
          nix.enable = false; # needed for Determinate Systems Nix

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = homeManagerConfig;
        };
      commonConfig =
        { lib, pkgs, ... }:
        {
          nix.settings.experimental-features = [
            "nix-command"
            "flakes"
          ];
          time.timeZone = "America/New_York";

          nixpkgs.config.allowUnfreePredicate =
            pkg:
            builtins.elem (lib.getName pkg) [
              "claude-code"
            ];
          environment.localBinInPath = true;
          environment.systemPackages = with pkgs; [
            git
            neovim
            htop
            curl
            wget
            ripgrep
            fzf
            zsh
            fish
            zoxide
            eza
            tmux

            nodejs_24
            bun
            uv

            codex
            claude-code
          ];
          # this pulls in termbench-pro, which does not compile
          # environment.enableAllTerminfo = true;
          security.sudo.keepTerminfo = true;
          fonts = {
            packages = with pkgs; [
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
          };

          programs.fish.enable = true;
          users.users."${user}" = {
            shell = pkgs.fish;
          };
        };
      linuxOnlyPackages =
        { pkgs, ... }:
        {
          environment.systemPackages = with pkgs; [
            ghostty
          ];
          fonts = {
            fontDir.enable = true;
            fontconfig.useEmbeddedBitmaps = true;
            enableDefaultPackages = true;
          };
        };
      macosOnlyPackages =
        { pkgs, ... }:
        {
          environment.systemPackages = with pkgs; [
            aerospace
            sketchybar
            raycast
          ];
        };

      homeManagerConfig =
        { config, ... }:
        let
          dotfilesDir = "${config.home.homeDirectory}/subvox/home";
        in
        {
          xdg.enable = true;

          home.file.".config/nvim/".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/nvim";
          home.file.".config/ghostty/".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/ghostty";

          home.file.".codex/config.template.toml".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.codex/config.template.toml";
          home.file.".codex/AGENTS.md".source =
            config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/ai/AGENTS.md";

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

          programs.fish = {
            enable = true;
            binds = { };
            interactiveShellInit = ''
              set fish_greeting
              set -gx fish_prompt_pwd_dir_length 3
              set -gx fish_prompt_pwd_full_dirs 3

              fish_add_path $HOME/subvox/bin

              set -l newpath (for p in $PATH
                if not string match -rq '^/mnt/c/' -- $p
                  echo $p
                end
              end)
              set -gx PATH (string join ":" $newpath)
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
            prefix = "f5";
            keyMode = "vi";
            mouse = true;
            focusEvents = true;
            clock24 = true;
            newSession = true;
            baseIndex = 1;
            historyLimit = 10000;
          };
          programs.git = {
            enable = true;
            lfs.enable = true;
            settings = {
              user.name = "Raymond W. Ko";
              user.email = "raymond.w.ko@gmail.com";
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
            linuxConfig
            wslConfig
            commonConfig
            linuxOnlyPackages
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
            macosConfig
            commonConfig
            macosOnlyPackages
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
