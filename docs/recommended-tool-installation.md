# Recommended Tool Installation

This document lists the recommended local tools for working on `agent-harness` and sibling repositories.

Recommended tools:

- `zellij`: terminal multiplexer used by FF15-style multi-agent flows.
- `rg`: fast recursive search used heavily by agents and shell workflows.
- `powershell-yaml`: PowerShell module for reading and writing YAML project profiles and config files.

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

### Install `powershell-yaml`

```powershell
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module -Name powershell-yaml -Scope CurrentUser -Force
```

### Verify the installation

```powershell
zellij --version
rg --version
pwsh -NoLogo -Command "Import-Module powershell-yaml; 'hello: world' | ConvertFrom-Yaml | ConvertTo-Json -Compress"
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

### Verify the installation

```bash
zellij --version
rg --version
pwsh -NoLogo -Command "Import-Module powershell-yaml; 'hello: world' | ConvertFrom-Yaml | ConvertTo-Json -Compress"
```

## Notes

- `powershell-yaml` is installed per user in both environments. That keeps setup local and avoids admin-only module paths.
- If you primarily work from Windows terminals, install the Windows set even when WSL is also available.
- If a workflow launches inside WSL, install the WSL set as well. Windows and WSL environments do not share binaries or PowerShell modules.