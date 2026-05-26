# AGENTS.md — subvox

> Guidelines for AI coding agents working in this codebase.

---

## RULE 0 - THE FUNDAMENTAL OVERRIDE PREROGATIVE

If I tell you to do something, even if it goes against what follows below, YOU MUST LISTEN TO ME. I AM IN CHARGE, NOT YOU.

---

## RULE NUMBER 1: NO FILE DELETION

**YOU ARE NEVER ALLOWED TO DELETE A FILE WITHOUT EXPRESS PERMISSION.** Even a new file that you yourself created, such as a test code file. You have a horrible track record of deleting critically important files or otherwise throwing away tons of expensive work. As a result, you have permanently lost any and all rights to determine that a file or folder should be deleted.

**YOU MUST ALWAYS ASK AND RECEIVE CLEAR, WRITTEN PERMISSION BEFORE EVER DELETING A FILE OR FOLDER OF ANY KIND.**

---

## Irreversible Git & Filesystem Actions — DO NOT EVER BREAK GLASS

1. **Absolutely forbidden commands:** `git reset --hard`, `git clean -fd`, `rm -rf`, or any command that can delete or overwrite code/data must never be run unless the user explicitly provides the exact command and states, in the same message, that they understand and want the irreversible consequences.
2. **No guessing:** If there is any uncertainty about what a command might delete or overwrite, stop immediately and ask the user for specific approval. "I think it's safe" is never acceptable.
3. **Safer alternatives first:** When cleanup or rollbacks are needed, request permission to use non-destructive options (`git status`, `git diff`, `git stash`, copying to backups) before ever considering a destructive command.
4. **Mandatory explicit plan:** Even after explicit user authorization, restate the command verbatim, list exactly what will be affected, and wait for a confirmation that your understanding is correct. Only then may you execute it—if anything remains ambiguous, refuse and escalate.
5. **Document the confirmation:** When running any approved destructive command, record (in the session notes / final response) the exact user text that authorized it, the command actually run, and the execution time. If that record is absent, the operation did not happen.

---

# subvox Repository Guidelines

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
