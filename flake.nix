{
  description = "subvox nixos configs for rko";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixos-wsl.url = "github:nix-community/NixOS-WSL";
  };

  outputs = { self, nixpkgs, nixos-wsl, ... }@inputs:
    let
      system = "x86_64-linux";
      lib = nixpkgs.lib;

      mkHost = { modules }:
        lib.nixosSystem {
          inherit system;
          modules = modules;
        };
    in {
      nixosConfigurations = {
        wsl2 = mkHost {
          modules = [
            ./profiles/common.nix
            ./hosts/wsl2.nix
            # wsl module if needed:
            nixos-wsl.nixosModules.default
          ];
        };

        vm = mkHost {
          modules = [
            ./profiles/common.nix
            ./hosts/vm.nix
          ];
        };
      };
    };
}
