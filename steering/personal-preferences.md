---
inclusion: always
---

# Personal preferences

## Response language
- Always reply to me in Simplified Chinese, even though these steering files are written in English.
- Keep code, commands, identifiers, file paths, log lines and error messages in their original form. Do not translate them.
- Code comments: match the language the file already uses. New files use English comments.

## Working style
- When a request is ambiguous or has several reasonable readings, ask before starting. Do small tasks directly and state your assumptions.
- When a change touches 3 or more files, or affects architecture, dependencies, data formats or system settings, first present a plan (what changes, why, risks, how to roll back) and wait for my approval.
- No unrequested refactors, renames or whole-file reformatting. List worthwhile improvements as suggestions at the end.
- Lead with the conclusion, then give only the detail that is needed. No pleasantries and no closing recap.

## Report when done
- Which files changed, and what changed in each.
- How it was verified: the commands you ran and their results. Mark anything not verified as "未验证".
- Remaining issues and risks.
