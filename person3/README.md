# FlowShift · Person 3 demo

This standalone implementation covers UC-04 (daily plan), UC-13/14 (rules and historical autopilot preview), UC-15 (savings receipt), UC-16 (notification simulation), and the local UC-19 audit viewer. It also provides a repeatable scenario for the shared UC-20 demo.

From the repository root, run:

```sh
python3 person3/server.py
```

Open [the local demo](http://127.0.0.1:8765). Requires Python 3.9+ with system IANA timezone data. No credentials or package installation needed. Use `--port 8766` if the default port is occupied. Stop and restart the server to reset the demo; it keeps state in memory.

## Walkthrough for the group

1. **Daily plan:** Start with $0 Safe to Spend and a payroll warning. Open the forecast table and try the activity filters. Mark the fixture stale to see the headline switch to Unavailable, then refresh it.
2. **Rules:** Show the $2,000 reserve, $2,500 per-action ceiling and $5,000 aggregate ceiling. Change the ceiling to $2,499.99 and save to demonstrate that even a one-cent difference matters. Restore $2,500 before the next step.
3. **Autopilot preview:** Run the historical replay. The office-supply action qualifies at exactly $2,500 including its fee. Open the split-payment example: each payment fits individually, but the plan exceeds the combined ceiling.
4. **Notifications:** Run the check at the default April 20 time. The daily summary and payroll alert appear. Repeat at the same time to show deduplication; the lock-screen text contains no financial amounts.
5. **Daily plan → Replay settled rescue:** Load the canonical settled simulation result. Safe to Spend rises to $833.16. This button replays a fixture rather than implementing the teammate-owned approval or payment flow.
6. **Savings receipt:** Show the $35.00 modeled avoided fee, $18.84 simulated cost, and $16.16 net. Open the evidence and export CSV. Switch to May to show the empty state.
7. **Audit history:** Expand the rule save, preview, notification, settlement and export entries.

## Integration handoff

- Person 1 can replace the synthetic snapshot and balance checkpoints used by `dashboard()` with the versioned forecast, business timezone, freshness, and incident data.
- Person 2 can replace `settle_fixture()` with their simulator's settled-result event, supplying plan/action IDs, evidence, costs and the documented counterfactual. A pending or failed action must not create a settled receipt. Use the active rules version when validating any plan.
- Shared API currently exposes `GET /api/state`, `GET /api/receipt`, `GET /api/receipt.csv`, and JSON POST routes for `rules`, `preview`, `notices`, and demo `fixture`. Monetary fields use integer USD cents. Rule writes require the expected version.
- Local scope: one synthetic owner and account, in-memory audit and version state, on-demand notification clock, and no bank or payment network access. Tenant auth, durable audit storage, scheduled delivery, and teammate services belong to shared integration.

Run the checks with `python3 -m unittest discover -s person3 -v`.
