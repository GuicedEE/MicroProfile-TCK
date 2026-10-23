# Baseline: 23 October 2026

GuicedEE 2.4.1; Java 25. No GuicedEE implementation fixes applied.

This is a composite diagnostic baseline. Each suite names its exact run; corrected harness runs replace earlier wiring failures. Raw test counts include lifecycle/configuration entries emitted by the upstream test engines. They are not a count of specification assertions.

| Suite | Status | Passed | Failed | Skipped |
| --- | --- | ---: | ---: | ---: |
| config | FAILED | 0 | 34 | 779 |
| health | FAILED | 0 | 20 | 84 |
| fault-tolerance | FAILED | 0 | 117 | 1019 |
| jwt | FAILED | 41 | 42 | 332 |
| openapi | FAILED | 0 | 27 | 645 |
| rest-client | FAILED | 0 | 66 | 435 |
| context-propagation | FAILED | 0 | 5 | 72 |
| graphql | FAILED | 0 | 1 | 310 |
| reactive-messaging | FAILED | 0 | 48 | 0 |
| reactive-streams | BLOCKED_NO_RESULTS | 0 | 0 | 0 |
| lra | FAILED | 5 | 8 | 0 |
| metrics-api | FAILED | 0 | 40 | 0 |
| metrics-rest | FAILED | 0 | 51 | 0 |
| metrics-optional | FAILED | 0 | 2 | 0 |
| telemetry-tracing | FAILED | 0 | 10 | 36 |
| telemetry-metrics | FAILED | 0 | 15 | 54 |
| telemetry-logs | FAILED | 0 | 2 | 6 |
| core-profile | FAILED | 0 | 4 | 0 |
| cdi-lite | BLOCKED_NO_RESULTS | 0 | 0 | 0 |
| cdi-lang-model | FAILED | 0 | 1 | 2 |
| jakarta-rest | FAILED | 517 | 660 | 1 |
| jsonb | FAILED | 25 | 268 | 2 |
| jsonp | FAILED | 18 | 161 | 0 |
| jsonp-pluggability | PASSED_DIAGNOSTIC | 18 | 0 | 0 |
| jakarta-inject | FAILED | 0 | 1 | 0 |
| annotations-signature | FAILED | 0 | 1 | 0 |

## Tracking records

- [Per-test records](cases.jsonl): every reported test/lifecycle result.
- [Open findings](findings.json): failure signatures and affected tests; no failures have been waived.
- [Coverage](summary.json): unobserved classes, factory/group selections, status and run provenance.
- [Upstream inventory](inventory.json): artifact coordinates, checksums and annotated methods.
- [Evidence hashes](provenance.json): exact commands and hashes of raw reports retained under `target/runs/`.
- [Run environments](environments.json): Java, Maven, matrix and working-tree state captured when each run began.
- [Work register](../WORK_REGISTER.md): shared harness and runtime investigation items.

All results are diagnostic. The embedded adapter has deployment-isolation limitations; blocked, skipped and unobserved tests prevent a compatibility claim.

## Run interventions

- rest-client: ReactiveStreamsPublisherTckTest exceeded the configured 240 second fork limit. Specific fork PID 69696 stopped after thread capture; remaining tests may continue. This class is incomplete, not passed.
