---
inclusion: always
---

# Machine environment

## OS and shell
- Windows 11 Pro 24H2 (build 26100), locale zh-CN. The system ANSI and OEM code pages are both 936 (GBK).
- Kiro runs commands in PowerShell 7 (pwsh). Scripts started from .bat files, scheduled tasks or `powershell.exe -File` run in Windows PowerShell 5.1, which has different syntax.
- Run commands directly in the current pwsh session. Do not wrap them in `pwsh -Command`, `powershell -Command`, `cmd /c` or `-EncodedCommand`. The permission rules cannot inspect a wrapped command, so every wrapper triggers an approval prompt. Wrap only when a step really needs Windows PowerShell 5.1 or cmd.exe, and expect the prompt. Never move a command into a script file to avoid a prompt.
- Always quote paths. The file system is case-insensitive, so never rely on case to tell file names apart.
- Do not elevate on your own. When a step needs administrator rights, tell me exactly what to run as administrator.

## Encoding (the most common pitfall)
- Pass an explicit encoding when reading or writing text, for example `Get-Content -Encoding utf8` and `Set-Content -Encoding utf8`.
- The console output encoding is GBK (gb2312). If Chinese output from an external program looks garbled, check the encoding first. Do not edit file contents because of it.
- Preserve each file's existing encoding, BOM and line endings. Do not convert them as a side effect.
- Git has `core.autocrlf=true` at the system level, so working-tree files are usually CRLF.

## Toolchain (customize for your machine)
- Git and GitHub CLI `gh`.
- Go, Python (`uv` / virtual environments — do not install packages into global/base Python), Node.js (`pnpm` / `npm`), .NET SDK, Java.
- PSScriptAnalyzer is installed for PowerShell linting.
- The versions a project requires come from its own files (`go.mod`, `pyproject.toml`, `package.json`, `.nvmrc` and so on), not from this list.

## Network
- Outbound traffic is governed by the local firewall (e.g. [AI-Net-Guard](https://github.com/YOIMIYA66/AI-Net-Guard)) and TUN/local proxy.
- If a download fails or times out, report the error and the target address, then stop. Do not "fix the network" by changing firewall rules, DNS, proxy settings, network adapters, the hosts file or package manager sources.

## Protected locations (read-only unless I explicitly ask for a change)
- Firewall and leak-protection scripts (e.g. `C:\AI-Net-Guard\`).
- Proxy client binaries, configurations, and subscription/node databases (never read `guiNDB.db*` even through shell commands; `.kiroignore` only blocks built-in file tools, so this rule covers the shell).
- Windows Firewall rules, DNS, routes, the registry, services and scheduled tasks.
