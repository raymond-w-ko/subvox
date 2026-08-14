{
  inputs,
  user,
  pkgs,
  ...
}:
{
  imports = [
    inputs.nixos-wsl.nixosModules.default
    ../../modules/nixos/base.nix
    ../../modules/shared/gui.nix
  ];

  fonts = {
    fontDir.enable = true;
    fontconfig.useEmbeddedBitmaps = true;
    enableDefaultPackages = true;
  };

  wsl = {
    enable = true;
    defaultUser = user;
    useWindowsDriver = true;
  };

  system.stateVersion = "25.05";

  hardware.graphics = {
    enable = true;
    enable32Bit = true;
  };

  environment.systemPackages = with pkgs; [
    mesa
    mesa-demos
    glmark2
    gst_all_1.gstreamer
    gst_all_1.gst-plugins-base
    gst_all_1.gst-plugins-good
    gst_all_1.gst-plugins-bad
    gst_all_1.gst-plugins-ugly
    gst_all_1.gst-libav
  ];

  environment.sessionVariables.GST_PLUGIN_PATH = with pkgs.gst_all_1; [
    "${gst-plugins-base}/lib/gstreamer-1.0"
    "${gst-plugins-good}/lib/gstreamer-1.0"
    "${gst-plugins-bad}/lib/gstreamer-1.0"
    "${gst-plugins-ugly}/lib/gstreamer-1.0"
    "${gst-libav}/lib/gstreamer-1.0"
  ];
  environment.sessionVariables.LD_LIBRARY_PATH = [ "/run/opengl-driver/lib/" ];
  environment.sessionVariables.GALLIUM_DRIVER = "d3d12";
  environment.sessionVariables.MESA_D3D12_DEFAULT_ADAPTER_NAME = "Nvidia";
  environment.sessionVariables.GDK_BACKEND = "x11";

  home-manager.users.${user}.imports = [
    ../../home/gui.nix
    ../../home/linux.nix
  ];
}
