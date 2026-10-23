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
mvn -B -ntp -pl harness -am install
mvn -B -ntp -fae test-compile
python scripts/run_tcks.py --jobs 2 --isolate-suite rest-client --isolate-suite cdi-lite
```

The harness installation builds infrastructure only. The final command runs the actual TCKs, continues through failures, and returns nonzero for failures, timeouts, skips or missing results. Every run uses a fresh report directory. Surefire is configured to fork per test class with a 240-second timeout, but the original REST Client run exceeded that limit. `--isolate-suite rest-client` enforces an outer process deadline for each selected class, kills that process tree on timeout, and continues through the full inventory. Other suites default to a 30-minute deadline. Timeouts remain incomplete results.

```sh
python scripts/run_tcks.py --suite config --suite health --run-id config-health
python scripts/run_tcks.py --suite jwt --port-base 19080 --run-id jwt-investigation
python scripts/run_classes.py --suite rest-client --jobs 4 --timeout 240 --run-id rest-client-classes
```

Use nonoverlapping port ranges for simultaneous runner processes. Individual suites can run with `mvn -f <suite>/pom.xml test` after installing the harness. A Maven `-Dtest=...` filter is an investigation tool, not a complete baseline.

Class mode derives selections from the inventory or official factory driver. For CDI Lite, the pinned TestNG engine discovers the selected methods from the unmodified official suite; generated per-class XML preserves its groups and listeners. A second discovery verifies exact method-set equality before execution. Other official XML selections and signature suites remain protected from class filtering. Compilation happens once before read-only Surefire invocations with separate reports and ports. Separate class processes do not solve archive isolation or multi-deployment semantics within a class.

CDI Lite also has a separate JPMS lane, using unchanged runtime artifacts and their actual module declarations. Arquillian remains on the test classpath:

```sh
python scripts/prepare_jpms.py
python scripts/run_tcks.py --suite cdi-lite --isolate-suite cdi-lite --run-id cdi-jpms --port-base 29080 --jvm-args-file target/jpms-cdi/jvm.args
```

The porting adapters delegate serialization, context lookup and EL access where possible. Proxy introspection and context lifecycle operations without a verified runtime hook throw explicit errors. These are diagnostic adapters, not replacement CDI functionality. CDI method parameter resolution uses only the real BeanContainer's Lite APIs rather than supplying null arguments or requiring CDI Full metadata APIs.

The Lite/Full API boundary follows the [CDI 4.0 programmatic container access specification](https://jakarta.ee/specifications/cdi/4.0/jakarta-cdi-spec-4.0.html). Unsupported Full-only metadata operations are not treated as Lite defects.

## Evidence

- [Baseline results](reports/baseline-2026-10-23/README.md)
- [Work register](reports/WORK_REGISTER.md)
- [Execution follow-up](reports/execution-followup-2026-10-23/README.md): hosted baseline and bounded REST Client class execution.
- [CDI follow-up](reports/cdi-followup-2026-10-23/README.md): official selection proof, porting hooks, and separate classpath/JPMS results.
- Raw logs, XML, dumps, classpaths, dependency hashes and environment metadata: `target/runs/<run-id>/`.
- GitHub Actions runs the matrix, stays red on failures, and uploads evidence even when the test step fails.

Retain a new baseline with completed run IDs in order; later records replace earlier records for a suite:

```sh
python scripts/record_baseline.py --run <run-id> --output reports/<baseline-name>
```

The recorder refuses an incomplete suite set. Lifecycle failures, skipped methods, unobserved classes and blocked factories are not counted as specification passes.

## Harness boundaries

The Arquillian adapter starts the real GuicedEE runtime, exports official deployment archives, enriches test objects through its injector, and exposes HTTP metadata. It does not add replacement CDI, REST Client, JSON-B or Reactive Streams implementations.

This adapter remains diagnostic, not certification-ready. The deployment loader is parent-first; the default lane uses the classpath and the optional CDI lane resolves runtime modules through JPMS. The adapter does not yet isolate deployment classes from the entire TCK JAR, provide separate server JVMs for multiple deployments within a class, or implement web.xml semantics. CDI porting hooks are registered, but unsupported proxy/context operations fail explicitly. These are work-register items. A second deployment fails because GuicedEE shutdown is terminal. Isolation acceptance tests are required before passing assertions can support compatibility claims.

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
