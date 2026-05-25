# Guidelines

## Environment

- M4 chip Macbook air 15, 32GB UMA memory, 1TB disk, 64GB swap, macOS
- Prefer mlx,  fall back to CPU only when needed

## Dev Rules

- Services: docker/podman; avoid native installs
- Install: brew
- **No pip.** Python: always use `uv` venv; prefer `uvx`
- Node.js via nvm; packages via npm/npx
- Push every project to a public GitHub repo (repo name = folder name)
- Always include a standard README.md
- Reply in Traditional Chinese (Taiwan); never use Simplified Chinese or mainland terms
- Never paste secrets/keys/tokens; read from env vars or `.env`
- **Never run `rm -rf /`**
- For APIs/functions/code, search the web first (use context7)
- Verify against current date, Taipei/Taiwan context, and project goals
- Prefer CLI when possible
- Run `pwd` before starting work
- Get approval before accessing parent directories

## CLI Tools

- Packages: brew, uv, npm (via nvm)
- Dev: git, gh, node (via nvm), python3, gcc/g++, cmake, make, hf
- Containers: docker, podman
- Utilities: ffmpeg, curl, wget, jq, yq, rg, fzf, eza, htop, vim, tmux
