# Prioritised security findings

> Preliminary manual review of the starter source. Replace/add scanner-confirmed results after running the required tools; no scanner output is represented as having run yet.

| ID | Source / detection | Severity | Finding and application-specific impact | Origin | Status |
|---|---|---:|---|---|---|
| F-01 | `app/database.py` / manual | Critical | User-controlled search text was interpolated into SQL. An authenticated user could alter the query and access or manipulate data beyond the intended search. | Starter | Fixed with bound parameters and owner scoping |
| F-02 | `app/auth.py` / manual | Critical | JWT decoder accepted `alg=none`, undermining signature verification and potentially enabling forged bearer tokens. | Starter | Fixed; only HS256 accepted |
| F-03 | `app/config.py` / manual | Critical | Static JWT key and database/service credentials were committed in source. Anyone with repository access could forge tokens or reuse credentials. | Starter | Fixed; secrets now required from environment/secret manager |
| F-04 | `app/main.py` / manual | High | Login handler logged plaintext passwords on success/failure paths. Logs could expose user credentials to operators or log-platform readers. | Starter | Fixed |
| F-05 | `app/main.py` / manual | High | Scan detail lookup did not filter by owner, enabling insecure direct object reference across tenants. | Starter | Fixed |
| F-06 | `app/main.py` / manual | High | CORS reflected arbitrary Origin values while allowing credentials. | Starter | Fixed by removing permissive CORS reflection; configure explicit allowlist if browser clients are required |
| F-07 | `app/main.py` / manual | High | Global exception response exposed stack traces, exception details and request path. | Starter | Fixed; generic response returned |
| F-08 | `app/main.py` / manual | High | Shared report URLs are bearer capabilities; leakage permits access until expiry. Passwords are accepted in the required query parameter, which can be captured by browser history and access logs. | New feature | Token entropy, digest-at-rest, 24-hour expiry, optional password hash and restricted response schema implemented; production log redaction and gateway rate limits remain required |
| F-09 | `notify/src/index.js` / manual | High | Arbitrary webhook destinations can target loopback, private networks or cloud metadata endpoints (SSRF). | Starter | Deferred; see remediation plan |
| F-10 | `notify/src/config.js` / manual | High | Internal service key is hardcoded. | Starter | Deferred; notification service is outside the required change scope; rotate and move to secret manager before production |
| F-11 | `notify/src/index.js` / manual | High | Webhook registration/list/delete and `/notify` lack authentication/authorization. | Starter | Deferred; see remediation plan |

| F-12 | `app/main.py` / manual | Medium | Public share-password verification has no distributed rate limiter in this prototype; repeated guesses could consume resources or attempt password guessing. | New feature | Deferred to API gateway/WAF or shared rate-limit store; see remediation plan |

## Scan evidence

The required SAST, SCA, container and IaC JSON reports must be generated from the completed source and committed under `reports/`. Do not treat this manual review as a substitute for those scans.
