# Report figures

Scripts that regenerate the capstone report's figures from the stored result
artefacts. Run these after any change to the benchmark so the figures and the
reported numbers cannot drift apart.

## Requirements

```bash
pip install matplotlib graphviz
```

`make_diagrams.py` also needs the Graphviz system binary, which the Python
package shells out to:

```bash
sudo apt install graphviz      # Debian, Ubuntu
brew install graphviz          # macOS
choco install graphviz         # Windows
```

Check it is on your PATH with `dot -V`.

## Usage

From the repository root:

```bash
python scripts/make_figures.py --outdir report/figures
python scripts/make_diagrams.py --outdir report/figures
```

Both default to `report/figures` if `--outdir` is omitted.

## What each script produces

| Script | Figure | Output |
| --- | --- | --- |
| `make_diagrams.py` | Figure 2, evaluation pipeline | `fig2_pipeline.png` |
| `make_figures.py` | Figure 3, mean F1 by input category | `fig3_f1_by_category.png` |
| `make_figures.py` | Figure 4, accuracy versus faithfulness trade-off | `fig4_tradeoff.png` |
| `make_figures.py` | Figure 5, verifier recall and usability cost | `fig5_verifier.png` |
| `make_diagrams.py` | Figure 6, user flow | `fig6_userflow.png` |

Figures 1 and 7 are not generated here. Figure 1, the research gap quadrant,
was drawn from the literature. Figure 7 is a composite of interface
screenshots.

## Where the numbers come from

Figure 5 reads `benchmark/verifier_results.json` directly, so it always
reflects the current verifier run. Pass a different path with `--results` if
the file lives elsewhere.

Figures 3 and 4 use the `ACCURACY` and `OVERALL` dictionaries near the top of
`make_figures.py`. These hold the mean F1 and hallucination figures taken from
the aggregate run summaries in `benchmark/outputs/` and
`benchmark/outputs_claude/`. **If the benchmark is re-run, update those two
dictionaries**, otherwise the charts will show stale numbers while the report
tables show new ones.

## Style

Both scripts share one palette so the figures stay consistent:

- Navy `#1F4E79` for Claude Sonnet 4.6 and headings
- Blue `#2E74B5` for GPT-5
- Grey `#8C9BAB` for the Regex baseline
- Red `#C00000` for the trade-off arrow and false flag rates

Charts are written at 200 dpi, which is sharp enough for print at the sizes
used in the report.
