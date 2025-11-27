{
  description = "subvox nixos configs for rko";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixos-wsl.url = "github:nix-community/NixOS-WSL";
    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, nixos-wsl, home-manager, ... }: {
    nixosConfigurations = {
      wsl2 = nixpkgs.lib.nixosSystem {
			  system = "x86_64-linux";
				modules = [
          nixos-wsl.nixosModules.default
					home-manager.nixosModules.home-manager
          ./profiles/common.nix
          ./hosts/wsl2.nix
				];
			};
	  };
	};
}
