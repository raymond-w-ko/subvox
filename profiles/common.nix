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
    ripgrep
    fzf
    fish
  ];

  services.openssh.enable = true;
  programs.fish.enable = true;

  users.users.rko = {
    shell = pkgs.fish;
  };
}
