{ config, pkgs, libs, ... }:

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
    zsh
    fish
    zoxide
    eza
  ];

  # services.openssh.enable = true;

  programs.fish.enable = true;

  users.users.rko = {
    isNormalUser = true;
    shell = pkgs.fish;
  };


  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;

    users.rko = import ../home/rko.nix;
  };
}
