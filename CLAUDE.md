# Repository Guidelines

## Structure
- `flake.nix` - single-file NixOS/nix-darwin config with all modules inline
- `home/` - dotfiles symlinked via home-manager (.config/nvim, .config/ghostty, etc.)
- `pkgs/` - custom package overlays (claude-code, raycast, kanata)
- `scripts/` - helper scripts for building/switching systems
- `bin/` - user scripts added to PATH
- `kanata/` - keyboard remapping configs

## Flake Outputs
- `nixosConfigurations.wsl2` - WSL2 NixOS (x86_64-linux)
- `darwinConfigurations.macos` - nix-darwin (aarch64-darwin)

## Commands
```sh
# validate
nix flake check

# build without applying
nix build .#nixosConfigurations.wsl2.config.system.build.toplevel
nix build .#darwinConfigurations.macos.config.system.build.toplevel

# apply changes
./scripts/linux-switch   # or: sudo nixos-rebuild switch --flake .#wsl2
./scripts/darwin-switch  # or: darwin-rebuild switch --flake .#macos

# format
nix fmt

# update inputs
nix flake update
```

## Style
- 2-space indent, trailing semicolons
- Keep modules inline in flake.nix unless complexity warrants extraction
- Run `nix fmt` after editing nix files
- Run `nix flake check` before committing

## Commits
- Conventional commits: `feat:`, `fix:`, `chore:`
- Include `flake.lock` changes with input updates
- No secrets or tokens in repo
