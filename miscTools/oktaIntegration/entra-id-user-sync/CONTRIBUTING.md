# Contributing

Contributions are welcome! Please follow the process below to ensure a smooth review:

1. Fork the repository and create a feature branch.
2. Execute `python -m pytest` to confirm the static tests pass before submitting changes.
3. Where possible, add or update Pester tests to cover PowerShell logic changes.
4. Document user-facing modifications in the README or inline comment-based help.
5. Submit a pull request with a concise summary and any relevant security considerations.

## Coding Style
- Prefer advanced PowerShell functions with `[CmdletBinding()]` when expanding functionality.
- Maintain comment-based help sections (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`).
- Use `Set-StrictMode -Version Latest` in future enhancements to encourage robust scripts.

## Security
Avoid committing credentials or secrets. Use placeholders and environment-based configuration for testing.
