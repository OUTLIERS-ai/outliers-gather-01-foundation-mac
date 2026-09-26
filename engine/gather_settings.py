"""
gather_settings.py - your answers, in one place, read by everything above.

The installer wrote these into the same config file every other layer of your CRM
uses, so there is one place you edit and one place anything reads. Nothing here
decides what a safe number is. You did, when you installed the layer, because the
safe number depends on your account, your history and how long you have had it.

Two switches live here and both arrive OFF:

    engine-on    false  -> nothing reaches the outside world at all
    plan-only    true   -> work out exactly what would happen and write it down
                           instead of doing it

Both have to be turned on by hand. The safe state is the state it arrives in, so a
half-finished setup does nothing rather than something.

    import gather_settings as gs
    gs.get()["hours"]          -> {"from": "09:00", "to": "17:30"}
    gs.armed()                 -> (False, "the engine is switched off")

Needs: Python 3.8 or newer. Nothing else.
"""

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import crm_paths                                            # noqa: E402
import safe_write                                           # noqa: E402

# Deliberately small. A first fortnight at these numbers looks like a person who
# has started using the site a bit more, which is the whole idea. The installer
# offers them as defaults and you can go lower without being asked twice.
DEFAULTS = {
    "engine-on": False,
    "plan-only": True,
    "hours": {"from": "09:00", "to": "17:30"},
    "days": ["mon", "tue", "wed", "thu", "fri"],
    "daily": {"look": 40, "profile": 20, "request": 8, "undo": 15},
    "weekly": {"request": 40},
    "ramp-days": 14,
    "session-dir": "",          # filled by the installer; kept outside the CRM
}

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

CONFIG_KEY = "gather"


def config_path():
    return crm_paths.vault() / "_layers" / "config.json"


def get():
    """Every setting, with anything you never answered filled from the defaults."""
    whole = safe_write.read_json(config_path(), {})
    mine = whole.get(CONFIG_KEY) or {}
    out = dict(DEFAULTS)
    for k, v in mine.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            merged.update(v)
            out[k] = merged
        else:
            out[k] = v
    return out


def put(changes):
    """Change one or more settings, leaving every other layer's answers alone."""
    whole = safe_write.read_json(config_path(), {})
    mine = dict(whole.get(CONFIG_KEY) or {})
    mine.update(changes)
    whole[CONFIG_KEY] = mine
    config_path().parent.mkdir(parents=True, exist_ok=True)
    safe_write.write_json(config_path(), whole)
    return get()


def session_dir():
    """Where the browser keeps the details that keep you signed in.

    Kept OUTSIDE the CRM on purpose. A CRM folder is the sort of place people
    back up, sync or put under version control, and a signed-in session copied
    anywhere else is a signed-in session somebody else can use.
    """
    s = (get().get("session-dir") or "").strip()
    return Path(s).expanduser() if s else (Path.home() / ".outliers-gather" / "session")


def armed():
    """Are both switches on? Returns (armed, reason) - the reason is for a person."""
    cfg = get()
    if not cfg.get("engine-on"):
        return False, "the engine is switched off"
    if cfg.get("plan-only"):
        return False, "plan-only is on, so nothing is actually done"
    return True, "armed"


# ------------------------------------------------------------------ the window

def _hhmm(text, fallback):
    try:
        h, m = str(text).split(":")[:2]
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (TypeError, ValueError):
        pass
    return fallback


def is_working_day(when=None):
    when = when or datetime.now()
    return DAY_NAMES[when.weekday()] in [d.lower()[:3] for d in get()["days"]]


def inside_hours(when=None):
    when = when or datetime.now()
    cfg = get()["hours"]
    fh, fm = _hhmm(cfg.get("from"), (9, 0))
    th, tm = _hhmm(cfg.get("to"), (17, 30))
    now = when.hour * 60 + when.minute
    return (fh * 60 + fm) <= now <= (th * 60 + tm)


# ------------------------------------------------------------------- the ramp

def ramp_started():
    """The day the ramp began, as a date, or None if it never has."""
    raw = get().get("ramp-started")
    try:
        return date.fromisoformat(raw) if raw else None
    except (TypeError, ValueError):
        return None


def start_ramp(on=None):
    return put({"ramp-started": (on or date.today()).isoformat()})


def ramp_fraction(today=None):
    """How much of your chosen limit is available today, between 0 and 1.

    A limit you have never worked at is not a limit your account has any history
    of. Starting at your ceiling on the first day is the single most recognisable
    pattern there is, so the ceiling opens gradually instead. If the ramp has not
    been started, nothing is held back - you are running by hand and watching.
    """
    began = ramp_started()
    if not began:
        return 1.0
    span = max(1, int(get().get("ramp-days") or 14))
    elapsed = ((today or date.today()) - began).days
    if elapsed >= span:
        return 1.0
    # Never below a fifth: a ramp that starts at almost nothing reads as broken
    # on day one and gets switched off, which helps nobody.
    return max(0.2, (elapsed + 1) / float(span))


def cap_for(action, today=None):
    """Today's ceiling for one kind of action, after the ramp is applied."""
    base = int(get()["daily"].get(action, 0) or 0)
    if base <= 0:
        return 0
    return max(1, int(base * ramp_fraction(today)))


def weekly_cap_for(action):
    return int(get()["weekly"].get(action, 0) or 0)
