{ lib, ... }:
{
  networking.networkmanager.enable = lib.mkForce false;
  networking.useDHCP = false;

  systemd.network.enable = true;
  systemd.network.networks."10-ens18" = {
    matchConfig.Name = "ens18";
    address = [ "10.10.10.10/24" ];
    routes = [
      { Gateway = "10.10.10.1"; }
    ];
    linkConfig.RequiredForOnline = "routable";
  };

  networking.nameservers = [
    "1.1.1.1"
    "9.9.9.9"
  ];
}
