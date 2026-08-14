{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    vim
    wget
    git
    git-lfs
    gh
  ];

  services.openssh.enable = true;
  services.tailscale.enable = true;
}
