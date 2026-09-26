"""
gather_walk.py - how it moves between pages, and how long it waits.

THE TELL THIS EXISTS TO AVOID. Going straight to a deep address is the clearest
possible sign that nobody human is driving. A person does not arrive at the third
page of a search result with no history of how they got there. They land somewhere
ordinary, pause, scroll a little, and click through. So does this.

THE SECOND TELL, WHICH IS SUBTLER AND WORSE. Being regular. One action exactly
every forty-five seconds is a pattern no person produces, and being under your
limit does not help you -- the pattern is the signal, not the volume. So the waits
here are not "forty-five seconds give or take two". They are mostly short, often
medium, occasionally very long indeed, the way real attention actually behaves.

    import gather_walk as walk
    walk.open_page(page, "https://example.com/somewhere/deep")   # lands, dwells, goes
    walk.pause()                                                 # between actions
    walk.read_pause(len(text))                                   # time to actually read

Needs: Python 3.8 or newer. Nothing else.
"""

import random
import time
from urllib.parse import urlsplit

# Ordinary places to land before going anywhere specific. A referrer and a dwell
# cost you a couple of seconds and remove the single most obvious signature.
LANDINGS = {
    "linkedin.com": "https://www.linkedin.com/feed/",
    "facebook.com": "https://www.facebook.com/",
}


def _sleep(seconds):
    time.sleep(max(0.0, seconds))


def pause():
    """The gap between two actions.

    Three kinds of gap, chosen at random with the weights below, because that is
    roughly how a person's attention is shaped: mostly brisk, sometimes distracted,
    and every so often they get up and make a cup of tea. A single narrow range,
    however randomised inside itself, is still a rhythm.
    """
    roll = random.random()
    if roll < 0.70:
        _sleep(random.uniform(8, 35))          # brisk, still reading
    elif roll < 0.95:
        _sleep(random.uniform(35, 120))        # distracted
    else:
        _sleep(random.uniform(180, 600))       # gone for a bit


def read_pause(length):
    """Time proportional to how much there was to read, with a floor and a ceiling."""
    seconds = 1.5 + (max(0, int(length)) / 900.0) * random.uniform(6, 14)
    _sleep(min(seconds, 45))


def _landing_for(url):
    host = (urlsplit(url).hostname or "").lower()
    for key, landing in LANDINGS.items():
        if host.endswith(key):
            return landing
    return None


def open_page(page, url, dwell=True):
    """Go to a page the way a person gets there: somewhere ordinary first.

    If the page is already on the right site, no landing hop is needed -- a person
    already inside a site does not go back to the front door between clicks.
    """
    landing = _landing_for(url)
    here = (page.url or "").lower()
    same_site = landing and urlsplit(here).hostname and \
        (urlsplit(here).hostname or "").endswith((urlsplit(landing).hostname or ""))

    if landing and not same_site:
        page.goto(landing, wait_until="domcontentloaded", timeout=60_000)
        if dwell:
            _sleep(random.uniform(1.8, 4.5))
            scroll(page)
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    if dwell:
        _sleep(random.uniform(1.6, 4.0))
    return page


def scroll(page, bursts=None):
    """A couple of scrolls, and sometimes back up again, which people do."""
    try:
        for _ in range(bursts or random.randint(1, 3)):
            page.mouse.wheel(0, random.randint(300, 900))
            _sleep(random.uniform(0.5, 1.4))
        if random.random() < 0.4:
            page.mouse.wheel(0, -random.randint(150, 400))
            _sleep(random.uniform(0.4, 0.9))
    except Exception:                                       # noqa: BLE001
        pass


def drift(page):
    """Move the pointer somewhere before clicking. Free, and it costs nothing to do."""
    try:
        page.mouse.move(random.randint(120, 1100), random.randint(120, 800),
                        steps=random.randint(8, 22))
    except Exception:                                       # noqa: BLE001
        pass
