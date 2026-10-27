"""The secret scanner must catch planted secrets and ignore placeholders."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_secrets.py"
spec = importlib.util.spec_from_file_location("check_secrets", SCRIPT)
assert spec and spec.loader
check_secrets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_secrets)


def labels(text: str) -> list[str]:
    return [label for _, label in check_secrets.scan_text(text)]


def test_detects_github_token_shape() -> None:
    fake = "ghp_" + "A" * 36  # synthetic, built at runtime so this file stays clean
    assert "GitHub token" in labels(f"token value {fake}")


def test_detects_private_key_block() -> None:
    marker = "-----BEGIN " + "RSA PRIVATE" + " KEY-----"  # assembled at runtime
    assert "Private key block" in labels(marker)


def test_detects_quoted_credential_assignment() -> None:
    value = "Xk29sLq0" + "PzT7vRw1"  # synthetic
    line = "DB_PASSWORD = " + chr(34) + value + chr(34)
    assert "Quoted credential assignment" in labels(line)


def test_ignores_placeholders_and_env_lookups() -> None:
    assert labels("SECRET_KEY=replace-with-a-long-random-unique-value") == []
    assert labels("DB_PASSWORD: ci-only-not-a-secret") == []
    assert labels('SECRET_KEY = os.environ.get("SECRET_KEY", "")') == []


def test_findings_never_contain_the_secret_value() -> None:
    fake = "ghp_" + "B" * 36
    assert all(fake not in str(f) for f in check_secrets.scan_text(fake))


def test_repository_is_clean() -> None:
    assert check_secrets.scan_repo(SCRIPT.parent.parent) == []
