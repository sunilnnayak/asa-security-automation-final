# Assignment submission notes

## Repository

Submit this GitHub repository URL:

https://github.com/sunilnnayak/asa-security-automation-final

The default branch is `main`.

## Included deliverables

- FastAPI VulnTracker application with the shared-report-link feature.
- Security remediations documented in `docs/findings.md`.
- Remediation and residual-risk plan in `docs/remediation-plan.md`.
- Executive security summary in `docs/executive-summary.md`.
- Dockerfile with non-root runtime user and health check.
- Helm deployment baseline with pod/container hardening, NetworkPolicy and External Secrets integration.
- Python and Node.js tests.
- GitHub Actions workflow for tests, SAST, Python/Node SCA, container scanning, IaC scanning and Helm validation.
- Dependabot configuration for Python, Node.js and GitHub Actions dependencies.
- Refreshed Python dependency pins and replaced python-jose with PyJWT; fresh tests and SCA confirmation are pending.
- Historical scanner JSON snapshots under `reports/`.
- Validation limitations and required follow-up steps in `docs/validation-status.md`.

## Verification status at submission time

The source tree passed Python bytecode compilation and JavaScript syntax checks in the preparation environment. Python dependency pins were refreshed, including replacing python-jose with PyJWT, but the updated dependencies could not be installed and runtime tests could not be repeated locally. The GitHub Actions workflow has been committed, but its latest execution has not been independently verified here.

The scanner reports in `reports/` are historical snapshots dated 2026-11-04. They are not a fresh scan of the latest commit. They show outstanding dependency and container findings, and the historical Checkov report evaluated zero resources. The updated workflow now checks rendered Kubernetes manifests and fails if zero resources are evaluated.

Local runtime tests, Docker build, Helm validation and fresh scanner runs could not be completed in the preparation environment because required packages/tools were unavailable and package downloads were not possible.

## Known residual risks

- Notification service webhook SSRF protections are not implemented.
- Notification service routes still need authentication and authorization.
- Dependency and base-image vulnerabilities need remediation and fresh scans.
- Production deployment still requires credential rotation, managed database migrations, distributed rate limiting, TLS, audit logging and tested backups.

The project must not be represented as production-ready or as having a green security pipeline until the latest GitHub Actions run and fresh scan artifacts have been reviewed.

## Suggested submission message

> Please find my Application Security Automation assignment in the repository below:
>
> https://github.com/sunilnnayak/asa-security-automation-final
>
> The repository includes the application changes, security findings and remediation plan, Docker and Helm deployment artifacts, automated tests, and a GitHub Actions security pipeline covering SAST, SCA, container and IaC scanning. The validation document transparently records the checks completed and the remaining items requiring execution or remediation.
