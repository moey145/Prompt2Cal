# Ground-truth labelling notes

Draft notes for supervisor review (target: 10% of dataset). Updated during Phase 5 label refinement.

## Ambiguous category

All ambiguous inputs label `start_time: null` when the clock time is vague, even if a day is mentioned (for example, "around 7ish"). This matches the proposal example in Table 1.

| ID | Rule applied |
| --- | --- |
| ambiguous_01–20 | Vague or approximate time expression → `start_time: null`; title extracted from event description |

## Missing-fields category

| ID | Rule applied |
| --- | --- |
| missing_01, 08, 14, 19, 20 | Date/day in text but no clock time → day-only `start_time`, not `null` |
| missing_02 | "Friday" present → `start_time: "friday"` |
| missing_03, 05, 07, 10, 12–13, 16 | No date or time in text → all temporal fields `null` |
| missing_06 | "next week" is a range, not a specific day → `start_time: null` |
| missing_09, 15 | Location explicit, time absent → `location` set, `start_time: null` |
| missing_18 | Recurrence explicit ("every Monday"), no clock time → `recurrence_type: weekly`, `start_time: null` |

## GPT-5 API note (Phase 5)

OpenAI's GPT-5 endpoint rejects `temperature=0`; the harness omits the parameter and uses the model default. Consistency is measured via three repeated runs per input, as specified in the proposal.
