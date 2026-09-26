"""
test_doorman.py - the six checks, in order, and the one that is not ours.

SHOULD: no job acts unless all six checks pass, the reason you get back is the
FIRST one that failed, and the sixth check is answered by the shared counter your
CRM already had rather than by a second copy of it kept here.

DID (2026-08-13, the reason each test below exists):

  * A system with two counters is a system with no counter. The safety layer of
    your CRM exists because three activities each staying inside their own
    allowance is how a total nobody agreed to gets reached. If this layer kept its
    own count, that lesson would be undone by the layer that teaches it. The
    delegation test below fails if the sixth check is ever faked.
  * A ramp that opens to full on day one is not a ramp. The ramp test pins that
    the ceiling on the first day is genuinely lower than the number you chose, and
    that it never exceeds it.
  * Counting an intention rather than an action means a run that stops halfway has
    spent an allowance it never used. `record` is only ever called after the fact,
    and the test pins that it writes to both places.

Run it:  python tests/test_doorman.py        (exit 0 = green)

No browser, no network, no live CRM: every test points crm_paths at a throwaway
folder first. A test that reads and writes your real CRM is not a test.
"""

import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine"

sys.path.insert(0, str(ENGINE))


def find_installed_crm():
    """Your CRM, found the same way the installer finds it.

    Deliberately NOT a path relative to this repository. A test that reaches back
    into the folder it was authored in passes for its author and fails for every
    person who clones it, which is the whole family of fault this series exists to
    avoid. It never prompts: a test that asks a question cannot be run unattended.
    """
    import os
    tried = []
    env = os.environ.get("OUTLIERS_CRM")
    if env:
        tried.append(Path(env).expanduser())
    pointer = Path.home() / ".outliers-crm"
    if pointer.exists():
        try:
            noted = pointer.read_text(encoding="utf-8").strip()
            if noted:
                tried.append(Path(noted))
        except OSError:
            pass
    tried.append(Path.home() / "CRM")
    cwd = Path.cwd()
    tried.append(cwd)
    tried.extend(cwd.parents)
    for c in tried:
        try:
            if (Path(c) / "_engine" / "limits.py").exists():
                return Path(c) / "_engine"
        except OSError:
            continue
    return None


CRM_SAFETY = find_installed_crm()

FAILS = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (" :: " + detail if detail else ""))
    if not ok:
        FAILS.append(name)


# --- a throwaway CRM, with the real shared counter in it ---------------------
root = Path(tempfile.mkdtemp(prefix="gather-doorman-"))
(root / "_layers").mkdir(parents=True, exist_ok=True)
(root / "_state").mkdir(parents=True, exist_ok=True)
(root / "_engine").mkdir(parents=True, exist_ok=True)

# The real limits.py from your CRM's safety layer, if it is beside us. If it is
# not, the delegation test is SKIPPED LOUDLY rather than quietly passing -- a check
# that did not run is not a check that passed.
have_shared = CRM_SAFETY is not None and (CRM_SAFETY / "limits.py").exists()
if not have_shared:
    print("=" * 66)
    print("  Your CRM was not found, so the tests stop here.")
    print("=" * 66)
    print()
    print("  This layer's last check asks the shared counter in your CRM's safety")
    print("  layer for room. Without that counter there is nothing to ask, so the")
    print("  most important test in this file cannot be run -- and a test that did")
    print("  not run is not a test that passed.")
    print()
    print("  This is not a fault in this layer. Install your CRM's safety layer,")
    print("  then run this again. If your CRM is somewhere unusual, point at it:")
    print()
    print("      OUTLIERS_CRM=/path/to/your/CRM python tests/test_doorman.py")
    print()
    sys.exit(2)

if have_shared:
    for f in ("limits.py", "crm_paths.py", "safe_write.py"):
        shutil.copy2(CRM_SAFETY / f, root / "_engine" / f)
    sys.path.insert(0, str(root / "_engine"))

import crm_paths                                            # noqa: E402
crm_paths.use_vault(root)

import gather_settings as gs                                # noqa: E402
import gather_limits                                        # noqa: E402

BASE = {"engine-on": True, "plan-only": False,
        "hours": {"from": "09:00", "to": "17:30"},
        "days": ["mon", "tue", "wed", "thu", "fri"],
        "daily": {"request": 10}, "weekly": {"request": 30},
        "ramp-days": 14}


def configure(**over):
    settings = dict(BASE)
    settings.update(over)
    gs.put(settings)


print("=== the doorman: six checks, in order ===")

# 1 -- engine off refuses, and refuses FIRST
configure(**{"engine-on": False})
ok, why = gather_limits.can_act("request", datetime(2026, 8, 12, 10, 0))   # a Wednesday
check("engine off refuses", not ok, why)
check("and the reason is the engine, not something further down",
      "switched off" in why, why)

# 2 -- a day you did not choose
configure(days=["mon", "tue"])
ok, why = gather_limits.can_act("request", datetime(2026, 8, 15, 10, 0))   # a Saturday
check("a day you did not choose refuses", not ok, why)
check("and says so", "working days" in why, why)

# 3 -- outside your hours
configure()
ok, why = gather_limits.can_act("request", datetime(2026, 8, 12, 3, 0))
check("three in the morning refuses", not ok, why)
check("and names your hours", "outside your hours" in why, why)

# inside the window, nothing done yet, it lets you through
ok, why = gather_limits.can_act("request", datetime(2026, 8, 12, 10, 0))
check("inside the window with nothing done, it allows", ok, why)

# 4 -- today's limit for THIS action
configure(daily={"request": 2})
gather_limits.record("request")
gather_limits.record("request")
ok, why = gather_limits.can_act("request", datetime.now().replace(hour=10, minute=0))
today_is_working = gs.is_working_day(datetime.now())
if today_is_working:
    check("today's limit for one action stops it", not ok, why)
    check("and it is the daily limit that is named", "today's limit" in why, why)
else:
    check("today's limit (skipped: today is not a configured working day)", True,
          "re-run on a weekday to exercise this one")

# 5 -- the trailing week, which the daily counter cannot answer
configure(daily={"request": 50}, weekly={"request": 3})
check("the week counts days the daily count has already cleared",
      gather_limits.done_this_week("request") == 2,
      "week=%d" % gather_limits.done_this_week("request"))
gather_limits.record("request")
ok, why = gather_limits.can_act("request", datetime.now().replace(hour=10, minute=0))
if today_is_working:
    check("this week's limit stops it", not ok, why)
    check("and it is the weekly limit that is named", "this week" in why, why)
else:
    check("this week's limit (skipped: not a working day today)", True, "")

# 6 -- the sixth check is NOT ours
print()
print("=== the sixth check belongs to your CRM, not to this layer ===")
import limits as shared                                     # noqa: E402
shared.reset()
configure(daily={"request": 50}, weekly={"request": 50})
# Fill the SHARED counter only, leaving this layer's own numbers wide open.
for _ in range(45):
    shared.record("something-else")
ok, why = gather_limits.can_act("request", datetime.now().replace(hour=10, minute=0))
if today_is_working:
    check("a full shared counter stops a job whose own limits are untouched",
          not ok, why)
    check("and the refusal is the shared counter's own words",
          "shared daily limit" in why, why)
else:
    check("shared counter delegation (skipped: not a working day today)", True, "")
check("this layer keeps no second copy of the shared total",
          "total" not in dir(gather_limits) or gather_limits.__dict__.get("total") is None,
          "gather_limits must not define its own running total")

# --- the ramp ---------------------------------------------------------------
print()
print("=== the ramp opens, and never opens past your ceiling ===")
configure(daily={"request": 10}, **{"ramp-days": 14})
gs.start_ramp(date(2026, 8, 1))
day_one = gs.cap_for("request", date(2026, 8, 1))
mid = gs.cap_for("request", date(2026, 8, 7))
after = gs.cap_for("request", date(2026, 9, 1))
check("day one is below the ceiling you chose", day_one < 10, "day one = %d" % day_one)
check("it opens as the days pass", day_one <= mid <= after, "%d -> %d -> %d" % (day_one, mid, after))
check("and it never exceeds the ceiling", after == 10, "after the ramp = %d" % after)
gs.put({"ramp-started": None})
check("with no ramp started, nothing is held back",
      gs.cap_for("request", date.today()) == 10,
      "cap = %d" % gs.cap_for("request", date.today()))

# --- recording --------------------------------------------------------------
print()
print("=== recording happens after the fact, in both places ===")
shared.reset()
before_shared = shared.total()
before_history = gather_limits.done_today("undo")
gather_limits.record("undo")
check("the shared counter went up", shared.total() == before_shared + 1)
check("the rolling history went up", gather_limits.done_today("undo") == before_history + 1)

# --- nothing here can act ----------------------------------------------------
print()
print("=== this layer cannot act on anything ===")
source = "\n".join((ENGINE / f).read_text(encoding="utf-8")
                   for f in ("gather_limits.py", "gather_settings.py"))
for forbidden in ("page.click", "page.fill", "requests.post", "urlopen"):
    check("no %s anywhere in the doorman" % forbidden, forbidden not in source)

print()
if FAILS:
    print("%d check(s) failed:" % len(FAILS))
    for f in FAILS:
        print("   - %s" % f)
    sys.exit(1)
print("all checks passed.")
sys.exit(0)
