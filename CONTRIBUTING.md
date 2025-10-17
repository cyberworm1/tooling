# Contributing

Thanks for helping improve the tooling sandbox! This document captures the baseline workflow for
submitting changes.

## Getting Started

1. Install the prerequisites listed in the [repository README](README.md).
2. Create a virtual environment when working on Python code and run `pip install -r <project>/requirements.txt`.
3. For Terraform modules, authenticate with the appropriate cloud provider before running `terraform init`.

## Development Standards

* Follow Python's PEP 8 style guide. Use descriptive logging and avoid executing code at import time.
* Keep Terraform resources modular. Define variables and outputs where a consumer might need to override values.
* Update documentation and examples whenever CLI flags, variables, or resource names change.
* Provide meaningful commit messages that describe the intent of the change.

## Testing and Validation

Before opening a pull request:

* Run `python -m compileall <python-module>` for syntax validation.
* Execute available unit tests or scripts when present.
* For Terraform, run `terraform fmt -check`, `terraform validate`, and `terraform plan` in the relevant directory.

Document any manual steps, recorded outputs, or screenshots in the pull request description when they help reviewers.

## Pull Request Checklist

- [ ] Link the TODO item(s) addressed by your change.
- [ ] Describe validation steps and test outputs.
- [ ] Request a review from a domain owner (AWS, Azure, or GCP) when touching their modules.
- [ ] Ensure CI is green before requesting final approval.

Thanks again for contributing!
