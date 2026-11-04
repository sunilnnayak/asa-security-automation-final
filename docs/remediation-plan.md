# Remediation plan and residual risk

## Deferred items

| Finding | Residual risk | Why not fully remediated in this submission | Compensating controls / next action |
|---|---|---|---|
| Notification webhook SSRF (F-09) | A user able to register a webhook may cause requests to internal services or metadata endpoints. DNS rebinding and redirect handling make naive URL checks insufficient. | Requires a dedicated outbound-request security design and integration tests for DNS resolution, redirects, IPv4/IPv6 and cloud metadata ranges. | Restrict service network egress at the cluster/firewall; only trusted administrators should reach the notification service. Implement hostname/IP allowlisting, block private/link-local/reserved ranges after DNS resolution, disable redirects, and revalidate each resolved address. |
| Notification service authentication (F-10/F-11) | Unauthenticated callers may register, enumerate, delete webhooks or trigger notifications; static key may be reused if leaked. | Notification service was identified as an additional component but is not required to be modified by the brief. | Keep it on a private network, restrict ingress to the API service, rotate the key, source it from a secret manager, authenticate service-to-service requests, and add per-webhook ownership/authorization. |
| Rate limiting and abuse controls | Login and public share-password endpoints can be brute-forced or abused for resource exhaustion. | Production-grade distributed rate limiting requires an external store/gateway and deployment-specific thresholds; a process-local counter would be bypassable across multiple replicas. | Apply API-gateway/WAF rate limits, alert on repeated failures, and add distributed rate limiting before production. |
| Share-password query-string exposure | The required GET query parameter may appear in browser history, reverse-proxy access logs, analytics and monitoring. | The assignment explicitly requires the password as a query parameter on the public GET endpoint. | Enforce HTTPS; redact `password` from all access logs and telemetry; set `Cache-Control: no-store` and `Referrer-Policy: no-referrer`; consider a POST-based password exchange in a future API version. |
| Database lifecycle and migrations | `create_all` at application startup is not a safe production schema migration strategy. SQLite is unsuitable for multi-replica production deployment. | The starter app has no migration framework or production database provisioned. | Adopt Alembic, managed PostgreSQL, backups, encryption at rest, least-privilege DB roles and tested restore procedures. |

## Operational requirements

- Rotate every credential previously committed in the starter repository; removing it from the current tree does not remove it from Git history.
- Supply `SECRET_KEY` and `DATABASE_URL` through a secret manager. The Helm chart uses External Secrets Operator with AWS Secrets Manager.
- Configure `helm/vulntracker/values.yaml` database CIDR to the actual managed database subnet range.
- Run all four required scanners against the final commit and record raw JSON output. Findings should be triaged, not blindly suppressed.
