# Recommended Tool Installation

This document lists the recommended local tools for working on `agent-harness` and sibling repositories.

Recommended tools:

- `zellij`: terminal multiplexer used by FF15-style multi-agent flows.
- `rg`: fast recursive search used heavily by agents and shell workflows.
- `Python`: runtime used by local automation helpers and general scripting.
- `powershell-yaml`: PowerShell module for reading and writing YAML project profiles and config files.
- `openspec`: spec-driven development CLI used in OpenSpec-based planning and implementation workflows.
- `GitHub Copilot CLI`: terminal-first Copilot interface for repository and shell assistance.

## Windows

The Windows examples below assume `winget` is available and that PowerShell 7 (`pwsh`) is the main shell.

### Install `zellij`

```powershell
winget install --id Zellij.Zellij -e
```

### Install `rg`

```powershell
winget install --id BurntSushi.ripgrep.MSVC -e
```

### Install `Python`

```powershell
winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity
py install
```

### Install `powershell-yaml`

```powershell
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module -Name powershell-yaml -Scope CurrentUser -Force
```

### Install `openspec`

```powershell
npm install -g @fission-ai/openspec@latest
```

### Install `GitHub Copilot CLI`

```powershell
npm install -g @github/copilot
```

### Verify the installation

```powershell
zellij --version
rg --version
py --version
pwsh -NoLogo -Command "Import-Module powershell-yaml; 'hello: world' | ConvertFrom-Yaml | ConvertTo-Json -Compress"
openspec --version
copilot --help
```

Expected YAML verification output:

```json
{"hello":"world"}
```

## WSL

The WSL examples below assume an Ubuntu-based distribution.

### Install `zellij` and `rg`

```bash
sudo apt update
sudo apt install -y zellij ripgrep
```

If your distribution does not ship `zellij`, install it from the upstream release or from Cargo instead of the distro package.

### Install `Python`

```bash
sudo apt update
sudo apt install -y python3 python3-pip
```

### Install PowerShell and `powershell-yaml`

```bash
sudo apt update
sudo apt install -y wget apt-transport-https software-properties-common
source /etc/os-release
wget -q https://packages.microsoft.com/config/ubuntu/$VERSION_ID/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt update
sudo apt install -y powershell
pwsh -NoLogo -Command "Set-PSRepository -Name PSGallery -InstallationPolicy Trusted; Install-Module -Name powershell-yaml -Scope CurrentUser -Force"
```

### Install `openspec`

```bash
npm install -g @fission-ai/openspec@latest
```

### Install `GitHub Copilot CLI`

```bash
npm install -g @github/copilot
```

### Verify the installation

```bash
zellij --version
rg --version
python3 --version
python3 -m pip --version
pwsh -NoLogo -Command "Import-Module powershell-yaml; 'hello: world' | ConvertFrom-Yaml | ConvertTo-Json -Compress"
openspec --version
copilot --help
```

## Notes

- The Windows examples install Python through the Python install manager, so `py` is the canonical launcher there.
- Ubuntu-based WSL images often already include Python 3, but installing `python3-pip` ensures `pip` is available for local tooling.
- `powershell-yaml` is installed per user in both environments. That keeps setup local and avoids admin-only module paths.
- `openspec` currently installs through `npm`, so `node` and `npm` must already be available in the target environment.
- `GitHub Copilot CLI` is shown in GitHub Docs with `npm` as the cross-platform install path; `winget`, Homebrew, and the install script remain valid platform-specific alternatives.
- `GitHub Copilot CLI` requires Node.js 22 or later when installed through `npm`, plus GitHub authentication and an active Copilot entitlement after installation.
- If you primarily work from Windows terminals, install the Windows set even when WSL is also available.
- If a workflow launches inside WSL, install the WSL set as well. Windows and WSL environments do not share binaries or PowerShell modules.