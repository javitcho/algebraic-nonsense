"""
MCP server exposing P2N normal-form tools to Claude.

Tools
-----
list_presets()
    Returns the available named hypergraphs and their alphabets.

compute_normal_form(word, preset)
    Full step-by-step trace for a word over a preset hypergraph.

compute_normal_form_custom(word, vertices, edges)
    Same, but with a user-defined hypergraph.

Run (stdio transport, used by Claude Code):
    python3 tools/mcp_server.py
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mcp.server.fastmcp import FastMCP

from tools.core.hypergraph import Hypergraph
from tools.viz.trace import normal_form_with_trace, compute_measure
from tools.viz.word_parser import parse_word, format_se, format_hyperword
from tests.fixtures import HEISENBERG, PATH, TRIANGLE

mcp = FastMCP("p2n-groups")

PRESETS = {
    "heisenberg": HEISENBERG,
    "path":       PATH,
    "triangle":   TRIANGLE,
}


def _alphabet_description(hg) -> str:
    verts = list(hg.vertices)
    edges = sorted(hg.E2, key=lambda e: tuple(sorted(e, key=lambda v: hg.vertices.index(v))))
    sep = ',' if any(len(v) > 1 for v in hg.vertices) else ''
    edge_strs = [
        'e_{' + sep.join(sorted(e, key=lambda v: hg.vertices.index(v))) + '}'
        for e in edges
    ]
    return f"V={list(verts)}, E2={[set(e) for e in edges]}, A={verts + edge_strs}"


def _format_step(i, step, vertices) -> str:
    n_V, K, T, length = step.measure
    word_str = format_hyperword(step.word, vertices)
    if step.rule is None:
        rule_str = "Initial (σ)"
    else:
        rule_str = step.description
    return f"  step {i:2d}  [{rule_str}]  measure=(n_V={n_V},K={K},T={T},len={length})  word: {word_str}"


def _run_trace(word_text: str, hg) -> str:
    try:
        word = parse_word(word_text.strip(), hg)
    except ValueError as e:
        return f"Parse error: {e}"

    steps = normal_form_with_trace(word, hg)
    lines = [f"Input: {word_text.strip()}",
             f"Hypergraph: {_alphabet_description(hg)}",
             f"Total steps: {len(steps) - 1}  (step 0 = initial)",
             ""]
    for i, step in enumerate(steps):
        lines.append(_format_step(i, step, hg.vertices))

    nf = steps[-1].word
    lines.append("")
    if nf:
        lines.append(f"Normal form: {format_hyperword(nf, hg.vertices)}")
    else:
        lines.append("Normal form: ε (identity)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_presets() -> str:
    """
    List the available named hypergraphs (presets) and their augmented alphabets.
    Use preset names as the 'preset' argument in compute_normal_form.
    """
    lines = []
    for name, hg in PRESETS.items():
        lines.append(f"  {name:12s}  {_alphabet_description(hg)}")
    return "Available presets:\n" + "\n".join(lines)


@mcp.tool()
def compute_normal_form(word: str, preset: str = "heisenberg") -> str:
    """
    Compute the normal form of a word in A± over a named hypergraph.

    Args:
        word:   Word in A± notation. Supports:
                  - space-separated tokens: 'x^-1 y^-1 x y'
                  - compact (no spaces):    'XYxy'  (uppercase = inverse)
                  - LaTeX exponent:         'x^{-1} y^{-1} x y'
                  - edge symbols:           'e_xy^-1 x^-1 e_xy x'
        preset: One of 'heisenberg', 'path', 'triangle'.

    Returns a full step-by-step trace with rule name, word state, and
    termination measure (n_V, K, T, len) at each step.
    """
    preset_key = preset.lower().strip()
    if preset_key not in PRESETS:
        return f"Unknown preset '{preset}'. Available: {list(PRESETS.keys())}"
    return _run_trace(word, PRESETS[preset_key])


@mcp.tool()
def compute_normal_form_custom(word: str, vertices: str, edges: str) -> str:
    """
    Compute the normal form of a word over a custom hypergraph.

    Args:
        word:     Word in A± notation (same formats as compute_normal_form).
        vertices: Comma-separated ordered vertex list, e.g. 'a,b,c'.
        edges:    Newline-separated edges, each edge is space-separated vertices,
                  e.g. 'a b\\nb c'  defines edges {a,b} and {b,c}.
                  Dense closure is computed automatically.

    Returns a full step-by-step trace.
    """
    verts = tuple(v.strip() for v in vertices.split(',') if v.strip())
    if not verts:
        return "Error: vertices list is empty."

    explicit_edges = []
    for line in edges.strip().splitlines():
        parts = [p.strip() for p in line.split() if p.strip()]
        if not parts:
            continue
        for p in parts:
            if p not in verts:
                return f"Error: vertex '{p}' in edge not found in vertices {list(verts)}."
        explicit_edges.append(frozenset(parts))

    # Dense (downward-closed) closure
    all_edges: set = {frozenset()}
    for e in explicit_edges:
        lst = list(e)
        for k in range(len(lst) + 1):
            for sub in _subsets(lst, k):
                all_edges.add(frozenset(sub))

    hg = Hypergraph(vertices=verts, edges=frozenset(all_edges))
    return _run_trace(word, hg)


def _subsets(lst, k):
    if k == 0:
        yield []
    elif k > len(lst):
        return
    else:
        first, rest = lst[0], lst[1:]
        for sub in _subsets(rest, k - 1):
            yield [first] + sub
        yield from _subsets(rest, k)


if __name__ == "__main__":
    mcp.run(transport="stdio")
