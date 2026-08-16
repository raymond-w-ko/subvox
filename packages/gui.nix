{ pkgs }:
let
  linux = with pkgs; [
    adwaita-icon-theme
    ghostty
    # GStreamer plugins for Ghostty bell support.
    gst_all_1.gstreamer
    gst_all_1.gst-plugins-base
    gst_all_1.gst-plugins-good
    gst_all_1.gst-plugins-ugly
    gst_all_1.gst-plugins-bad
    gst_all_1.gst-libav
  ];

  darwin = with pkgs; [
    kanata
    aerospace
    sketchybar
    raycast
  ];

  platform =
    (if pkgs.stdenv.hostPlatform.isDarwin then darwin else [ ])
    ++ (if pkgs.stdenv.hostPlatform.isLinux then linux else [ ]);
in
{
  inherit linux darwin;

  forHome = platform;
}
