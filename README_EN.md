# Kiro Windows Autonomy

English | [简体中文](README.md)

A **rule-driven autonomy** configuration (`permissions.yaml`) and Windows 11 / PowerShell steering ruleset (`steering/`) for **Kiro IDE**.

> **Scope & Intent**: This configuration is a **convenience guardrail against accidental agent actions**, NOT a security sandbox or an OS-level security boundary.

Goal: **Reduce interruptions during routine coding and builds while prompting before reading/writing common secrets or running destructive Windows/Git commands**, paired with steering rules for PowerShell 5.1 vs. 7 compatibility and UTF-8 BOM / GBK (CP936) encoding pitfalls.

---

## Repository Structure

```text
.
├── .github/workflows/
│   └── ci.yml                  # CI workflow for YAML & rule-matching regression tests
├── settings/
│   ├── permissions.yaml        # Kiro user-level permissions (core)
│   ├── kiroignore.example      # Example ignore list for sensitive local DBs/keys
│   └── mcp.example.json        # Example MCP config using env-var auth
├── steering/
│   ├── engineering-principles.md  # Debugging, error handling, reversibility, Git & security
│   ├── powershell-and-batch.md    # PS 5.1 compatibility, BOM/CP936 encoding, PSScriptAnalyzer
│   ├── windows-environment.md     # Windows 11 + pwsh shell rules & encoding template
│   └── personal-preferences.md    # Response style, plan-first threshold, verification report
└── tests/
    └── test_permissions.py     # Regression tests for YAML schema and rule matching
```

---

## Design Philosophy: `permissions.yaml`

### 1. Why Blanket `allow` + Explicit `ask` Rules?

Kiro resolves permissions in order of `deny > ask > allow > evaluate`.
Relying solely on the probabilistic `evaluate` classifier under `approve-for-me` can still interrupt benign commands or misclassify edge cases. By setting:

```yaml
- capability: all
  effect: allow
```

the `evaluate` classifier is bypassed in favor of deterministic `ask` rules (**rule-driven autonomy**).

### 2. Three Layers of Guardrails

- **`fs_read`**: Prompts before reading `.ssh`, `.aws`, `.kube`, `.docker/config.json`, `.env` / `.env.*` (excluding `.env.example`), private keys/certificates (`.pem`, `.key`, `.pfx`, `.p12`), Git credentials, and GitHub CLI config (`~/AppData/Roaming/GitHub CLI/**` and `~/.config/gh/**`).
- **`fs_write`**: Prompts before modifying credentials, `~/.gitconfig`, core Windows OS directories (`C:/Windows/**`, `C:/Program Files/**`, `C:/Program Files (x86)/**`, `C:/ProgramData/**`), and optional protected service folders.
- **`shell`**:
  - **Destructive file & disk operations**: `rm`, `del`, `Remove-Item`, `robocopy /MIR|/PURGE`, `format`, `diskpart`, `bcdedit`, `shutdown`, etc.
  - **Registry, ACLs, services & scheduled tasks**: `reg add|delete`, `Set-Acl`, `icacls`, `takeown`, `sc`, `Set-Service`, `schtasks`, etc.
  - **Firewall & network stack**: `New-NetFirewallRule`, `Set-NetFirewallRule`, `netsh advfirewall`, DNS / IP / route / adapter / WinHTTP changes (read-only `show` / `Get-*` commands stay silent).
  - **Destructive Git operations**: `git reset --hard`, `git clean`, `git push --force|-f`, `git filter-repo`, `git restore --worktree` (while silently allowing harmless `git restore --staged *`).
  - **Process termination, elevation & publishing**: `taskkill`, `Stop-Process`, `Start-Process *RunAs*`, `npm publish`, `gh repo delete`.
  - **Common inline interpreter wrappers**: Prompts on standard `powershell` / `pwsh` (`-Command`, `-command`, `-c`, `-EncodedCommand`, `-encodedcommand`, `-enc`) and `cmd` / `cmd.exe` (`/c`, `/C`, `/k`, `/K`) calls whose inline payloads cannot be inspected by outer shell rules.

### 3. Case-Sensitive Shell Matching: Mitigating All-Lowercase Bypasses (Not a Security Boundary)

Kiro's shell rule matching is **case-sensitive** (e.g., listing `Set-Acl *` alone does not trigger a prompt for lowercase `set-acl`), whereas PowerShell and `cmd` are case-insensitive.

To **mitigate known all-lowercase bypasses**, [`settings/permissions.yaml`](settings/permissions.yaml) mirrors standard PowerShell cmdlets in lowercase and adds common `cmd /C` and `/K` variants at the bottom of the file.

> **Important Limitation**: Mirror rules cannot practically enumerate every arbitrary mixed-case permutation (such as `sEt-aCl` or `CmD /c`), so **Kiro's case-sensitive matching can still leave unhandled case variants**. Likewise, shell rules only match command text and cannot inspect commands inside `.ps1` / `.bat` / `.py` scripts, full-path/aliased invocations, or dynamically constructed variables. Treat `permissions.yaml` strictly as a **convenience guardrail against mistakes**, not a security boundary.

---

## Steering Rules (`steering/`)

| File | Inclusion | Highlights |
| :--- | :--- | :--- |
| [`engineering-principles.md`](steering/engineering-principles.md) | `always` | Evidence-based diagnosis, no swallowed errors, no fake test passes, backup-before-replace, Git & least-privilege security rules |
| [`powershell-and-batch.md`](steering/powershell-and-batch.md) | `*.ps1`, `*.bat`, etc. | Targets Windows PowerShell 5.1 compatibility, enforces UTF-8 BOM / ASCII-only `.bat` CRLF encoding, requires `PSScriptAnalyzer` verification |
| [`windows-environment.md`](steering/windows-environment.md) | `always` | Instructs Kiro not to wrap commands in `pwsh -Command` / `cmd /c` (avoiding wrapper prompts), documents GBK console encoding & read-only network boundaries |
| [`personal-preferences.md`](steering/personal-preferences.md) | `always` | Enforces Simplified Chinese replies (keeping code/paths verbatim), requires a plan before touching 3+ files or system settings, and defines a verification report format |

---

## Companion Project: [AI-Net-Guard](https://github.com/YOIMIYA66/AI-Net-Guard)

Because `permissions.yaml` only operates at the Kiro application layer, you can pair it with kernel-level network isolation on Windows 11:

> **[YOIMIYA66/AI-Net-Guard](https://github.com/YOIMIYA66/AI-Net-Guard)** — *Zero-resident Windows 11 kernel WFP static firewall & DNS leak shield for AI coding tools and TUN proxies (Xray / sing-box / Hysteria2 / Mihomo)*

How they work together:
1. **AI-Net-Guard** enforces outbound allowlists and prevents DNS leaks at the Windows Filtering Platform (WFP) kernel layer.
2. Uncomment the protected directory rule in [`settings/permissions.yaml`](settings/permissions.yaml):
   ```yaml
   - "C:/AI-Net-Guard/**"
   ```
   Combined with the firewall/DNS/route `shell` ask rules, this helps prevent AI agents from accidentally modifying your firewall rules, DNS settings, or proxy configuration when troubleshooting network issues.

---

## Quick Start

1. Clone the repository:
   ```powershell
   git clone https://github.com/YOIMIYA66/kiro-windows-autonomy.git
   cd kiro-windows-autonomy
   ```

2. Copy `permissions.yaml` to your Kiro user settings directory (back up any existing file first):
   ```powershell
   Copy-Item .\settings\permissions.yaml "$env:USERPROFILE\.kiro\settings\permissions.yaml"
   ```
   *(Optional)* Uncomment and adjust protected application paths under `fs_write` to match your machine.

3. Copy the steering rules you want into `%USERPROFILE%\.kiro\steering\`:
   ```powershell
   Copy-Item .\steering\*.md "$env:USERPROFILE\.kiro\steering\"
   ```
   *(Customize [`steering/windows-environment.md`](steering/windows-environment.md) and [`steering/personal-preferences.md`](steering/personal-preferences.md) for your own toolchain and preferred reply language.)*

4. *(Optional)* Refer to [`settings/kiroignore.example`](settings/kiroignore.example) and [`settings/mcp.example.json`](settings/mcp.example.json) for local ignore patterns and MCP environment-variable auth:
   - [`settings/mcp.example.json`](settings/mcp.example.json) references `${CONTEXT7_API_KEY}`;
   - **Kiro prompts for approval the first time an unapproved environment variable is referenced by an MCP server** — set `CONTEXT7_API_KEY` in your environment and approve it when Kiro prompts.

---

## Verification & Regression Tests

After editing `permissions.yaml`, run the automated regression suite (`PyYAML` required):

```powershell
python -m pip install pyyaml
python -m unittest discover -s tests -v
```

[`tests/test_permissions.py`](tests/test_permissions.py) validates YAML syntax, `fs_read`/`fs_write` credential parity, lowercase PowerShell mirrors, `cmd /c`/`/C` wrapper rules, `git` rules, and explicitly documents known Kiro matching limitations.

---

## License

[MIT](LICENSE) © 2026 [YOIMIYA66](https://github.com/YOIMIYA66)
