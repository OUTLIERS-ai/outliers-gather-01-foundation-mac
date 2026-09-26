**This is the Mac version.** On Windows, use [outliers-gather-01-foundation](https://github.com/OUTLIERS-ai/outliers-gather-01-foundation).

# Outliers Gather — Layer 1 — The Foundation

One browser that is not the one you use, and the doorman every later job has to get past.

This layer collects nobody and reads nothing. On its own it does no work. It is the ground the
next four layers stand on, and none of them run without it.

---

## Before you start

You need three items, and it is worth checking all three now rather than halfway through:

| | What | How to check |
|---|---|---|
| 1 | **Python 3.8 or newer** | `python3 --version` |
| 2 | **Your CRM**, with its safety layer installed | the folder has `_layers` and `_engine/limits.py` inside it |
| 3 | **Playwright**, for the sign-in step only | it goes into a private Python folder: the next section |

Nothing here costs money.

---

## Playwright, in a private Python folder

On a Mac, Playwright goes into a private Python folder called `outliers-gather-python` in your home
folder: a folder with its own copy of Python's add-ons. It works whether your Terminal uses Python
from python.org or from Homebrew (an add-on installer many Mac owners use, whose Python refuses a
plain `python3 -m pip install`). Type these 4 lines, one at a time, in the same Terminal window:

```
python3 -m venv ~/outliers-gather-python
source ~/outliers-gather-python/bin/activate
python3 -m pip install playwright
python3 -m playwright install chromium
```

The second line switches this Terminal window into the private folder, until you close the window.
**Each time you open a new Terminal window to use Gather, type that `source` line first.** The last
line downloads Chromium, the free browser Google Chrome is built from. Playwright keeps it in its own
folder, `~/Library/Caches/ms-playwright`, not in the private folder. It takes a minute or two.

---

## Install

```
git clone https://github.com/OUTLIERS-ai/outliers-gather-01-foundation-mac
cd outliers-gather-01-foundation-mac
source ~/outliers-gather-python/bin/activate
python3 install.py
```

It finds your CRM, asks four questions, and copies the layer into `_engine` inside it.

**Nothing reaches the outside world during installation.** It writes files, asks the questions,
and stops.

### The four questions

| Question | What it changes |
|---|---|
| What hours do you work? | Nothing runs outside them. |
| Which days? | The days it is allowed to do anything at all. |
| How many people a day, at most? | Your ceiling. It opens gradually over a fortnight. |
| Where should the login be kept? | A folder outside anything that syncs or backs itself up. |

### If the installer says Playwright is missing

The Terminal window was not switched into the private Python folder. Type the `source` line from the
block above, then `python3 install.py` again.

---

## Use it

The tools live in `_engine` inside your CRM, alongside the ones your earlier layers installed.
In Terminal, switch the window into the private Python folder and go **there** (if your CRM is not
at `~/CRM`, put your own folder in the `cd` line):

```
source ~/outliers-gather-python/bin/activate
cd ~/CRM/_engine
python3 gather.py status
```

It prints what you chose, then a line for every kind of action saying **blocked** — because the
engine arrives switched off. That is correct. Watching the doorman turn everything away is the
only way to know he is standing there.

Then sign in, once:

```
python3 gather.py login
```

A browser window opens. Sign in as yourself, including any code sent to your phone, and keep
going until you reach your normal home page. Come back to Terminal and press Return.
**It waits for you and there is no time limit on this step.**

Run `status` again. The login shows as saved and everything still says blocked. Both are meant
to be true at once.

---

## The two switches

Both arrive off, in `_layers/config.json` under `"gather"`:

```json
"engine-on": false,
"plan-only": true
```

`engine-on` false means nothing reaches the outside world at all. `plan-only` true means it
works out exactly what it would do and writes it down instead of doing it. **Both have to be
turned on by hand.** The safe state is the state it arrives in, so a half-finished setup does
nothing rather than something.

---

## The six checks, in order

Every job asks the doorman before it acts, and gets the same six questions in the same order:

1. Is the engine switched on at all
2. Is today a day you chose to work
3. Is it inside the hours you set
4. Are you under today's limit for this kind of action
5. Are you under this week's limit for it
6. Is there room in the shared total

**The sixth one is not new, and that is the point.** You already built one shared counter, in
your CRM's safety layer, because three activities each staying inside their own allowance is how
a total nobody agreed to gets reached. This layer does not replace it and keeps no second copy.
It asks it, last, and takes its answer. One counter, still.

The order matters: the reason you get back is the **first** one that failed, which is the one
that would still stop you if you fixed all the others.

---

## What is in here

| File | What it is |
|---|---|
| `engine/gather_settings.py` | Your answers, and the two switches |
| `engine/gather_limits.py` | The doorman: six checks, and the rolling seven-day history |
| `engine/gather_browser.py` | One browser, its own profile, the sign-in that waits for you |
| `engine/gather_walk.py` | How it moves between pages, and how long it waits |
| `engine/gather.py` | The command you type |
| `engine/crm_paths.py`, `engine/safe_write.py` | Shared with your CRM. Written only if missing, never overwritten |
| `tests/test_doorman.py` | The proof |

---

## The tests are the proof

```
python3 tests/test_doorman.py
```

Each check is there because of something that would otherwise be believed rather than known —
most importantly that the sixth check really is answered by your CRM's counter and is not faked
here.

| Exit code | What it means |
|---|---|
| **0** | Everything passed. |
| **1** | Something failed. The line that failed says what. |
| **2** | Your CRM was not found, so the tests stopped rather than run a shorter version of themselves. Not a fault in this layer — install your CRM's safety layer and run it again. |

That third case matters. A check that did not run is not a check that passed, so this refuses to
report green on a partial run. If your CRM is somewhere unusual, point at it:

```
OUTLIERS_CRM=/path/to/your/CRM python3 tests/test_doorman.py
```

No browser, no network, and it never touches your real CRM — every test points at a throwaway
folder first.

---

## Why reading is not free

It is tempting to think limits are for sending, and that looking at pages costs nothing.
Looking is where most of the risk sits.

- Reading who reacted to a post is the most visible activity in the whole set.
- A free search allowance is spent by **searching**, not by what the search returns.
- Speed alone raises a flag long before any limit is reached, because no person opens forty
  pages in a minute.
- Being regular is a signature on its own. One action exactly every forty-five seconds is a
  pattern no person produces, and being under your limit does not help you.

That is why the pauses here are not one narrow range with a little randomness in it. They are
mostly brisk, sometimes distracted, and occasionally very long — which is what real attention
looks like from the outside.

---

## What this layer leaves unsolved

You now have a browser that can go outside and nothing that goes anywhere. The doorman stands at
a door nobody has walked through, and the only way to know it works is to send something through.

**Next: Layer 2 — Going and looking.**

This repo is made automatically from outliers-gather-01-foundation@d8d2331. To report a problem or suggest a change, use that repo, not this one.
