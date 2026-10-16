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


FAIL = {"style": "filled,rounded", "shape": "box", "fillcolor": "#FFEBEE", "color": "#C62828"}


def userflow_graph():
    """Figure 6: what the user does and sees, from any way in to a confirmed event."""
    d = new_graph("userflow")
    d.attr(dpi="200")

    d.node("s", "User has event details\nin an email, message or web page", **START)

    # Three ways in, side by side.
    with d.subgraph() as row:
        row.attr(rank="same")
        row.node("type", "Types or speaks the event\nin the popup", **PROC)
        row.node("select", "Selects text on a page and\nchooses Add to calendar\nfrom the right-click menu", **PROC)
        row.node("slot", "Picks an open time in\nFind a free time", **PROC)

    d.node("read", "Prompt2Cal reads the text\n(it keeps going if the popup is closed;\nthe toolbar badge shows when it is ready)", **PROC)
    d.node("q0", "Event found\nin the text?", **DEC)
    d.node("none", "Told no event was found, or that\nthe service is unavailable;\nnothing is created", **FAIL)

    d.node("preview", "Reviews the event\nin the preview", **SEES)
    d.node("cancel", "Cancels at any point,\nnothing is saved", **END)
    d.node("q1", "Any detail not\nin the text?", **DEC)
    d.node("flags", 'Those details are highlighted;\na default end time is\nlabelled "assumed"', **WARN)
    d.node("q2", "Clashes with an\nexisting event?", **DEC)
    d.node("clash", "Sees a clash warning with the\nnearest free times; one click\nmoves the event", **WARN)
    d.node("q3", "Details\ncorrect?", **DEC)
    d.node("edit", "Edits the event: time, place,\nguests, colour or category,\nreminder", **PROC)
    d.node("confirm", "Clicks Create Event", **PROC)
    d.node("done", "Event added to their\nGoogle or Outlook calendar", **END)

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
    d.edge("q0", "none", xlabel="  no")
    d.edge("q0", "preview", xlabel="  yes")
    # A picked time opens the editor with that time already filled in.
    d.edge("slot", "edit", xlabel="  time filled in")
    # Cancelling is available throughout, so it hangs off the preview.
    d.edge("preview", "cancel", style="dashed", constraint="false", xlabel="  cancel")
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
