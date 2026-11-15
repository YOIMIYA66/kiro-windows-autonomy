---
inclusion: fileMatch
fileMatchPattern: ["**/*.ps1", "**/*.psm1", "**/*.psd1", "**/*.bat", "**/*.cmd"]
---

# PowerShell and batch scripts

## Target Windows PowerShell 5.1
Scripts started from .bat files, scheduled tasks or `powershell.exe` run in Windows PowerShell 5.1. Unless the file starts with `#Requires -Version 7` or is only ever run with `pwsh`, write code that works in 5.1:
- Do not use `??`, `??=`, `?.`, the ternary `a ? b : c`, the pipeline chain operators `&&` / `||`, or `ForEach-Object -Parallel`.
- Do not use parameters added in PowerShell 6+, such as `ConvertFrom-Json -AsHashtable`, `Join-Path -AdditionalChildPath`, or `-Encoding utf8NoBOM`.

## File encoding
- Windows PowerShell 5.1 reads a BOM-less .ps1 file as ANSI (GBK on this machine). A .ps1 file that contains non-ASCII text (Chinese strings or comments) must be saved as UTF-8 with BOM, or kept ASCII-only.
- cmd.exe parses .bat files in the console code page (936). Keep .bat files ASCII-only and use CRLF line endings. LF-only batch files can break labels and `goto`.
- `-Encoding utf8` means UTF-8 with BOM in 5.1 and UTF-8 without BOM in 7. When the exact bytes matter, write with `[System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))`.

## Style
- New scripts start with `[CmdletBinding()]` and a `param()` block when they take input, and set `$ErrorActionPreference = 'Stop'`.
- Use full cmdlet names and named parameters in scripts, not aliases (`ForEach-Object`, not `%`; `Remove-Item`, not `rm`).
- Use `-LiteralPath` for paths that come from input or contain `[`, `]` or spaces.
- Support `-WhatIf` (`SupportsShouldProcess`) in scripts that delete files or change system state.
- Batch files: start with `@echo off` and `setlocal`, resolve paths with `%~dp0`, quote every path, and check `%errorlevel%` after each critical step.

## Verification
Run these on every .ps1 file you create or change, and fix the findings:
```powershell
# Syntax check
$errs = $null
[void][System.Management.Automation.Language.Parser]::ParseFile('<file>', [ref]$null, [ref]$errs)
$errs

# Lint, plus syntax compatibility with 5.1 and 7
Invoke-ScriptAnalyzer -Path '<file>' -Severity Warning,Error
Invoke-ScriptAnalyzer -Path '<file>' -Settings @{
    IncludeRules = @('PSUseCompatibleSyntax')
    Rules = @{ PSUseCompatibleSyntax = @{ Enable = $true; TargetVersions = @('5.1', '7.0') } }
}
```
Do not run scripts that need administrator rights or change firewall, DNS, network or registry settings as a test. Tell me the command and let me run it.
