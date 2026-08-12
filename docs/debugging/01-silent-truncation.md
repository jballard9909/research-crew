# Bug 01 — Silent truncation of Writer output

**Status:** Resolved
**Date identified:** 08/10/26
**Component:** `research_crew/crew.py` — shared `LLM` object

## Symptom

Reports saved to `outputs/` ended mid-sentence. The run raised no exception, logged no
warning, and exited normally. The pipeline reported success and wrote a partial file.

## Investigation

Planner and Web Researcher output looked complete. Both produce comparatively short
output: A question list and a set of findings. The Writer was the only agent generating
a long, multi-section report with inline citations, and it was the only one affected.

That pattern (failure correlated with output length rather than with topic, agent logic,
or input) pointed at an output-length ceiling rather than a bug in the prompt or task
wiring.

## Root cause

The `LLM` object was instantiated without `max_tokens`. Generation stopped at the default
ceiling and returned what it had produced so far.

*Inferred, not directly confirmed:* the request appears to terminate normally from the
framework's perspective, so CrewAI passes the partial string through as a successful
result rather than raising. I did not instrument the response object to verify the stop
reason. [VERIFY OR CUT — you can confirm this by logging the raw response.]

## Fix

Two changes.

**1. Set `max_tokens` explicitly.**

```python
llm = LLM(model="anthropic/claude-sonnet-5", max_tokens=16000)
```

[FILL IN: why 16000 specifically — e.g. "sized above the longest report observed during
testing." If the number was arbitrary, say so; an honest arbitrary is better than an
invented rationale.]

**2. Add a truncation check in `run()`.**

```python
if not output.rstrip().endswith((".", "!", "?", ")", "*")):
    print(
        "\n WARNING: Output may be truncated — it doesn't end with "
        "normal sentence punctuation. Check max_tokens on the LLM object.\n"
    )
```

This is a heuristic, not a guarantee. It will miss a report that happens to be cut off at
a period, and it can false-positive on output ending in an unusual character. It was
chosen because the original failure mode was *silence* — a check that sometimes cries wolf
is strictly better than no signal at all.

## Evidence

The original truncated output was not retained. The four reports in [`examples/`](../../examples/) 
were generated after the fix and each terminates normally.

## Takeaway

Set `max_tokens` explicitly on any agent producing long-form output. The default is not
"as much as needed," and exceeding it does not raise. Where a failure can be silent, add
a cheap check that makes it loud.
