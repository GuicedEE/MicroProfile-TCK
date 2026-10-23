# CDI Lite follow-up: 23 October 2026

The official CDI Lite selection is now discoverable and attempted in separate class processes in both classpath and JPMS modes. No GuicedEE implementation functionality was changed. This remains diagnostic evidence, not a compatibility claim.

## Selection and execution

The pinned TestNG 7.4.0 engine selected 718 method identifiers across 294 classes from the unmodified Core Profile 10.0.1 suite XML. Per-class XML preserves its listeners and group exclusions. A second engine discovery confirmed an identical method set across every generated partition before the corrected JPMS run.

| Lane | Selected classes attempted | Passed entries | Failed entries | Skipped entries |
| --- | ---: | ---: | ---: | ---: |
| Classpath | 294 | 0 | 294 | 1,436 |
| JPMS, corrected Lite parameter adapter | 294 | 10 | 663 | 402 |

Counts include test-engine lifecycle/configuration entries; they are not a count of specification assertions. The JPMS lane has 287 failing classes and seven classes marked PASSED_DIAGNOSTIC. Every selected class has a terminal record; none timed out in the corrected run. Unexecuted or skipped methods are not passes.

The classpath run was interrupted after 143 completed classes. Those immutable class records were preserved, and the remaining classes resumed; classpath-resume.json documents this. Its elapsed value is a sum of process durations, not wall time. The classpath run preceded the Lite parameter correction but failed during startup before parameter resolution.

## Harness changes

- Registered Beans, Contexts and EL porting adapters through the official configuration properties and enabled CDI Lite mode.
- Delegated supported operations to actual runtime APIs; unverified proxy introspection and context lifecycle operations fail explicitly. No reference implementation or replacement provider was added.
- Partitioned the official suite without changing its selected method set, avoiding terminal runtime reuse between test classes.
- Resolved the unchanged GuicedEE runtime's actual JPMS graph while leaving Arquillian on the test classpath. This gets past the classpath-specific MissingScopeAnnotation startup failure.
- Replaced null CDI test-method parameters with typed lookup, qualifier recognition, resolution and contextual reference access through BeanContainer only.

An early parameter probe used createAnnotatedType, which belongs to CDI Full. That run was stopped and marked SUPERSEDED; its results are not included here or treated as Lite runtime findings. The corrected adapter follows the [CDI 4.0 Lite/Full API boundary](https://jakarta.ee/specifications/cdi/4.0/jakarta-cdi-spec-4.0.html).

## Evidence and checks

- [Results and failure signatures](jpms-results.json)
- [Lane summaries and per-class status](summary.json)
- [Official and partitioned selection proof](selection.json)
- [Unsupported API observations](unsupported-api-observations.json): getBeans, getContext, resolve and Instance.getHandle origins, with affected test references. These are observed failures, not an automatic repair prescription.
- [Runtime module artifact hashes](runtime-modules.json)
- [Raw evidence hashes](evidence-hashes.json): 2,360 files checked/recorded under target/runs/.
- classpath-environment.json and jpms-environment.json retain the run environments; raw logs and XML remain local under their named run directories.

All 26 suite modules plus the harness compile. Five porting contract checks, three parameter-enrichment checks and fourteen Python reporting/selection checks pass. These 22 infrastructure checks are separate from upstream TCK totals. The final quoted JVM argument-file form was verified in an actual test JVM by its module-path property.

CI now runs the original matrix and a separate CDI JPMS lane, retains failures and uploads both evidence sets. Updated hosted execution is not yet validated by these local results.

## Remaining readiness limits

Deployment archives still use a parent-first loader with the complete TCK on the test classpath. Archive/resource isolation, multiple deployments within one class, web.xml semantics, and unsupported porting proxy/context hooks remain open. Provider availability and CDI behavior failures are retained for the later implementation phase. Do not call the harness certification-ready or the TCK fully passing based on this record.
