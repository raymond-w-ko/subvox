{ modulesPath, ... }:
{
  imports = [ (modulesPath + "/profiles/qemu-guest.nix") ];

  services.qemuGuest.enable = true;

  boot.kernelParams = [
    "console=tty0"
    "console=ttyS0,115200"
  ];

  systemd.services."serial-getty@ttyS0".enable = true;
}
