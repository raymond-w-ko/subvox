{ config, pkgs, ... }:

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
  ];

  # shared services / defaults go here
  # programs.zsh.enable = true;
  # services.openssh.enable = true;
}
