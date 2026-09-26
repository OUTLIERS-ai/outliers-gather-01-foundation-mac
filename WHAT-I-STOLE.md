# What I stole

Nothing in this layer is original, and none of it cost anything. Naming where each idea came
from is the practice, not a courtesy — you should be able to do the same on your next build,
and knowing what already exists is most of the work.

---

## Playwright — Microsoft, Apache 2.0

The browser control. It drives a genuine Chromium the way a person drives a browser: clicking
real controls, typing at a real speed, scrolling. Free, maintained by people who work on
browsers for a living, and installed with two lines.

**Why this rather than writing it yourself.** Talking to a browser properly is thousands of
hours of work that has already been done, twice, by two large companies. Nobody should be
writing that in 2026.

**What was deliberately NOT taken.** There is a family of add-ons that disguise an automated
browser — changing what it reports about itself, its screen, its graphics card, its location.
They are skipped on purpose. This runs on your own machine, on your own connection, in a real
browser, which is already the most ordinary set of details a site can see. A genuine browser
telling one lie about itself is **easier** to spot than one telling none, because the lie
disagrees with everything around it. The honest fingerprint is the asset. Do not spoof it.

---

## The chokepoint idea — from your own CRM's safety layer

The rule that every activity asks one counter for room, rather than each keeping its own
allowance, is not invented here. You built it. This layer asks it as the last of its six checks
and keeps no second copy.

Taking this rather than writing a new counter is the single most important decision in the
layer, and it is worth saying why: two counters is the same as no counter. The moment a second
one exists, the total nobody agreed to becomes reachable again, and the layer that teaches the
lesson would be the layer that broke it.

---

## Human pacing — from published account-safety research, 2026

The shape of the pauses, the working window, the ramp and the ban signals come from a survey of
what the automation vendors publish and what platform help pages actually document, done in
June 2026. Two findings changed the design:

- **It is behaviour, not technology.** For something running on your own machine and your own
  connection, roughly nine tenths of the risk is in timing, volume and rhythm, and almost none
  of it is in what the browser reports about itself.
- **The published caps are ceilings that flagged accounts sit near, not safe operating points.**
  Every default here is a fraction of them.

Numbers from that survey are ranges reported by vendors rather than figures any platform
publishes, and they are treated as directional. Nothing here depends on a specific one being
exactly right.

---

## The ramp — from the cloud outreach tools, inverted

The graduated start is lifted straight from tools built the opposite way to this one. They ramp
because they have to manufacture a history their account does not have. Running on your own
machine, you already have the history — the ramp exists only so today never looks unlike
yesterday.

**And the honest caveat, which those tools do not print.** A slow ramp saves nobody if the
underlying rhythm is robotic. Volume and rhythm are two separate problems. That is why this
layer solves both and says so.

---

## What nothing here does

No paid service. No account with anybody. No key, token or subscription. Nothing leaves your
machine except the pages the browser asks for, which is what a browser is.
