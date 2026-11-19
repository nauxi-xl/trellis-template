#!/usr/bin/env bash
# ==============================================================================
# Trellis Template — Cross-Platform Toolchain Installer
# Installs and verifies all tools used by the Trellis AI workflow framework:
#   - uv (Python tool manager)
#   - Trellis CLI (@mindfoldhq/trellis)
#   - Graphify (graphifyy -> graphify, graphify-mcp)
#   - NotebookLM MCP & CLI (notebooklm-mcp-cli -> notebooklm-mcp, nlm)
#   - Context7 MCP & CLI (@upstash/context7-mcp, context7)
#   - agent-lsp (unified multi-language LSP MCP server & CLI)
#   - Language Servers (pyright, ruff, typescript-language-server, etc.)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DRY_RUN=0
CHECK_ONLY=0
MINIMAL=0
INIT_MCP=0
FORCE_MCP=0
LSP_LANGS="python,ts"
AUTO_DETECT_LSP=1

# Ensure user-local bins are visible in the current session
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

log_info()  { printf '[INFO]  %s\n' "$*"; }
log_ok()    { printf '[OK]    %s\n' "$*"; }
log_warn()  { printf '[WARN]  %s\n' "$*"; }
log_err()   { printf '[ERROR] %s\n' "$*" >&2; }

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN] %s\n' "$*"
  else
    eval "$@"
  fi
}

usage() {
  cat <<'EOF'
Usage: ./scripts/install-tools.sh [OPTIONS]

Install or verify the Trellis Template framework toolchain.

Options:
  --check              Check installed tools and exit non-zero if core tools are missing
  --dry-run            Print install commands without executing them
  --minimal            Install core framework tools only (skip language servers)
  --lsp-langs <csv>    Comma-separated LSP stacks to install (default: python,ts)
                       Supported: python, ts, rust, go, cpp, all, none
  --init-mcp           Copy .mcp.json.example to .mcp.json if .mcp.json does not exist
  --force-mcp          Overwrite .mcp.json from .mcp.json.example
  -h, --help           Show this help message

Examples:
  ./scripts/install-tools.sh
  ./scripts/install-tools.sh --init-mcp --lsp-langs python,ts,rust
  ./scripts/install-tools.sh --check
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --check)
      CHECK_ONLY=1
      shift
      ;;
    --minimal)
      MINIMAL=1
      AUTO_DETECT_LSP=0
      shift
      ;;
    --lsp-langs)
      if [[ $# -lt 2 ]]; then
        log_err "--lsp-langs requires a value"
        exit 1
      fi
      LSP_LANGS="$2"
      AUTO_DETECT_LSP=0
      shift 2
      ;;
    --init-mcp)
      INIT_MCP=1
      shift
      ;;
    --force-mcp)
      INIT_MCP=1
      FORCE_MCP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_err "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

npm_install_global() {
  local prefix
  prefix="$(npm prefix -g 2>/dev/null || true)"
  if [[ -n "$prefix" && -w "$prefix" ]]; then
    run_cmd "npm install -g $*"
  elif [[ "$(id -u)" -eq 0 ]]; then
    run_cmd "npm install -g $*"
  else
    log_info "Global npm prefix '${prefix:-unknown}' is not writable; installing into \$HOME/.local instead."
    run_cmd "NPM_CONFIG_PREFIX=\"\$HOME/.local\" npm install -g $*"
  fi
}

check_tools() {
  local missing=0
  local core_cmds=(git python3 node npm uv trellis graphify nlm notebooklm-mcp agent-lsp)
  local opt_cmds=(context7 pyright ruff typescript-language-server rust-analyzer gopls clangd)

  echo "=== Core Framework Tools ==="
  for cmd in "${core_cmds[@]}"; do
    if has_cmd "$cmd"; then
      log_ok "$cmd -> $(command -v "$cmd")"
    else
      log_warn "$cmd -> NOT FOUND"
      missing=$((missing + 1))
    fi
  done

  echo ""
  echo "=== Optional CLI & Language Servers ==="
  for cmd in "${opt_cmds[@]}"; do
    if has_cmd "$cmd"; then
      log_ok "$cmd -> $(command -v "$cmd")"
    else
      log_info "$cmd -> not installed"
    fi
  done

  return "$missing"
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  if check_tools; then
    echo ""
    log_ok "All core framework tools are installed."
    exit 0
  else
    echo ""
    log_err "Some core framework tools are missing. Run ./scripts/install-tools.sh to install them."
    exit 1
  fi
fi

# ------------------------------------------------------------------------------
# 1. Verify System Prerequisites
# ------------------------------------------------------------------------------
log_info "Checking base prerequisites..."
missing_prereqs=()
for req in git python3 node npm curl; do
  if ! has_cmd "$req"; then
    missing_prereqs+=("$req")
  fi
done

if [[ ${#missing_prereqs[@]} -gt 0 ]]; then
  log_err "Missing required system tools: ${missing_prereqs[*]}"
  log_err "Please install them using your OS package manager (apt, dnf, pacman, brew, etc.) and re-run this script."
  exit 1
fi
log_ok "Base prerequisites found (git, python3, node, npm, curl)."

# ------------------------------------------------------------------------------
# 2. Install uv if missing
# ------------------------------------------------------------------------------
if has_cmd uv; then
  log_ok "uv already installed ($(uv --version))."
else
  log_info "Installing uv..."
  run_cmd 'curl -LsSf https://astral.sh/uv/install.sh | sh'
fi

# ------------------------------------------------------------------------------
# 3. Install Core Framework Tools
# ------------------------------------------------------------------------------
log_info "Installing Trellis CLI (@mindfoldhq/trellis)..."
npm_install_global "@mindfoldhq/trellis@latest"

log_info "Installing Graphify (graphifyy)..."
run_cmd 'uv tool install --upgrade graphifyy'

log_info "Installing NotebookLM MCP & CLI (notebooklm-mcp-cli)..."
run_cmd 'uv tool install --upgrade notebooklm-mcp-cli'

log_info "Installing Context7 MCP & CLI (@upstash/context7-mcp, context7)..."
npm_install_global "@upstash/context7-mcp context7"

install_agent_lsp() {
  local install_dir="$HOME/.local/bin"
  run_cmd "mkdir -p \"$install_dir\""

  log_info "Installing agent-lsp into $install_dir..."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd "curl -fsSL https://raw.githubusercontent.com/blackwell-systems/agent-lsp/main/install.sh | INSTALL_DIR=\"$install_dir\" sh"
    return 0
  fi

  if curl -fsSL https://raw.githubusercontent.com/blackwell-systems/agent-lsp/main/install.sh | INSTALL_DIR="$install_dir" sh; then
    if has_cmd agent-lsp || [[ -x "$install_dir/agent-lsp" ]]; then
      log_ok "agent-lsp installed via official installer."
      return 0
    fi
  fi

  log_warn "Official install.sh failed; trying GitHub release tarball fallback..."
  local os arch tag url tmp_dir
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *)
      log_err "Unsupported architecture for fallback binary: $arch"
      return 1
      ;;
  esac

  tag="$(curl -fsSL https://api.github.com/repos/blackwell-systems/agent-lsp/releases/latest | python3 -c "import sys, json; print(json.load(sys.stdin)['tag_name'])" 2>/dev/null || echo "v0.24.2")"
  url="https://github.com/blackwell-systems/agent-lsp/releases/download/${tag}/agent-lsp_${os}_${arch}.tar.gz"
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' RETURN

  if curl -fsSL "$url" -o "$tmp_dir/agent-lsp.tar.gz"; then
    tar -xzf "$tmp_dir/agent-lsp.tar.gz" -C "$tmp_dir"
    if [[ -f "$tmp_dir/agent-lsp" ]]; then
      mv "$tmp_dir/agent-lsp" "$install_dir/agent-lsp"
      chmod +x "$install_dir/agent-lsp"
      log_ok "agent-lsp (${tag}) installed from GitHub release."
      return 0
    fi
  fi

  log_err "Failed to install agent-lsp automatically. See https://github.com/blackwell-systems/agent-lsp"
  return 1
}

install_agent_lsp

# ------------------------------------------------------------------------------
# 4. Install Language Servers (LSP)
# ------------------------------------------------------------------------------
contains_lang() {
  local target="$1"
  [[ "$LSP_LANGS" == "all" ]] && return 0
  [[ ",$LSP_LANGS," == *",$target,"* ]] && return 0
  return 1
}

if [[ "$MINIMAL" -eq 0 && "$LSP_LANGS" != "none" ]]; then
  if contains_lang "python"; then
    log_info "Installing Python LSP & linter (pyright, ruff)..."
    run_cmd 'uv tool install --upgrade pyright'
    run_cmd 'uv tool install --upgrade ruff'
  fi

  if contains_lang "ts"; then
    log_info "Installing TypeScript/JavaScript LSP (typescript-language-server, typescript)..."
    npm_install_global "typescript-language-server typescript"
  fi

  if contains_lang "rust" || { [[ "$AUTO_DETECT_LSP" -eq 1 ]] && has_cmd rustup; }; then
    if has_cmd rustup; then
      log_info "Installing Rust LSP (rust-analyzer)..."
      run_cmd 'rustup component add rust-analyzer'
    else
      log_warn "rustup not found; skipping rust-analyzer."
    fi
  fi

  if contains_lang "go" || { [[ "$AUTO_DETECT_LSP" -eq 1 ]] && has_cmd go; }; then
    if has_cmd go; then
      log_info "Installing Go LSP (gopls)..."
      run_cmd 'go install golang.org/x/tools/gopls@latest'
    else
      log_warn "go not found; skipping gopls."
    fi
  fi

  if contains_lang "cpp"; then
    if has_cmd clangd; then
      log_ok "clangd already installed."
    else
      log_warn "clangd not found. Install via OS package manager (e.g. 'sudo apt install clangd' or 'brew install llvm')."
    fi
  fi
fi

# ------------------------------------------------------------------------------
# 5. Optional .mcp.json Initialization
# ------------------------------------------------------------------------------
if [[ "$INIT_MCP" -eq 1 ]]; then
  if [[ -f "$REPO_ROOT/.mcp.json.example" ]]; then
    if [[ ! -f "$REPO_ROOT/.mcp.json" || "$FORCE_MCP" -eq 1 ]]; then
      log_info "Creating .mcp.json from .mcp.json.example..."
      run_cmd "cp \"$REPO_ROOT/.mcp.json.example\" \"$REPO_ROOT/.mcp.json\""
    else
      log_info ".mcp.json already exists (use --force-mcp to overwrite)."
    fi
  else
    log_warn ".mcp.json.example not found in $REPO_ROOT"
  fi
fi

# ------------------------------------------------------------------------------
# 6. Verification & Post-Install Guidance
# ------------------------------------------------------------------------------
echo ""
if [[ "$DRY_RUN" -eq 0 ]]; then
  check_tools || true
  echo ""
  if has_cmd agent-lsp; then
    log_info "Running agent-lsp doctor..."
    (cd "$REPO_ROOT" && agent-lsp doctor) || true
  fi
  if [[ -f "$REPO_ROOT/.trellis/scripts/verify.py" ]]; then
    echo ""
    log_info "Running verify.py --dry-run..."
    (cd "$REPO_ROOT" && python3 .trellis/scripts/verify.py --dry-run) || true
  fi
fi

echo ""
echo "=== Next Steps ==="
if [[ ":${PATH}:" != *":$HOME/.local/bin:"* ]]; then
  echo "1. Add ~/.local/bin to your shell PATH (e.g. ~/.bashrc or ~/.zshrc):"
  echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
echo "- Initialize your Trellis developer identity in this repo:"
echo "    python3 .trellis/scripts/init_developer.py <your-name>"
echo "- Authenticate Google NotebookLM before using notebooklm-mcp / nlm:"
echo "    nlm login"
echo "- Review .mcp.json (or copy .mcp.json.example to .mcp.json) for your AI agent host."
