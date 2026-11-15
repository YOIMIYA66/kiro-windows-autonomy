import fnmatch
import json
from pathlib import Path
import unittest

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PERMISSIONS_PATH = REPO_ROOT / "settings" / "permissions.yaml"
MCP_EXAMPLE_PATH = REPO_ROOT / "settings" / "mcp.example.json"

PRIORITY = {"deny": 3, "ask": 2, "allow": 1, "evaluate": 0}


def matches_rule(rule: dict, capability: str, target: str) -> bool:
    rule_cap = rule.get("capability")
    if rule_cap not in ("all", capability):
        return False
    patterns = rule.get("match")
    if not patterns:
        return rule_cap == "all" or capability == rule_cap
    if not any(fnmatch.fnmatchcase(target, pat) for pat in patterns):
        return False
    excludes = rule.get("exclude") or []
    if any(fnmatch.fnmatchcase(target, pat) for pat in excludes):
        return False
    return True


def evaluate_permission(rules: list[dict], capability: str, target: str) -> str:
    """Evaluate Kiro permission effect using deny > ask > allow > evaluate precedence."""
    winning_effect = "evaluate"
    winning_priority = PRIORITY[winning_effect]
    for rule in rules:
        if matches_rule(rule, capability, target):
            effect = rule["effect"]
            prio = PRIORITY[effect]
            if prio > winning_priority:
                winning_effect = effect
                winning_priority = prio
    return winning_effect


class PermissionsRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with PERMISSIONS_PATH.open("r", encoding="utf-8") as fh:
            cls.config = yaml.safe_load(fh)
        cls.rules = cls.config["rules"]

    def assertEffect(self, capability: str, target: str, expected: str) -> None:
        actual = evaluate_permission(self.rules, capability, target)
        self.assertEqual(
            actual,
            expected,
            f"Expected {expected!r} for ({capability}, {target!r}), got {actual!r}",
        )

    def test_yaml_schema_and_baseline(self) -> None:
        self.assertIsInstance(self.config, dict)
        self.assertIn("rules", self.config)
        self.assertEqual(self.config.get("policies"), ["approve-for-me"])
        self.assertTrue(
            any(
                r.get("capability") == "all" and r.get("effect") == "allow"
                for r in self.rules
            ),
            "Baseline all: allow rule is missing",
        )

    def test_fs_read_and_write_credential_parity(self) -> None:
        sensitive_paths = [
            "~/.ssh/id_ed25519",
            "~/.aws/credentials",
            "~/AppData/Roaming/GitHub CLI/hosts.yml",
            "~/.config/gh/hosts.yml",
            "~/.docker/config.json",
            "~/.kube/config",
            "app/.env",
            "app/.env.production",
            "certs/ca.pem",
            "certs/server.key",
            "certs/cert.pfx",
            "certs/cert.p12",
            "repo/.git-credentials",
        ]
        for path in sensitive_paths:
            self.assertEffect("fs_read", path, "ask")
            self.assertEffect("fs_write", path, "ask")

        for allowed_path in ("app/.env.example", "src/index.ts"):
            self.assertEffect("fs_read", allowed_path, "allow")
            self.assertEffect("fs_write", allowed_path, "allow")

    def test_fs_write_only_protections(self) -> None:
        protected_write_paths = [
            "~/.gitconfig",
            "C:/Windows/System32/drivers/etc/hosts",
            "C:/Program Files/App/app.exe",
            "C:/Program Files (x86)/App/app.exe",
            "C:/ProgramData/App/config.ini",
        ]
        for path in protected_write_paths:
            self.assertEffect("fs_write", path, "ask")

    def test_shell_destructive_and_lowercase_mirrors(self) -> None:
        commands = [
            "Remove-Item foo",
            "remove-item foo",
            "Set-Acl bar",
            "set-acl bar",
            "Stop-Service x",
            "stop-service x",
            "New-NetFirewallRule -Name x",
            "new-netfirewallrule -Name x",
            "Set-DnsClientServerAddress -InterfaceIndex 1",
            "set-dnsclientserveraddress -InterfaceIndex 1",
            "robocopy src dst /MIR",
            "robocopy src dst /mir",
            "Stop-Process -Id 1",
            "stop-process -Id 1",
            "Start-Process pwsh -Verb RunAs",
            "start-process pwsh -verb runas",
        ]
        for cmd in commands:
            self.assertEffect("shell", cmd, "ask")

    def test_shell_interpreter_wrappers(self) -> None:
        wrappers = [
            "powershell -Command dir",
            "powershell -command dir",
            "powershell -c dir",
            "powershell -EncodedCommand ZABpAHIA",
            "powershell -encodedcommand ZABpAHIA",
            "powershell -enc ZABpAHIA",
            "pwsh -Command ls",
            "pwsh -command ls",
            "pwsh.exe -c ls",
            "cmd /c del a",
            "cmd.exe /c del a",
            "cmd /C del a",
            "cmd.exe /C del a",
            "cmd /k echo 1",
            "cmd.exe /K echo 1",
        ]
        for cmd in wrappers:
            self.assertEffect("shell", cmd, "ask")

    def test_shell_known_kiro_limitations_documented(self) -> None:
        # Kiro shell matching is case-sensitive and matches command text only.
        # Arbitrary mixed-case variants and external script files are outside
        # static glob coverage and require steering + OS-level controls.
        self.assertEffect("shell", "sEt-aCl foo", "allow")
        self.assertEffect("shell", "powershell -File script.ps1", "allow")

    def test_shell_git_rules(self) -> None:
        ask_git = [
            "git reset --hard",
            "git clean -fd",
            "git push --force",
            "git push origin main -f",
            "git restore foo.go",
            "git restore --worktree foo.go",
            "git restore --staged --worktree foo.go",
        ]
        for cmd in ask_git:
            self.assertEffect("shell", cmd, "ask")

        allow_git = [
            "git restore --staged foo.go",
            "git status",
            "git diff",
        ]
        for cmd in allow_git:
            self.assertEffect("shell", cmd, "allow")

    def test_mcp_example_json_valid(self) -> None:
        with MCP_EXAMPLE_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        auth_header = data["mcpServers"]["context7"]["headers"]["Authorization"]
        self.assertIn("${CONTEXT7_API_KEY}", auth_header)


if __name__ == "__main__":
    unittest.main()
