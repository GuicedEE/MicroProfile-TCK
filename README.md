# MicroProfile-TCK

Independent MicroProfile compatibility test harness and TCK results for GuicedEE.

## Status

Repository bootstrap only. No TCK suites or compatibility claims are established yet.
The first planned suites are MicroProfile Config and Health.

## Scope

- Consume official TCK artifacts and provide GuicedEE runtime/deployment adapters.
- Pin the GuicedEE, specification, TCK and JDK versions used for each run.
- Retain reproducible test reports and explicitly record failures and exclusions.
- Keep implementation fixes and ordinary regression tests in the owning GuicedEE repositories.

Individual specification results and full MicroProfile platform compatibility are
tracked separately.

## DevSuite checkout

This repository is included in DevSuite at `GuicedEE/microprofile-tck`:

```sh
git submodule update --init GuicedEE/microprofile-tck
```

The submodule tracks `master`; DevSuite records the exact commit used by its checkout.

## License

Apache License 2.0; see [LICENSE](LICENSE). Upstream TCK artifacts retain their own licenses.
