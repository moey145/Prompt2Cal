# Weekday prompt rule experiment (28 September 2026)

**Not part of the capstone report.** The report's results are in
`benchmark/outputs/` (GPT-5) and `benchmark/outputs_claude/` (Claude Sonnet
4.6), produced by the code at tag `capstone-results`.

## What was tested

After the report, a rule was added to the system prompt telling the model to
write a weekday the user did not call "next" as the soonest one ("Monday at
9am", not "next Monday at 9am"). The aim was to stop "every Monday" starting a
weekly series a week late.

| Folder | Run | Claude mean F1 |
| --- | --- | --- |
| `benchmark/outputs_claude/` | Report baseline, 100 inputs × 3 runs | 0.756 |
| `full_run/` | Prompt rule added, 100 inputs × 3 runs | 0.716 |
| `spot_check/` | Reworded rule, the 21 inputs that moved, × 1 run | 0.615 on those 21 (baseline 0.738) |

## Outcome

The rule was reverted. On four vague inputs ("Catch up with Sam when we can")
the model began returning no event at all, which scores zero. The weekday
problem is now handled in code instead (`drop_unasked_next` in
`backend/services/event_parser.py`).

## Caveat

Both runs also include a bug, introduced by a log-redaction change and later
fixed in commit `1580e2a2`: the recurrence rules read a placeholder instead of
the user's text, so a series stated "for the next 4 weeks" lost its end. The
F1 differences therefore mix the prompt rule with that bug, and only the four
empty-answer regressions can be attributed to the rule with confidence.
