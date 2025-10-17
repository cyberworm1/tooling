"""Static tests for sync-users.ps1 to ensure documentation and parameters remain intact."""

from pathlib import Path
import re

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "sync-users.ps1"


def test_comment_based_help_sections_present():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    required_sections = [
        ".SYNOPSIS",
        ".DESCRIPTION",
        ".PARAMETER TenantId",
        ".PARAMETER AppId",
        ".PARAMETER AppSecret",
        ".EXAMPLE",
        ".NOTES",
    ]
    for section in required_sections:
        assert section in content, f"Expected help section {section} to be present"


def test_parameters_declared():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    match = re.search(r"param\((.*?)\)\s", content, re.DOTALL)
    assert match, "param block not found"
    parameters = {"TenantId", "AppId", "AppSecret", "GroupFilter", "OutputFile", "OutputFormat"}
    for name in parameters:
        assert re.search(rf"\${name}\b", match.group(1)), f"Missing parameter {name}"


def test_logging_function_includes_timestamp():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "Write-Log" in content
    assert "Get-Date -Format 'u'" in content, "Expected UTC timestamp format in Write-Log"
