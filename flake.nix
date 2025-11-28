{
  description = "declarative linux/unix os config for rko";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    darwin.url = "github:nix-darwin/nix-darwin";
    darwin.inputs.nixpkgs.follows = "nixpkgs";

    nixos-wsl.url = "github:nix-community/NixOS-WSL";
    nixos-wsl.inputs.nixpkgs.follows = "nixpkgs";

    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

  };

  outputs =
    inputs@{
      nixpkgs,
      nixos-wsl,
      darwin,
      home-manager,
      ...
    }:
    let
      user = "rko";
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

          # services.openssh.enable = true;

          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users."${user}" = homeManagerConfig;
        };
      commonConfig =
        { pkgs, ... }:
        {
          nix.settings.experimental-features = [
            "nix-command"
            "flakes"
          ];
          time.timeZone = "America/New_York";

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
          ];

          programs.fish.enable = true;
          users.users."${user}" = {
            shell = pkgs.fish;
          };
        };
      homeManagerConfig =
        { ... }:
        {
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
          programs.git = {
            enable = true;
            settings = {
              user.name = "Raymond W. Ko";
              user.email = "raymond.w.ko@gmail.com";
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
            wslConfig
            commonConfig
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
        darwin = darwin.lib.darwinSystem {
          system = "aarch64-darwin";

          modules = [
            home-manager.darwinModules.home-manager
            commonConfig
            homeManagerConfig
          ];
        };
      };
    };
}
# vim: ts=2 sts=2 sw=2 et
