# Project Roadmap

This roadmap is a living document describing the direction of the project across three horizons:

* Near Term (next minor release: 0.3.x)
* Mid Term (toward 0.4.0)
* Longer Term / Exploration (0.5.0+ or when resourced)

Dates are not promises; sequencing is based on dependency ordering and risk reduction. Items marked (★) are candidate stretch goals if capacity remains after core scope.

---
## Guiding Principles
1. Headless-first: automation logic must never require a GUI import path.
2. Deterministic signal processing: numerical routines produce stable results across platforms (float tolerances codified in tests).
3. Fail safely with instrumentation: timeouts and partial data tolerated with clear user feedback.
4. Guardrail tooling: pre-commit + CI prevents recurrence of large binary / virtualenv commits.
5. Minimal public surface area growth: prefer internal helpers unless user value is clear.

---
## Near Term (0.3.x incremental releases)
| Category | Item | Rationale | Acceptance |
|----------|------|-----------|-----------|
| Automation | Add SNR, noise floor metrics | Broaden KPI set | Tested numeric routines + doc update |
| Automation | IMD (SMPTE/CCIF) experiment (★) | Evaluate complexity vs value | Prototype + decision note |
| DSP | Windowing options (Hann, Blackman) | Improve THD accuracy | Parameterized THD test passes |
| Type Safety | Gradually enable stricter mypy (disallow untyped defs in dsp/automation) | Catch latent bugs | CI passes with stricter config |
| CI | Pre-commit workflow (added) refine caching | Faster feedback | Median run time < 90s |
| Docs | Publish v0.3.0 release + usage examples for automation module | Discoverability | Release page + README section |
| Packaging | Optional extra `metrics` if deps added later | Isolation | pyproject extra defined |

---
## Mid Term (Target 0.4.0)
| Category | Item | Rationale | Acceptance |
|----------|------|-----------|-----------|
| Architecture | Extract instrument interfaces to protocol-style ABCs | Easier mocking & alt hardware | Tests use ABC mocks |
| CLI | Add headless sweep CLI (`amp-benchkit sweep --config file.json`) | Scriptable automation | CLI help + integration test |
| Server | Lightweight REST/WebSocket control layer (opt-in) | Remote orchestration | Start/stop, run sweep endpoints |
| GUI | Layout polish + non-blocking progress pane | UX clarity | User can cancel sweep |
| Coverage | 80% line coverage threshold enforced (currently below) | Quality gate | CI fails under threshold |
| Docs | Architecture overview diagram | Contributor onboarding | Diagram committed & referenced |

---
## Longer Term / Exploration (0.5.0+)
| Category | Item | Rationale |
|----------|------|-----------|
| Hardware Lab | Hardware-in-loop nightly matrix (env gated) | Real device regression safety |
| Plugin System | Dynamic instrument discovery via entry points | Extensibility |
| UI | Theming / dark mode | Accessibility |
| Performance | Optional PyO3/Rust FFT backend | Speed for large sweeps |
| Data Layer | Structured result export (Parquet) | Downstream analytics |

---
## Deferred / Watch List
| Idea | Reason Deferred | Revisit Trigger |
|------|-----------------|----------------|
| Git LFS adoption for captured waveforms | Avoid user friction until needed | If >5MB user artifacts common |
| Full static type coverage (strict mypy project-wide) | High churn areas remain | After API stabilization |

---
## Roadmap Maintenance
* Update when: a milestone closes, new dependency arises, or scope descopes.
* Keep PRs small: one roadmap table row change per rationale when feasible.
* Cross-reference issues: each committed item should link to an issue for discussion.

---
Last updated: 2025-09-28