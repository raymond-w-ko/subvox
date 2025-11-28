{
  description = "subvox nix configs for rko";

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
      lib = nixpkgs.lib;
    in {
      ########################
      # nixos
      ########################
      nixosConfigurations = {
        wsl2 = lib.nixosSystem {
          system = "x86_64-linux";
          modules = [
            nixos-wsl.nixosModules.default
            ./hosts/wsl2.nix
            home-manager.nixosModules.home-manager
            ./profiles/common.nix
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
            ./profiles/common.nix
          ];
        };
      };
    };
}
