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


# Figure 6 keeps the look of the report's original hand-drawn user flow:
# pill-shaped green ends (class "terminal"), blue steps, peach decisions.
FLOW_END = {"shape": "box", "style": "rounded,filled", "fillcolor": "#B5EFCB", "color": "#2F8F55", "class": "terminal"}
FLOW_STEP = {"shape": "box", "style": "rounded,filled", "fillcolor": "#C7DBFA", "color": "#3A6BD4"}
FLOW_DEC = {"shape": "diamond", "style": "filled", "fillcolor": "#F7D3B0", "color": "#A9581B"}
FLOW_SEES = {"shape": "box", "style": "rounded,filled", "fillcolor": "#F7D3B0", "color": "#A9581B"}
FLOW_STOP = {"shape": "box", "style": "rounded,filled", "fillcolor": "#F8D4D4", "color": "#B23B3B", "class": "terminal"}


def userflow_graph():
    """Figure 6: what the user does and sees, from any way in to a confirmed event."""
    d = new_graph("userflow")
    d.attr(dpi="200", nodesep="0.45", ranksep="0.5")
    d.attr("node", fontname="Arial", fontsize="10", margin="0.22,0.1", penwidth="1.2")
    d.attr("edge", color="#111111", fontname="Arial", fontsize="8", arrowsize="0.8")

    d.node("s", "User has event details in an email, message, or page", **FLOW_END)

    # Three ways in, side by side.
    with d.subgraph() as row:
        row.attr(rank="same")
        row.node("type", "Opens the extension and types,\npastes, or speaks the event", **FLOW_STEP)
        row.node("select", "Selects text on a page and chooses\nAdd to calendar from the right-click menu", **FLOW_STEP)
        row.node("slot", "Picks an open time\nin Find a free time", **FLOW_STEP)

    d.node("read", "Prompt2Cal reads the text, even if the popup is closed", **FLOW_STEP)
    d.node("q0", "Event found\nin the text?", **FLOW_DEC)
    d.node("none", "Told no event was found,\nnothing is created", **FLOW_STOP)

    d.node("preview", "Reviews the extracted event in the preview", **FLOW_STEP)
    d.node("cancel", "Discards event at any point,\nnothing is saved", **FLOW_END)
    d.node("q1", "Are any fields missing\nfrom the text?", **FLOW_DEC)
    d.node("flags", "Sees those fields highlighted as not in\nyour text, assumed values labelled", **FLOW_SEES)
    d.node("q2", "Clashes with an\nexisting event?", **FLOW_DEC)
    d.node("clash", "Sees a clash warning with\nthe nearest free times", **FLOW_SEES)
    d.node("q3", "Details correct?", **FLOW_DEC)
    d.node("edit", "Edits or fills in the event details", **FLOW_STEP)
    d.node("confirm", "Confirms event, optionally setting\nevent colours and reminders", **FLOW_STEP)
    d.node("done", "Event added to their calendar", **FLOW_END)

    # Each side outcome sits level with the step it branches from, which keeps
    # the diagram short enough for a page.
    for pair in (("q0", "none"), ("preview", "cancel"), ("q1", "flags"), ("q2", "clash")):
        with d.subgraph() as level:
            level.attr(rank="same")
            for node in pair:
                level.node(node)

    d.edge("s", "type")
    d.edge("s", "select")
    d.edge("s", "slot")
    d.edge("type", "read")
    d.edge("select", "read")
    d.edge("read", "q0")
    d.edge("q0", "none", label=" No")
    d.edge("q0", "preview", label=" Yes")
    # A picked time opens the editor with that time already filled in.
    d.edge("slot", "edit", label=" Time filled in")
    # Discarding is available throughout, so it hangs off the preview.
    d.edge("preview", "cancel", style="dashed", constraint="false", label=" Discard")
    d.edge("preview", "q1")
    d.edge("q1", "flags", label=" Yes")
    d.edge("q1", "q2", label=" No")
    d.edge("flags", "q2")
    d.edge("q2", "clash", label=" Yes")
    d.edge("q2", "q3", label=" No")
    d.edge("clash", "q3")
    d.edge("q3", "confirm", label=" Yes")
    d.edge("q3", "edit", label=" No")
    d.edge("edit", "preview", style="dashed", label=" Recheck")
    d.edge("confirm", "done")
    return d


def userflow(outdir):
    path = os.path.join(outdir, "fig6_userflow")
    userflow_graph().render(path, cleanup=True)
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
