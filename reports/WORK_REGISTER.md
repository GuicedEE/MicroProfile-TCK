# TCK work register

Status is recorded per item below. This phase establishes tests and evidence only; no GuicedEE implementation fixes were made.

The [machine-readable findings](baseline-2026-10-23/findings.json) retain exception signatures and affected tests. These grouped investigations do not presume every failure is a GuicedEE defect.

| ID | Area | Evidence / boundary | Later investigation |
| --- | --- | --- | --- |
| HARNESS-001 | Deployment isolation | Parent-first embedded loader; all TCK classes remain on the test classpath. Multi-deployment tests fail explicitly. | Isolated runtime processes or a verified module/classloader design; test class, resource and service-provider visibility. |
| HARNESS-002 | CDI Lite porting, PARTIAL | Beans/Contexts/EL adapters now satisfy official configuration discovery. Context lookup and EL delegate to the actual provider; serialization uses standard Java object streams. Unsupported proxy introspection and context lifecycle hooks throw explicit errors. | Obtain verified runtime proxy/lifecycle hooks before claiming complete porting. No Weld or replacement CDI behavior was introduced. |
| HARNESS-003 | Web deployment | Root HTTP context; full archive context paths, web.xml and Servlet semantics are not implemented. | Validate fixture hosting against actual GuicedEE routing; distinguish unsupported contracts from adapter defects. |
| HARNESS-004 | Execution mode, CDI LANE IMPLEMENTED | An optional CDI lane resolves unchanged GuicedEE runtime modules with their actual JPMS service declarations while leaving Arquillian on the test classpath. The runtime starts beyond the classpath scope-registration error. | Extend validated module configurations to other runtime components; this does not resolve deployment archive isolation. |
| HARNESS-005 | Fork timeout enforcement, MITIGATED | The original REST Client publisher fork exceeded 240 seconds; hosted execution also reached its suite deadline. Class mode now uses one externally bounded Maven process per inventoried class and continues after a timeout. See the [execution follow-up](execution-followup-2026-10-23/README.md). | SSE fixture hosting and assertions remain OPEN. A timeout is an incomplete class, never a pass. This scheduling mitigation does not provide archive isolation. |
| HARNESS-006 | CDI suite scheduling, IMPLEMENTED | The official XML otherwise shares a terminal runtime across classes. The pinned TestNG engine discovers 718 methods across 294 classes; generated class XML preserves groups/listeners, and a second discovery checks exact method-set equality. | Preserve these checks as the official suite evolves. Multi-deployment semantics within one class remain HARNESS-001. |
| HARNESS-007 | CDI method parameters, IMPLEMENTED | The adapter previously supplied null method parameters. CDI parameter resolution now uses only BeanContainer APIs: qualifier recognition, typed bean lookup, resolution and contextual references. Unsupported API errors propagate. | BeanContainer functionality is a later runtime investigation, not a harness substitute. An early probe using CDI Full createAnnotatedType was superseded and is not a Lite finding. |
| RUNTIME-001 | CDI/Guice startup, CLASSPATH-SPECIFIC | MissingScopeAnnotation for jakarta.inject.Singleton and jakarta.enterprise.context.ApplicationScoped reproduces in the classpath lane. The unchanged runtime's JPMS declarations get past this failure. | Treat this as an execution/packaging distinction, not evidence that named-module scope registration is broken. No registration changed here. |
| RUNTIME-002 | Reactive Streams Operators | Upstream factory cannot obtain a ReactiveStreamsEngine from ServiceLoader. | Establish intended support; this engine contract differs from ordinary Reactive Streams interfaces. |
| RUNTIME-003 | JSON-B | Tests report missing org.eclipse.yasson.JsonBindingProvider; no replacement provider added. | Determine intended JSON-B support; Jackson representation support alone does not establish it. |
| RUNTIME-004 | Other assertions/providers | JWT, LRA, Jakarta REST, JSON-P and other suites produce individual failures; deployment failures skip dependent tests. | Triage after isolation/bootstrap boundaries; preserve original results. |
| MATRIX-001 | Annotations baseline | Core Profile 10 signature reports jakarta.annotation.ManagedBean removed against GuicedEE Annotations 3.0. | Decide the intended platform baseline before repairs; this is an explicit version mismatch. |
| COVERAGE-001 | Unexecuted cases | summary.json lists unobserved candidates; factories, CDI Lite groups, upstream-disabled tests and discovery errors affect execution. | Reconcile each unobserved case; separate official selections from local failures. No failure waivers. |

## Later repair-phase criteria

1. Preserve the baseline and upstream hashes.
2. Resolve harness isolation and porting gaps without replacing runtime implementations.
3. Compare per-test results on reruns.
4. Only then make separately reviewed changes in GuicedEE implementation repositories.
5. Compatibility requires official execution requirements and complete passing results, not a diagnostic subset.
