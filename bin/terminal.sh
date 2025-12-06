#!/usr/bin/env -S bash -l
setsid -f nix-shell -p gst_all_1.gstreamer gst_all_1.gst-plugins-base gst_all_1.gst-plugins-good gst_all_1.gst-plugins-bad gst_all_1.gst-plugins-ugly gst_all_1.gst-libav gst_all_1.gst-vaapi --run "ghostty" </dev/null >/dev/null 2>&1 || exit 1
exit 0
