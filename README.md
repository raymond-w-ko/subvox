# subvox

## GVfs

NixOS hosts enable GVfs for mounting, trash, and other file-management features.
Linux GUI Home Manager profiles install GVfs, expose its GIO modules, and register
its systemd user units. Standalone profiles still need host-provided D-Bus, FUSE,
and UDisks2 support for mounting. macOS profiles are unchanged.
