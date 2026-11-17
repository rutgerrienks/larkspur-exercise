# Client review: Larkspur disruption-care agent

**To:** Room 2  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-17 10:07

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. PITCH.md Number says 13k input and 1k output tokens across five ticket types, but the only committed run is readout-trace.json.**

readout-trace.json records one run: 18556 tokens in, 1080 out, 4 API turns, 5 tool calls. The 13k average is not in that trace, and PITCH.md names no five-run output and no bench file. The 18556 is also above 13k, so the single run you can show sits well over your stated average.

Run python3 run.py --all --trace and paste the totals footer, so the per-booking token counts behind the 13k are visible.

**2. agent.py has no cache_control, and readout-trace.json shows 0 tokens read and 0 written from cache.**

Every create() call in run_agent() resends runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM plus tool_list(), now 11 schemas. The trace's hit ratio is None. The same prefix is paid for on each of the 4 turns, and a bigger model would repeat that bill at a higher price.

Run python3 run.py --tool-tax and paste its output, so the per-turn cost of your 11 tool definitions is a number.

**3. The loop in run_agent() reads tool_calls < MAX_TOOL_CALLS with MAX_TOOL_CALLS = 8, and no run in the repo reaches 8.**

Your diff replaced the turn counter with tool_calls += len(results) and added a fallback string, "I'm handing this to a colleague who can finish it for you." The committed trace shows 5 tool calls over 4 turns, so the fallback has never fired on any evidence you can show. A model change cannot tell you whether an 8-call booking shape ends in a clean handoff.

Run python3 run.py --all --trace and paste any booking where tool calls reach 8, or state that none does.

**4. hold_seat and send_confirmation are 73 and 71 characters in build_tools(), and you rewrote neither.**

Your diff touched search_alternatives (920 characters), next_available_day (593) and fare_rules (936). hold_seat reads "Place a 15-minute hold on one alternative. Reversible. It simply expires." and send_confirmation is one sentence. Both are the tools closest to the customer, and the readout-trace.json run never calls either.

Run python3 verify.py 1.3 and paste the result, then run python3 run.py --show-tools and paste the two short descriptions.

**5. PITCH.md Next says to cover "all the possible dialogue options", and there is no evals/cases.json to hold them.**

The repository contains agent.py, PITCH.md, TEAM.md, readout-trace.json and readout.html, with no eval cases. Banked gates run 1.2 to 2.2 only, so 3.1 and 4.1 have no recorded result. Your Lever line still reads "<cost | speed | intelligence>" with nothing chosen, so the answer to Priya's model question has no target yet. The unfilled TONE_ADDENDUM at 0 characters is a separate gap from the model.

Run python3 eval_harness.py and paste the suite output, then fill in the Lever line in PITCH.md with the one you are optimising.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (308 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
