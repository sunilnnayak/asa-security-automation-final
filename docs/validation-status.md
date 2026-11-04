# Validation status

This document separates checks performed in the local preparation environment from checks that must run on GitHub-hosted runners. A committed historical scanner report is not proof that the current commit passed a fresh scan.

## Local source checks

| Check | Result | Evidence / limitation |
|---|---|---|
| Python syntax compilation | Passed | `python -m compileall -q app tests` |
| JavaScript syntax | Passed | `node --check` for notification service source files |
| CI workflow YAML parsing | Passed locally | Workflow structure parsed during preparation; GitHub Actions execution is still required |
| Python pytest suite | Blocked | Project dependencies were not installed in the local environment; package installation was unavailable |
| Node.js tests | Not run | Node.js is installed, but `npm ci --offline` failed because required packages were not cached and outbound package access is unavailable |
| Docker build/run | Not run | Docker CLI/daemon unavailable locally |
| Helm lint/template | Not run | Helm CLI unavailable locally |
| Fresh SAST/SCA/container/IaC scans | Not run | Scanner CLIs unavailable locally |

## GitHub Actions workflow

The workflow `.github/workflows/ci.yml` has been added and subsequently improved. It runs on pushes, pull requests and manual dispatch, and defines eight independent jobs:

- Python API tests
- Node.js notification tests
- Bandit SAST
- pip-audit Python SCA
- npm audit Node.js SCA
- Trivy container scanning
- Checkov IaC scanning of Helm-rendered Kubernetes manifests
- Helm lint and template validation

The Python and Node dependency audits are separate jobs so a failing Python audit does not prevent the Node audit from running. Scanner versions were refreshed to Bandit 1.9.4, pip-audit 2.10.1, Checkov 3.4.3 and Trivy Action v0.36.0. The Checkov job renders the Helm chart first and fails if Checkov evaluates zero resources. Scanner JSON reports are uploaded as workflow artifacts. High/critical Bandit, npm audit and Trivy findings are configured to fail their respective jobs; pip-audit and Checkov also fail on scanner findings or execution errors.

**Important:** adding the workflow does not mean it has passed. Open the repository's Actions tab and inspect the run for the latest commit. Resolve failures and regenerate reports against the final code before describing the pipeline as green.

## Historical scanner snapshots (2026-11-04)

The reports already present under `reports/` are historical snapshots, not fresh results for the current commit:

| Report | Recorded result | Assessment |
|---|---|---|
| Bandit | 1 LOW finding; 0 HIGH | Review the low-severity finding |
| pip-audit | 67 vulnerability records | Dependency gate requires remediation and a fresh audit |
| npm audit | 11 vulnerable packages: 1 CRITICAL, 5 HIGH, 2 MODERATE, 3 LOW | High/critical dependency gate requires remediation |
| Trivy | 510 vulnerability records, including 12 CRITICAL and 99 HIGH | Historical image scan is not proof that the current image is clean |
| Checkov | 0 resources evaluated | Not a valid clean result; the updated CI job renders the Helm chart and requires Checkov to evaluate at least one Kubernetes resource |

The Python dependency manifest was refreshed to remove the vulnerable `python-jose` package in favour of PyJWT, upgrade FastAPI and python-multipart, and update test/runtime dependencies. The Docker base tag was moved to the maintained Python 3.11 Bookworm image. These changes have not yet been verified by a fresh pip-audit or runtime test.

The npm audit and Checkov JSON snapshots were normalized to UTF-8 for easier tooling interoperability. Their findings and timestamps were not changed; they remain historical results.

## Required before final submission

1. Open GitHub Actions and confirm the workflow triggered for the latest commit.
2. Fix Python and Node test failures, if any.
3. Resolve high/critical dependency and image findings, then rerun the SCA and Trivy scans.
4. Confirm Checkov evaluates a non-zero number of rendered Kubernetes resources and review its findings.
5. Confirm Helm lint and template rendering succeed.
6. Replace historical scanner snapshots with fresh artifacts/reports where appropriate and update `docs/findings.md` and `docs/executive-summary.md` from the new evidence.
7. Do not claim production readiness while the notification service's SSRF/authorization risks and operational controls remain outstanding.

No scanner results have been fabricated or marked clean without execution.
