{ pkgs, user, ... }:
{
  virtualisation.docker.enable = true;
  users.users.${user}.extraGroups = [ "docker" ];

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
