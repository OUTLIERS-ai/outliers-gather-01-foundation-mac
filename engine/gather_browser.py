"""
gather_browser.py - one browser, and it is not the one you use.

Your machine gets a second browser that only this system drives. It keeps its own
signed-in session in a folder outside your CRM, and it is never the browser you
personally browse in. Keep your own browsing where it is; these two never meet.

THREE DECISIONS, AND THE REASON FOR EACH

**One window, opened once, kept open.** Opening and closing a window for every job
is slow, and it looks nothing like a person: somebody working opens one window in
the morning and clicks around inside it. Every job here attaches to the window that
is already open rather than starting its own.

**The real browser, not a disguised one.** It runs on your machine, on your own
internet connection, using a genuine browser. That is the most ordinary set of details a
site can see, and it is free. The temptation is to hide something -- to claim a
different browser, a different screen, a different location. Do not. A genuine
browser telling one lie about itself is easier to spot than one telling none,
because the lie disagrees with everything around it.

**It waits for you at the sign-in, with no time limit.** Signing in means finding a
password and often a code from your phone. A step like that must never run against
a clock. It opens the window, you sign in, and you tell it when you are done.

    import gather_browser as gb
    with gb.window() as page:            # attaches, or opens one if none is open
        page.goto("https://example.com")

Needs: Python 3.8 or newer, plus Playwright. The installer tells you how.
"""

import sys
from contextlib import contextmanager
from pathlib import Path

# What a member types to start Python. A Mac has `python3` and no plain `python`; Windows
# keeps `python`, exactly as before.
PY = "python3" if sys.platform == "darwin" else "python"

# The key a member presses. A Mac keyboard's key is Return; Windows keeps Enter, exactly as before
# (Mac build plan V3, wave s2: the Session 7 ruling on the words installers print).
KEY = "Return" if sys.platform == "darwin" else "Enter"

# The 2 lines that get Playwright. On a Mac they go through `python3 -m`, because pip can put
# its own `pip` and `playwright` commands in a folder Terminal does not search.
if sys.platform == "darwin":
    PLAYWRIGHT_STEPS = ["python3 -m pip install playwright", "python3 -m playwright install chromium"]
else:
    PLAYWRIGHT_STEPS = ["pip install playwright", "playwright install chromium"]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gather_settings as gs                                # noqa: E402

# The sites this series knows about. Layer 2 uses the first; Layer 4 adds its own.
# `signed_in` is a piece of the page that only exists once you are signed in --
# checking the address alone is not enough, because a signed-out page can sit on a
# perfectly ordinary-looking address.
SITES = {
    "linkedin": {
        "home": "https://www.linkedin.com/feed/",
        "signed_in": ['a[href*="/in/"]', 'input[placeholder*="Search"]', '.global-nav'],
        "signed_out": ["/login", "/checkpoint", "/uas/", "authwall"],
    },
}

VIEWPORT = {"width": 1280, "height": 900}
LOCALE = "en-GB"


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "Playwright is not installed yet. In this terminal, run:\n"
            + "".join("    %s\n" % step for step in PLAYWRIGHT_STEPS)
            + "then try again."
        )
    return sync_playwright


def profile_dir(site="linkedin"):
    d = gs.session_dir() / site
    d.mkdir(parents=True, exist_ok=True)
    return d


@contextmanager
def window(site="linkedin", visible=True):
    """Open the one browser on its own profile and hand back a page.

    Visible by default. A window you can see is a window you can stop, and while
    you are learning what this does, watching it is the point.
    """
    sync_playwright = _playwright()
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir(site)),
            headless=not visible,
            viewport=VIEWPORT,
            locale=LOCALE,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            yield page
        finally:
            try:
                context.close()
            except Exception:                               # noqa: BLE001
                pass


def looks_signed_in(page, site="linkedin"):
    """Is this page a signed-in page? Judged on the page, not on the address."""
    spec = SITES.get(site) or {}
    url = (page.url or "").lower()
    for marker in spec.get("signed_out", []):
        if marker in url:
            return False
    for sel in spec.get("signed_in", []):
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:                                   # noqa: BLE001
            continue
    return False


def sign_in(site="linkedin"):
    """Open a window and wait for you to sign in. No time limit, on purpose."""
    spec = SITES.get(site)
    if not spec:
        print("I do not know a site called %r." % site)
        return 2

    # NOTHING OPENS UNLESS SOMEBODY IS THERE TO USE IT.
    #
    # This waits for you to press Enter. With no keyboard attached -- run from a
    # timetable, a script, or any automated check -- that wait ends the instant it
    # starts, so the window would appear and vanish before anybody could type into
    # it. A browser flashing onto the screen and closing again is worse than useless:
    # it interrupts whatever you were doing and achieves nothing.
    #
    # So the window is not opened at all unless there is a person at a keyboard.
    if not sys.stdin or not sys.stdin.isatty():
        print("")
        print("  Signing in needs you at the keyboard, so nothing has been opened.")
        print("")
        print("  Run this yourself in a terminal:")
        print("      %s gather.py login" % PY)
        print("")
        print("  It will open a window and wait for you, with no time limit.")
        print("")
        return 2

    print("")
    print("A browser window is opening. It is not your usual browser.")
    print("")
    print("  1. Sign in as yourself, exactly as you normally would.")
    print("  2. Include any code sent to your phone, if you use one.")
    print("  3. Keep going until you reach your normal home page.")
    print("  4. Then come back here and press %s." % KEY)
    print("")
    print("There is no time limit on this. Take as long as you need.")
    print("")

    with window(site) as page:
        try:
            page.goto(spec["home"], wait_until="domcontentloaded", timeout=60_000)
        except Exception:                                   # noqa: BLE001
            pass                                            # a sign-in wall is a fine place to land
        try:
            input("  Press %s once you are signed in and can see your home page... " % KEY)
        except (EOFError, KeyboardInterrupt):
            print("\n  Stopped. Nothing was saved.")
            return 1
        if looks_signed_in(page, site):
            print("\n  Signed in. The session is saved and you will not need to do this again.")
            return 0
        print("\n  I could not confirm you are signed in.")
        print("  If you ARE signed in, it is still saved -- carry on, and run this again")
        print("  only if a later job says it cannot see your account.")
        return 0


def session_status(site="linkedin"):
    """Has a session ever been saved? Read off disk, without opening anything."""
    d = gs.session_dir() / site
    if not d.exists():
        return False, "no session saved yet"
    cookies = list(d.glob("**/Cookies")) + list(d.glob("**/cookies.sqlite"))
    if not cookies:
        return False, "no session saved yet"
    return True, "a session is saved at %s" % d
