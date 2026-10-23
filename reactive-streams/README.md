# reactive-streams

Official artifact: `org.eclipse.microprofile.reactive-streams-operators:microprofile-reactive-streams-operators-tck:3.0.1`.
GuicedEE runtime: `com.guicedee:vertx:2.4.1`. Engine: testng.

Selection: com.guicedee.tck.ReactiveStreamsVerificationTest

Run through `python scripts/run_tcks.py --suite reactive-streams` after the root setup steps.
See the [baseline](../reports/baseline-2026-10-23/README.md) and [work register](../reports/WORK_REGISTER.md).
Blocked, skipped and unobserved tests do not count as passes.
