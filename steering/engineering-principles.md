---
inclusion: always
---

# Engineering principles

## Diagnose before changing
- Reproduce a bug before fixing it. Base conclusions on evidence (logs, diagnostic output, a minimal repro), not on guesses such as "probably a permissions issue" or "probably caused by a Windows update".
- In comparison experiments, change one variable at a time and state the evidence behind each conclusion.

## Scope of changes
- Make the smallest change that solves the task. Follow the repository's existing style, layout and toolchain.
- Do not add or upgrade dependencies, or change build or CI configuration, without my approval.
- Keep public interfaces, config formats and data formats backward compatible. If a breaking change is unavoidable, explain the impact before making it.

## Error handling
- Never swallow errors. Empty `catch {}`, `except: pass`, `_ = err`, `|| true`, and unexplained `2>$null` or `>nul 2>&1` all count. If an error is genuinely safe to ignore, add a comment explaining why.
- No fake success: when a test fails, do not edit the test to fit the implementation, skip it, or hard-code expected values.
- Error messages carry context: the operation, the input, and the original error.

## Verification
- After a change, run the project's configured formatter, linter and tests. If there are no tests, write down minimal verification steps and actually run them.
- In the report, list the commands you ran and the key output.

## Reversibility
- Back up before replacing binaries, config files or system settings (for example `name.orig` or `name.bak-20260101`), and state how to roll back.
- Do not overwrite a file that is in use. Build the new version next to it, verify it, then switch.

## Git
- Do not commit features or fixes directly to main/master. Create a branch first (`feat/...`, `fix/...`).
- Before committing, review `git status` and `git diff`, and commit only the files that belong to the task.
- Do not run `reset --hard`, `clean` or `push --force`, or rewrite history, unless I explicitly ask.
- Never commit secrets, tokens, `.env` files, proxy node or subscription data, or personal logs.
- Follow the repository's existing commit message style. If it has none, use English Conventional Commits (for example `fix: handle empty DNS list`).

## Security
- Keep secrets in environment variables or the OS credential manager, never in code, logs or steering files.
- Escape or parameterize external input before putting it into shell commands, SQL, file paths or templates.
- Firewall and permission changes follow least privilege: an allow rule must be scoped by program, remote address and interface. Never create an unscoped allow-all rule.

## External documentation
- Use Context7 for third-party libraries when the version matters or the API may have changed recently. Do not call it for questions the repository source or local tools already answer.
- For the Go standard library, use `go doc` locally instead. It matches the installed Go version.
- Treat Context7 results as hints. Confirm import paths, signatures and flags against go.mod, the module source or the installed package before relying on them.
