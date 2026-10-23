# Baseline verification

- All 26 suite modules and the harness passed `mvn -B -ntp -fae test-compile` on Java 25 / Maven 4.0.0-rc-6.
- Fresh upstream inventory matched committed coordinates, checksums and exact class selection.
- Seven reporting regression tests passed, including duplicate TestNG XML, malformed reports, missing results, skips and failed executions.
- All 26 baseline totals were independently counted from authoritative top-level Surefire XML. TestNG's nested `junitreports` copies are excluded. Earlier derived result snapshots are retained locally; upstream XML was not changed.
- Every evidence hash in provenance.json was checked against its local source; cases.jsonl contains exactly 5,985 reported test/lifecycle entries.
- Diagnostic totals: 624 passed, 1,584 failed, 3,777 skipped; 123 open failure signatures. Two suites produced no test results and remain blocked. These totals do not imply complete execution or certification.
- REST Client publisher timeout intervention is recorded in the baseline README and HARNESS-005.
- Raw build output is retained in target/research/final-test-compile.log. CI configuration is supplied; hosted execution has not been validated by this local baseline.

No GuicedEE implementation changes were made in this phase.
