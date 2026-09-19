{ pkgs, user, ... }:
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

  environment.systemPackages = with pkgs; [
    chromium
    google-chrome
    ghostty.terminfo
  ];

  security.sudo.extraConfig = ''
    @includedir /etc/sudoers.d
  '';

  # Static files served over the tailnet by `tailscale serve --bg /var/www/html`.
  systemd.tmpfiles.rules = [ "d /var/www/html 0755 ${user} users -" ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  system.stateVersion = "26.05";
}
