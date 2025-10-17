# TODOs

- [ ] Replace the mock OIDC fallback with integration tests that exercise a real Okta tenant via the Okta Test Server or mocked responses.
- [ ] Add automated linting (ESLint + Prettier) and incorporate it into CI.
- [ ] Extend RBAC to support granular roles (e.g., Supervisors, External Vendors) pulled dynamically from Okta groups.
- [ ] Provide infrastructure-as-code examples (Terraform/Okta Workflows) to provision the Okta application automatically.
- [ ] Harden session storage by switching to a persistent store such as Redis for production deployments.
