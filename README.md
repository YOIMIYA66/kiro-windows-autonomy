# Kiro Windows Autonomy

[English](README_EN.md) | 简体中文

一套面向 Windows 11 环境的 **Kiro IDE** 规则驱动自治配置（Rule-Driven Autonomy），包含经过实战验证的 [`permissions.yaml`](settings/permissions.yaml) 权限护栏、[`steering/`](steering/) 工程规范，以及自动化回归测试。

> **定位说明**：本配置是**防误操作的便利性护栏（convenience guardrail）**，而非可靠的安全沙箱或系统级安全边界。

---

## 核心优势

1. **告别弹窗疲劳，保留关键刹车（Rule-Driven Autonomy）**
   - 用基线 `capability: all -> allow`（不含 `sandbox_network`）替代 Kiro 默认的概率分类器（`evaluate`），日常读写代码、跑构建和测试、执行只读查询（`git status`、`Get-NetFirewallRule`、`netsh advfirewall show` 等）**全程零打扰自动放行**。
   - 仅在读取/写入敏感凭据、修改系统目录或执行破坏性命令与危险 Git 操作时弹出确认。

2. **专为 Windows 11 + PowerShell 深度避坑**
   - **缓解大小写绕过**：Kiro 的 `shell` 规则区分大小写，而 PowerShell 与 `cmd` 不区分大小写。配置内置高危 PowerShell Cmdlet 全小写镜像及 `cmd /c`、`/C`、`/k`、`/K` 常见包装拦截，缓解已知全小写绕过。
   - **解决 PS 5.1 / 7 混用报错**：默认按 Windows PowerShell 5.1 兼容性约束脚本写法，禁用仅 PS 7 支持的语法糖（`??`、`&&`、`-Encoding utf8NoBOM` 等）。
   - **根治 UTF-8 BOM 与 GBK (CP936) 乱码**：明确 `.ps1`（UTF-8 with BOM 或纯 ASCII）与 `.bat`（纯 ASCII + CRLF）编码规范，避免中文脚本在中文版 Windows 上语法崩坏，并要求对 `.ps1` 运行 `Parser::ParseFile` 与 `PSScriptAnalyzer` 校验。

3. **高信噪比工程纪律（Steering 规范）**
   - 强制先取证复现再动手修复、禁止空 `catch {}` / `2>$null` 静默吞异常、禁止篡改测试凑通过。
   - 改动超过 3 个文件或涉及系统配置前先出可回滚方案；明确划定本地防火墙、DNS、路由与代理配置的只读红线，防止 AI 排障时擅自改坏网络栈。

4. **自带回归测试与 GitHub Actions CI**
   - 提供 [`tests/test_permissions.py`](tests/test_permissions.py) 自动化测试套件，覆盖 YAML 语法、`fs_read`/`fs_write` 凭据对称性、`sandbox_network` 隔离校验、PowerShell 小写镜像、包装命令及已知边界限制，改规则不怕改坏。

---

## 一键安装：直接复制给 AI 的提示词

如果你已经装好 Kiro（或其他本地 AI 编程助手），可以直接复制下方提示词发送给 AI，让它自动备份你现有的 `~/.kiro` 配置、拉取本仓库、按你的本机环境定制并完成验证：

```text
请帮我安装并适配 https://github.com/YOIMIYA66/kiro-windows-autonomy 仓库中的 Kiro Windows 配置，按以下顺序执行：

1. 先备份我现有的 `%USERPROFILE%\.kiro\settings` 和 `%USERPROFILE%\.kiro\steering`（如果存在），备份目录命名为 `.bak-YYYYMMDD` 并告诉我回滚方式。
2. 将 `https://github.com/YOIMIYA66/kiro-windows-autonomy.git` 克隆到临时目录（例如 `%USERPROFILE%\.kiro\_upstream-kiro-windows-autonomy`）。
3. 复制 `settings/permissions.yaml` 到 `%USERPROFILE%\.kiro\settings\permissions.yaml`：
   - 保留所有默认护栏规则。
   - 检查我本机是否有需要额外保护的目录（例如防火墙/代理脚本目录），先向我确认后再取消注释或添加到 `fs_write` 规则中。
4. 复制 `steering/*.md` 到 `%USERPROFILE%\.kiro\steering\`：
   - 检测我本机实际安装的工具链（Git、Go、Python/uv/conda、Node.js/pnpm、.NET、Java、PSScriptAnalyzer 等版本与路径）和当前代理设置，据此定制 `steering/windows-environment.md`（不要把未安装的软件写进去，也不要泄露或写入任何密钥/节点/订阅数据）。
   - 检查 `steering/personal-preferences.md` 是否符合我的回复语言偏好。
5. 如果我使用了 `mcp.json` 或需要忽略本地敏感数据库，向我说明如何参考 `settings/kiroignore.example` 和 `settings/mcp.example.json`（注意 `${CONTEXT7_API_KEY}` 等环境变量首次使用会在 Kiro 中触发审批提示）。
6. 在仓库目录运行 `python -B -m unittest discover -s tests -v`（如缺少 PyYAML 请先询问我或使用虚拟环境），并对安装后的 `%USERPROFILE%\.kiro\settings\permissions.yaml` 做一次 YAML 语法校验，最后向我汇报：备份位置、修改/复制了哪些文件、测试与校验结果。
```

---

## 手动安装指南

> [!TIP]
> 在覆盖之前，建议先备份你原有的 `%USERPROFILE%\.kiro` 相关文件。

### 第 1 步：备份原有配置并克隆仓库

```powershell
$kiroDir = "$env:USERPROFILE\.kiro"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (Test-Path "$kiroDir\settings") { Copy-Item -Recurse "$kiroDir\settings" "$kiroDir\settings.bak-$stamp" }
if (Test-Path "$kiroDir\steering") { Copy-Item -Recurse "$kiroDir\steering" "$kiroDir\steering.bak-$stamp" }

git clone https://github.com/YOIMIYA66/kiro-windows-autonomy.git
cd kiro-windows-autonomy
```

### 第 2 步：安装 `permissions.yaml`

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kiro\settings" | Out-Null
Copy-Item .\settings\permissions.yaml "$env:USERPROFILE\.kiro\settings\permissions.yaml"
```

*(可选)* 打开 `%USERPROFILE%\.kiro\settings\permissions.yaml`，根据你本机实际目录取消注释或新增受保护路径（如 `C:/AI-Net-Guard/**` 或本地代理软件配置目录）。

### 第 3 步：安装并定制 `steering/` 规范

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kiro\steering" | Out-Null
Copy-Item .\steering\*.md "$env:USERPROFILE\.kiro\steering\"
```

建议按需调整以下两份文件：
- `%USERPROFILE%\.kiro\steering\windows-environment.md`：把 `## Toolchain` 和 `## Protected locations` 改成你本机实际的开发工具和只读目录。
- `%USERPROFILE%\.kiro\steering\personal-preferences.md`：调整回复语言（默认简体中文）或汇报格式偏好。

### 第 4 步：*(可选)* 配置忽略规则与 MCP 环境变量

参考 [`settings/kiroignore.example`](settings/kiroignore.example) 与 [`settings/mcp.example.json`](settings/mcp.example.json)：
- 如果你使用 `mcp.example.json` 中的 `${CONTEXT7_API_KEY}` 变量展开，请先在系统/用户环境变量中设置 `CONTEXT7_API_KEY`；
- **首次使用未批准的环境变量时，Kiro 会弹出安全确认提示**，在弹窗中点击批准后即可正常使用。

---

## 目录结构

```text
.
├── .github/workflows/
│   └── ci.yml                  # YAML 语法与权限匹配回归测试 CI
├── .gitignore                  # 忽略本地 Python 测试字节码缓存
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

## 规则原理与边界说明

### 1. 为什么采用「全量放行 + 显式 `ask` 护栏」？

Kiro 的权限优先级为：`deny > ask > allow > evaluate`。
基线规则设置：

```yaml
- capability: all
  effect: allow
```

使 `evaluate` 分类器不再介入（注：按 [Kiro 官方权限文档](https://kiro.dev/docs/permissions/)，`capability: all` **不包含 `sandbox_network`**），转而用确定性的 `ask` 规则清单降低日常误操作风险。

### 2. 三维防护范围

- **`fs_read`（敏感文件读取确认）**：拦截读取 `.ssh`、`.aws`、`.kube`、`.docker/config.json`、`.env` / `.env.*`（放行 `.env.example`）、私钥证书（`.pem` / `.key` / `.pfx` / `.p12`）、Git 凭据及 GitHub CLI 配置（`~/AppData/Roaming/GitHub CLI/**` 与 `~/.config/gh/**`）。
- **`fs_write`（敏感与系统目录写入确认）**：除上述凭据目录外，额外拦截写入 `~/.gitconfig`、`C:/Windows/**`、`C:/Program Files/**`、`C:/Program Files (x86)/**`、`C:/ProgramData/**` 以及你自定义的受保护服务目录。
- **`shell`（高危命令确认）**：覆盖破坏性文件/磁盘命令、注册表与 ACL、服务与计划任务、防火墙/DNS/路由/代理修改、危险 Git 操作（单独放行 `git restore --staged *`）、进程终止/提权/远端删除，以及常见的 `powershell` / `pwsh` / `cmd` 内联包装命令。

### 3. 踩坑与局限：缓解已知的全小写绕过（非安全边界）

实测发现 **Kiro 的 `shell` 模式匹配是区分大小写的**（例如配置了 `Set-Acl *`，但执行全小写的 `set-acl ...` 会跳过提示），而 PowerShell 与 `cmd` 本身不区分大小写。

为此，[`settings/permissions.yaml`](settings/permissions.yaml) 末尾补充了标准 PowerShell Cmdlet 的全小写镜像以及常见的 `cmd /C`、`/K` 变体，用来**缓解已知的全小写绕过**。

> **重要局限**：镜像规则无法实用地穷举所有混合大小写组合（如 `sEt-aCl`、`CmD /c`），**Kiro 的大小写敏感匹配仍可能留下未覆盖的变体**；同时规则只匹配命令文本本身，无法检查 `.ps1` / `.bat` / `.py` 脚本内部、完整绝对路径/别名调用或变量拼接传递的参数。请始终将其视为**防误操作的便利性护栏**，切勿依赖它替代操作系统权限控制或网络隔离。

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

## 规则校验与回归测试

每次修改 `permissions.yaml` 后，建议运行仓库自带的自动化回归测试（依赖 `PyYAML`）：

```powershell
python -m pip install pyyaml
python -m unittest discover -s tests -v
```

测试脚本 [`tests/test_permissions.py`](tests/test_permissions.py) 会验证 YAML 解析、`capability: all` 不包含 `sandbox_network`、`fs_read`/`fs_write` 凭据保护一致性、PowerShell 常见小写镜像、`cmd /c`/`/C` 包装命令、`git` 规则以及已知 Kiro 限制边界。

---

## License

[MIT](LICENSE) © 2026 [YOIMIYA66](https://github.com/YOIMIYA66)
