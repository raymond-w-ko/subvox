# subvox

## User executables

All host and standalone Home Manager profiles add `$HOME/.local/bin` to `PATH`
through `home/common.nix`. NixOS hosts also enable `environment.localBinInPath`.
Apply the configuration with `./scripts/rebuild switch <target>`, then start a new
shell to pick up the updated path.

## GVfs

NixOS hosts enable GVfs for mounting, trash, and other file-management features.
Linux GUI Home Manager profiles install GVfs, expose its GIO modules, and register
its systemd user units. Standalone profiles still need host-provided D-Bus, FUSE,
and UDisks2 support for mounting. macOS profiles are unchanged.

NixOS hosts and Linux GUI Home Manager profiles also include `trash-cli` for
command-line access to the freedesktop.org trash, including `trash-put`,
`trash-list`, and `trash-restore`.
