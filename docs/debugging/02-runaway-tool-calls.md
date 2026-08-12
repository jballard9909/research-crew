# Bug 02 — Runaway tool calls on the Web Researcher

**Status:** Resolved
**Date identified:** 08/10/26
**Component:** `research_crew/crew.py` — `web_researcher` agent

## Symptom

The first full pipeline run consumed over 100 Serper API calls on a single topic
("the economic impact of remote work"). Verified against both the verbose run log and the
Serper.dev dashboard.

## Investigation

Reading the verbose log, the agent was not stuck in a loop or repeating identical queries.
It was searching productively — but long past the point of having enough material to
answer the research question. It chased corroborating sources for details already
supported and searched to confirm exact wording of specific claims.

This was a stopping-condition problem, not a logic error. The agent had no definition of
"enough," and nothing forced one on it.

## Root cause

Two gaps, one structural and one instructional:

- The agent had no ceiling on tool-call iterations
- Nothing in the goal or backstory told it when to stop researching a question

## Fix

**1. A hard ceiling.**

```python
web_researcher = Agent(
    ...
    max_iter=25,
)
```

**2. Prompt-level stopping guidance** added to the backstory: once the agent has 2–3
solid, well-sourced findings for a research question, move on rather than continuing to
search for additional corroboration or chase a single source's exact wording.

The two changes do different jobs. The ceiling bounds the worst case. The instruction is
what keeps the agent from reaching the ceiling in the first place — a cap alone would
still permit 25 iterations of unproductive searching on every question.

## Evidence

Serper dashboard call counts, before and after:

| Run | Serper calls |
|-----|--------------|
| Middle-school Music Engagement — before fix | 104 |
| AI School Impact — after fix | 14 |
| Fastest Growing Careers — after fix | 20 |

The dashboard itself is not committed to this repo, so these figures rest on my record
rather than on an artifact a reader can inspect. Reports produced by the post-fix runs are
in [`examples/`](../../examples/).

I did not run a controlled comparison against the uncapped configuration. The pre-fix run
terminated on an API error before producing a report, so there is no "before" report to
compare against the four "after" reports.

## Unresolved observation

The pre-fix run terminated with an Anthropic API error referencing `assistant message
prefill`. Root cause was never confirmed. It may be related to the high iteration count,
or it may be unrelated and coincidental. Recording it here for completeness — it has not
recurred in any post-fix run.

## Takeaway

Any agent with a search tool needs both a hard iteration ceiling and prompt-level guidance
on what "enough" means. Without the ceiling there is no worst case. Without the guidance,
the ceiling becomes the default.
