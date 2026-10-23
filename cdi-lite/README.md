# cdi-lite

Official artifact: `jakarta.enterprise:cdi-tck-core-impl:4.0.13`.
GuicedEE runtime: `com.guicedee:cdi:2.4.1`. Engine: testng.

Selection: Core Profile 10.0.1 cdi-lite-tck-suite XML; excludes upstream cdi-full and se groups

Run through `python scripts/run_tcks.py --suite cdi-lite --isolate-suite cdi-lite` after the root setup steps.
See the [baseline](../reports/baseline-2026-10-23/README.md) and [work register](../reports/WORK_REGISTER.md).
Blocked, skipped and unobserved tests do not count as passes.

The pinned TestNG engine discovers the official group-filtered methods, then verifies that per-class XML selects the identical method set. Each selected class runs in a separate externally bounded process. This preserves the official exclusions while avoiding terminal runtime reuse between classes.

`src/test/resources/META-INF/cdi-tck.properties` registers diagnostic Beans, Contexts and EL porting adapters and enables CDI Lite mode. Missing proxy/context lifecycle hooks throw explicit unsupported-operation errors. No replacement CDI implementation is provided.

Use the root README's JPMS command to exercise actual runtime module service declarations. [CDI follow-up evidence](../reports/cdi-followup-2026-10-23/README.md) distinguishes these results from the classpath baseline. PortingContractTest is a harness check outside the official suite's package selection; its passes are not included in TCK totals.
