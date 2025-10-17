# Contributing Guidelines

Thank you for your interest in improving the Okta SSO for Studio Tools sample. This document outlines the process for contributing code, documentation, or tests.

## How to Contribute
1. **Fork and clone** the repository.
2. **Create a feature branch** for your change.
3. **Install dependencies** with `npm install`.
4. **Run `npm test`** to ensure the existing test suite passes before making changes.
5. **Add or update tests** that cover your change.
6. **Document updates** in the README or inline JSDoc comments where appropriate.
7. **Submit a pull request** describing the change and relevant test results.

## Coding Standards
- Use modern JavaScript (ES2019+) and adhere to the existing code style.
- Provide JSDoc-style comments for functions and middleware.
- Ensure linting passes if additional tooling is introduced.

## Security Considerations
- Never commit real Okta credentials or secrets.
- Discuss substantial authentication or authorization changes in the pull request for peer review.

## Communication
For significant proposals, open an issue to discuss design choices before implementation.
