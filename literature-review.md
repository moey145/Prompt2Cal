# Literature Review: A Comparative Evaluation of Large Language Models and Rule-Based Systems for Event Extraction

## 1. Introduction

In our increasingly busy digital lives, we are often overwhelmed by an explosion of unstructured event data. From casual email invitations to detailed community newsletters, much of this information remains difficult for our daily productivity tools to handle without us having to step in and manage it manually. Event Extraction, a helpful subfield of Information Extraction, seeks to ease this burden by automatically identifying event triggers and their details including time, location, and description, directly from natural language (Viet Dac Lai, 2022, p.1). This review explores how we have moved from rigid, rule-based methods to more intuitive, modern approaches using Large Language Models (LLMs). In doing so, it identifies a vital need to understand how these systems can work together more reliably and efficiently to truly support our real-world workflows.

## 2. Consensus: The Shift from Rules to Reason

There is a broad understanding that traditional rule-based systems using Regular Expressions (Regex) and pattern matching, are incredibly reliable when dealing with structured information. Liu et al. (2024, p. 9594) observed that a major challenge for LLMs compared to traditional rule-based approaches is hallucination, and suggested that integrating rule-based methods into LLM frameworks can improve faithfulness and reliability.

The emergence of generative LLMs like GPT-4 has revolutionised the field by allowing for a more open way of extracting information. Latifi (2025) found that LLMs generally outperform traditional NLP tools when handling ambiguous, context-dependent language, though conventional systems remain preferable where determinism and speed are priorities. Dennstädt et al. (2025) reinforced this by showing that Regex was over 28,000 times faster than an LLM on structured data extraction, yet its patterns could not account for all linguistic variations, suggesting that LLMs are better suited for more complex, unstructured text.


## 3. Divergence: Accuracy vs. Reliability

Despite the success of LLMs, a key point of divergence concerns the trade-off between flexibility and faithfulness. A primary concern is hallucination, where LLMs fabricate event fields when information is missing, rather than returning null as rule-based systems would (Dang Anh-Hoang et al., 2025). Marin (2026) argued that hallucinations are an inherent architectural feature of Transformers, not a bug that can be fully prompted away.

There is also disagreement on the practicality of LLMs for high-volume event parsing, given their time inefficiency and high token costs compared to lightweight Regex parsers (Suneja, 2026). Nawalny et al. (2025) found that open-weight models reached only 73–79% completeness compared to GPT-4o, revealing that even within LLM-based approaches, significant performance-cost trade-offs exist. These limitations have fuelled interest in hybrid architectures that attempt to offset the weaknesses of each method. Kumar (2026) proposed one such pattern, a rules-first, LLM-fallback architecture that routes predictable inputs through Regex and reserves LLM calls for ambiguous cases, reportedly reducing costs by 70%. However, whether this orchestration logic generalises beyond structured form validation to more complex domains like event extraction remains an open question.

## 4. Gap: The Productivity Workflow Integration

While researchers have compared LLMs and Regex on benchmark datasets and domain-specific tasks, including radiology report parsing (Dennstädt et al., 2025) and CV-to-JSON extraction (Nawalny et al., 2025), these evaluations have not addressed the informal, ambiguous event descriptions typical of calendar scheduling contexts, such as "Dinner at Sarah's next Thursday around 7ish." Huang et al. (2024) evaluated five LLMs across 16 standardised event extraction datasets and found that LLMs struggle to achieve satisfactory performance, yet none of these benchmarks reflected everyday productivity scenarios. Nishimura et al. (2025) demonstrated that while GPT-4o achieves strong accuracy on string-based data extraction (up to 96.3%), it struggles with numeric and date precision, the very fields most critical for calendar event creation. Furthermore, existing comparisons tend to focus on isolated metrics such as accuracy or speed, rather than evaluating across multiple reliability dimensions simultaneously, including output consistency over repeated runs and robustness to common input imperfections like typos or voice-to-text artefacts. There is also no empirical guidance on how confidence scoring, a mechanism to flag uncertain or potentially hallucinated extractions, affects user trust in automated event detection.

## 5. Contribution and Research Question

This project addresses this gap by developing Prompt2Cal, a dual-parser system that serves as an evaluation platform. By implementing a GPT-4 based extractor alongside a Regex-based parser within a rules-first, LLM-fallback architecture (Kumar, 2026), this research will contribute empirical data on the "sweet spot" between rule-based rigidity and LLM flexibility across a multi-dimensional evaluation framework.

### Research Question

> How does the reliability of LLM-based event extraction compare to rule-based methods for unstructured natural language text, and what are the practical trade-offs across accuracy, robustness, consistency, and hallucination rate?

## 6. References

Arora, S., Narayan, S., Chen, D., & Manning, C. D. (2025). ExtractBench: A benchmark and evaluation methodology for complex structured extraction. *arXiv preprint*, arXiv:2602.12247. https://arxiv.org/abs/2602.12247

Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., … Amodei, D. (2020). Language models are few-shot learners. *Advances in Neural Information Processing Systems*, *33*, 1877–1901. https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html

Chang, A. X., & Manning, C. D. (2012). SUTime: A library for recognizing and normalizing time expressions. In *Proceedings of the Eighth International Conference on Language Resources and Evaluation (LREC'12)* (pp. 3735–3740). European Language Resources Association. https://nlp.stanford.edu/pubs/lrec2012-sutime.pdf

Dennstädt, F., Lerch, L., Schmerder, M., Cihoric, N., Cereghetti, G. M., Gaio, R., Bonel, H., Filchenko, I., Hastings, J., & Dammann, F. (2025). A comparative performance analysis of regular expressions and a large language model-based approach to extract the BI-RADS score from radiological reports. *JAMIA Open*, *8*(6), Article ooaf128. https://doi.org/10.1093/jamiaopen/ooaf128

Dang, A.-H., Tran, V., & Nguyen, L.-M. (2025). Survey and analysis of hallucinations in large language models: Attribution to prompting strategies or model behavior. *Frontiers in Artificial Intelligence*, *8*, Article 1622292. https://doi.org/10.3389/frai.2025.1622292

Liu, P., Gao, W., Dong, W., Ai, L., Gong, Z., Huang, S., Li, Z., Hoque, E., Hirschberg, J. and Zhang, Y. (2024). A survey on open information extraction from rule-based model to large language model. In *Findings of the Association for Computational Linguistics: EMNLP 2024*, pp. 9572–9600. https://aclanthology.org/2024.findings-emnlp.560/

Han, Q., & Zhang, Y. (2025). Enhancing pre-trained language model by answering natural questions for event extraction. *Frontiers in Artificial Intelligence*, *8*, Article 1520290. https://doi.org/10.3389/frai.2025.1520290

Huang, K., Huang, J., Liu, Y., Wang, W., Chen, M., & Huang, L. (2024). TextEE: Benchmark, reevaluation, reflections, and future challenges in event extraction. In *Findings of the Association for Computational Linguistics: ACL 2024* (pp. 12804–12825). Association for Computational Linguistics. https://aclanthology.org/2024.findings-acl.760

Kumar, H. (2026, February). The hybrid validation pattern: Rules-first, LLM fallback. *Medium*. https://medium.com/@kumarharsh74799/the-hybrid-validation-pattern-rules-first-llm-fallback-cfe545efcd44

Lai, V. D., Nguyen, M. V., Nguyen, T. H., & Dernoncourt, F. (2022). Event extraction: A survey. *arXiv preprint*, arXiv:2210.03419. https://doi.org/10.48550/arXiv.2210.03419

Marin, J. (2026, March). Hallucinations in LLMs are not a bug in the data. *Towards Data Science*. https://towardsdatascience.com/hallucinations-in-llms-are-not-a-bug-in-the-data/

Nawalny, M., Łępicki, M., Latkowski, T., Bujak, S., Bukowski, M., Świderski, B., Baranik, G., Nowak, B., Zakowicz, R., & Kurek, J. (2025). Comparative evaluation of GPT-4o, GPT-OSS-120B and Llama-3.1-8B-Instruct language models in a reproducible CV-to-JSON extraction pipeline. *Applied Sciences*, *16*(1), Article 217. https://doi.org/10.3390/app16010217

Nishimura, T., Kataoka, Y., Defined, T., Tsujimoto, Y., & Furukawa, T. A. (2025). Automating the data extraction process for systematic reviews using GPT-4o and o3. *Research Synthesis Methods*. https://doi.org/10.1017/rsm.2025.10030

Suneja, S. (2026, February 12). Hybrid extraction: When to use LLMs vs local models vs regex. *ritw.dev*. https://ritw.dev/blog/hybrid-extraction-llms-local-models-regex/

Strötgen, J., & Gertz, M. (2010). HeidelTime: High quality rule-based extraction and normalization of temporal expressions. In *Proceedings of the 5th International Workshop on Semantic Evaluation (SemEval 2010)* (pp. 321–324). Association for Computational Linguistics. https://aclanthology.org/S10-1071

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. *Advances in Neural Information Processing Systems*, *35*, 24824–24837. https://proceedings.neurips.cc/paper_files/paper/2022/file/9d5609613524ecf4f15af0f7b31abca4-Paper-Conference.pdf

Latifi, P. (2025). Is 'Hope' a person or an idea? A pilot benchmark for NER: Comparing traditional NLP tools and large language models on ambiguous entities. *arXiv preprint*, arXiv:2509.12098. https://arxiv.org/abs/2509.12098
