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

    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    neru = {
      url = "github:y3owk1n/neru";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    claude-code = {
      url = "github:sadjow/claude-code-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    codex-cli-nix = {
      url = "github:sadjow/codex-cli-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      nixpkgs,
      nix-darwin,
      home-manager,
      ...
    }:
    let
      user = "rko";
      packageConfig = import ./lib/packages.nix { inherit inputs; };

      specialArgs = {
        inherit inputs user packageConfig;
      };

      mkHome =
        {
          system,
          homeDirectory,
          extraModules ? [ ],
        }:
        home-manager.lib.homeManagerConfiguration {
          pkgs = packageConfig.mkPkgs system;
          extraSpecialArgs = specialArgs;
          modules = [
            ./home/common.nix
          ]
          ++ extraModules
          ++ [
            {
              home.username = user;
              home.homeDirectory = homeDirectory;
              home.stateVersion = "26.05";
            }
          ];
        };
    in
    {
      formatter.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.nixfmt-tree;
      formatter.aarch64-darwin = nixpkgs.legacyPackages.aarch64-darwin.nixfmt-tree;

      nixosConfigurations.wsl2 = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        inherit specialArgs;
        modules = [ ./hosts/wsl2 ];
      };

      darwinConfigurations.macos = nix-darwin.lib.darwinSystem {
        inherit specialArgs;
        modules = [ ./hosts/macos ];
      };

      homeConfigurations = {
        "${user}@linux" = mkHome {
          system = "x86_64-linux";
          homeDirectory = "/home/${user}";
          extraModules = [ ./home/linux.nix ];
        };

        "${user}@macos" = mkHome {
          system = "aarch64-darwin";
          homeDirectory = "/Users/${user}";
        };

        "${user}@linux-arm" = mkHome {
          system = "aarch64-linux";
          homeDirectory = "/home/${user}";
          extraModules = [ ./home/linux.nix ];
        };
      };
    };
}
# vim: ts=2 sts=2 sw=2 et
