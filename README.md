# VulnTracker — Security Automation Engineer Assignment

This repository contains the VulnTracker FastAPI service, the supplied Node.js notification service, the shared-report-link feature, security remediations, a hardened Dockerfile, a Helm deployment baseline, and security-assessment documentation.

## Implementation decisions

- **Shared URL base:** `PUBLIC_BASE_URL` is used to construct share URLs. It defaults to `http://localhost:8000` for the prototype. Set it to the externally reachable HTTPS origin in a real deployment. This avoids trusting an arbitrary incoming `Host` header.
- **Share token:** 32 bytes of cryptographically secure randomness (`secrets.token_urlsafe(32)`). Only the SHA-256 digest is stored; the raw token is returned once.
- **Expiry:** Share grants expire 24 hours after creation. Expired or unknown grants return the same `404` response.
- **Optional password:** Share passwords are bcrypt-hashed and never stored in plaintext. The endpoint rejects passwords exceeding bcrypt's 72-byte input limit. Password-protected links require the `password` query parameter as specified by the assignment.
- **Public response:** The shared endpoint uses a restricted response schema and does not disclose the scan owner's internal user ID.
- **Search:** SQL is parameterised and search results are scoped to the authenticated owner.
- **JWT:** Only HS256 is accepted. `SECRET_KEY` must be provided at runtime and must contain at least 32 characters.
- **CORS:** The unsafe wildcard/reflected-origin credentialed CORS middleware has been removed. Add a strict explicit allowlist only if a browser frontend is introduced.

## Requirements

- Python **3.11** (the CI workflow uses this exact minor version)
- Node.js 20+ (only needed for the notification service tests)
- Docker (for image build/run)
- Helm 3 (for chart validation)

## Run the Python API locally

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PUBLIC_BASE_URL="http://localhost:8000"
cd app
uvicorn main:app --reload
```

On Windows PowerShell, set the secret with:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:PUBLIC_BASE_URL = "http://localhost:8000"
cd app
uvicorn main:app --reload
```

API documentation: <http://localhost:8000/docs>

## Run tests

Run Python tests from the repository root:

```bash
pytest tests/ -v
```

Run notification service tests (the supplied service is unchanged):

```bash
cd notify
npm ci
npm test
```

## Shared report API usage

Create a scan and authenticate as its owner. Then generate a link:

```http
POST /scans/{scan_id}/share
Authorization: Bearer <access-token>
Content-Type: application/json

{}
```

Or enable password protection:

```json
{"password":"A-long-unique-password"}
```

The response is:

```json
{"share_url":"http://localhost:8000/share/<opaque-token>"}
```

The recipient opens the URL without a bearer token. For a protected share, supply the password using the `password` query parameter, as required by the assignment. Because query strings can be captured by browser history, reverse-proxy access logs and monitoring systems, production deployments must redact this parameter at every logging layer and use HTTPS. A production design could instead accept the password in a POST body, but that would change the specified GET contract.

## Docker build and run

Build from the repository root:

```bash
docker build -t vulntracker:1.0.0 .
```

Run the container with a runtime secret (never bake it into the image):

```bash
docker run --rm --name vulntracker \
  -p 8000:8000 \
  -e SECRET_KEY="replace-with-a-random-secret-of-at-least-32-characters" \
  -e DATABASE_URL="sqlite:////tmp/vulntracker.db" \
  -e PUBLIC_BASE_URL="http://localhost:8000" \
  vulntracker:1.0.0
```

Verify `http://localhost:8000/health`. The image runs as UID 10001 and includes a Docker `HEALTHCHECK`. For persistent production data, use managed PostgreSQL and a managed secret store rather than container-local SQLite.

## Helm deployment

The chart is under `helm/vulntracker`. It expects an existing Kubernetes `ClusterSecretStore` named `aws-secrets-manager` backed by AWS Secrets Manager and an External Secrets Operator installation. The remote secret `production/vulntracker` must contain `SECRET_KEY` and `DATABASE_URL` properties. Configure `publicBaseUrl` to the externally reachable HTTPS origin, enable/configure ingress if needed, and set the database CIDR for the target environment.

Validate locally:

```bash
helm lint helm/vulntracker
helm template vulntracker helm/vulntracker
```

The chart configures non-root execution, a runtime-default seccomp profile, dropped Linux capabilities, no service-account token mount, a read-only root filesystem, resource requests/limits, health probes, and a NetworkPolicy. The default Service is ClusterIP; expose it only through an approved ingress controller and TLS configuration.

## Security scanning

The selected tools are:

| Category | Tool | Scope |
|---|---|---|
| SAST | Bandit | Python application source (`app/`) |
| SCA | pip-audit and npm audit | Python requirements and Node lockfile |
| Container | Trivy | Built FastAPI image |
| IaC | Checkov | Helm chart |

Run the scans after the final code and deployment artifacts are ready:

```bash
mkdir -p reports
bandit -r app -f json -o reports/sast.bandit.json
pip-audit -r requirements.txt -f json -o reports/sca.pip-audit.json
(cd notify && npm audit --json > ../reports/sca.npm-audit.json || true)
docker build -t vulntracker:1.0.0 .
trivy image --format json --output reports/container.trivy.json vulntracker:1.0.0
checkov -d helm/vulntracker -o json --output-file-path reports/iac.checkov.json
```

Do not invent or hand-author scanner results. Commit the raw reports generated by these commands and update `docs/findings.md` with the scanner-confirmed results and your manual findings. A scanner's absence of findings is not proof that the application is secure.

## Documentation

- `docs/findings.md` — prioritised source-review findings; update with real scan evidence.
- `docs/remediation-plan.md` — fixes, residual risks and compensating controls.
- `docs/executive-summary.md` — business-oriented security posture and recommendations.

## Important production limitations

This is a take-home prototype, not a production security certification. The Node.js notification service remains unchanged per the assignment scope and still requires authentication, webhook destination allowlisting/SSRF controls, and secret rotation before exposure. Production also requires distributed rate limiting, database migrations, managed PostgreSQL, audit logging, TLS, backup/restore testing, and secret rotation. The `password` query parameter must be redacted from access logs. Rotate credentials that appeared in the starter repository and consider removing them from Git history.

## Windows PowerShell helper scripts

From the repository root, `scripts/validate.ps1` installs the pinned Python dependencies, runs the Python and Node test suites, builds the Docker image, and validates the Helm chart. Run it from a PowerShell terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\validate.ps1
```

After installing Bandit, pip-audit, Trivy, Checkov, Docker and Node.js, generate the required raw scan outputs with:

```powershell
.\scripts\run-security-scans.ps1
```

Review the exit code and output of every scanner. A scanner may return a non-zero code because it found vulnerabilities or because it failed to run; neither case should be represented as a clean scan. Validate that the JSON files are complete before committing them. The scripts do not manufacture reports.
