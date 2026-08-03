# Results and Discussion

Three way comparison of Regex, GPT-5, and Claude Sonnet 4.6 on the 100 input
Prompt2Cal benchmark. Source data: `benchmark/outputs/summary.json` (GPT-5) and
`benchmark/outputs_claude/summary.json` (Claude Sonnet 4.6).

## 5. Results

### 5.1 Evaluation setup

Three extractors were evaluated on the 100 input stratified benchmark: a Regex baseline, GPT-5 from OpenAI, and Claude Sonnet 4.6 from Anthropic. Each input was processed once by Regex and three times by each large language model. All timestamps were normalised to the Australia/Sydney timezone, and predicted events were aligned to ground truth using greedy Levenshtein matching before field level precision, recall, and F1 were computed over the six schema fields.

Both language models used an identical prompt, schema, and post processing pipeline, so only the underlying model differed. One methodological difference concerns temperature. GPT-5 does not accept a custom temperature value and therefore ran at the API default, whereas Claude ran at a temperature of 0.0, which is deterministic decoding. Claude's consistency is therefore measured under stricter conditions.

### 5.2 Overall accuracy

| Extractor | Mean F1 | SD | F1 equal to 0 | F1 at least 0.9 | Fully correct |
|---|---|---|---|---|---|
| Regex | 0.025 | 0.146 | 97 | 0 | 1 |
| GPT-5 | 0.679 | 0.305 | 15 | 31 | 3 |
| Claude Sonnet 4.6 | 0.756 | 0.174 | 3 | 27 | 4 |

Both language models vastly outperformed Regex. Claude achieved the highest mean F1 at 0.756 compared with GPT-5 at 0.679, and it also produced the lowest variance, with a standard deviation of 0.174 against 0.305. This indicates more uniformly reliable extraction across inputs.

### 5.3 Accuracy by category

| Category | Regex | GPT-5 | Claude Sonnet 4.6 |
|---|---|---|---|
| Clean | 0.095 | 0.779 | 0.829 |
| Typos | 0.000 | 0.709 | 0.759 |
| Voice to text | 0.000 | 0.714 | 0.780 |
| Ambiguous | 0.030 | 0.610 | 0.654 |
| Missing fields | 0.000 | 0.583 | 0.759 |

Claude outperformed GPT-5 in every category, with the largest margin on missing field inputs at plus 0.176 F1. Regex achieved marginal performance only on clean inputs and scored zero F1 in every other category.

### 5.4 Robustness

Robustness was measured as the relative F1 drop from clean inputs to noisy inputs, where noisy inputs combine the typos and voice to text categories.

| Extractor | Clean F1 | Noisy F1 | Robustness drop |
|---|---|---|---|
| Regex | 0.095 | 0.000 | 100 percent |
| GPT-5 | 0.779 | 0.711 | 8.7 percent |
| Claude Sonnet 4.6 | 0.829 | 0.769 | 7.2 percent |

Claude was marginally more robust than GPT-5, with a 7.2 percent drop against 8.7 percent, retaining roughly 93 percent of its clean input performance under noise. Regex collapsed entirely on noisy inputs.

### 5.5 Consistency

| Extractor | Mean pairwise consistency | Decoding condition |
|---|---|---|
| GPT-5 | 0.707 | API default temperature |
| Claude Sonnet 4.6 | 0.733 | Temperature of 0.0 |

Claude was more consistent than GPT-5, at 0.733 against 0.707, and it did so under true deterministic decoding, which makes its stability advantage methodologically stronger. Regex is deterministic by construction and therefore has an implicit consistency of 1.0.

### 5.6 Hallucination

Hallucination rate is defined as the proportion of ground truth null fields for which the extractor fabricated a non null value. It was computed on the 20 missing field inputs, since that is the category where ground truth systematically contains null fields.

| Extractor | Mean hallucination rate | SD |
|---|---|---|
| Regex | 0.000 | 0.000 |
| GPT-5 | 0.517 | 0.142 |
| Claude Sonnet 4.6 | 0.646 | 0.142 |

This is the one dimension where GPT-5 outperformed Claude. Claude fabricated absent fields more aggressively, at 0.646 against 0.517. Regex never hallucinated. Claude's higher accuracy on missing field inputs is therefore partly attributable to a greater willingness to infer and populate fields, which is a direct illustration of the accuracy versus faithfulness trade off operating within the large language model class.

### 5.7 Statistical significance

| Test | GPT-5 versus Regex | Claude versus Regex |
|---|---|---|
| McNemar (input level, N equal to 100) | p equal to 0.480 | p equal to 0.248 |
| Wilcoxon (category level, N equal to 5) | p equal to 0.0625 | p equal to 0.0625 |

Neither test reached significance at an alpha of 0.05. This reflects the strict fully correct criterion used by McNemar and the small number of category strata used by Wilcoxon. The effect sizes remain large and directionally consistent, since both language models beat Regex in all five categories and Claude beat GPT-5 in all five.

### 5.8 Summary of findings

| Dimension | Best performer |
|---|---|
| Accuracy (F1) | Claude at 0.756 |
| Low variance of accuracy | Claude at 0.174 |
| Robustness to noise | Claude at a 7.2 percent drop |
| Output consistency | Claude at 0.733, under a temperature of 0.0 |
| Faithfulness (low hallucination) | GPT-5 at 0.517 among the language models, and Regex at 0.000 overall |

Claude Sonnet 4.6 is the strongest extractor on four of the five dimensions and trades only faithfulness. Regex remains faithful by abstention but functionally inadequate as a standalone extractor for this domain.

## 6. Discussion

### 6.1 Answering the research question

This study compared three extractors across four reliability dimensions on a 100 input benchmark of informal calendar scheduling language. The results give a clear answer to the research question.

On accuracy, both language models decisively outperformed Regex, and Claude led with a mean F1 of 0.756 against GPT-5 at 0.679 and Regex at 0.025. This aligns with Latifi (2025), who found that language models handle ambiguous and context dependent language more effectively than traditional natural language processing tools. It also extends findings from domain specific comparisons such as Dennstadt et al. (2025), who observed that Regex patterns cannot account for all linguistic variation, a limitation that proved severe here, where Regex scored zero F1 on 97 of 100 inputs.

On robustness, the language models retained most of their clean input performance under noise, with drops of 7.2 percent for Claude and 8.7 percent for GPT-5, while Regex collapsed to a 100 percent drop. This is a novel contribution, since prior work has compared accuracy on clean structured data but has not systematically measured degradation under the input imperfections common in real productivity workflows.

On consistency, Claude achieved a mean pairwise agreement of 0.733 and GPT-5 achieved 0.707. This partially addresses the gap identified by Huang et al. (2024), who noted that existing benchmarks rarely evaluate output stability over repeated extractions.

On hallucination, GPT-5 fabricated absent fields at a rate of 0.517 and Claude at 0.646, while Regex never fabricated. This confirms the concern raised by Liu et al. (2024) and Dang et al. (2025) that language models tend to populate fields rather than return null, and it resonates with Marin (2026), who argued that hallucination is an architectural tendency rather than a prompting artefact.

In summary, the language models are substantially more accurate and robust for unstructured calendar text, but they trade faithfulness for flexibility. Regex is faithful by abstention but functionally inadequate on its own.

### 6.2 The distribution of failures

A notable difference between the two language models lies in the distribution of failures rather than the average alone. GPT-5 produced a completely failed extraction, meaning an F1 of 0, on 15 of 100 inputs, whereas Claude did so on only 3. This large reduction in catastrophic failures is the primary driver of Claude's higher mean F1, at 0.756 against 0.679, and its substantially lower variance, at a standard deviation of 0.174 against 0.305. Interestingly, GPT-5 recorded slightly more near perfect extractions, with 31 inputs at an F1 of at least 0.9 against Claude's 27, which suggests that GPT-5 behaves in a more all or nothing manner, achieving more perfect scores but also more total failures. Claude, by contrast, is more uniformly reliable, rarely excelling beyond GPT-5 on any single input yet rarely collapsing. For a calendar application, where a completely missed event is more damaging to user trust than a partially imperfect one, Claude's tendency to avoid catastrophic failures is arguably more valuable than a marginally higher rate of perfect extractions.

### 6.3 The accuracy versus faithfulness trade off

The most consequential finding is not the size of the accuracy gap but its shape, and adding a second language model shows that the trade off operates within the language model class rather than only between language models and Regex. Claude is more accurate than GPT-5 precisely on the category, missing fields, where it also hallucinates more, at plus 0.176 F1 alongside plus 0.129 hallucination. This supports the argument by Marin (2026) that a more capable model does not necessarily abstain more, and may instead infer more, raising both accuracy and fabrication together. For a calendar application this means model selection cannot be reduced to choosing the highest F1 model, because a model that scores higher by populating uncertain fields may create more incorrect events in practice.

This pattern is also consistent with Nishimura et al. (2025), who reported that a leading model excels at string based extraction but struggles with date precision, a field that is central to calendar events. In this benchmark, the lowest category scores for both models were on ambiguous and missing field inputs, which are exactly the categories where the correct answer often requires the model to withhold inference.

### 6.4 Consistency findings are strengthened methodologically

Because Claude supports a temperature of 0.0, its higher pairwise consistency of 0.733 reflects genuine deterministic decoding, whereas GPT-5 was measured under a forced default sampling condition. This removes a confound that was flagged as a limitation in the original single model study and gives a cleaner estimate of the output stability that is achievable in practice.

### 6.5 Implications for system design

Three practical recommendations follow from these results.

First, user facing confirmation is essential. With only a handful of inputs fully correct under either language model, and hallucination rates above 0.5 on missing field inputs, automatically committing extracted events without review would produce unreliable calendars. A preview before create flow is therefore a reliability requirement rather than a user experience preference.

Second, confidence scoring should reward abstention. A parser that returns partial events with explicit null values is more trustworthy than one that fills every field. The hallucination metric provides a foundation for such scoring, since fields where ground truth is null and the model predicts a value should reduce confidence. This matters more when using the higher accuracy model, because Claude's elevated hallucination rate means its confident looking outputs need closer scrutiny.

Third, the rules first routing logic proposed by Kumar (2026) should be recalibrated. On this benchmark Regex handled almost none of the inputs, scoring zero F1 on 97 of 100, so a routing strategy that assumes Regex can serve most inputs would not hold. A more realistic strategy uses Regex as a lightweight confirmation of high confidence pattern matches, and uses agreement between Regex and a language model as a faithfulness anchor, while routing everything else to the language model with mandatory review.

### 6.6 Limitations

Several limitations should be acknowledged. The dataset contains 100 inputs across five categories of 20 each, which is modest by the standards of natural language processing benchmarking, and this limited the statistical power of both the McNemar and Wilcoxon tests. Both language models are proprietary frontier models, so the results may not generalise to open weight or smaller locally deployable models, as shown by the performance variation reported in Nawalny et al. (2025). The temperature condition differed between the two language models, since GPT-5 ran at its default while Claude ran at a temperature of 0.0, which means the two were not evaluated under identical decoding conditions and this is a residual confound for the accuracy and consistency comparisons. Hallucination rate could only be computed on the 20 missing field inputs, so the reported rates describe behaviour on incomplete inputs specifically rather than across the full benchmark. This evaluation focused on reliability dimensions only and did not measure latency or cost, which prior work identifies as major advantages of Regex. Finally, the ambiguous and missing field labels required judgement calls, and different labelling conventions would shift the F1 and hallucination scores.

### 6.7 Contribution and future work

This study addresses the gap identified in the literature review, since no prior evaluation has compared language model and rule based extractors on informal everyday calendar scheduling language across multiple reliability dimensions at once. By adding a second language model, the study further shows that the observed trade offs persist across two independently developed frontier models while still revealing meaningful differences between them, which strengthens the empirical basis for reasoning about the sweet spot between rule based rigidity and language model flexibility.

Three extensions would strengthen these findings. First, expanding the benchmark beyond 100 inputs and adding a human adjudication pass would improve statistical power and label reliability. Second, evaluating open weight models would clarify whether the trade offs are specific to frontier models or more general. Third, a user study that measures how confidence scoring and preview workflows affect trust and correction rates would connect the reliability metrics to real world adoption.
