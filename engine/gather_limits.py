"""
gather_limits.py - the doorman. Every job asks him first, and he answers the same
six questions in the same order, every time.

    1  is the engine switched on at all
    2  is today a day you chose to work
    3  is it inside the hours you set
    4  are you under today's limit for THIS kind of action
    5  are you under this week's limit for it
    6  is there room in the shared total

THE SIXTH CHECK IS NOT NEW, AND THAT IS THE POINT. You already built one shared
counter, in the safety layer of your CRM, and the rule it enforces is that every
activity asks the same counter for room so three activities each staying inside
their own allowance cannot add up to a total nobody agreed to. This module does
not replace it and does not keep a second copy of it. It asks it, last, and takes
its answer. One counter, still.

WHY THE ORDER MATTERS. The checks run cheapest and most decisive first. There is
no point counting anything if the engine is off, and no point reading a file if it
is Sunday. It also means the reason you get back is the FIRST reason, which is the
one that would still stop you if you fixed all the others.

WHAT IT DOES NOT DO. It never acts, never opens anything, and never decides that a
job is a good idea. It answers may-this-happen and nothing else.

    import gather_limits
    ok, why = gather_limits.can_act("request")
    if not ok:
        print("not now:", why)     # and that is the end of it
    ...
    gather_limits.record("request")   # AFTER it happened, never before

Needs: Python 3.8 or newer. Nothing else.
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import crm_paths                                            # noqa: E402
import safe_write                                           # noqa: E402
import gather_settings as gs                                # noqa: E402

try:
    import limits as shared_counter                         # your CRM's safety layer
except ImportError:                                         # not installed yet
    shared_counter = None


# The rolling history. Your CRM's counter resets when the date changes, which is
# right for a daily limit and useless for a weekly one -- by the time you ask "how
# many this week", six of those days have already been cleared. So this keeps one
# small tally per day and nothing else, and answers the weekly question from it.
HISTORY_DAYS = 30


def history_path():
    return crm_paths.state_dir() / "gather_history.json"


def _history():
    data = safe_write.read_json(history_path(), {})
    return data if isinstance(data, dict) else {}


def _prune(data):
    cutoff = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    return {d: v for d, v in data.items() if d >= cutoff}


def done_today(action, today=None):
    day = (today or date.today()).isoformat()
    return int((_history().get(day) or {}).get(action, 0))


def done_this_week(action, today=None):
    """The trailing seven days, including today.

    Trailing rather than Monday-to-Monday on purpose: the window that matters
    resets seven days after the first action in it, not on a calendar boundary,
    so a calendar week would hand the allowance back on the wrong day.
    """
    today = today or date.today()
    data = _history()
    total = 0
    for back in range(7):
        day = (today - timedelta(days=back)).isoformat()
        total += int((data.get(day) or {}).get(action, 0))
    return total


# ------------------------------------------------------------------ the doorman

def can_act(action, when=None):
    """May one more of this kind of action happen right now? -> (allowed, reason).

    The reason is written for a person reading a log later, not for a machine.
    """
    when = when or datetime.now()

    # 1 -- is the engine on at all
    cfg = gs.get()
    if not cfg.get("engine-on"):
        return False, "the engine is switched off"

    # 2 -- is today a day you chose
    if not gs.is_working_day(when):
        return False, "today is not one of your working days"

    # 3 -- is it inside your hours
    if not gs.inside_hours(when):
        h = cfg["hours"]
        return False, "it is outside your hours (%s to %s)" % (h.get("from"), h.get("to"))

    # 4 -- today's limit for this kind of action
    cap = gs.cap_for(action, when.date())
    if cap <= 0:
        return False, "no daily limit is set for '%s', so nothing is allowed" % action
    used = done_today(action, when.date())
    if used >= cap:
        frac = gs.ramp_fraction(when.date())
        extra = "" if frac >= 1 else " (the ramp is still opening: %d%% of your ceiling)" % int(frac * 100)
        return False, "today's limit for '%s' is used up, %d of %d%s" % (action, used, cap, extra)

    # 5 -- this week's limit
    wcap = gs.weekly_cap_for(action)
    if wcap:
        wused = done_this_week(action, when.date())
        if wused >= wcap:
            return False, ("this week's limit for '%s' is used up, %d of %d over the last seven days"
                           % (action, wused, wcap))

    # 6 -- the shared total you already built. Asked last, and never duplicated.
    if shared_counter is not None:
        ok, why = shared_counter.allow(action)
        if not ok:
            return False, why

    return True, "%d of %d today for '%s'" % (used, cap, action)


def record(action, note=None):
    """Count one action that HAS HAPPENED. Never call this before the fact.

    Counting an intention means a run that stops halfway has spent an allowance it
    never used, and every later run behaves as though it did.

    Recorded in two places on purpose: your CRM's shared counter, so the total
    stays true across everything you run, and the rolling history here, so the
    weekly question can still be answered after the daily count resets.
    """
    day = date.today().isoformat()
    data = _prune(_history())
    data.setdefault(day, {})
    data[day][action] = int(data[day].get(action, 0)) + 1
    if note:
        data[day].setdefault("_last", {})[action] = str(note)
    history_path().parent.mkdir(parents=True, exist_ok=True)
    safe_write.write_json(history_path(), data)

    if shared_counter is not None:
        shared_counter.record(action, note)
    return data[day][action]


def report(when=None):
    """One row per kind of action: used, today's ceiling, and the week."""
    when = when or datetime.now()
    rows = []
    for action in sorted(gs.get()["daily"]):
        rows.append({
            "action": action,
            "today": done_today(action, when.date()),
            "cap": gs.cap_for(action, when.date()),
            "week": done_this_week(action, when.date()),
            "weekly_cap": gs.weekly_cap_for(action),
            "verdict": can_act(action, when),
        })
    return rows
