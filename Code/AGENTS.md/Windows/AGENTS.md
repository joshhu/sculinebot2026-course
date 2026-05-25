# Guidelines

## Environment

- Windows 11, Intel 12400 cpu, NVIDIA 4060GPU，64gb ram，8gb vram
- CUDA 13.0, driver 580
- Prefer CUDA; fall back to CPU only when needed

## Dev Rules

- Services: docker; avoid native installs
- Install: winget first
- **No pip.** Python: always use `uv` venv; prefer `uvx`
- Node.js via nvm; packages via npm/npx
- Push every project to a public GitHub repo (repo name = folder name)
- Always include a standard README.md
- Tests required: unit, functional, e2e (use browser tools); ensure coverage
- Reply in Traditional Chinese (Taiwan); never use Simplified Chinese or mainland terms
- Never paste secrets/keys/tokens; read from env vars or `.env`
- For APIs/functions/code, search the web first (use context7)
- Verify against current date, Taipei/Taiwan context, and project goals
- Prefer CLI when possible
- Run `pwd` before starting work
- Get approval before accessing parent directories

## CLI Tools

- Packages: winget, uv, npm (via nvm), snap
- Dev: git, gh, node (via nvm), python3, hf
- GPU/CUDA: nvidia-smi, nvcc
- Containers: docker
- Utilities: ffmpeg, curl, wget, jq, yq, rg 
