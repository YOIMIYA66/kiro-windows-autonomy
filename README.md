# Kiro Windows Autonomy

[English](README_EN.md) | 简体中文

一套面向 Windows 11 环境的 **Kiro IDE** 规则驱动自治配置（Rule-Driven Autonomy），包含经过实战验证的 [`permissions.yaml`](settings/permissions.yaml) 权限护栏与 [`steering/`](steering/) 工程规范。

> **定位说明**：本配置是**防误操作的便利性护栏（convenience guardrail）**，而非可靠的安全沙箱或系统级安全边界。

核心目标：**日常开发零打扰放行，常见敏感凭据读写与高危系统操作弹出确认**，同时通过 Steering 规范约束 PS 5.1 / 7 语法混用、UTF-8 BOM / GBK (CP936) 编码踩坑等 Windows 高频问题。

---

## 目录结构

```text
.
├── .github/workflows/
│   └── ci.yml                  # YAML 语法与权限匹配回归测试 CI
├── settings/
│   ├── permissions.yaml        # Kiro 用户级权限策略（核心）
│   ├── kiroignore.example      # 敏感数据库/密钥文件忽略模板
│   └── mcp.example.json        # 使用环境变量注入 Key 的 MCP 配置模板
├── steering/
│   ├── engineering-principles.md  # 通用工程准则（诊断、错误处理、Git、安全）
│   ├── powershell-and-batch.md    # PS 5.1 兼容性、BOM/CP936 编码、PSScriptAnalyzer 校验
│   ├── windows-environment.md     # Windows 11 + pwsh 环境约束与编码避坑模板
│   └── personal-preferences.md    # 中文回复规范、大改动先出方案、完成汇报格式
└── tests/
    └── test_permissions.py     # 规则语法与高危命令匹配回归测试
```

---

## 核心设计理念：`permissions.yaml`

### 1. 为什么采用「全量放行 + 显式 `ask` 护栏」？

Kiro 的权限优先级为：`deny > ask > allow > evaluate`。
在默认的 `approve-for-me` 策略下，如果依赖概率分类器（`evaluate`），高频只读或常规构建命令仍可能频繁中断，或出现边界误判。本配置通过基线规则：

```yaml
- capability: all
  effect: allow
```

使 `evaluate` 分类器不再介入，转而用**确定性的 `ask` 规则清单**降低日常误操作风险（Rule-Driven Autonomy）。

### 2. 三维防护范围

- **`fs_read`（敏感文件读取确认）**：拦截读取 `.ssh`、`.aws`、`.kube`、`.docker/config.json`、`.env` / `.env.*`（放行 `.env.example`）、私钥证书（`.pem` / `.key` / `.pfx` / `.p12`）、Git 凭据及 GitHub CLI 配置（`~/AppData/Roaming/GitHub CLI/**` 与 `~/.config/gh/**`）。
- **`fs_write`（敏感与系统目录写入确认）**：除上述凭据目录外，额外拦截写入 `~/.gitconfig`、`C:/Windows/**`、`C:/Program Files/**`、`C:/Program Files (x86)/**`、`C:/ProgramData/**` 以及你自定义的受保护服务目录。
- **`shell`（高危命令确认）**：
  - **破坏性文件与磁盘操作**：`rm` / `del` / `Remove-Item` / `robocopy /MIR|/PURGE`、`format` / `diskpart` / `bcdedit` / `shutdown` 等；
  - **注册表、ACL、服务与计划任务**：`reg add|delete`、`Set-Acl` / `icacls` / `takeown`、`sc` / `Set-Service` / `schtasks` 等；
  - **防火墙与网络栈**：`New-NetFirewallRule` / `Set-NetFirewallRule` / `netsh advfirewall`、DNS / IP / 路由 / 网卡 / WinHTTP 代理修改（保留只读 `show` / `Get-*` 静默放行）；
  - **危险 Git 操作**：`git reset --hard`、`git clean`、`git push --force|-f`、`git filter-repo`、`git restore --worktree` 等（单独放行无害的 `git restore --staged *`）；
  - **进程终止、提权与远端删除**：`taskkill` / `Stop-Process`、`Start-Process *RunAs*`、`npm publish`、`gh repo delete`；
  - **常见内联解释器包装命令**：对常见的 `powershell` / `pwsh`（`-Command` / `-command` / `-c` / `-EncodedCommand` / `-encodedcommand` / `-enc`）与 `cmd` / `cmd.exe`（`/c` / `/C` / `/k` / `/K`）调用触发确认，因为它们的内联载荷无法被外层规则审计。

### 3. 踩坑与局限：缓解已知的全小写绕过（非安全边界）

实测发现 **Kiro 的 `shell` 模式匹配是区分大小写的**（例如配置了 `Set-Acl *`，但执行全小写的 `set-acl ...` 会跳过提示），而 PowerShell 与 `cmd` 本身不区分大小写。

为此，[`settings/permissions.yaml`](settings/permissions.yaml) 末尾补充了标准 PowerShell Cmdlet 的全小写镜像以及常见的 `cmd /C`、`/K` 变体，用来**缓解已知的全小写绕过**。

> **重要局限**：镜像规则无法实用地穷举所有混合大小写组合（如 `sEt-aCl`、`CmD /c`），**Kiro 的大小写敏感匹配仍可能留下未覆盖的变体**；同时规则只匹配命令文本本身，无法检查 `.ps1` / `.bat` / `.py` 脚本内部、完整绝对路径/别名调用或变量拼接传递的参数。请始终将其视为**防误操作的便利性护栏**，切勿依赖它替代操作系统权限控制或网络隔离。

---

## Steering 规范说明（`steering/`）

| 文件 | 适用范围 | 核心作用 |
| :--- | :--- | :--- |
| [`engineering-principles.md`](steering/engineering-principles.md) | `always` | 先取证复现再修复、禁止静默吞异常（空 `catch` / `2>$null`）、禁止篡改测试凑通过、改动前备份可回滚、Git 分支与凭据红线 |
| [`powershell-and-batch.md`](steering/powershell-and-batch.md) | `*.ps1`, `*.bat` 等 | 约束脚本默认兼容 Windows PowerShell 5.1（禁用 PS7 专属运算符）、明确 UTF-8 with BOM 与 GBK (CP936) 编码规则、强制执行 `PSScriptAnalyzer` 语法与兼容性检查 |
| [`windows-environment.md`](steering/windows-environment.md) | `always` | 禁止 AI 使用 `pwsh -Command` / `cmd /c` 包装命令（避免无意义触发权限弹窗）、规范 GBK 控制台输出处理、声明只读网络与防火墙边界（含本机工具链模板） |
| [`personal-preferences.md`](steering/personal-preferences.md) | `always` | 强制简体中文回复（保留原路径与代码标识符）、修改涉及 3 个以上文件或系统设置前先给方案、禁止顺手重构、输出包含验证命令的结项报告 |

---

## 配套推荐：[AI-Net-Guard](https://github.com/YOIMIYA66/AI-Net-Guard)

因为 `permissions.yaml` 只是 Kiro 应用层的命令文本护栏（不提供系统级网络或内核隔离），如果你在 Windows 11 上运行各类 AI 编程工具或搭配 TUN 代理，建议配合我的另一个开源项目使用以在 OS 内核层补齐网络边界：

> **[YOIMIYA66/AI-Net-Guard](https://github.com/YOIMIYA66/AI-Net-Guard)** — *Zero-resident Windows 11 kernel WFP static firewall & DNS leak shield for AI coding tools and TUN proxies (Xray / sing-box / Hysteria2 / Mihomo)*

联动方式：
1. 系统层由 **AI-Net-Guard** 通过 Windows 11 内核 WFP 静态防火墙规则接管出站与防 DNS 泄露；
2. 在 [`settings/permissions.yaml`](settings/permissions.yaml) 的 `fs_write` 中取消注释以下保护规则（并按需放开 `logs/**`）：
   ```yaml
   - "C:/AI-Net-Guard/**"
   ```
   配合 `shell` 规则中的防火墙与网络命令拦截，减少 AI Agent 在排查下载超时或网络问题时误改防火墙策略、DNS 或代理配置的概率。

---

## 快速安装

> [!TIP]
> 在覆盖之前，建议先备份你原有的 `%USERPROFILE%\.kiro` 相关文件。

1. 克隆本仓库：
   ```powershell
   git clone https://github.com/YOIMIYA66/kiro-windows-autonomy.git
   cd kiro-windows-autonomy
   ```

2. 复制权限配置到 Kiro 用户目录：
   ```powershell
   Copy-Item .\settings\permissions.yaml "$env:USERPROFILE\.kiro\settings\permissions.yaml"
   ```
   *(可选)* 根据你的实际目录取消注释 `fs_write` 中的 `AI-Net-Guard` 或本地代理软件路径保护。

3. 复制 Steering 规范（按需选择，建议先检查并修改 `windows-environment.md` 中的工具链与网络描述）：
   ```powershell
   Copy-Item .\steering\*.md "$env:USERPROFILE\.kiro\steering\"
   ```

4. *(可选)* 参考 [`settings/kiroignore.example`](settings/kiroignore.example) 与 [`settings/mcp.example.json`](settings/mcp.example.json) 配置本地忽略清单与 MCP 环境变量鉴权：
   - [`settings/mcp.example.json`](settings/mcp.example.json) 使用了 `${CONTEXT7_API_KEY}` 变量展开；
   - **首次使用未批准的环境变量时，Kiro 会弹出安全确认提示**——请先在系统/用户环境变量中配置 `CONTEXT7_API_KEY`，并在 Kiro 弹窗时批准使用该变量。

---

## 规则校验与回归测试

每次修改 `permissions.yaml` 后，建议运行仓库自带的自动化回归测试（依赖 `PyYAML`）：

```powershell
python -m pip install pyyaml
python -m unittest discover -s tests -v
```

测试脚本 [`tests/test_permissions.py`](tests/test_permissions.py) 会验证 YAML 解析、`fs_read`/`fs_write` 凭据保护一致性、PowerShell 常见小写镜像、`cmd /c`/`/C` 包装命令、`git` 规则以及已知 Kiro 限制边界。

---

## License

[MIT](LICENSE) © 2026 [YOIMIYA66](https://github.com/YOIMIYA66)
