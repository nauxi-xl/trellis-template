<#
.SYNOPSIS
    Cross-machine toolchain installer for Trellis Template (Windows PowerShell).
.DESCRIPTION
    Installs and verifies all tools used by the Trellis AI workflow framework:
      - uv (Python tool manager)
      - Trellis CLI (@mindfoldhq/trellis)
      - Graphify (graphifyy -> graphify, graphify-mcp)
      - NotebookLM MCP & CLI (notebooklm-mcp-cli -> notebooklm-mcp, nlm)
      - Context7 MCP & CLI (@upstash/context7-mcp, context7)
      - agent-lsp (unified multi-language LSP MCP server & CLI)
      - Language Servers (pyright, ruff, typescript-language-server, etc.)
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$DryRun,
    [switch]$Minimal,
    [string]$LspLangs = "python,ts",
    [switch]$InitMcp,
    [switch]$ForceMcp,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$LocalBin = Join-Path $env:USERPROFILE ".local\bin"
if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $LocalBin })) {
    $env:PATH = "$LocalBin;$env:PATH"
}

function Has-Cmd([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Run-Step([string]$Description, [scriptblock]$Action) {
    Write-Host "[INFO]  $Description"
    if ($DryRun) {
        Write-Host "[DRY-RUN] $($Action.ToString().Trim())"
    } else {
        & $Action
    }
}

function Check-Tools {
    $missing = 0
    $core = @("git", "python", "node", "npm", "uv", "trellis", "graphify", "nlm", "notebooklm-mcp", "agent-lsp")
    $opt = @("context7", "pyright", "ruff", "typescript-language-server", "rust-analyzer", "gopls", "clangd")

    Write-Host "=== Core Framework Tools ==="
    foreach ($cmd in $core) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "[OK]    $cmd -> $($found.Source)"
        } else {
            Write-Host "[WARN]  $cmd -> NOT FOUND"
            $missing++
        }
    }

    Write-Host ""
    Write-Host "=== Optional CLI & Language Servers ==="
    foreach ($cmd in $opt) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "[OK]    $cmd -> $($found.Source)"
        } else {
            Write-Host "[INFO]  $cmd -> not installed"
        }
    }
    return $missing
}

if ($Check) {
    $m = Check-Tools
    if ($m -eq 0) {
        Write-Host "`n[OK]    All core framework tools are installed."
        exit 0
    } else {
        Write-Host "`n[ERROR] $m core tool(s) missing. Run .\scripts\install-tools.ps1 to install them."
        exit 1
    }
}

# 1. Prerequisites
foreach ($req in @("git", "node", "npm")) {
    if (-not (Has-Cmd $req)) {
        throw "Missing required tool '$req'. Please install it first (e.g. via winget) and re-run."
    }
}
if (-not (Has-Cmd "python") -and -not (Has-Cmd "python3")) {
    throw "Missing Python 3. Please install Python 3.11+ and re-run."
}

# 2. uv
if (-not (Has-Cmd "uv")) {
    Run-Step "Installing uv..." {
        irm https://astral.sh/uv/install.ps1 | iex
    }
} else {
    Write-Host "[OK]    uv already installed."
}

# 3. Core tools
Run-Step "Installing Trellis CLI (@mindfoldhq/trellis)..." {
    npm install -g @mindfoldhq/trellis@latest
}
Run-Step "Installing Graphify (graphifyy)..." {
    uv tool install --upgrade graphifyy
}
Run-Step "Installing NotebookLM MCP & CLI (notebooklm-mcp-cli)..." {
    uv tool install --upgrade notebooklm-mcp-cli
}
Run-Step "Installing Context7 MCP & CLI (@upstash/context7-mcp, context7)..." {
    npm install -g @upstash/context7-mcp context7
}

# 4. agent-lsp
Run-Step "Installing agent-lsp into $LocalBin..." {
    New-Item -ItemType Directory -Force -Path $LocalBin | Out-Null
    $arch = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "amd64" }
    $tag = "v0.24.2"
    try {
        $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/blackwell-systems/agent-lsp/releases/latest" -UseBasicParsing
        if ($rel.tag_name) { $tag = $rel.tag_name }
    } catch {}
    $zipUrl = "https://github.com/blackwell-systems/agent-lsp/releases/download/$tag/agent-lsp_windows_${arch}.zip"
    $tmpZip = Join-Path $env:TEMP "agent-lsp.zip"
    $tmpDir = Join-Path $env:TEMP "agent-lsp-extract"
    Invoke-WebRequest -Uri $zipUrl -OutFile $tmpZip -UseBasicParsing
    if (Test-Path $tmpDir) { Remove-Item -Recurse -Force $tmpDir }
    Expand-Archive -Path $tmpZip -DestinationPath $tmpDir -Force
    $exe = Get-ChildItem -Path $tmpDir -Filter "agent-lsp.exe" -Recurse | Select-Object -First 1
    if (-not $exe) { throw "agent-lsp.exe not found in archive" }
    Copy-Item -Path $exe.FullName -Destination (Join-Path $LocalBin "agent-lsp.exe") -Force
    Remove-Item -Force $tmpZip
    Remove-Item -Recurse -Force $tmpDir
}

# Ensure $LocalBin is persisted in user PATH
if (-not $DryRun) {
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$LocalBin*") {
        [Environment]::SetEnvironmentVariable("PATH", "$LocalBin;$userPath", "User")
        Write-Host "[OK]    Added $LocalBin to User PATH."
    }
}

# 5. Language Servers
if (-not $Minimal -and $LspLangs -ne "none") {
    $langs = $LspLangs.Split(",") | ForEach-Object { $_.Trim().ToLower() }
    if ($langs -contains "all" -or $langs -contains "python") {
        Run-Step "Installing Python LSP & linter (pyright, ruff)..." {
            uv tool install --upgrade pyright
            uv tool install --upgrade ruff
        }
    }
    if ($langs -contains "all" -or $langs -contains "ts") {
        Run-Step "Installing TypeScript/JS LSP (typescript-language-server, typescript)..." {
            npm install -g typescript-language-server typescript
        }
    }
    if (($langs -contains "all" -or $langs -contains "rust") -and (Has-Cmd "rustup")) {
        Run-Step "Installing Rust LSP (rust-analyzer)..." {
            rustup component add rust-analyzer
        }
    }
    if (($langs -contains "all" -or $langs -contains "go") -and (Has-Cmd "go")) {
        Run-Step "Installing Go LSP (gopls)..." {
            go install golang.org/x/tools/gopls@latest
        }
    }
}

# 6. Optional .mcp.json initialization
if ($InitMcp -or $ForceMcp) {
    $example = Join-Path $RepoRoot ".mcp.json.example"
    $target = Join-Path $RepoRoot ".mcp.json"
    if (Test-Path $example) {
        if (-not (Test-Path $target) -or $ForceMcp) {
            Run-Step "Creating .mcp.json from .mcp.json.example..." {
                Copy-Item -Path $example -Destination $target -Force
            }
        }
    }
}

if (-not $DryRun) {
    Write-Host ""
    Check-Tools | Out-Null
}

Write-Host "`n=== Next Steps ==="
Write-Host "- Initialize developer identity: python .trellis/scripts/init_developer.py <your-name>"
Write-Host "- Authenticate NotebookLM:       nlm login"
