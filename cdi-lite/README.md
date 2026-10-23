# cdi-lite

Official artifact: `jakarta.enterprise:cdi-tck-core-impl:4.0.13`.
GuicedEE runtime: `com.guicedee:cdi:2.4.1`. Engine: testng.

Selection: Core Profile 10.0.1 cdi-lite-tck-suite XML; excludes upstream cdi-full and se groups

Run through `python scripts/run_tcks.py --suite cdi-lite` after the root setup steps.
See the [baseline](../reports/baseline-2026-10-23/README.md) and [work register](../reports/WORK_REGISTER.md).
Blocked, skipped and unobserved tests do not count as passes.
