# Updating flake inputs

Run the guarded updater from the repository root:

```sh
./scripts/update
```

The default selection is the frequently updated group: `neru`, `claude-code`, and `codex-cli-nix`.
Core inputs (`nixpkgs`, `nix-darwin`, `home-manager`, `nixos-wsl`, and `rust-overlay`) are selected manually.
You can preselect a group from the command line:

```sh
./scripts/update high
./scripts/update core
./scripts/update all
./scripts/update neru home-manager
```

The updater writes changes to a temporary candidate lock first. **Generate candidate** shows direct and transitive revisions without changing `flake.lock`. **Validate + build** evaluates the flake and builds the macOS system against that candidate. **Apply validated lock** replaces `flake.lock` only after validation succeeds. **Commit lock** is optional and never pushes.

`claude-code` and `codex-cli-nix` follow the repository's root `nixpkgs`. Updating either application therefore cannot silently update a private Nixpkgs revision. Update root `nixpkgs` through the core group when ready to test infrastructure changes.

If `flake.lock` already has uncommitted changes, the updater refuses to generate a candidate so existing work cannot be overwritten.
