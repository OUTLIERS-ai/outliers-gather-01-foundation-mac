"""
Outliers Gather - Layer 1 - The Foundation

Your records system works and everything in it came off your own machine. This
layer installs the part that goes outside: one browser that is not the one you use,
and the doorman every later job has to get past.

    python install.py

It finds the CRM you built, asks you four questions, and installs the layer into it.

Nothing here reaches the outside world. It writes files, asks the questions, and
stops. The engine arrives switched off and stays off until you turn it on by hand.

Needs: Python 3.8 or newer. The `login` command also needs Playwright, which this
installer checks for and tells you how to get if it is missing.
"""

import json
import os
import shutil
import sys
from pathlib import Path

# What a member types to start Python. A Mac has `python3` and no plain `python`, so every
# command printed below uses this name; Windows keeps `python`, exactly as before.
PY = "python3" if sys.platform == "darwin" else "python"

# The 2 lines that get Playwright. On a Mac they go through `python3 -m`, because pip can put
# its own `pip` and `playwright` commands in a folder Terminal does not search.
if sys.platform == "darwin":
    PLAYWRIGHT_STEPS = ["python3 -m pip install playwright", "python3 -m playwright install chromium"]
else:
    PLAYWRIGHT_STEPS = ["pip install playwright", "playwright install chromium"]

LAYER = 1
LAYER_NAME = "The Foundation"
SERIES = "Gather"

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "engine"

# crm_paths and safe_write are shared with your CRM and are IDENTICAL there. They
# are only written if missing, never overwritten, so installing this can never
# replace one of your existing files with a narrower version of itself.
SHARED = ["crm_paths.py", "safe_write.py"]
MINE = ["gather_settings.py", "gather_limits.py", "gather_browser.py",
        "gather_walk.py"]

# `gather.py` is the command surface, and later layers ADD commands to it. If this
# installer overwrote it, running Layer 1 again after Layer 2 -- to repair a setting,
# or because somebody worked through the guides twice -- would silently take four
# working commands away and leave no sign of what happened. So it is written only
# when it is absent, and the installer says which of the two it did.
KEEP_IF_PRESENT = ["gather.py"]

# No colour codes anywhere. Plenty of terminals print them as literal gibberish and
# a member's first minute with this must not look broken.
def say(msg=""):
    print(msg, flush=True)


def ask(question, default=None, helptext=None):
    say()
    say(question)
    if helptext:
        say("  " + helptext)
    prompt = "  > " if default is None else "  [%s] > " % default
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        say("\nStopped. Nothing was changed.")
        sys.exit(1)
    return answer or (default or "")


# ------------------------------------------------------------- finding your CRM

def config_path(home):
    return Path(home) / "_layers" / "config.json"


def looks_like_a_crm(home):
    try:
        return config_path(home).exists()
    except OSError:
        return False


def find_vault():
    """Find the CRM you built, by looking for its config file."""
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
    here = Path.cwd()
    tried.append(here)
    tried.extend(here.parents)

    for candidate in tried:
        if looks_like_a_crm(candidate):
            return Path(candidate)

    say()
    say("  Could not find your CRM automatically.")
    raw = ask("Where is it?", default=str(Path.home() / "CRM"),
              helptext="The folder your first layer built. It has a _layers folder inside it.")
    candidate = Path(raw.strip().strip('"').strip("'")).expanduser()
    return candidate if looks_like_a_crm(candidate) else None


def refuse(reason, fix=None):
    say()
    say("=" * 66)
    say("  Not yet.")
    say("=" * 66)
    say()
    say("  " + reason)
    if fix:
        say()
        say("  " + fix)
    say()
    sys.exit(1)


# ------------------------------------------------------------------- questions

def ask_hours():
    raw = ask("What hours do you work?",
              default="09:00-17:30",
              helptext="Nothing runs outside them. The hours you are genuinely at your "
                       "desk, not the ones you would like to be.")
    parts = [p.strip() for p in raw.replace(" to ", "-").split("-")]
    if len(parts) != 2:
        say("  I could not read that. Using 09:00-17:30.")
        return {"from": "09:00", "to": "17:30"}
    return {"from": parts[0], "to": parts[1]}


DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def ask_days():
    raw = ask("Which days?",
              default="mon,tue,wed,thu,fri",
              helptext="The days it is allowed to do anything at all. Weekends off is "
                       "the ordinary answer, and weekend activity is one of the patterns "
                       "that gets noticed.")
    chosen = [d.strip().lower()[:3] for d in raw.replace(" ", ",").split(",") if d.strip()]
    chosen = [d for d in chosen if d in DAYS]
    return chosen or ["mon", "tue", "wed", "thu", "fri"]


def ask_cap():
    raw = ask("How many people a day, at most?",
              default="8",
              helptext="Your ceiling for asking to connect. It starts here and opens "
                       "gradually over a fortnight, because a sudden jump against what "
                       "your account normally does is what gets noticed. Lower is fine.")
    try:
        n = max(1, min(int(raw), 25))
    except ValueError:
        n = 8
    if n > 15:
        say("  That is on the high side for a first fortnight. Keeping it, but the ramp")
        say("  still opens gradually and you can lower it whenever you like.")
    return n


def ask_session_dir():
    default = str(Path.home() / ".outliers-gather" / "session")
    raw = ask("Where should the browser keep your login?",
              default=default,
              helptext="Outside anything that syncs or backs itself up. A signed-in "
                       "session copied somewhere else is a signed-in session somebody "
                       "else can use.")
    return str(Path(raw.strip().strip('"').strip("'")).expanduser())


# --------------------------------------------------------------------- the work

def playwright_present():
    try:
        import playwright                                   # noqa: F401
        return True
    except ImportError:
        return False


def install_modules(engine_dir):
    engine_dir.mkdir(parents=True, exist_ok=True)
    written, kept = [], []
    for name in SHARED:
        target = engine_dir / name
        if target.exists():
            kept.append(name)
            continue
        shutil.copy2(ENGINE / name, target)
        written.append(name)
    for name in MINE:
        shutil.copy2(ENGINE / name, engine_dir / name)
        written.append(name)
    for name in KEEP_IF_PRESENT:
        target = engine_dir / name
        if target.exists():
            kept.append(name + " (a later layer has added commands to it)")
            continue
        shutil.copy2(ENGINE / name, target)
        written.append(name)
    return written, kept


def main():
    say()
    say("=" * 66)
    say("  Outliers %s - Layer %d - %s" % (SERIES, LAYER, LAYER_NAME))
    say("=" * 66)
    say()
    say("  This installs one browser that is not the one you use, and the")
    say("  doorman every later job has to get past. It collects nobody and")
    say("  reads nothing. Nothing here reaches the outside world.")

    home = find_vault()
    if not home:
        refuse("That folder does not look like your CRM - there is no _layers folder inside it.",
               "Install the first layer of your CRM before this one.")

    engine_dir = Path(home) / "_engine"
    if not (engine_dir / "limits.py").exists():
        refuse("Your CRM does not have its safety layer installed yet.",
               "This layer asks that shared counter for room as its last check, rather "
               "than keeping a second copy of it. Install the safety layer first.")

    say()
    say("  Found your CRM: %s" % home)

    hours = ask_hours()
    days = ask_days()
    cap = ask_cap()
    session = ask_session_dir()

    written, kept = install_modules(engine_dir)

    cfg = {}
    try:
        cfg = json.loads(config_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    cfg["gather"] = {
        "engine-on": False,
        "plan-only": True,
        "hours": hours,
        "days": days,
        "daily": {"look": 40, "profile": 20, "request": cap, "undo": max(cap * 2, 10)},
        "weekly": {"request": cap * 5},
        "ramp-days": 14,
        "session-dir": session,
    }
    config_path(home).parent.mkdir(parents=True, exist_ok=True)
    config_path(home).write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    say()
    say("-" * 66)
    say("  Installed.")
    say("-" * 66)
    say()
    say("  Written into %s:" % engine_dir)
    for n in written:
        say("    %s" % n)
    for n in kept:
        say("    %s (already there, left alone)" % n)
    say()
    say("  Your answers are in %s under \"gather\"." % config_path(home))
    say()
    say("  Both switches are OFF. Nothing can reach the outside world until you")
    say("  turn them on by hand, which is deliberate.")

    if not playwright_present():
        say()
        say("  ONE MORE STEP before you can sign in. The browser needs Playwright,")
        say("  which is not installed yet. In this same terminal, run:")
        say()
        for step in PLAYWRIGHT_STEPS:
            say("      " + step)
        say()
        say("  The second line downloads the browser itself, so it takes a minute.")

    say()
    say("  Now, in a terminal in that _engine folder:")
    say()
    say("      %s gather.py status" % PY)
    say()
    say("  Everything will say blocked. That is correct - it is how you know the")
    say("  doorman is standing there. Then sign in, once:")
    say()
    say("      %s gather.py login" % PY)
    say()
    return 0


if __name__ == "__main__":
    sys.exit(main())
