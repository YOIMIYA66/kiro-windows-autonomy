# Kiro Windows Autonomy

English | [简体中文](README.md)

A **rule-driven autonomy** configuration (`permissions.yaml`), Windows 11 / PowerShell steering ruleset (`steering/`), and automated regression test suite for **Kiro IDE**.

> **Scope & Intent**: This configuration is a **convenience guardrail against accidental agent actions**, NOT a security sandbox or an OS-level security boundary.

---

## Why Kiro Windows Autonomy?

1. **End Prompt Fatigue Without Dropping Guardrails (Rule-Driven Autonomy)**
   - Replaces Kiro's probabilistic `evaluate` classifier with a deterministic baseline (`capability: all -> allow`, which excludes `sandbox_network`) plus explicit `ask` rules.
   - Routine coding, builds, test runs, and read-only inspection (`git status`, `Get-NetFirewallRule`, `netsh advfirewall show`) run silently without interruptions, while credential access, core Windows OS folders, destructive commands, and dangerous Git operations still prompt.

2. **Built Specifically for Windows 11 & PowerShell**
   - **Mitigates case-sensitivity bypasses**: Kiro's `shell` matcher is case-sensitive while PowerShell and `cmd` are not. Includes lowercase mirrors for risky PowerShell cmdlets and common `cmd /c` / `/C` / `/k` / `/K` wrapper flags.
   - **Prevents PowerShell 5.1 vs. 7 syntax breaks**: Enforces PowerShell 5.1 compatibility for `.ps1` scripts spawned via `powershell.exe`, batch files, or scheduled tasks (disallowing PS 7-only operators like `??`, `&&`, or `-Encoding utf8NoBOM`).
   - **Eliminates UTF-8 BOM / GBK (CP936) garbling**: Codifies exact BOM rules for `.ps1`, ASCII + CRLF rules for `.bat`, and mandatory `Parser::ParseFile` + `PSScriptAnalyzer` checks.

3. **Disciplined Engineering Steering Rules**
   - Requires evidence-based diagnosis, forbids silent error swallowing (`catch {}`, `2>$null`) or faking test passes, enforces a plan-before-change threshold for 3+ files or system settings, and locks down local firewall/DNS/proxy config as read-only boundaries.

4. **Regression-Tested & CI-Verified**
   - Ships with [`tests/test_permissions.py`](tests/test_permissions.py) to verify YAML validity, `fs_read`/`fs_write` credential parity, `sandbox_network` exclusion, lowercase cmdlet mirrors, inline wrapper prompts, and documented Kiro limitations.

---

## One-Shot AI Setup Prompt (Copy & Paste)

Using Kiro (or another coding agent) already? Paste this prompt directly to have the agent back up your existing `~/.kiro` setup, install these rules, tailor `windows-environment.md` to your actual machine, and verify everything:

```text
Please install and adapt the Kiro Windows configuration from https://github.com/YOIMIYA66/kiro-windows-autonomy for my machine in this order:

1. Back up my existing `%USERPROFILE%\.kiro\settings` and `%USERPROFILE%\.kiro\steering` (if present) with a `.bak-YYYYMMDD` suffix and tell me how to roll back.
2. Clone `https://github.com/YOIMIYA66/kiro-windows-autonomy.git` into a temporary directory (e.g. `%USERPROFILE%\.kiro\_upstream-kiro-windows-autonomy`).
3. Copy `settings/permissions.yaml` to `%USERPROFILE%\.kiro\settings\permissions.yaml`:
   - Keep all default guardrail rules.
   - Ask me if I have any local firewall/proxy directories I want protected before uncommenting or adding paths under `fs_write`.
4. Copy `steering/*.md` to `%USERPROFILE%\.kiro\steering\`:
   - Inspect the toolchain actually installed on my machine (Git, Go, Python/uv/conda, Node.js/pnpm, .NET, Java, PSScriptAnalyzer, etc.) and customize `steering/windows-environment.md` accordingly (do not list tools that are missing, and never include any keys, tokens, or proxy node/subscription data).
   - Check with me whether to keep or adjust the reply language rule in `steering/personal-preferences.md` (default is Simplified Chinese).
5. If I use `mcp.json` or need local ignore rules, explain how to adapt `settings/kiroignore.example` and `settings/mcp.example.json` (and note that referencing `${CONTEXT7_API_KEY}` triggers a one-time Kiro approval prompt).
6. Run `python -B -m unittest discover -s tests -v` inside the cloned repo (check/install `pyyaml` in a venv or ask first if missing), validate YAML syntax on `%USERPROFILE%\.kiro\settings\permissions.yaml`, and report backup paths, changed files, and test output.
```

---

## Manual Installation

> [!TIP]
> Back up your existing `%USERPROFILE%\.kiro` settings and steering files before overwriting anything.

### Step 1: Back up existing files and clone the repository

```powershell
$kiroDir = "$env:USERPROFILE\.kiro"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (Test-Path "$kiroDir\settings") { Copy-Item -Recurse "$kiroDir\settings" "$kiroDir\settings.bak-$stamp" }
if (Test-Path "$kiroDir\steering") { Copy-Item -Recurse "$kiroDir\steering" "$kiroDir\steering.bak-$stamp" }

git clone https://github.com/YOIMIYA66/kiro-windows-autonomy.git
cd kiro-windows-autonomy
```

### Step 2: Install `permissions.yaml`

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kiro\settings" | Out-Null
Copy-Item .\settings\permissions.yaml "$env:USERPROFILE\.kiro\settings\permissions.yaml"
```

*(Optional)* Open `%USERPROFILE%\.kiro\settings\permissions.yaml` and uncomment or add your own protected application directories under `fs_write` (e.g. `C:/AI-Net-Guard/**` or your proxy client directory).

### Step 3: Install and customize `steering/` rules

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kiro\steering" | Out-Null
Copy-Item .\steering\*.md "$env:USERPROFILE\.kiro\steering\"
```

Tailor these two files to your setup:
- `%USERPROFILE%\.kiro\steering\windows-environment.md`: Adjust `## Toolchain` and `## Protected locations` to match your installed tools and protected folders.
- `%USERPROFILE%\.kiro\steering\personal-preferences.md`: Adjust preferred reply language (defaults to Simplified Chinese) and reporting style.

### Step 4: *(Optional)* Configure ignore patterns and MCP env vars

Refer to [`settings/kiroignore.example`](settings/kiroignore.example) and [`settings/mcp.example.json`](settings/mcp.example.json):
- [`settings/mcp.example.json`](settings/mcp.example.json) uses `${CONTEXT7_API_KEY}` environment variable expansion;
- **Kiro prompts for approval the first time an unapproved environment variable is referenced by an MCP server** — set `CONTEXT7_API_KEY` in your user/system environment and approve it when Kiro prompts.

---

## Repository Structure

```text
.
├── .github/workflows/
│   └── ci.yml                  # CI workflow for YAML & rule-matching regression tests
├── .gitignore                  # Ignores local Python bytecode cache
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

## Design & Limitations

### 1. Why Blanket `allow` + Explicit `ask` Rules?

Kiro resolves permissions in order of `deny > ask > allow > evaluate`.
Setting:

```yaml
- capability: all
  effect: allow
```

bypasses the probabilistic `evaluate` classifier in favor of deterministic `ask` rules. Per [Kiro's permissions documentation](https://kiro.dev/docs/permissions/), `capability: all` **does not include `sandbox_network`**.

### 2. Three Layers of Guardrails

- **`fs_read`**: Prompts before reading `.ssh`, `.aws`, `.kube`, `.docker/config.json`, `.env` / `.env.*` (excluding `.env.example`), private keys/certificates (`.pem`, `.key`, `.pfx`, `.p12`), Git credentials, and GitHub CLI config (`~/AppData/Roaming/GitHub CLI/**` and `~/.config/gh/**`).
- **`fs_write`**: Prompts before modifying credentials, `~/.gitconfig`, core Windows OS directories (`C:/Windows/**`, `C:/Program Files/**`, `C:/Program Files (x86)/**`, `C:/ProgramData/**`), and optional protected service folders.
- **`shell`**: Covers destructive file/disk ops, registry & ACLs, services & scheduled tasks, firewall/DNS/route/adapter/WinHTTP changes (read-only `show`/`Get-*` stay silent), destructive Git commands (allowing `git restore --staged *`), process kill/UAC elevation/remote deletion, and common `powershell` / `pwsh` / `cmd` inline wrapper flags.

### 3. Case-Sensitive Shell Matching: Mitigating All-Lowercase Bypasses

Kiro's shell rule matching is **case-sensitive** (e.g., listing `Set-Acl *` alone does not trigger a prompt for lowercase `set-acl`), whereas PowerShell and `cmd` are case-insensitive.

To **mitigate known all-lowercase bypasses**, [`settings/permissions.yaml`](settings/permissions.yaml) mirrors standard PowerShell cmdlets in lowercase and adds common `cmd /C` and `/K` variants at the bottom of the file.

> **Important Limitation**: Mirror rules cannot practically enumerate every arbitrary mixed-case permutation (such as `sEt-aCl` or `CmD /c`), so **Kiro's case-sensitive matching can still leave unhandled case variants**. Likewise, shell rules only match command text and cannot inspect commands inside `.ps1` / `.bat` / `.py` scripts, full-path/aliased invocations, or dynamically constructed variables. Treat `permissions.yaml` strictly as a **convenience guardrail against mistakes**, not a security boundary.

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

## Verification & Regression Tests

After editing `permissions.yaml`, run the automated regression suite (`PyYAML` required):

```powershell
python -m pip install pyyaml
python -m unittest discover -s tests -v
```

[`tests/test_permissions.py`](tests/test_permissions.py) validates YAML syntax, verifies that `capability: all` excludes `sandbox_network`, checks `fs_read`/`fs_write` credential parity, lowercase PowerShell mirrors, `cmd /c`/`/C` wrapper rules, `git` rules, and explicitly documents known Kiro matching limitations.

---

## License

[MIT](LICENSE) © 2026 [YOIMIYA66](https://github.com/YOIMIYA66)
