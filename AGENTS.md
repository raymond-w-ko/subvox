# Repository Guidelines

## Structure
- `flake.nix` - single-file NixOS/nix-darwin config with all modules inline
- `packages.nix` - shared package definitions for home-manager
- `home/` - dotfiles symlinked via home-manager
  - `.config/nvim/` - neovim config (lazy.nvim, plugins in `lua/rko/plugins/`)
  - `.config/ghostty/` - terminal emulator config and shaders
  - `.codex/` - codex AI agent template config
  - `.pi/` - pi agent config (hooks, skills, sessions)
  - `ai/AGENTS.md` - agent definitions for AI tools
- `pkgs/` - custom package overlays (claude-code, raycast, kanata, mactop)
- `scripts/` - build/switch scripts for each platform
- `bin/` - user scripts added to PATH
- `kanata/` - keyboard remapping configs (kbd files, clojure generator)
- `docs/` - documentation (git hooks setup guide)
- `nix-darwin-template/` - starter templates for nix-darwin

## Flake Outputs
- `nixosConfigurations.wsl2` - WSL2 NixOS (x86_64-linux)
- `darwinConfigurations.macos` - nix-darwin (aarch64-darwin)
- `homeConfigurations."rko@linux"` - standalone home-manager (x86_64-linux)
- `homeConfigurations."rko@macos"` - standalone home-manager (aarch64-darwin)
- `homeConfigurations."rko@linux-arm"` - standalone home-manager (aarch64-linux)

## Commands
```sh
# validate
nix flake check

# build without applying
nix build .#nixosConfigurations.wsl2.config.system.build.toplevel
nix build .#darwinConfigurations.macos.config.system.build.toplevel

# apply changes
./scripts/linux-switch   # nixos-rebuild switch
./scripts/darwin-switch  # darwin-rebuild switch
./scripts/hm-switch      # home-manager switch (auto-detects platform)

# format
nix fmt

# update inputs
nix flake update
# or: ./scripts/update
```

## Adding Packages
- **Programs with config**: add to `programs.*` in flake.nix (e.g., `programs.git`, `programs.tmux`)
- **Simple packages**: add to `packages.nix` in the appropriate section
- **Custom overlays**: create new directory in `pkgs/` with `package.nix`

## Key Configurations

### Fish Shell
- Aliases: `g`=git, `gs`=git status, `v`=nvim, `j`=zoxide, `c`=claude
- Paths: `~/subvox/bin`, `~/bin` added to PATH
- Secrets: optional `~/.config/secrets.fish` sourced if present

### Tmux
- Prefix: F4
- Theme: catppuccin latte
- Sessions start at 1

### Neovim
- Plugin manager: lazy.nvim
- Theme: selenized
- Key plugins: telescope, nvim-tree, lualine, barbar, conform, leap

## macOS Notes
- GUI apps via `home.packages` → `~/Applications/Home Manager Apps/`
- GUI apps via `environment.systemPackages` → `/Applications/Nix Apps/`
- Additional packages: mactop, aerospace, sketchybar, raycast

## WSL2 Notes
- Graphics: mesa with d3d12 driver
- Removes Windows paths from PATH automatically

## Style
- 2-space indent, trailing semicolons
- Keep modules inline in flake.nix unless complexity warrants extraction
- Run `nix fmt` after editing nix files
- Run `nix flake check` before committing

## Commits
- Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`
- Include `flake.lock` changes with input updates
- No secrets or tokens in repo
