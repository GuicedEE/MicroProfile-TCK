# health

Official artifact: `org.eclipse.microprofile.health:microprofile-health-tck:4.0.2`.
GuicedEE runtime: `com.guicedee:health:2.4.1`. Engine: testng.

Selection: All inventoried concrete test classes, including nested and inherited tests.

Run through `python scripts/run_tcks.py --suite health` after the root setup steps.
See the [baseline](../reports/baseline-2026-10-23/README.md) and [work register](../reports/WORK_REGISTER.md).
Blocked, skipped and unobserved tests do not count as passes.
