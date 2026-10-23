# TCK execution follow-up: 23 October 2026

This follow-up changes TCK execution only. No GuicedEE implementation fixes were made. The original 26-suite baseline is preserved unchanged.

## Hosted baseline

[GitHub run 39985709735](https://github.com/GuicedEE/MicroProfile-TCK/actions/runs/39985709735) compiled and attempted all 26 suites, retained its artifacts, and correctly failed. REST Client hit the 30-minute suite deadline. CDI Lite and Reactive Streams remained blocked before test results. [Hosted summary](hosted-summary.json) records the commit, timestamps, statuses and original summary checksum.

## Bounded REST Client execution

All 62 inventoried concrete classes were selected, each in a separate Maven process. The suite compiled once before parallel execution; each class received a distinct report directory and port. All 62 have terminal execution records:

- 61 classes failed and one timed out.
- 501 reported test/lifecycle entries: 0 passed, 66 failed, 435 skipped.
- BasicReactiveStreamsTest completed with six assertion failures.
- ReactiveStreamsPublisherTckTest reached its 240-second external deadline. The runner stopped its process tree automatically and retained a TIMED_OUT record with no reported cases. Its tests remain unexecuted/incomplete, not passed.
- The class phase finished in 354.78 seconds, without manual process intervention.

[Class table](classes.md), [full results and failure signatures](rest-client-result.json), [environment](environment.json), and [evidence hashes](evidence-hashes.json) retain the execution record. Raw evidence stays under target/runs/rest-client-isolated-2026-10-23/. Every class selection and reported count was checked against the inventory and authoritative top-level Surefire XML. TestNG duplicate reports are excluded.

Separate processes per class address the scheduler timeout gap. They do not provide deployment archive isolation, CDI vendor porting, or valid multi-deployment semantics inside a class. Failing assertions remain diagnostic until those harness boundaries are resolved.

## Verification and CI

- 13 Python regression checks pass, covering selection integrity, official group-selection protection, timeout cleanup, aggregation, duplicate reports and failure classification.
- An integration run through run_tcks.py with class isolation completed the official JSON-P pluggability class: 18 reported tests passed. This is an execution check, not a GuicedEE compatibility claim.
- The 26-suite inventory/coordinate/engine validation passes.
- GitHub Actions now selects class isolation for REST Client, retaining all other suites and failure behavior. The updated hosted workflow has not yet been validated by this local follow-up.

CDI porting, deployment isolation, provider availability and the remaining functionality findings stay open in the work register. No runtime repairs have started.
