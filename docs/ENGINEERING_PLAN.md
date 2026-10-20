# Engineering Delivery Plan

This is a proposed backlog for engineers, not work implemented in this repository. PM approves scope and open decisions; engineers own design choices and evidence. See [the specification](../PROJECT_SPEC.md) for required behaviors and [the integration guide](JACK_HENRY.md) before estimating access work.

## Team Ownership

| Workstream | Deliverables |
| --- | --- |
| Backend / integrations | Auth, tenant isolation, data normalization, scheduler/worker, simulator, audit, reconciliation |
| Forecasting / optimization | Recurrence, uncertainty, CP-SAT choices and constraints, golden fixtures, chronological backtests |
| Frontend / product | Seven experiences, shared data contracts, all interaction/error states, accessibility, host-plugin behavior |
| Explainability / research | Structured explanations, numerical validation, owner/bank interviews, savings attribution review, synthetic business scenarios |
| PM / bank sponsor | Decision log, canonical fixture approval, pilot priorities, provider access, security/compliance and operational sign-off |

## Milestone 0: Contract And Access

**Before implementation estimates become commitments.**

- [ ] PM approves strict reserve default, canonical arithmetic, fee-aware ceiling, and MVP simulator-only boundary.
- [ ] Assign engineering owners and document a minimal stack/deployment ADR; no microservice requirement.
- [ ] Confirm developer-account access and separate sandbox/staging availability; record blockers without publishing credentials.
- [ ] Select neutral host branding and define business identity/role mapping.
- [ ] Agree normalized schemas, plan versioning, rounding policy, freshness policy, and test clock conventions.

Exit: signed-off MVP contract and integration capability matrix. UC-01/02/19; EC-08/09/44/45. A blocked sandbox does not prevent synthetic development but cannot count as completed integration.

## Milestone 1: Ingestion And Confirmed Obligations

**Proposal weeks 1-3.**

- [ ] FS-01: Authorized sandbox login and account read, with redacted evidence.
- [ ] FS-02: Balance/transaction normalization, pagination, duplicate handling, and pending-to-posted reconciliation.
- [ ] FS-03: Tenant-scoped relational model, source snapshots, versioned audit, and explicit synthetic/sandbox environment labels.
- [ ] FS-04: Confirm/edit/reject/manual obligation flow; model immovable auto-debits and payroll funding dates.
- [ ] FS-05: Begin interviews; target 15 SMB owners and 3 bank staff by week 4.

Exit: one business imports data reproducibly without duplicate cash events; confirmed obligations survive refresh; revoked access blocks new reads. UC-01/02/03/18/19; EC-01 through EC-12 and EC-44/45.

## Milestone 2: Forecast And Safe To Spend

**Proposal weeks 4-6.**

- [ ] FS-06: Recurrence suggestions with confidence and confirmation gates.
- [ ] FS-07: Exactly 14 local days, daily and funding checkpoints, expected/P10/P90, reserve/gap, and deterministic cent-based headroom.
- [ ] FS-08: Forecast assumptions view and accessible chart/table from shared data.
- [ ] FS-09: Backtest harness with chronological splits, near-zero denominator policy, interval coverage, and injected shortfalls.
- [ ] FS-10: Event and scheduled-refresh replanning; stale and partial-data blocks.

Exit: arithmetic invariants pass; forecast uncertainty is labeled honestly; intraday payroll risk is caught even if end-of-day balance is positive. UC-04/05/06; EC-13/14/21/36/46/47/48.

## Milestone 3: Optimized Plans And Simulator

**Proposal weeks 7-9. Build the first end-to-end daily-plan -> review -> simulate slice here.**

- [ ] FS-11: CP-SAT timing/rail/payout choices, hard deadlines, strict reserve, eligible fee model, deterministic tie-breaks, solver-status reporting.
- [ ] FS-12: Canonical example with exact cents and separately modeled baseline fee; tiny-instance exhaustive comparison tests.
- [ ] FS-13: Scenario comparison and before/after forecasts; immutable draft/source versioning.
- [ ] FS-14: Human approval, atomic obligation reservation, durable job/outbox, stable idempotency, and stale-plan rejection.
- [ ] FS-15: Simulator for success/rejection/failure/unknown/cancellation and multi-action dependencies; no real banking network submission path.
- [ ] FS-16: Payroll rescue and infeasible-plan flows; protect auto-debits and existing scheduled actions.

Exit: payroll rescue works from data through explanation, exact-version approval, simulation, and audit; double clicks do not duplicate actions; partial failures expose renewed risk. UC-07/08/10/11/12/17; EC-15 through EC-35 and EC-39.

## Milestone 4: Complete Owner Experience

**Proposal weeks 10-11.**

- [ ] FS-17: Finish all seven screens and navigation, host-plugin adaptation, responsive layouts, permissions, loading/empty/stale/error states.
- [ ] FS-18: Discount Hunter logic using confirmed terms, deadline/reserve checks, and net benefit evidence.
- [ ] FS-19: Versioned rules and autopilot historical preview, never live autopilot.
- [ ] FS-20: Daily-summary and critical-risk notification simulator with timezone/dedup/preferences tests.
- [ ] FS-21: Savings attribution, gross/cost/net reconciliation, period filters, drilldowns, and safe CSV export.

Exit: every visible action works; savings reconcile; settings invalidate incompatible plans; mockup inconsistencies are not copied into UI. UC-09/13/14/15/16; EC-19/20/27/28/35/37/38/40/41/42/43.

## Milestone 5: Verify And Demonstrate

**Proposal weeks 12-13.**

- [ ] FS-22: Generate 200 synthetic businesses with fixed seeds and varied recurring/seasonal/irregular flows; document generator assumptions.
- [ ] FS-23: Complete unit, integration, authorization, concurrency, accessibility, and browser end-to-end testing for the use-case/edge-case matrix.
- [ ] FS-24: Run benchmark and backtest report; record accuracy, interval coverage, shortfall lead time, false positives, solver status/latency, and savings distribution.
- [ ] FS-25: Rehearse the canonical rescue plus stale data, infeasible plan, and failed payout; verify mode labels and audit trail in each.
- [ ] FS-26: Publish setup/run/test commands and environment-variable **names only** for the implemented system; document remaining blockers and PM-approved deferrals.

Exit: PM can run the demo without engineering improvisation, see evidence behind each amount, and distinguish synthetic demonstration from verified sandbox integration.

## Required Test Layers

| Layer | Mandatory examples |
| --- | --- |
| Unit | Money rounding, 14 dates across DST, recurring deduplication, headroom, fee/discount netting, cutoff computation, exact threshold boundaries |
| Property/invariant | Cash conservation, no double-counted principal, no duplicate obligation execution, no feasible plan with a violated hard constraint |
| Integration | Sandbox contract mapping, token/consent failures, complete pagination, transaction lineage, audit persistence and version conflicts |
| Optimizer | Exhaustive tiny instances, canonical fixture, infeasible strict reserve, unsupported rails, expired quotes, timeout with/without feasible solution |
| Simulator/concurrency | Retry after crash, two concurrent approvals, aggregate rule limit, dependency failure, unknown reconciliation, cancellation boundary |
| Security | Cross-tenant reads/mutations/exports, role downgrade, session protection, webhook authenticity when applicable, CSV injection, untrusted merchant text |
| Browser | All seven journeys at mobile/desktop sizes; keyboard and chart-table parity; double approval click; stale-data rejection; report totals |
| Backtest | Held-out chronological data, seed reproducibility, no lookahead, 200-business stratification, interval coverage and negative savings cases |

Tests SHOULD be traceable to UC/EC IDs in names or a coverage matrix. Sandbox-only tests may be conditionally skipped without credentials, but the report MUST distinguish skipped integration checks from passing synthetic checks.

## Definition Of Done For Every Ticket

1. Acceptance cases and relevant UC/EC IDs are explicit.
2. Numbers derive from normalized inputs; no placeholder mockup amounts survive.
3. Authorization, versioning, failure/retry, and environment behavior are covered where applicable.
4. Focused automated tests pass; integration limitations are disclosed.
5. User-visible changes have responsive/accessibility checks and screenshots with no secrets.
6. Audit evidence exists for state-changing or decision-producing behavior.
7. Setup and decisions are documented; no unrelated refactor or production capability is introduced.

## Production Gate: Separate Future Project

Live execution requires a sponsor institution, actual product/rail entitlements, merchant payout agreement where applicable, verified payees, fraud/compliance review, approved authentication and secrets handling, retention/access policy, settlement reconciliation, payment-finality handling, monitoring, incident response, support ownership, legal review, and a staged rollout with kill switches. The bank and qualified reviewers define regulatory obligations; this handoff does not certify compliance.

Do not use the semester timeline or prototype sign-off as approval for production money movement.
