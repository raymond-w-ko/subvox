{ config, pkgs, ... }:

{
  imports = [
    ../profiles/common.nix
  ];

  # Target Apple Silicon by default; override in the flake output if needed.
  nixpkgs.hostPlatform = "aarch64-darwin";

  # Pin the nix-darwin state version; update only after reading release notes.
  system.stateVersion = "24.05";
}
