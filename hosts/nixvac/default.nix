{ pkgs, ... }:
{
  imports = [
    ../../modules/nixos/base.nix
    ../../modules/nixos/server.nix
    ../../modules/nixos/virtualisation/proxmox-guest.nix
    ./hardware-configuration.nix
    ./networking.nix
  ];

  networking.hostName = "nixvac";
  services.tailscale.extraSetFlags = [ "--hostname=nixvac" ];

  environment.systemPackages = [ pkgs.ghostty.terminfo ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  system.stateVersion = "26.05";
}
