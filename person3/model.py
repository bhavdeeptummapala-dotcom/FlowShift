"""Single-account synthetic demo. All money is integer USD cents."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import csv
import io

ZONE = ZoneInfo("America/Chicago")
START = date(2026, 4, 20)
DEFAULT = dict(reserve=200000, ceiling=250000, aggregate=500000,
               instant=True, routine=True, weekends=False)
OPENING = 840000
BASE = [(1, -180000), (2, -288800), (3, -400000), (3, -3500), (4, 314000)]
RESCUE = [(2, -288800), (3, 314000), (3, -1884), (3, -400000), (4, -180000)]


def cash_path(events):
    balance = low = OPENING
    days = []
    for offset in range(14):
        for day, delta in events:
            if day == offset:
                balance += delta
                low = min(low, balance)
        days.append(dict(date=str(START + timedelta(days=offset)), balance=balance))
    return low, days


def initial():
    return dict(version=1, rules=DEFAULT.copy(), audit=[], notices=[], receipts=[],
                scenario="baseline", fresh=True)


def audit(state, event, detail):
    state["audit"].append(dict(id=len(state["audit"]) + 1, event=event, detail=detail,
                               actor="Demo owner", mode="synthetic",
                               rulesVersion=state["version"],
                               at=datetime.now(ZONE).isoformat(timespec="seconds")))


def dashboard(state):
    low, days = cash_path(RESCUE if state["scenario"] == "rescue" else BASE)
    reserve = state["rules"]["reserve"]
    feed = []
    if not state["fresh"]:
        feed.append(dict(kind="Alerts", title="Account snapshot is stale", detail="Refresh before using this forecast.", source="snapshot-1"))
    if state["scenario"] == "baseline":
        feed.append(dict(kind="Alerts", title="Payroll funding at risk", detail="Modeled shortfall: $288.00 before fees, Thursday at 9:00 AM CT.", source="payroll-0423"))
        feed.append(dict(kind="Suggestions", title="Review the synthetic payroll rescue", detail="Move the supplier payment and accelerate the existing settlement.", source="rescue-v1"))
    elif low < reserve:
        feed.append(dict(kind="Alerts", title="Reserve target at risk", detail="The simulated plan dips below your active reserve.", source="rescue-v1"))
    if state["receipts"]:
        feed.append(dict(kind="Savings", title="Simulated savings receipt ready", detail="Review avoided fees and execution costs.", source="receipt-rescue-v1"))
    return dict(low=low, days=days, safe=max(0, low-reserve) if state["fresh"] else None,
                gap=max(0, reserve-low) if state["fresh"] else None, feed=feed,
                count=sum(i["kind"]=="Alerts" for i in feed), reserve=reserve,
                asOf="2026-04-20 07:00 CT", source="snapshot-1",
                plan="rescue-v1" if state["scenario"]=="rescue" else "baseline-v1")


def save_rules(state, version, rules):
    if type(version) is not int or version != state["version"]:
        raise ValueError("Rules changed. Reload the active version and try again.")
    if not isinstance(rules, dict) or rules.keys() != DEFAULT.keys():
        raise ValueError("A complete rules form is required.")
    for key in ("reserve", "ceiling", "aggregate"):
        if type(rules[key]) is not int or not 0 <= rules[key] <= 100_000_000_000:
            raise ValueError("Amounts must be nonnegative and within the demo limit.")
    for key in ("instant", "routine", "weekends"):
        if type(rules[key]) is not bool:
            raise ValueError("Invalid preference.")
    state["rules"] = rules.copy()
    state["version"] += 1
    audit(state, "rules.saved", "Prior previews invalidated; dashboard recalculated.")


# Each record represents the information available at the replay timestamp.
HISTORY = [
    dict(name="Office supply plan", asOf="2026-03-13", low=300000, actions=[
        dict(name="Office supplies", amount=245000, fee=5000)]),
    dict(name="Same-day split payments", asOf="2026-03-16", low=290000, actions=[
        dict(name="Supplier A", amount=200000, fee=0),
        dict(name="Supplier B", amount=200000, fee=0),
        dict(name="Supplier C", amount=200000, fee=0)]),
    dict(name="New contractor", asOf="2026-03-17", low=280000, actions=[
        dict(name="Contractor", amount=90000, fee=0, changed=True)]),
    dict(name="Instant payment", asOf="2026-03-18", low=320000, actions=[
        dict(name="Equipment", amount=90000, fee=1500, instant=True, alternative=0)]),
    dict(name="Payroll conflict", asOf="2026-03-19", low=180000, payroll=False, actions=[
        dict(name="Stock purchase", amount=50000, fee=0)]),
    dict(name="Expired quote", asOf="2026-03-20", low=320000, fresh=False, actions=[
        dict(name="Insurance", amount=70000, fee=0)]),
    dict(name="Unverified destination", asOf="2026-03-23", low=320000, authorized=False, actions=[
        dict(name="Supplier", amount=70000, fee=0, eligible=False, deadline=False)]),
]


def preview(plan, rules):
    shared = []
    if not plan.get("authorized", True): shared.append("Authorization missing")
    if not plan.get("fresh", True): shared.append("Stale inputs or fee quote")
    if not plan.get("payroll", True): shared.append("Payroll deadline at risk")
    if plan["low"] < 0: shared.append("Negative projected balance")
    if plan["low"] < rules["reserve"]: shared.append("Reserve would be breached")
    total = sum(a["amount"] + a["fee"] for a in plan["actions"])
    if total + plan.get("priorExposure", 0) > rules["aggregate"]:
        shared.append("Combined plan or daily exposure exceeds the aggregate ceiling")
    actions = []
    for a in plan["actions"]:
        reasons = shared.copy()
        if a["amount"]+a["fee"] > rules["ceiling"]: reasons.append("Amount plus fees exceeds ceiling")
        if a.get("changed"): reasons.append("New or changed payee requires human approval")
        if not a.get("eligible", True): reasons.append("Rail or destination ineligible")
        if not a.get("deadline", True): reasons.append("Arrival deadline missed")
        if a.get("instant") and rules["instant"] and (
            a.get("alternative") is None or a["fee"]-a.get("benefit", 0) >= a["alternative"]
        ): reasons.append("Instant rail has no documented cost advantage")
        actions.append(dict(name=a["name"], exposure=a["amount"]+a["fee"], reasons=reasons))
    return dict(name=plan["name"], asOf=plan["asOf"], total=total,
                eligible=bool(actions) and not any(a["reasons"] for a in actions), actions=actions)


def notices(state, local_time):
    rules = state["rules"]
    items = state["notices"]

    def add(key, title, detail):
        if any(i["key"] == key for i in items):
            return
        items.append(dict(key=key, title=title, detail=detail, at=local_time.isoformat(),
                          lockScreen="Open FlowShift for details"))
        audit(state, "notification.simulated", key)

    funding = datetime(2026, 4, 23, 9, tzinfo=ZONE)
    if state["scenario"] == "baseline" and local_time >= funding - timedelta(hours=72):
        detail = "Funding deadline passed; check payroll status." if local_time >= funding else "Review the funding deadline and rescue options."
        add("payroll-0423", "Payroll funding alert", detail)
    if (local_time.hour >= 7 and rules["routine"] and
            (rules["weekends"] or local_time.weekday() < 5)):
        add("summary-" + str(local_time.date()), "Daily cash summary", "Review the daily plan and any related actions.")


def settle_fixture(state):
    if state["scenario"] == "rescue":
        return
    low, _ = cash_path(RESCUE)
    if not state["fresh"] or low < state["rules"]["reserve"]:
        raise ValueError("The fixture is stale or violates the active reserve.")
    state["scenario"] = "rescue"
    state["receipts"].append(dict(id="receipt-rescue-v1", date="2026-04-24",
        category="Avoided overdraft fee", gross=3500, cost=1884, count=1,
        baseline="baseline-v1: one modeled $35 overdraft fee",
        action="rescue-v1: simulated $18.84 settlement acceleration fee",
        mode="simulated"))
    audit(state, "fixture.settled", "snapshot-1 → baseline-v1 → rescue-v1 → receipt-rescue-v1")


def receipt(state, period):
    rows = [r for r in state["receipts"] if r["date"].startswith(period)]
    monthly = defaultdict(int)
    for r in rows:
        monthly[r["date"][:7]] += r["gross"]-r["cost"]
    gross, cost = (sum(r[k] for r in rows) for k in ("gross", "cost"))
    return dict(rows=rows, gross=gross, cost=cost, net=gross-cost,
                count=sum(r["count"] for r in rows), monthly=dict(monthly))


def export_csv(report):
    def safe(value):
        if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@"))
                                       or value.startswith(("\t", "\n", "\r"))):
            return "'" + value
        return value
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(("Business date", "Category", "Gross cents", "Cost cents", "Net cents",
                     "Modeled incidents", "Baseline evidence", "Action evidence", "Mode"))
    for r in report["rows"]:
        writer.writerow(map(safe, (r["date"], r["category"], r["gross"], r["cost"],
                        r["gross"]-r["cost"], r["count"], r["baseline"], r["action"], r["mode"])))
    writer.writerow(("Total", "", report["gross"], report["cost"], report["net"],
                     report["count"], "", "", "simulated"))
    return output.getvalue()
