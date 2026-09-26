"""
gather.py - the one command you type. Layer 1 gives it two jobs.

    python gather.py status     what is set, and what is allowed right now
    python gather.py login      sign in by hand, once

Run it from the `_engine` folder inside your CRM, which is where the installer put
it, alongside the tools your earlier layers installed.

`status` is the useful one and it is worth running before and after anything. It
prints what you chose, then asks the doorman about every kind of action and prints
his answer. On a fresh install every answer is a refusal, because the engine
arrives switched off. That is correct, and watching it refuse is the only way to
know the doorman is standing there at all.

Nothing in this file reaches the outside world except `login`, which opens a window
and waits for you.

Needs: Python 3.8 or newer. `login` also needs Playwright - see the README.
"""

import sys
from datetime import datetime
from pathlib import Path

# What a member types to start Python. A Mac has `python3` and no plain `python`; Windows
# keeps `python`, exactly as before.
PY = "python3" if sys.platform == "darwin" else "python"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import crm_paths                                            # noqa: E402
import gather_settings as gs                                # noqa: E402
import gather_limits                                        # noqa: E402


def _rule():
    print("-" * 62)


def cmd_status():
    cfg = gs.get()
    now = datetime.now()

    print("")
    print("YOUR SETTINGS")
    _rule()
    print("  records system      %s" % crm_paths.vault())
    print("  working days        %s" % ", ".join(cfg["days"]))
    print("  working hours       %s to %s" % (cfg["hours"].get("from"), cfg["hours"].get("to")))
    print("  browser session     %s" % gs.session_dir())

    saved, note = (False, "")
    try:
        import gather_browser
        saved, note = gather_browser.session_status()
    except Exception:                                       # noqa: BLE001
        note = "could not be read"
    print("  signed in           %s" % ("yes" if saved else "not yet - run: %s gather.py login" % PY))

    print("")
    print("THE TWO SWITCHES")
    _rule()
    print("  engine-on           %s" % ("ON" if cfg.get("engine-on") else "off"))
    print("  plan-only           %s" % ("ON" if cfg.get("plan-only") else "off"))
    armed, why = gs.armed()
    print("  so right now        %s" % ("armed - actions are real" if armed else why))

    frac = gs.ramp_fraction()
    print("")
    print("TODAY, BY KIND OF ACTION")
    _rule()
    if frac < 1:
        print("  the ramp is still opening: %d%% of your chosen ceiling today" % int(frac * 100))
    print("  %-10s %-12s %-14s %s" % ("action", "today", "this week", "allowed right now?"))
    for row in gather_limits.report(now):
        ok, reason = row["verdict"]
        week = ("%d of %d" % (row["week"], row["weekly_cap"])) if row["weekly_cap"] else "%d" % row["week"]
        print("  %-10s %-12s %-14s %s"
              % (row["action"], "%d of %d" % (row["today"], row["cap"]), week,
                 "yes" if ok else "blocked"))
        if not ok:
            print("  %-38s %s" % ("", reason))

    print("")
    if not armed:
        print("Everything is refused because %s." % why)
        print("That is the state it arrives in. Turn the switches on in")
        print("  %s" % (crm_paths.vault() / "_layers" / "config.json"))
        print("under \"gather\", when you are ready.")
    print("")
    return 0


def cmd_login(argv):
    site = argv[2] if len(argv) > 2 else "linkedin"
    import gather_browser
    return gather_browser.sign_in(site)


USAGE = """gather - Layer 1, the foundation

  %(py)s gather.py status            what is set, and what is allowed right now
  %(py)s gather.py login [site]      sign in by hand, once (default: linkedin)

Run this from the _engine folder inside your CRM.
""" % {"py": PY}


def main(argv):
    cmd = (argv[1] if len(argv) > 1 else "status").strip().lower()
    if cmd in ("status", "st"):
        return cmd_status()
    if cmd == "login":
        return cmd_login(argv)
    if cmd in ("help", "-h", "--help"):
        print(USAGE)
        return 0
    print("I do not know the command %r." % cmd)
    print("")
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
