# Comparing Large Language Models and Rule-Based Systems for Calendar Event Extraction: A Comprehensive Reliability Study

**Final Report, Engineering Capstone (41030 and 42003)**

Student: Mohamad Eldhaibi
Supervisor: Mahira Mohamed Mowjoon
Project platform: Prompt2Cal (Chrome extension and evaluation harness)

---

## Abstract

Millions of events are published daily in unstructured natural language across emails, newsletters, and messages, yet users must still transfer this information into calendar tools by hand. This project investigated whether Large Language Model (LLM) based extraction or traditional rule-based (Regex) extraction is more reliable for converting informal scheduling language into structured calendar events. A controlled quantitative experiment was conducted using Prompt2Cal, a purpose-built dual parser platform, on a stratified benchmark of 100 informal calendar inputs spanning five categories: clean inputs, typos, voice to text artefacts, ambiguous expressions, and missing fields. Reliability was operationalised through four separately measured dimensions: accuracy (field level F1), robustness (relative F1 degradation under noisy input), consistency (pairwise agreement across repeated runs), and hallucination rate (fabrication of absent fields). The evaluation compared a 23 pattern Regex parser against two frontier LLMs, GPT-5 and Claude Sonnet 4.6, with each LLM run three times per input. Results show that both LLMs vastly outperformed Regex on accuracy (mean F1 of 0.679 for GPT-5 and 0.756 for Claude against 0.025 for Regex) and robustness (drops of 8.7 percent and 7.2 percent against a complete 100 percent collapse for Regex). However, the LLMs fabricated absent field values on more than half of all opportunities (0.517 for GPT-5 and 0.646 for Claude), while Regex never hallucinated. A lightweight source grounding verifier, implemented post hoc over the stored outputs with rules frozen before scoring, detected 80 percent of GPT-5 fabrications and 96 percent of Claude fabrications on the missing field subset at a false flag rate of approximately 4 percent, demonstrating that the recommended confidence scoring is practically achievable. The findings demonstrate that the accuracy versus faithfulness trade off operates not only between method classes but also within the LLM class, and they yield practical decision criteria for engineers selecting extraction methods for productivity tools: LLM extraction is necessary for informal text, but must be deployed behind user confirmation workflows and confidence scoring that rewards abstention.

---

## 1. Introduction

### 1.1 Background and context

Digital calendars are central to personal and professional productivity, yet the information that populates them rarely arrives in structured form. Event details are embedded in casual emails, community newsletters, group chats, and voice notes, phrased in informal language such as "Dinner at Sarah's next Thursday around 7ish". Users currently bridge this gap manually, reading unstructured text and re-typing dates, times, and locations into scheduling tools. This process is tedious, error prone, and repeated millions of times daily across the population of calendar users.

Automating this task requires reliable event extraction: converting natural language descriptions into structured event objects with discrete fields for title, start time, end time, location, notes, and recurrence. Two fundamentally different engineering approaches exist. Traditional rule-based systems using Regular Expressions (Regex) match predefined textual patterns and are fast, deterministic, and inexpensive, but they are brittle when language deviates from expected forms. Large Language Models (LLMs) interpret language flexibly and can handle ambiguity, but they introduce concerns around hallucination, where the model fabricates plausible values for information that is absent from the input (Dang et al., 2025), reduced accuracy on numeric variables such as dates and times (Kataoka et al., 2025), and substantially higher computational cost per query (Suneja, 2026).

Prior comparative studies have evaluated these approaches in formal domains such as radiology report parsing (Dennstadt et al., 2025) and CV to JSON extraction (Nawalny et al., 2025). However, no prior study had evaluated them on informal calendar scheduling text, and existing comparisons typically report a single aggregate metric, collapsing the trade offs between dimensions that matter differently in different deployment contexts.

### 1.2 Aims and objectives

The aim of this project was to conduct a controlled, reproducible comparison of LLM based and rule-based event extraction on informal calendar language, measured across four separately reported reliability dimensions, and to derive practical decision criteria for engineers building productivity tools.

The specific objectives were to:

1. Design and construct a stratified benchmark of 100 informal calendar event descriptions with manually labelled ground truth, covering clean inputs, typos, voice to text artefacts, ambiguous expressions, and missing fields.
2. Implement an evaluation harness within the Prompt2Cal platform capable of running multiple extractors under identical conditions, aligning multi event outputs to ground truth, and computing all four reliability metrics.
3. Execute the full benchmark against a 23 pattern Regex parser and the GPT-5 LLM extractor, with three repeated LLM runs per input to measure consistency.
4. Extend the evaluation with a second frontier LLM, Claude Sonnet 4.6, to test whether observed trade offs are model specific or persist across independently developed models.
5. Analyse the results statistically, interpret the trade offs, and derive evidence based decision criteria for extraction method selection.
6. Implement and evaluate a lightweight source grounding verifier over the stored extraction outputs, testing whether the fabrications measured by the hallucination metric can be detected automatically at acceptable usability cost.

### 1.3 Research question

The main research question is:

> How reliable is LLM based event extraction compared to rule-based methods for informal natural language calendar text?

This is operationalised through four sub questions, each addressing a distinct reliability dimension:

- **SQ1 (Accuracy):** How does field level extraction accuracy compare between the LLM based and rule-based methods across the benchmark dataset?
- **SQ2 (Robustness):** How much does extraction accuracy degrade for each method when inputs contain typos or voice to text artefacts compared to clean inputs?
- **SQ3 (Consistency):** How consistent are the LLM extractor's outputs across three repeated runs on the same input, compared to the rule-based parser's deterministic baseline?
- **SQ4 (Hallucination rate):** What proportion of absent fields does each method fabricate when inputs are missing required information?

### 1.4 Scope and limitations

The scope of this study is the technical comparison of extraction methods on constructed benchmark inputs. The Prompt2Cal Chrome extension provides the engineering platform, but the rules first, LLM fallback production architecture is treated as engineering context rather than a third experimental condition. A user perception study was considered during proposal development and explicitly scoped out in consultation with the project supervisor, and it is identified as future work.

One deliberate extension beyond the approved proposal was made during execution. The proposal specified a single LLM (GPT-5). During the analysis phase, a second frontier LLM (Claude Sonnet 4.6) was added as a comparison condition. This extension directly addresses the single model limitation identified in the proposal, tests whether the observed trade offs are architectural or model specific, and reuses the identical prompt, schema, and post processing pipeline so that only the underlying model differs. The deviation is documented transparently in the methodology and discussion sections.

The study does not measure extraction latency or per query cost as formal experimental variables, although indicative observations are reported. It evaluates two proprietary frontier models and one rule-based parser; open weight models are out of scope. These limitations are discussed in Section 6.

### 1.5 Report structure

Section 2 reviews the literature and defines the research gap. Section 3 details the methodology, including the benchmark design, the evaluation pipeline, the metric definitions, and the statistical analysis plan. Section 4 presents the findings for each sub question. Section 5 discusses the meaning and implications of the results, including the derived decision criteria. Section 6 acknowledges limitations. Section 7 documents project organisation, supervisor feedback, and personal reflection. Section 8 concludes with recommendations and future work. Appendices provide the benchmark dataset, system prompt, labelling notes, raw artefacts, and communication logs.

---

## 2. Literature Review

### 2.1 From rule-based systems to LLM based extraction

Event Extraction is a subfield of Information Extraction that identifies event triggers and their details, including time, location, and description, directly from natural language (Lai, 2022). There is broad agreement that traditional rule-based systems using Regex and pattern matching are reliable when dealing with structured information. Liu et al. (2024) observed that a major challenge for LLMs compared to traditional rule-based approaches is hallucination, and suggested that integrating rule-based methods into LLM frameworks can improve faithfulness and reliability.

The emergence of generative LLMs has changed the field by allowing a more open way of extracting information. Latifi (2025) found that LLMs generally outperform traditional natural language processing tools when handling ambiguous, context dependent language, though conventional systems remain preferable where determinism and speed are priorities. Dennstadt et al. (2025) reinforced this by showing that Regex was over 28,000 times faster than an LLM on structured data extraction, yet its patterns could not account for all linguistic variations, suggesting that LLMs are better suited for more complex, unstructured text. However, that comparison was conducted on highly structured medical reports, leaving open whether the same trade off holds for informal user generated text such as the natural language people use when describing upcoming events.

### 2.2 Hallucination as an architectural limitation

A key point of divergence in the literature concerns the trade off between flexibility and faithfulness. The primary concern is hallucination, where LLMs fabricate event fields when information is missing, rather than returning null as rule-based systems would (Dang et al., 2025). Recent peer reviewed work goes further, arguing that hallucination is not a removable flaw but an intrinsic outcome of transformer based generalisation, best managed through external verification rather than eliminated (Singh et al., 2026). This position is supported by Huang, L. et al. (2024), whose survey identifies hallucination as arising from multiple architectural and inference stage factors, including the unidirectional pre training objective and the tendency toward over confidence during token generation. If hallucination is genuinely architectural rather than fixable, then empirical measurement of hallucination rates becomes essential for any deployment decision, rather than something that can be engineered away through prompt design. This project's fourth reliability dimension directly operationalises that requirement.

### 2.3 Hybrid architectures and cost trade offs

There is also disagreement on the practicality of LLMs for high volume event parsing, given their time inefficiency and high token costs compared to lightweight Regex parsers (Suneja, 2026). Nawalny et al. (2025) found that open weight models reached only 73 to 79 percent completeness compared to GPT-4o, revealing that even within LLM based approaches, significant performance and cost trade offs exist. These limitations have fuelled interest in hybrid architectures. Hybrid approaches have a long precedent in information extraction: Keraghel et al. (2024) document that combining rule-based methods with machine learning has repeatedly improved accuracy in complex text domains such as biomedical literature, supporting the intuition that neither approach dominates on its own. Kumar (2026) proposed one such pattern, a rules first, LLM fallback architecture that routes predictable inputs through Regex and reserves LLM calls for ambiguous cases, reportedly reducing costs by around 70 percent. Whether this orchestration logic generalises beyond structured form validation to more complex domains such as event extraction remained an open question that this project's results now inform.

### 2.4 Gaps in existing benchmarks

While researchers have compared LLMs and Regex on domain specific tasks, including radiology report parsing (Dennstadt et al., 2025) and CV to JSON extraction (Nawalny et al., 2025), these evaluations have not addressed the informal, ambiguous event descriptions typical of calendar scheduling contexts. Huang, K.-H. et al. (2024) evaluated five LLMs across 16 standardised event extraction datasets spanning eight diverse domains, including news, biomedical, and cybersecurity, and found that LLMs fall short of achieving reliable performance, yet none of those benchmarks reflected everyday productivity scenarios. Kataoka et al. (2025) demonstrated that while GPT-4o can achieve strong overall accuracy on structured data extraction of up to 96.3 percent, it struggles with numeric variables, a limitation the authors noted makes it unable yet to replace human extractors for numeric data. For calendar event creation, where dates, times, and durations are predominantly numeric, this limitation is particularly concerning.

Mapping prior comparative studies against text domain (formal versus informal) and dimensional coverage (single versus multiple reliability dimensions) shows that no prior study occupies the quadrant representing informal text evaluated across multiple reliability dimensions simultaneously. This unaddressed region defines the position of this research.

### 2.5 A multi dimensional framework for reliability

Existing comparisons often focus on isolated metrics such as accuracy or speed. This project operationalises four dimensions. Accuracy captures field level extraction correctness. Robustness measures performance under input imperfections, including typos and voice to text artefacts. Consistency assesses output stability across repeated runs. Hallucination rate quantifies the proportion of outputs that fabricate a field value instead of returning null when information is absent. Treating these dimensions separately, rather than collapsing them into a single accuracy score, preserves the trade offs identified in prior work instead of averaging them away.

---

## 3. Methodology

### 3.1 Research design

This research employed a quantitative experimental design in which multiple implementations of the same structured event extraction task were evaluated under controlled conditions to enable direct comparison, following the comparative evaluation approach established in prior LLM versus rule-based studies (Dennstadt et al., 2025; Nawalny et al., 2025). The task is defined as converting an informal natural language scheduling description (for example, "Lunch with Sarah next Tuesday at 1pm at the cafe") into a structured event object with six discrete fields: title, start_time, end_time, location, notes, and recurrence_type.

The study compared three extraction methods: a Regex based parser, an LLM based extractor using GPT-5 (OpenAI), and a second LLM based extractor using Claude Sonnet 4.6 (Anthropic). All methods received identical inputs and were evaluated against the same ground truth labels, isolating the extraction approach as the independent variable. The dependent variables were the four reliability dimensions: accuracy, robustness, consistency, and hallucination rate.

### 3.2 Engineering platform

The evaluation platform is Prompt2Cal, a Chrome extension with a FastAPI (Python) backend that integrates both extraction paths behind a shared interface producing standardised event outputs. The extension was originally developed as a personal productivity project and was adapted for research use during the preparation phases, with a modular architecture that separates the extraction methods so each can be tested independently.

For the research evaluation, a dedicated evaluation harness was implemented as a Python package (`backend/evaluation`) comprising:

- **Data models** defining the benchmark schema and a canonical evaluation event with the six comparison fields.
- **Normalisation** converting both extractors' natural language date and time expressions into ISO 8601 using the shared `dateparser` library, so that the comparison reflects end to end extraction performance under a common output schema rather than penalising either method for formatting differences.
- **Alignment** matching predicted events to ground truth events in multi event inputs by greedy assignment on normalised title similarity, computed as a lowercase, whitespace trimmed Levenshtein ratio via the `rapidfuzz` library, with matches accepted at similarity of at least 0.7. Predicted events with no matching ground truth count as false positives, and ground truth events with no matching prediction count as false negatives, so both over segmentation and under segmentation are penalised.
- **Metrics** implementing the four reliability dimensions and the two statistical tests.
- **A runner** orchestrating both extractors across the dataset, persisting one JSON artefact per input plus an aggregate summary, supporting reproducibility and post hoc audit.

The harness is executed through a command line script (`scripts/run_evaluation.py`) that accepts the dataset path, output directory, number of LLM repetitions, provider selection, and an optional restriction to specific input identifiers for smoke testing. Unit tests covering the metric implementations were written and passed before any benchmark execution.

### 3.3 The extraction methods under comparison

**Regex parser.** The rule-based extractor uses a pattern library of 23 distinct scheduling patterns covering explicit time ranges, 12 and 24 hour time formats with and without am/pm markers, relative and specific weekday references, week based references, explicit month and day combinations, and ordinal recurring patterns such as "first Monday of every month". When no direct pattern matches, the system falls back to the `dateparser` library for additional natural language coverage. The Regex parser does not attempt semantic interpretation of vague expressions such as "around 7ish"; in those cases it returns null for the affected field. By design it processes one event per input and does not split multi event inputs. This under segmentation is reflected in the F1 calculation and treated as a measurable comparative finding rather than excluded from analysis.

**GPT-5 extractor.** Each input is submitted to GPT-5 via the OpenAI API with a fixed system prompt instructing the model to return the six structured fields in JSON format and to return null for absent fields (the full prompt is reproduced in Appendix B). The response format is constrained to a JSON object. One deviation from the proposal arose here: the GPT-5 API rejects non default temperature values, returning an error when temperature 0 is requested. The extractor therefore omits the temperature parameter and runs at the API default. The consistency measurement design (three repeated runs per input) is unaffected, but GPT-5's consistency is measured under default sampling rather than deterministic decoding. This is documented as a methodological note and revisited in the discussion.

**Claude Sonnet 4.6 extractor.** The second LLM extractor was implemented as a subclass of the GPT extractor that overrides only the raw model call. It reuses the identical system prompt, user prompt, JSON schema, post processing, recurrence normalisation, and validation pipeline, so the two LLM conditions differ only in the underlying model. Claude has no native JSON response format flag, so JSON only output is enforced through the system prompt with defensive stripping of markdown fences. Claude accepts a temperature of 0.0, so its three runs were executed under true deterministic decoding.

### 3.4 Population and sample

The population is the set of all possible informal calendar event descriptions an end user might enter when scheduling a personal event. The sample is a benchmark of 100 event descriptions constructed by the researcher, stratified across five categories of 20 inputs each (Table 1). Within each category, recurring events and multi event inputs are distributed alongside one off single events. Seven inputs contain multiple ground truth events. The dataset size of 100 follows precedent in comparable studies: Dennstadt et al. (2025) used 100 radiology reports and Latifi (2025) employed a similarly sized pilot benchmark.

**Table 1. Stratified benchmark dataset categories.**

| # | Category | n | Description | Example |
|---|---|---|---|---|
| 1 | Clean | 20 | Well formed text with explicit date, time, and description | "Team meeting next Tuesday at 3pm" |
| 2 | Typos | 20 | Common spelling errors in dates, times, and descriptions | "Lunch meeting Wednesdya at 1pm" |
| 3 | Voice to text | 20 | Transcription errors such as homophone substitutions | "call mom Sunday eight thirty aye em" |
| 4 | Ambiguous | 20 | Vague time references and informal phrasing | "Dinner with Sarah next Thursday around 7ish" |
| 5 | Missing fields | 20 | One or more required fields absent, designed to elicit hallucination | "Meeting with John next Tuesday" (no time) |

Ground truth labels were manually constructed before running either extractor, eliminating post hoc bias toward any method. For ambiguous inputs, fields were labelled null where no specific value is reasonably inferable from the text alone; for example, a vague clock time such as "around 7ish" is labelled with a null start time even when a weekday is present. For missing field inputs, any field explicitly present in the text was labelled, and only genuinely absent fields were set to null. Non obvious labelling decisions were documented in labelling notes (Appendix C) to support supervisor review of a 10 percent subset. The full dataset with ground truth summaries is provided in Appendix A.

### 3.5 Evaluation procedure

Both extractor families processed the full benchmark under identical conditions. Each input was submitted three times to each LLM extractor, consistent with the multiple run approach used by Kataoka et al. (2025), while the Regex extractor was run once because its outputs are deterministic by construction. Timestamps were resolved relative to the Australia/Sydney timezone; run durations are reported in Section 4.8. Response caching was disabled for all evaluation runs so that every call reflected fresh model behaviour.

**Data management and verification.** All data in this study is original: the benchmark inputs and ground truth labels were constructed by the researcher, and every extractor output was generated fresh during the evaluation runs. To support verification and reproducibility, the harness persists one JSON artefact per input containing the raw Regex events, all three LLM runs verbatim, the ground truth, and the per input metrics, alongside an aggregate summary recording the complete run configuration (dataset version, timezone, repetition count, provider, and resolved model name). All artefacts, the dataset, the labelling notes, the harness source code, and its unit tests are stored in the project's version controlled Git repository, providing a tamper evident record of the data collection process. Any reported figure in this report can be recomputed from the stored artefacts, and the full benchmark can be re executed from a single documented command.

### 3.6 Metric definitions

Table 2 summarises the operationalisation of the four reliability dimensions against the four sub questions.

**Table 2. Operationalisation of the four reliability dimensions.**

| Dimension (SQ) | Measurement target | Dataset subset | Computation |
|---|---|---|---|
| Accuracy (SQ1) | Field level extraction correctness | All 100 inputs | F1 score across six fields (harmonic mean of precision and recall against ground truth) |
| Robustness (SQ2) | Accuracy degradation under noisy input | Clean subset versus typo and voice to text subsets | Relative drop: (F1 clean minus F1 noisy) divided by F1 clean |
| Consistency (SQ3) | Output stability across repeated runs | LLM extractors only (3 runs per input) | Pairwise agreement rate averaged across all three run pairs |
| Hallucination (SQ4) | Fabrication of values when ground truth is null | Missing fields subset (n equal to 20) | Fabricated fields divided by total null ground truth fields |

Two additional specifications apply to the hallucination metric. First, for multi event inputs, hallucination is measured per event field combination, so a two event input with both times missing produces two hallucination opportunities. Second, the system prompt explicitly instructs the LLM to return empty events when input is unclear (Appendix B, Rule 6), so the metric measures the model's tendency to fabricate values despite explicit instructions to abstain, a stronger test of intrinsic hallucination behaviour than measurement under unconstrained prompts, following the field level approach of Dang et al. (2025).

### 3.7 Statistical analysis

Quantitative results are summarised using descriptive statistics (mean and standard deviation per dimension). To test whether extractors differ significantly in extraction correctness, McNemar's test was applied on paired binary outcomes at the input level, where an input is classified as correctly extracted only if all events are identified with all six fields matching ground truth. This aggregation preserves the independence assumption required by McNemar's test. Differences in F1 across input categories were tested using a Wilcoxon signed rank test, appropriate for paired non parametric data. Significance is reported at an alpha of 0.05, with effect sizes reported alongside p values. Results are presented per sub question as a multi dimensional comparison rather than a single aggregate score.

### 3.8 Ethical, Indigenous, and sustainability considerations

This research involved no human participants, biospecimens, or sensitive datasets as defined under the National Statement on Ethical Conduct in Human Research (NHMRC, 2023), and therefore fell outside the categories requiring formal ethics approval. All benchmark inputs are constructed examples containing no personal or identifiable information, and API usage followed the providers' terms of service. The project aligns with Australia's AI Ethics Principles (Department of Industry, Science and Resources, 2019), particularly transparency, accountability, and reliability, which motivate the focus on measuring and disclosing LLM reliability trade offs.

The research does not involve Indigenous communities, knowledge systems, or data, and therefore does not fall within the scope of the AIATSIS Code of Ethics (AIATSIS, 2020). It is acknowledged that the informal language patterns studied reflect primarily Western English language scheduling conventions, and cross cultural extension is noted as future work.

Sustainability considerations centred on minimising computational waste. LLM API calls were limited to the planned benchmark executions (300 calls per model) plus minimal smoke tests, with no exploratory or redundant calls beyond the experimental design (Strubell et al., 2019). The broader sustainability contribution of the work is decision criteria that help developers choose computationally efficient methods where appropriate rather than defaulting to LLM approaches for every query (Suneja, 2026).

### 3.9 Confidence verification layer

To test whether the hallucinations measured under SQ4 can be detected automatically, a source grounding verifier was implemented as a post hoc analysis over the stored extraction artefacts, requiring no additional API calls. For each non null field an LLM produced, the verifier checks whether the value is locatable in the original input text using lexical rules: title tokens must fuzzy match the source (partial ratio of at least 85 for at least half of the content words), locations and notes must fuzzy match the source (partial ratio of at least 80), a start time is grounded by any explicit date or clock time signal, an end time requires explicit range or end evidence (two or more time signals, a from to construction, an until marker, or a dash adjacent to a time), and a non none recurrence requires an explicit recurrence keyword. Two deliberate rules mirror the ground truth labelling conventions: a weekday alone does not ground a clock time, and vague approximations such as "7ish" do not ground a precise time. Spelled out times such as "eight thirty aye em" do ground a time, because the voice to text category transcribes clock times as words by design.

The verifier is then evaluated as a binary hallucination detector against ground truth. For every non null predicted field, the field is fabricated if the corresponding ground truth field is null (including all fields of predicted events with no aligned ground truth event, consistent with the hallucination metric), and legitimate otherwise. A verifier flag on a fabricated field is a true positive; a flag on a legitimate field is a false positive, the usability cost. Detection recall, precision, and the false flag rate are reported on the missing field subset (the headline detection condition) and across the full dataset. To guard against tuning the detector to the results, the grounding rules were frozen and covered by 21 unit tests before the verifier was scored against any benchmark artefact, the same freeze before measurement discipline applied to the ground truth labels. This analysis falls within the planned Phase 10 scope of sensitivity analysis and additional comparison conditions.

### 3.10 Verification, sensitivity, and failure analysis

Three further post hoc analyses were conducted in the verification phase, all running over the stored artefacts without additional API calls. First, reproducibility was checked in two ways: every headline F1 figure was independently recomputed from the per input artefacts and compared against the persisted summaries, and the deterministic Regex condition was fully re executed from the documented command two weeks after the original run and compared input by input. A second full LLM re execution was attempted but halted by exhaustion of the API credit envelope; run to run stability for the LLMs is instead evidenced by the three repeated runs already collected per input under SQ3. Second, a sensitivity analysis tested whether the results depend on the 0.7 event alignment threshold by recomputing mean F1 at thresholds of 0.6 and 0.8 (`scripts/run_sensitivity.py`). Third, a failure mode taxonomy was constructed by categorising every deviation from ground truth in each extractor's primary run into seven modes defined before counting: empty output, missed event, spurious event, fabricated field, missed field, wrong time value, and wrong other value (`scripts/build_failure_taxonomy.py`).

### 3.11 Project management and risk

The project was executed across twelve planned phases spanning February to November 2026, with the proposal finalised in May 2026 (Phases 1 to 4), the benchmark construction, harness implementation, and GPT-5 migration completed in Phases 5, the full benchmark execution in Phase 6, metric computation in Phase 7, and analysis and reporting in Phases 8 onward. Key risks identified in the proposal materialised and were managed as planned. The GPT-5 migration introduced an API incompatibility (temperature rejection) that was resolved with a documented workaround rather than reverting to the GPT-4.1 fallback. A parsing defect discovered during functional testing, in which a correctly extracted multi day end time was overwritten by a default one hour duration, was fixed and covered by a regression unit test before benchmark execution. Budget monitoring kept API costs within the planned envelope, and the Claude extension was costed (approximately five dollars of API credit) and approved before execution.

---

## 4. Findings

### 4.1 Overall accuracy (SQ1)

Table 3 reports overall accuracy across all 100 inputs. Both LLMs vastly outperformed the Regex baseline. Claude Sonnet 4.6 achieved the highest mean F1 at 0.756, with GPT-5 at 0.679 and Regex at 0.025. Claude also produced the lowest variance (standard deviation 0.174 against GPT-5's 0.305), indicating more uniformly reliable extraction.

**Table 3. Overall accuracy (N equal to 100).**

| Extractor | Mean F1 | SD | F1 equal to 0 | F1 at least 0.9 | Fully correct |
|---|---|---|---|---|---|
| Regex | 0.025 | 0.146 | 97 | 0 | 1 |
| GPT-5 | 0.679 | 0.305 | 15 | 31 | 3 |
| Claude Sonnet 4.6 | 0.756 | 0.174 | 3 | 27 | 4 |

The distribution of failures is as informative as the means. The Regex parser failed completely (F1 of 0) on 97 of 100 inputs, GPT-5 on 15, and Claude on only 3, while GPT-5 produced slightly more near perfect extractions than Claude. Fully correct extractions, where every field of every event matched ground truth exactly, were rare for all methods, reflecting the strictness of the six field criterion.

Table 4 breaks accuracy down by category. Claude outperformed GPT-5 in every category, with the largest margin on missing field inputs (plus 0.176 F1). Both LLMs scored lowest on the two categories that require withholding inference, ambiguous and missing fields, which is consistent with the design intent of those strata.

**Table 4. Mean F1 by input category.**

| Category | Regex | GPT-5 | Claude Sonnet 4.6 |
|---|---|---|---|
| Clean | 0.095 | 0.779 | 0.829 |
| Typos | 0.000 | 0.709 | 0.759 |
| Voice to text | 0.000 | 0.714 | 0.780 |
| Ambiguous | 0.030 | 0.610 | 0.654 |
| Missing fields | 0.000 | 0.583 | 0.759 |

### 4.2 Robustness (SQ2)

Robustness was measured as the relative F1 drop from clean inputs to noisy inputs, where the noisy set combines the typos and voice to text categories (Table 5).

**Table 5. Robustness drop from clean to noisy inputs.**

| Extractor | Clean F1 | Noisy F1 | Robustness drop |
|---|---|---|---|
| Regex | 0.095 | 0.000 | 100 percent |
| GPT-5 | 0.779 | 0.711 | 8.7 percent |
| Claude Sonnet 4.6 | 0.829 | 0.769 | 7.2 percent |

Both LLMs degraded only modestly under input noise, retaining roughly 91 to 93 percent of their clean input performance. The Regex parser collapsed entirely, scoring zero F1 across all 40 noisy inputs. Regex's determinism provided no robustness benefit because its patterns simply failed to match misspelled or transcribed text.

### 4.3 Consistency (SQ3)

Pairwise agreement across the three repeated runs is reported in Table 6. Claude was more consistent than GPT-5 (0.733 against 0.707), and achieved this under true deterministic decoding (temperature of 0.0), whereas GPT-5 was measured under the API default sampling condition because the GPT-5 endpoint rejects custom temperature values. GPT-5 produced identical outputs across all three runs on 65 of 100 inputs. For both models, consistency was highest on clean and typo inputs and lowest on missing field inputs, where the models had the greatest latitude to infer absent values differently between runs. The Regex parser is deterministic by construction and has an implicit consistency of 1.0.

**Table 6. Consistency across three repeated runs.**

| Extractor | Mean pairwise consistency | Decoding condition |
|---|---|---|
| Regex | 1.000 (implicit) | Deterministic by construction |
| GPT-5 | 0.707 | API default temperature |
| Claude Sonnet 4.6 | 0.733 | Temperature of 0.0 |

### 4.4 Hallucination rate (SQ4)

Hallucination rate, the proportion of ground truth null fields for which a non null value was fabricated, was computed on the 20 missing field inputs, the category where ground truth systematically contains null fields (Table 7).

**Table 7. Hallucination rate on missing field inputs (n equal to 20).**

| Extractor | Mean hallucination rate | SD |
|---|---|---|
| Regex | 0.000 | 0.000 |
| GPT-5 | 0.517 | 0.142 |
| Claude Sonnet 4.6 | 0.646 | 0.142 |

This is the only dimension on which the ordering reverses. The Regex parser never fabricated a value: it either matched a pattern or returned nothing. GPT-5 fabricated absent fields on 51.7 percent of opportunities and Claude on 64.6 percent, despite the system prompt explicitly instructing both models to return null for absent information. Notably, the model with higher accuracy hallucinated more.

### 4.5 Statistical significance

McNemar's test on paired fully correct outcomes returned p equal to 0.480 for GPT-5 versus Regex and p equal to 0.248 for Claude versus Regex; neither reached significance at an alpha of 0.05, principally because the strict all fields correct criterion was satisfied on very few inputs for any method (4 or fewer of 100), leaving few discordant pairs. The Wilcoxon signed rank test on category level F1 returned p equal to 0.0625 for both LLM versus Regex comparisons, with the LLM winning in all five of five categories in each case; with only five category strata this is the minimum achievable p value for a one sided sign pattern and sits just above the 0.05 threshold. Effect sizes are large and directionally uniform: both LLMs beat Regex in every category, with F1 gaps ranging from 0.55 to 0.78, and Claude beat GPT-5 in every category.

### 4.6 Reflexive analysis of potential bias

Because the benchmark inputs, ground truth labels, and both extractor integrations were produced by a single researcher who also authored the Prompt2Cal LLM prompt, the risk of confirmation bias toward the LLM methods was considered explicitly and mitigated through four safeguards. First, all ground truth labels were fixed before either extractor was run, so labels could not drift toward whichever method was performing better. Second, the labelling rules for ambiguous and missing field inputs deliberately favour abstention (null values), a convention that penalises the LLMs' inferential style and inflates their measured hallucination rates rather than flattering them. Third, results unfavourable to the LLMs, including hallucination rates above 50 percent and non significant hypothesis tests, are reported with the same prominence as favourable results. Fourth, the Regex parser evaluated here is the genuine production parser with 23 patterns and a natural language fallback, not a weakened strawman, and its under segmentation behaviour was measured rather than excluded. A residual source of bias remains: the benchmark was written by the same person who knew both systems' capabilities, which is acknowledged in Section 6 and motivates the recommendation of independent label adjudication in future work.

### 4.7 Hallucination detection with the source grounding verifier

Table 8 reports the verifier's performance as a hallucination detector, scored against the primary LLM run of every input using the rules frozen in Section 3.9.

**Table 8. Source grounding verifier performance.**

| Extractor | Fabricated fields (missing subset) | Caught | Detection recall | Detection precision | False flag rate (full dataset) | False flag rate (clean subset) |
|---|---|---|---|---|---|---|
| GPT-5 | 40 | 32 | 80.0 percent | 100 percent | 4.4 percent | 2.0 percent |
| Claude Sonnet 4.6 | 46 | 44 | 95.7 percent | 100 percent | 4.0 percent | 0.0 percent |

On the missing field subset, the verifier caught 80.0 percent of GPT-5 fabrications and 95.7 percent of Claude fabrications with perfect precision: no legitimate field in that subset was wrongly flagged. Across the full dataset the usability cost was low, with 4.4 percent of GPT-5's legitimately extracted fields and 4.0 percent of Claude's wrongly flagged, and near zero false flags on clean inputs (2.0 and 0.0 percent respectively).

Detection recall over the full dataset was lower (66.4 percent for GPT-5 and 71.5 percent for Claude, over 146 and 172 fabricated fields respectively). The missed fabrications concentrate in the ambiguous category, where the input contains a partial temporal signal (for example a weekday or the word "weekend") that grounds the fabricated value lexically even though the ground truth deems it too vague to label. Detecting this class of fabrication requires distinguishing vague from precise evidence, which lexical grounding cannot do reliably; this boundary is discussed in Section 5.6.

It is notable that the verifier was most effective against exactly the model that hallucinates most: it caught 95.7 percent of Claude's missing field fabrications against 80.0 percent of GPT-5's, because Claude's fabrications more often occur with no supporting signal in the text at all.

### 4.8 Observed operational characteristics

Although latency and cost were not formal experimental variables, two observations are reported for completeness. The GPT-5 benchmark run (300 calls) took approximately 104 minutes end to end, while the Claude run (300 calls through the identical pipeline) took approximately 17 minutes. Token accounting places the marginal API cost of a full 300 call run in the order of a few dollars for either provider at current pricing, whereas the Regex parser incurs no per query cost and executes in microseconds per input, consistent with the speed differentials reported by Dennstadt et al. (2025).

### 4.9 Reproducibility, sensitivity, and failure mode analysis

Both reproducibility checks passed. Recomputing mean F1 from the stored per input artefacts reproduced the persisted summary values exactly (0.6788 for GPT-5 and 0.7563 for Claude at the 0.7 threshold). The Regex re execution produced structurally identical extractions on all 100 inputs and the identical mean F1 to full precision; the only byte level differences were four inputs with relative expressions such as "tomorrow", whose resolved dates track the execution date; ground truth resolves against the same reference date, so no metric is affected.

Table 9 shows the alignment threshold sensitivity. Mean F1 shifts by at most 0.030 across the 0.6 to 0.8 range for any extractor, the ordering of the three methods is unchanged at every threshold, and the Regex result is completely insensitive. The main findings therefore do not depend on the specific choice of 0.7.

**Table 9. Mean F1 at alternative alignment thresholds.**

| Extractor | Threshold 0.6 | Threshold 0.7 (main analysis) | Threshold 0.8 |
|---|---|---|---|
| Regex | 0.025 | 0.025 | 0.025 |
| GPT-5 | 0.709 | 0.679 | 0.667 |
| Claude Sonnet 4.6 | 0.756 | 0.756 | 0.744 |

Table 10 presents the failure mode taxonomy over each extractor's primary run on all 100 inputs. Field level counts cover aligned event pairs; the fields of unaligned predicted events are subsumed under spurious event. The three Regex fabricated fields occurred outside the missing field subset and are therefore consistent with the zero hallucination rate in Table 7, which measures that subset only.

**Table 10. Failure mode taxonomy (occurrences; empty output counted per input).**

| Failure mode | Regex | GPT-5 | Claude Sonnet 4.6 |
|---|---|---|---|
| Empty output | 96 | 5 | 0 |
| Missed event | 1 | 11 | 3 |
| Spurious event | 1 | 11 | 3 |
| Fabricated field | 3 | 113 | 161 |
| Missed field | 0 | 0 | 0 |
| Wrong time value | 0 | 18 | 15 |
| Wrong other value | 1 | 24 | 22 |

The taxonomy sharpens the earlier findings in two ways. First, the failure profiles of the two method classes are almost perfectly complementary: Regex fails silently by extracting nothing (96 of 100 inputs), while the LLMs fail by extracting too much, with fabricated fields the dominant mode for both models. Second, neither LLM recorded a single missed field: in every aligned event, every field present in the ground truth received some value. LLM extraction error is therefore almost entirely an over extraction phenomenon, which is precisely the error class the source grounding verifier of Section 4.7 targets.

---

## 5. Discussion

### 5.1 Answering the research question

The results give a clear answer to the main research question. For informal natural language calendar text, LLM based extraction is dramatically more reliable than rule-based extraction on three of the four dimensions, and dramatically less reliable on the fourth.

On accuracy (SQ1), both LLMs decisively outperformed Regex (Table 3). This aligns with Latifi (2025), who found that LLMs handle ambiguous and context dependent language more effectively than traditional tools, and extends the domain specific findings of Dennstadt et al. (2025) into informal text, where the limitation they observed, that Regex patterns cannot account for all linguistic variation, proved far more severe: Regex scored zero F1 on 97 of 100 inputs despite its 23 pattern library and dateparser fallback.

On robustness (SQ2), the LLMs retained most of their clean input performance under noise (drops of 7.2 and 8.7 percent), while Regex collapsed completely. This quantifies, for the first time in a calendar context, that rule-based determinism offers no robustness advantage when patterns fail to match at all; prior comparisons did not systematically measure degradation under realistic input imperfections.

On consistency (SQ3), the LLMs achieved pairwise agreement of 0.707 (GPT-5) and 0.733 (Claude), against the Regex parser's implicit 1.0. This partially addresses the gap noted by Huang, K.-H. et al. (2024) that benchmarks rarely evaluate output stability across repeated extractions. Consistency fell substantially on missing field inputs for both models, indicating that inferential behaviour is least stable precisely where users most need predictability.

On hallucination (SQ4), the ordering reversed: Regex never fabricated, while GPT-5 fabricated 51.7 percent and Claude 64.6 percent of absent fields, despite explicit abstention instructions. This confirms the concern raised by Liu et al. (2024) and Dang et al. (2025) that LLMs tend to populate fields rather than return null, and is consistent with the position of Singh et al. (2026) and Huang, L. et al. (2024) that hallucination is an architectural tendency that prompt design constrains but does not eliminate.

### 5.2 The distribution of failures

A notable difference between the two LLMs lies in the distribution of failures rather than the averages alone. GPT-5 produced a completely failed extraction on 15 of 100 inputs, whereas Claude did so on only 3. This large reduction in catastrophic failures is the primary driver of Claude's higher mean F1 and its substantially lower variance. Interestingly, GPT-5 recorded slightly more near perfect extractions (31 inputs at F1 of at least 0.9 against Claude's 27), suggesting that GPT-5 behaves in a more all or nothing manner, achieving more perfect scores but also more total failures, while Claude is more uniformly reliable. For a calendar application, where a completely missed event is more damaging to user trust than a partially imperfect one, the tendency to avoid catastrophic failures is arguably more valuable than a marginally higher rate of perfect extractions.

### 5.3 The accuracy versus faithfulness trade off operates within the LLM class

The most consequential finding is not the size of the accuracy gap but its shape, and the two model comparison shows that the trade off operates within the LLM class rather than only between method classes. Claude is more accurate than GPT-5 precisely on the category, missing fields, where it also hallucinates more (plus 0.176 F1 alongside plus 0.129 hallucination). A more capable model did not abstain more; it inferred more, raising accuracy and fabrication together. This is empirical support for the architectural view of hallucination (Singh et al., 2026): if fabrication were a defect that greater capability removes, the more accurate model should have hallucinated less, and the opposite was observed.

This has a direct engineering implication: model selection cannot be reduced to choosing the highest F1 model. A model that scores higher partly by populating uncertain fields may create more factually incorrect calendar events in deployment. The result also echoes Kataoka et al. (2025), who found strong string extraction but weaker numeric precision in a leading model; in this benchmark, both models scored lowest on the categories where the correct answer often requires withholding a numeric or temporal inference.

### 5.4 Implications for the hybrid architecture

The results recalibrate the rules first, LLM fallback pattern proposed by Kumar (2026). That pattern assumes rules can serve a meaningful share of traffic, with the LLM reserved for hard cases. On this benchmark, Regex achieved non zero F1 on only 3 of 100 inputs, so a routing strategy that assumes Regex handles most inputs would not hold for informal scheduling text. The hybrid value is therefore not primarily cost reduction. Instead, the Regex parser is best used as a faithfulness anchor: when Regex and the LLM agree on a field, confidence is high; when only the LLM produces a value, particularly for a field the input may not actually specify, the extraction should be flagged for user review. Agreement between an abstention prone method and an inference prone method is a stronger reliability signal than either output alone.

### 5.5 Decision criteria for practitioners

Synthesising the four dimensions yields the following evidence based decision criteria for engineers selecting extraction methods for productivity tools:

1. **If inputs are informal or user generated, an LLM extractor is necessary.** Rule based extraction alone is functionally inadequate (mean F1 of 0.025), even with a substantial pattern library and a natural language parsing fallback.
2. **If inputs may contain typos or transcription noise, the case for the LLM strengthens further.** LLM performance degrades by less than 9 percent under noise; Regex performance disappears entirely.
3. **Never auto commit LLM extractions for inputs that may omit fields.** With hallucination rates above 50 percent on absent fields for both frontier models, a preview and confirm workflow is a reliability requirement, not a user experience preference.
4. **Score confidence by source grounding, not completeness.** This is a demonstrated result, not a recommendation (Section 4.7): a roughly 100 line lexical verifier caught 80 to 96 percent of fabricated fields with perfect precision at a false flag rate of about 4 percent. A parser output with explicit nulls is more trustworthy than a fully populated one, and fields whose values cannot be located in the source text should reduce confidence and trigger review.
5. **Prefer models with fewer catastrophic failures over models with more perfect outputs**, when the application cost of a missed event exceeds the cost of a partially imperfect one.
6. **Reserve Regex for cost free confirmation, not routing.** Use pattern matches to corroborate LLM output and to short circuit only the small minority of rigidly structured inputs.

### 5.6 Practicality of hallucination detection

The verifier results transform the hallucination finding from a caution into an engineering path forward. Section 4.4 showed that both frontier models fabricate absent fields at rates above 50 percent despite explicit abstention instructions, consistent with the architectural view of hallucination (Singh et al., 2026; Huang, L. et al., 2024). If fabrication cannot be prompted away, the remaining question is whether it can be detected cheaply at the system boundary, and the answer measured here is largely yes: purely lexical source grounding, with no additional model calls and no semantic understanding, caught 80 to 96 percent of missing field fabrications with perfect precision, at a usability cost of roughly one false alarm per 25 legitimately extracted fields.

The recall and false flag trade off has a clear structure. The verifier is strongest exactly where the risk is highest: fields fabricated from no evidence at all, the pattern that dominates the missing field category and that Claude, the more aggressive inferrer, exhibits most. It is weakest where fabrication shades into interpretation, the ambiguous category, where a vague temporal signal such as "sometime this weekend" lexically grounds a fabricated precise value. Full dataset recall of 66 to 72 percent therefore understates the verifier's deployment value, because the residual misses are mostly values a user can see are interpretations of vague language, whereas the caught cases are silent inventions the user has no way to suspect. This supports the external verification position of Singh et al. (2026) with a concrete cost benefit datum, and connects to Liu et al. (2024): the faithfulness contribution of rule based methods survives even when rules are demoted from extraction to verification.

### 5.7 Methodological reflections

Two methodological deviations occurred during execution, both documented at the time. First, the GPT-5 API rejected the planned temperature of 0, so GPT-5 ran at the provider default while Claude ran at a true 0.0. This asymmetry means the two LLMs were not evaluated under identical decoding conditions; however, it also strengthens the Claude consistency finding, which was obtained under the stricter condition the proposal originally intended. Second, the addition of Claude Sonnet 4.6 was a scope extension beyond the approved single model design. It was implemented so that only the model call differs, reuses every other pipeline component unchanged, and was undertaken specifically to address the single model limitation identified in the proposal. The extension proved valuable: it converted a two way comparison into a three way one and revealed the intra LLM trade off discussed in Section 5.3.

The verification phase strengthened confidence in the internal validity of the results. The exact reproduction of all headline figures from the stored artefacts, the byte level reproducibility of the deterministic condition, and the insensitivity of the F1 ordering to the alignment threshold (Section 4.9) together indicate that the reported differences reflect the extractors rather than artefacts of the pipeline or of a single parameter choice.

The statistical results also warrant reflection. Neither McNemar's test nor the Wilcoxon test reached significance at an alpha of 0.05, despite very large observed effect sizes. This is a limitation of the strict fully correct criterion (which few inputs satisfied for any method, leaving McNemar with few discordant pairs) and of the small number of category strata available to the Wilcoxon test (five). The effect sizes and their directional uniformity, with the LLMs winning every category against Regex and Claude winning every category against GPT-5, carry the practical interpretive weight, and are reported alongside the p values as planned.

### 5.8 Application to the production platform

The findings were applied directly back to the Prompt2Cal platform, closing the loop between evaluation and artefact. The source grounding verifier now runs on every live extraction: the backend attaches a per field confidence verdict to each parsed event, and the extension preview highlights ungrounded fields with a warning that the value was not found in the user's text. Silent defaults were made visible: an end time derived from the default duration is now labelled as assumed rather than presented as extracted fact, and an absent location is shown as an explicit empty state instead of being hidden. The Regex parser was repurposed from a routing mechanism into a corroboration signal that raises a field's confidence when it independently extracts the same value. The deployed system therefore embodies decision criteria 3, 4, and 6 rather than merely recommending them.

---

## 6. Limitations

Several limitations should be acknowledged when interpreting these findings.

**Benchmark size and construction.** The dataset contains 100 inputs across five categories of 20 each, modest by natural language processing benchmarking standards, and constructed by a single researcher. Although labelling rules were documented and a subset was reviewed, different labelling conventions, for example whether a vague expression warrants a fuzzy time or a null, would shift the F1 and hallucination scores. The sample size also limited the statistical power of both hypothesis tests.

**Model coverage.** Two proprietary frontier models were evaluated. Open weight and smaller locally deployable models, which Nawalny et al. (2025) show can differ substantially in completeness, remain untested, so the decision criteria may not transfer to those model classes.

**Decoding asymmetry.** GPT-5 ran at the provider's default sampling setting while Claude ran at a temperature of 0.0, a residual confound for the accuracy and consistency comparisons specifically, as discussed in Section 5.7.

**Hallucination measurement scope.** Hallucination rate was computable only on the 20 missing field inputs, the category where ground truth systematically contains nulls. The reported rates describe behaviour on incomplete inputs specifically rather than across the full benchmark.

**Latency and cost.** These were observed informally (Section 4.8) but not measured as controlled variables. Prior work identifies speed and cost as major Regex advantages (Dennstadt et al., 2025; Suneja, 2026), and a complete trade off analysis would quantify them under production conditions.

**Language and cultural scope.** All inputs reflect Western English language scheduling conventions. Generalisation to other languages and cultural time keeping conventions is untested.

---

## 7. Project Organisation, Feedback, and Reflection

### 7.1 Organisation and project management

The project was managed against the twelve phase plan established in the approved proposal, spanning February to November 2026, with scope, deliverables, timelines, and responsibilities defined per phase and tracked against a Gantt chart. Phases 1 to 4 (scoping, platform adaptation, functional testing, and proposal finalisation) concluded with the proposal submission on 17 May 2026. Phases 5 to 7 (benchmark construction, harness implementation, GPT-5 migration, full benchmark execution, and metric computation) were completed on schedule between May and July 2026, and the analysis and reporting phases proceeded from July 2026.

A defined communications procedure was maintained with the supervisor throughout: regular meetings (in person and online) supplemented by Teams messages for work in progress uploads, document reviews, and administrative submissions, with each interaction and its outcome recorded in a communication log (Appendix F). Deliverables were version controlled in the project Git repository, giving both parties visibility of progress between meetings. Risk management operated as planned: each phase carried predefined contingencies, and the two risks that materialised (the GPT-5 temperature incompatibility and a date range parsing defect) were resolved using documented workarounds without schedule slippage. API budget monitoring kept evaluation costs within the planned envelope, and the Claude scope extension was costed and assessed before execution.

### 7.2 Seeking and responding to feedback

Feedback was actively sought and acted upon at every stage of the project, with the full record in Appendices F and G. The most consequential instances were:

- **Formulation of research questions.** Peer and supervisor feedback that the original research question was too broad led to its restructuring into one main question with four sub questions (SQ1 to SQ4), each mapped to a distinct reliability dimension and operationalised through a specific metric. This structure ultimately organised the entire findings section of this report.
- **Research design.** Supervisor consultation on the planned user evaluation survey concluded that it contributed little to the technical research question and posed recruitment difficulty. The survey was scoped out, the project refocused entirely on the four dimension technical evaluation, and the user study was repositioned as future work. This decision preserved methodological depth and proved correct: the technical evaluation alone filled the report's scope.
- **Literature search and review.** Peer feedback requesting more sources and clearer structure led to an expanded reference summary table, additional in text citations grounding each claimed gap, and restructuring of the literature review into thematic sub sections.
- **Analysis and interpretation.** Supervisor review of the labelling rules for ambiguous and missing field inputs shaped the abstention favouring conventions documented in the labelling notes, which directly affect the hallucination measurement reported in Section 4.
- **Referencing.** Peer feedback on APA 7 compliance prompted a comprehensive manual review of the reference list.

### 7.3 Personal reflection on professional growth

This project developed my engineering practice in three areas. First, it taught me the discipline of measurement before opinion. I began with an intuition that LLM extraction was simply better than the Regex parser I had written; the benchmark forced me to specify what better means, and the result complicated my intuition considerably, since the method I favoured fabricates data more than half the time when information is absent. Designing metrics that could prove me wrong, and reporting the unfavourable results with equal prominence, is the clearest professional growth I can point to.

Second, I learned to manage scope changes as an engineer rather than a hobbyist. Three deviations occurred during execution: an API incompatibility (GPT-5 rejecting the planned temperature setting), a defect found in my own production code (the multi day end time being overwritten), and a genuine scope extension (adding a second LLM). In each case the professional habit was the same: document the deviation, assess its effect on validity, implement the minimal correct change, and cover it with a regression test where applicable. Earlier in my degree I would have silently patched and moved on.

Third, the feedback process changed how I value external review. The decision I initially resisted most, dropping the user survey, was the one that most improved the project, and the peer feedback on structure that seemed cosmetic at the time is what made the four sub question architecture of this report possible. I now treat supervisor and peer review as a design input rather than a compliance step, and I expect this to carry directly into professional practice, where design reviews serve the same function.

---

## 8. Conclusion and Recommendations

### 8.1 Conclusion

This project delivered a controlled, reproducible comparison of LLM based and rule-based event extraction on informal calendar text, evaluated across four separately measured reliability dimensions on a purpose built 100 input stratified benchmark. It contributes, to the author's knowledge, the first multi dimensional reliability benchmark for informal calendar event extraction, and a set of empirical decision criteria for practitioners.

The central findings are: LLM extraction is vastly more accurate than rule-based extraction on informal text; it is robust to typos and voice to text noise where Regex collapses entirely; LLM outputs are imperfectly stable across repeated runs; and both LLMs fabricate values for more than half of genuinely absent fields despite explicit abstention instructions, whereas Regex never fabricates. The two model comparison further showed that the accuracy versus faithfulness trade off operates within the LLM class: the more accurate model hallucinated more, and its accuracy advantage was driven primarily by avoiding catastrophic failures rather than by more perfect extractions. Finally, a lightweight source grounding verifier demonstrated that this fabrication risk is manageable in practice, catching 80 to 96 percent of missing field fabrications with perfect precision at a false flag rate of approximately 4 percent, using purely lexical rules frozen before scoring.

For the engineering problem that motivated the work, the answer is that reliable calendar automation requires LLM extraction wrapped in verification: a preview before create workflow, confidence scoring that rewards abstention, and rule-based corroboration used as a faithfulness signal rather than as a primary routing mechanism. These safeguards are now implemented in the Prompt2Cal platform itself (Section 5.8).

### 8.2 Recommendations

For practitioners building extraction features into productivity tools, the decision criteria in Section 5.5 are the actionable output of this research. In summary: adopt LLM extraction for informal inputs, never auto commit outputs when fields may be absent, score confidence by abstention, prefer models with fewer catastrophic failures, and use rules as corroboration rather than as the primary path.

For future research, three extensions would strengthen these findings. First, expanding the benchmark beyond 100 inputs with an independent human adjudication pass would improve statistical power and label reliability. Second, evaluating open weight models under the same harness would clarify whether the observed trade offs are specific to frontier models, and adding controlled latency and cost measurement would complete the practical trade off picture. Third, a user study examining whether subjective trust in extraction outputs tracks the objective reliability dimensions measured here, building on Zhang et al. (2020), would connect the benchmark to real world adoption.

---

## References

AIATSIS. (2020). *Code of Ethics.* https://aiatsis.gov.au/research/ethical-research/code-ethics

Dang, A.-H., Tran, V., & Nguyen, L.-M. (2025). Survey and analysis of hallucinations in large language models: attribution to prompting strategies or model behavior. *Frontiers in Artificial Intelligence, 8.* https://doi.org/10.3389/frai.2025.1622292

Dennstadt, F., Lerch, L., Schmerder, M., Cihoric, N., Cereghetti, G. M., Gaio, R., Bonel, H., Filchenko, I., Hastings, J., Dammann, F., Aebersold, D. M., von Tengg-Kobligk, H., & Nairz, K. (2025). A comparative performance analysis of regular expressions and a large language model-based approach to extract the BI-RADS score from radiological reports. *JAMIA Open, 8*(6). https://doi.org/10.1093/jamiaopen/ooaf128

Department of Industry, Science and Resources. (2019). *Australia's Artificial Intelligence Ethics Principles.* https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles

Huang, K.-H., Hsu, I-H., Parekh, T., Xie, Z., Zhang, Z., Natarajan, P., Chang, K.-W., Peng, N., & Ji, H. (2024). TEXTEE: Benchmark, reevaluation, reflections, and future challenges in event extraction. *Findings of the Association for Computational Linguistics: ACL 2024,* 12804 to 12825. https://aclanthology.org/2024.findings-acl.760

Huang, L., Yu, W., Ma, W., Zhong, W., Feng, Z., Wang, H., Chen, Q., Peng, W., Feng, X., Qin, B., & Liu, T. (2024). A survey on hallucination in large language models: Principles, taxonomy, challenges, and open questions. https://arxiv.org/pdf/2311.05232

Kataoka, Y., Takayama, T., Yoshimura, K., So, R., Tsujimoto, Y., Yamagishi, Y., Takagi, S., Furukawa, Y., Sakata, M., Basic, D., Cipriani, A., Cuijpers, P., Karyotaki, E., Harrer, M., Leucht, S., Homiar, A., Ostinelli, E. G., Miguel, C., Rodolico, A., & Furukawa, T. A. (2025). Automating the data extraction process for systematic reviews using GPT-4o and o3. *Research Synthesis Methods, 17*(1), 1 to 21. https://doi.org/10.1017/rsm.2025.10030

Keraghel, I., Morbieu, S., & Nadif, M. (2024). Recent advances in named entity recognition: A comprehensive survey and comparative study. https://arxiv.org/abs/2401.10825

Kumar, H. (2026, February 11). Hybrid validation agent: Rule-based engine plus LLM fallback. *Medium.* https://medium.com/@kumarharsh74799/the-hybrid-validation-pattern-rules-first-llm-fallback-cfe545efcd44

Lai, V. D. (2022). Event extraction: A survey. https://arxiv.org/abs/2210.03419

Latifi, P. (2025). Is "Hope" a person or an idea? A pilot benchmark for NER: comparing traditional NLP tools and large language models on ambiguous entities. https://arxiv.org/abs/2509.12098

Liu, P., Gao, W., Dong, W., Ai, L., Gong, Z., Huang, S., Li, Z., Hoque, E., Hirschberg, J., & Zhang, Y. (2024). A survey on open information extraction from rule-based model to large language model. *Findings of the Association for Computational Linguistics: EMNLP 2024,* 9586 to 9608. https://aclanthology.org/2024.findings-emnlp.560

Nawalny, M., Lepicki, M., Latkowski, T., Bujak, S., Bukowski, M., Swiderski, B., Baranik, G., Nowak, B., Zakowicz, R., Dobrakowski, L., Oczeretko, A., Sadowski, P., Szlaga, K., Kubica, B., & Kurek, J. (2025). Comparative evaluation of GPT-4o, GPT-OSS-120B and Llama-3.1-8B-Instruct language models in a reproducible CV-to-JSON extraction pipeline. *Applied Sciences, 16*(1), 217. https://doi.org/10.3390/app16010217

NHMRC. (2023). *National Statement on Ethical Conduct in Human Research.* https://www.nhmrc.gov.au/about-us/publications/national-statement-ethical-conduct-human-research-2023

Singh, S., Saha, R., Kumar, G., Nayyar, A., & Kim, T.-K. (2026). Are you hallucinated? Insights into large language models. *ICT Express, 12*(2). https://doi.org/10.1016/j.icte.2025.12.011

Strubell, E., Ganesh, A., & McCallum, A. (2019). Energy and policy considerations for deep learning in NLP. *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics,* 3645 to 3650. https://doi.org/10.18653/v1/P19-1355

Suneja, S. (2026, February 12). Hybrid extraction: When to use LLMs vs local models vs Regex. *Ritw.dev.* https://ritw.dev/blog/hybrid-extraction-llms-local-models-regex/

Zhang, Y., Liao, Q. V., & Bellamy, R. K. E. (2020). Effect of confidence and explanation on accuracy and trust calibration in AI-assisted decision making. *Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency,* 295 to 305. https://doi.org/10.1145/3351095.3372852

---

## Appendices

**Appendix A: Benchmark dataset (100 inputs with ground truth).** See `benchmark/APPENDIX_dataset.md` (Markdown) or `benchmark/APPENDIX_dataset.tex` (LaTeX longtable). Regenerate from the dataset source with `scripts/build_appendix_table.py`.

**Appendix B: LLM system prompt.** The complete system prompt and user prompt template sent to both LLM extractors are defined in `backend/services/intelligent_parser.py`. The system prompt enforces JSON only output, natural language date formatting, location extraction patterns, recurrence handling, valid time ranges, and abstention when input is unclear (Rule 6). Both extractors received the identical prompt; the Claude extractor appends a JSON only reminder because the Anthropic API lacks a native JSON response format flag.

**Appendix C: Ground truth labelling notes.** Documented labelling decisions for the ambiguous and missing field categories, including the rule that vague clock times are labelled with a null start time and the per input rules applied to the missing field stratum, are in `benchmark/labelling_notes.md`.

**Appendix D: Raw results.** Per input JSON artefacts and aggregate summaries for each run: `benchmark/outputs/` (GPT-5) and `benchmark/outputs_claude/` (Claude Sonnet 4.6). Each summary records the run configuration (dataset version, timezone, repetition count, provider, and model) alongside all per input outputs and metrics.

**Appendix E: Evaluation harness.** Source code for the models, normalisation, alignment, metrics, and runner is in `backend/evaluation/`, with unit tests in `backend/tests/` and the command line entry point at `scripts/run_evaluation.py`. The source grounding verifier is in `backend/evaluation/verifier.py` with its 21 unit tests in `backend/tests/test_verifier.py`, its scoring script at `scripts/run_verifier.py`, and its full confusion matrices per extractor and category in `benchmark/verifier_results.json`. The verification phase scripts and outputs are `scripts/run_sensitivity.py` with `benchmark/sensitivity_results.json`, `scripts/build_failure_taxonomy.py` with `benchmark/failure_taxonomy.json`, and the reproducibility comparison script `scripts/check_reproducibility.py`. The production integration of the verifier (Section 5.8) is in `backend/services/confidence.py` with tests in `backend/tests/test_confidence.py`.

**Appendix F: Communication log with supervisor.** The dated log of all supervisor meetings and Teams correspondence, with the topic and outcome of each interaction, is maintained from the research proposal (Appendix B of that document) and extended through the capstone phases. Update this log with capstone semester meetings before submission.

**Appendix G: Peer review summary.** The table of peer review feedback received on the literature review and research proposal, with the response and action taken for each item, is maintained from the research proposal (Appendix C of that document).
