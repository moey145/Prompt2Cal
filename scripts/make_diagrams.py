#!/usr/bin/env python3
"""
Generate the report's flow diagrams.

Usage:
    python scripts/make_diagrams.py
    python scripts/make_diagrams.py --outdir report/figures

Writes:
    fig2_pipeline.png     evaluation pipeline (methodology)
    fig6_userflow.png     user flow through the extension

Requires: graphviz, both the Python package and the system binary.
    pip install graphviz
    sudo apt install graphviz      # or: brew install graphviz
Check the binary is on your PATH with: dot -V
"""

import argparse
import os

from graphviz import Digraph

# House style, matching the report palette
START = {"style": "filled,rounded", "shape": "box", "fillcolor": "#C8E6C9", "color": "#2E7D32"}
PROC  = {"style": "filled,rounded", "shape": "box", "fillcolor": "#D6E4F0", "color": "#1F4E79"}
SEES  = {"style": "filled,rounded", "shape": "box", "fillcolor": "#E8EEF5", "color": "#5B7FA6"}
DEC   = {"style": "filled",         "shape": "diamond", "fillcolor": "#FFF3E0", "color": "#E65100"}
WARN  = {"style": "filled,rounded", "shape": "box", "fillcolor": "#FFE0B2", "color": "#E65100"}
END   = {"style": "filled,rounded", "shape": "box", "fillcolor": "#C8E6C9", "color": "#2E7D32"}


def new_graph(name):
    d = Digraph(name, format="png")
    d.attr(rankdir="TB", bgcolor="white", nodesep="0.38", ranksep="0.45")
    d.attr("node", fontname="Helvetica", fontsize="10")
    d.attr("edge", color="#555555", fontname="Helvetica", fontsize="9")
    return d


def pipeline(outdir):
    """Figure 2: the evaluation pipeline, from benchmark input through to metrics."""
    d = new_graph("pipeline")

    d.node("input", "Benchmark input\n(n = 100)", **START)
    d.node("gpt", "GPT-5 extractor\nAPI default temperature\n3 runs per input", **PROC)
    d.node("regex", "Regex extractor\n23 patterns + dateparser fallback", **PROC)
    d.node("claude", "Claude Sonnet 4.6 extractor\ntemperature 0.0\n3 runs per input", **PROC)
    d.node("gptout", "3 JSON outputs per input", **START)
    d.node("claudeout", "3 JSON outputs per input", **START)
    d.node("regexout", "1 JSON output per input", **START)
    d.node("post", "Shared post-processing\n(dateparser to ISO 8601)", **PROC)
    d.node("align", "Per-event alignment\n(rapidfuzz Levenshtein ratio at least 0.7)", **PROC)
    d.node("compare", "Comparison against ground-truth labels", **PROC)

    d.node("m1", "Accuracy\nF1 score", **WARN)
    d.node("m2", "Robustness\nF1 across categories", **WARN)
    d.node("m3", "Consistency\npairwise agreement", **WARN)
    d.node("m4", "Hallucination rate\nfabricated vs null fields", **WARN)
    d.node("verifier", "Source grounding verifier\nhallucination detection", **WARN)

    for a, b in [("input", "gpt"), ("input", "claude"), ("input", "regex"),
                 ("gpt", "gptout"), ("claude", "claudeout"), ("regex", "regexout"),
                 ("gptout", "post"), ("claudeout", "post"), ("regexout", "post"),
                 ("post", "align"), ("align", "compare"),
                 ("compare", "m1"), ("compare", "m2"),
                 ("compare", "m3"), ("compare", "m4")]:
        d.edge(a, b)

    # dashed: the verifier is a later analysis derived from the hallucination results
    d.edge("m4", "verifier", style="dashed")

    path = os.path.join(outdir, "fig2_pipeline")
    d.render(path, cleanup=True)
    return path + ".png"


def userflow(outdir):
    """Figure 6: what the user does and sees, from input to confirmed event."""
    d = new_graph("userflow")

    d.node("s", "User has event details\nin an email, message, or page", **START)
    d.node("open", "Opens the extension", **PROC)
    d.node("input", "Types, pastes, speaks,\nor selects text on the page", **PROC)
    d.node("preview", "Reviews the extracted event\nin the preview", **SEES)
    d.node("cancel", "Discards at any point,\nnothing is saved", **END)

    d.node("q1", "Any field missing\nfrom the text?", **DEC)
    d.node("flags", 'Sees those fields flagged as\n"not found in your text",\nassumed values labelled', **WARN)
    d.node("q2", "Clashes with an\nexisting event?", **DEC)
    d.node("clash", "Sees a clash warning", **WARN)
    d.node("q3", "Details\ncorrect?", **DEC)
    d.node("edit", "Edits or fills in\nthe flagged field", **PROC)
    d.node("confirm", "Confirms, optionally setting\ncalendar, colour, and reminders", **PROC)
    d.node("done", "Event added to their calendar", **END)

    d.edge("s", "open")
    d.edge("open", "input")
    d.edge("input", "preview")
    # discard is available throughout, so it hangs off the preview
    d.edge("preview", "cancel", style="dashed", constraint="false", xlabel="  discard")
    d.edge("preview", "q1")
    d.edge("q1", "flags", xlabel="  yes")
    d.edge("q1", "q2", xlabel="  no")
    d.edge("flags", "q2")
    d.edge("q2", "clash", xlabel="  yes")
    d.edge("q2", "q3", xlabel="  no")
    d.edge("clash", "q3")
    d.edge("q3", "confirm", xlabel="  yes")
    d.edge("q3", "edit", xlabel="  no")
    d.edge("edit", "preview", style="dashed", xlabel="  recheck")
    d.edge("confirm", "done")

    path = os.path.join(outdir, "fig6_userflow")
    d.render(path, cleanup=True)
    return path + ".png"


def main():
    parser = argparse.ArgumentParser(description="Generate report diagrams.")
    parser.add_argument("--outdir", default="report/figures")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    for path in (pipeline(args.outdir), userflow(args.outdir)):
        print("wrote", path)


if __name__ == "__main__":
    main()
