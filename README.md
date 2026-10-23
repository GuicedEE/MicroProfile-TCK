# GuicedEE MicroProfile TCK

Official TCK modules, a diagnostic GuicedEE deployment adapter, and a durable baseline of failures to investigate before changing GuicedEE functionality.

## Coverage

The reactor contains a shared harness and 26 suite modules. [matrix.json](matrix.json) pins every coordinate, version and engine. [reports/inventory.json](reports/inventory.json) records upstream JAR hashes, concrete test candidates and annotated methods. Factories and data providers determine actual invocation counts at runtime.

| Area | Modules |
| --- | --- |
| MicroProfile platform components | Config, Health, Fault Tolerance, JWT, OpenAPI, REST Client |
| Telemetry | Tracing, metrics, logs |
| Additional specifications | Context Propagation, GraphQL, Reactive Messaging, Reactive Streams Operators, LRA |
| Legacy Metrics | API, REST, optional |
| Jakarta Core prerequisites | Core integration, CDI Lite, CDI language model, REST, JSON-B, JSON-P, JSON-P pluggability, injection, annotations signatures |

The platform reference is [MicroProfile 7.1](https://microprofile.io/releases/7-1/). JWT 2.2 follows GuicedEE's current API. This is a diagnostic matrix, not a claim that GuicedEE's Jakarta API versions align with Core Profile 10. The signature check makes that mismatch visible. Jakarta REST runs the full published test artifact, a superset of Core requirements. CDI Lite uses the official Core Profile selection, excluding upstream `cdi-full` and `se` groups.

## Run

Requires JDK 25, Maven and Python 3.11+. The initial baseline used Maven 4.0.0-rc-6 and Oracle JDK 25. Run from this repository:

```sh
python scripts/prepare_core.py
python scripts/inventory.py
python scripts/validate.py
mvn -B -ntp -pl harness -am install -DskipTests
mvn -B -ntp -fae test-compile
python scripts/run_tcks.py --jobs 2
```

The harness installation builds infrastructure only. The final command runs the actual TCKs, continues through failures, and returns nonzero for failures, timeouts, skips or missing results. Every run uses a fresh report directory. JVMs are forked per test class with a 240-second fork timeout; a suite defaults to 30 minutes. Timeouts remain failures.

```sh
python scripts/run_tcks.py --suite config --suite health --run-id config-health
python scripts/run_tcks.py --suite jwt --port-base 19080 --run-id jwt-investigation
```

Use nonoverlapping port ranges for simultaneous runner processes. Individual suites can run with `mvn -f <suite>/pom.xml test` after installing the harness. A Maven `-Dtest=...` filter is an investigation tool, not a complete baseline.

## Evidence

- [Baseline results](reports/baseline-2026-10-23/README.md)
- [Work register](reports/WORK_REGISTER.md)
- Raw logs, XML, dumps, classpaths, dependency hashes and environment metadata: `target/runs/<run-id>/`.
- GitHub Actions runs the matrix, stays red on failures, and uploads evidence even when the test step fails.

Retain a new baseline with completed run IDs in order; later records replace earlier records for a suite:

```sh
python scripts/record_baseline.py --run <run-id> --output reports/<baseline-name>
```

The recorder refuses an incomplete suite set. Lifecycle failures, skipped methods, unobserved classes and blocked factories are not counted as specification passes.

## Harness boundaries

The Arquillian adapter starts the real GuicedEE runtime, exports official deployment archives, enriches test objects through its injector, and exposes HTTP metadata. It does not add replacement CDI, REST Client, JSON-B or Reactive Streams implementations.

This first adapter is diagnostic, not certification-ready. It uses a classpath and parent-first deployment loader. It does not yet isolate deployment classes from the entire TCK JAR, provide separate server JVMs for multiple deployments, implement web.xml semantics, or implement the CDI TCK vendor porting SPI. These are explicit work-register items. A second deployment fails because GuicedEE shutdown is terminal. Isolation acceptance tests are required before passing assertions can support compatibility claims.

Some upstream TCKs declare their APIs as provided dependencies. The harness supplies these test APIs, not implementations; their presence does not prove GuicedEE bundles them. The signature suite separately checks the annotations API version currently supplied by GuicedEE.

`prepare_core.py` downloads the [official Core Profile distribution](https://download.eclipse.org/jakartaee/coreprofile/10.0/jakarta-core-profile-tck-10.0.1.zip), verifies its pinned SHA-256 and installs its support artifacts locally. Upstream binaries and tests are not rewritten or committed.

## Change policy

During baseline establishment, edit this repository only. GuicedEE implementation repairs are a later phase. Do not suppress failures, introduce reference implementations to obtain green results, or treat missing reports as success. Distinguish harness defects, API-version mismatches and confirmed runtime failures.

## DevSuite and license

```sh
git submodule update --init GuicedEE/microprofile-tck
```

DevSuite pins an exact commit; the submodule tracks master. This reactor is intentionally outside ordinary DevSuite packaging profiles so a compatibility failure does not prevent collecting other results.

Apache License 2.0; see [LICENSE](LICENSE). Official TCK artifacts retain their own licenses.
