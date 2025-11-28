{
  description = "declarative linux/unix os config for rko";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    darwin.url = "github:nix-darwin/nix-darwin";
    darwin.inputs.nixpkgs.follows = "nixpkgs";

    nixos-wsl.url = "github:nix-community/NixOS-WSL";

    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

  };

  outputs = inputs@{ nixpkgs, nixos-wsl, darwin, home-manager, ... }:
    let
      wslConfig = { pkgs, ... } : {
        wsl.enable = true;
        wsl.defaultUser = "rko";

        # This value determines the NixOS release from which the default
        # settings for stateful data, like file locations and database versions
        # on your system were taken. It's perfectly fine and recommended to leave
        # this value at the release version of the first install of this system.
        # Before changing this value read the documentation for this option
        # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
        system.stateVersion = "25.05"; # Did you read the comment?
        
        hardware.graphics.enable = true;
        hardware.graphics.enable32Bit = true;
        environment.systemPackages = with pkgs; [ mesa mesa-demos ];
        environment.sessionVariables.LD_LIBRARY_PATH = [
          "/run/opengl-driver/lib/"
          "${pkgs.openssl.out}/lib"
        ];
        environment.sessionVariables.GALLIUM_DRIVER = "d3d12";
      };
      commonConfig = { pkgs, ... } : {
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

        # services.openssh.enable = true;

        programs.fish.enable = true;

        users.users.rko = {
          shell = pkgs.fish;
        };
      };
    in
    {
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
            ./hosts/darwin.nix
            home-manager.darwinModules.home-manager
            {
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              home-manager.users.jdoe = ./home.nix;
              home-manager.users.rko = {
                home.username = "rko";
                home.homeDirectory = "/Users/rko";
                home.stateVersion = "25.11";
              };
            }
            commonConfig
          ];
        };
      };
    };
}
# vim: ts=2 sts=2 sw=2 et
