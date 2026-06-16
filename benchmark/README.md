# Benchmark dataset

This folder holds the stratified benchmark used by the research evaluation harness.

## Files

- `dataset.json` — 100-input stratified benchmark (20 per category). Rebuild from `inputs_catalog.py` via `scripts/build_benchmark_dataset.py`.
- `outputs/` — created by the evaluation runner (one JSON file per input plus `summary.json`).

## Categories

| Category | Target count |
| --- | --- |
| `clean` | 20 |
| `typos` | 20 |
| `voice_to_text` | 20 |
| `ambiguous` | 20 |
| `missing_fields` | 20 |

## Ground-truth labelling rules

1. Label all six fields for every event: `title`, `start_time`, `end_time`, `location`, `notes`, `recurrence_type`.
2. Use `null` when a field is absent or not reasonably inferable from the text alone.
3. For ambiguous times such as "around 7ish", label `start_time` as `null`.
4. For missing-field inputs, label absent fields as `null` so hallucination can be measured.
5. Use lowercase titles in ground truth; the harness normalises casing before comparison.
6. Dates may be stored as natural language (for example, `"next tuesday at 3pm"`). Both predictions and ground truth are normalised through the shared date parser before scoring.

## Labelling rules for ambiguous and missing-field inputs

- **Ambiguous inputs** — label `start_time` as `null` whenever the clock time is vague or approximate, even if a weekday appears in the text (matches proposal Table 1).
- **Missing-field inputs** — label any field explicitly present in the text (date, location, recurrence) and `null` only for fields genuinely absent. `(no time)` means no clock time, not no date.
- Document non-obvious decisions in `benchmark/labelling_notes.md` for supervisor review.

## Adding a new input

```json
{
  "id": "clean_03",
  "category": "clean",
  "text": "Yoga class Saturday 8am at Bondi Gym",
  "ground_truth": [
    {
      "title": "yoga class",
      "start_time": "saturday at 8am",
      "end_time": null,
      "location": "bondi gym",
      "notes": null,
      "recurrence_type": "none"
    }
  ]
}
```

Have a supervisor review at least 10% of labels before running the full benchmark.
