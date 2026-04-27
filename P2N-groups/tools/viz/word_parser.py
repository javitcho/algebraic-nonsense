"""
Parsing and formatting for words in A±.

Supported token formats:
  Vertex positive : x  y  z
  Vertex inverse  : x^-1  x^{-1}  x⁻¹
  Edge positive   : e_xy  e_{xy}  e_x,y
  Edge inverse    : e_xy^-1  e_{xy}^{-1}  e_xy⁻¹
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import re
from tools.core.alphabet import is_vertex, total_order_key
from tools.core.hyperletter import HyperLetter, interpret


def _strip_inverse_suffix(token: str):
    """Return (base_token, exponent). Strips ^-1 / ^{-1} / ⁻¹ suffix."""
    for suffix in ('^{-1}', '^-1', '⁻\xb9'):  # ⁻¹
        if token.endswith(suffix):
            return token[:-len(suffix)], -1
    return token, +1


def _parse_edge_base(body: str, hg):
    """
    Parse the body after 'e_' into a frozenset edge symbol.
    Handles:  xy  {xy}  x,y  {x,y}  x y  (for multi-char vertex names)
    Returns frozenset or raises ValueError.
    """
    body = body.strip('{}')
    # Try comma-split first, then space-split, then two-char split
    if ',' in body:
        parts = [p.strip() for p in body.split(',')]
    elif ' ' in body:
        parts = [p.strip() for p in body.split()]
    elif len(body) == 2 and all(c in hg.vertices for c in body):
        parts = [body[0], body[1]]
    else:
        # Try to greedily match vertex names (longest first)
        ordered = sorted(hg.vertices, key=len, reverse=True)
        remaining = body
        parts = []
        while remaining:
            matched = False
            for v in ordered:
                if remaining.startswith(v):
                    parts.append(v)
                    remaining = remaining[len(v):]
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Cannot parse edge body '{body}' using vertices {hg.vertices}")
        if len(parts) != 2:
            raise ValueError(f"Edge symbol must have exactly 2 vertices, got {parts}")

    if len(parts) != 2:
        raise ValueError(f"Edge symbol must have exactly 2 vertices, got {parts}")
    v1, v2 = parts
    edge = frozenset({v1, v2})
    if edge not in hg.E2:
        raise ValueError(f"{{'{v1}','{v2}'}} is not an edge in this hypergraph")
    return edge


def _greedy_split_vertices(s: str, hg) -> list | None:
    """
    Greedily consume vertex names from left to right.
    Returns list of vertex names, or None if the string cannot be fully consumed.
    """
    ordered = sorted(hg.vertices, key=len, reverse=True)
    parts = []
    remaining = s
    while remaining:
        matched = False
        for v in ordered:
            if remaining.startswith(v):
                parts.append(v)
                remaining = remaining[len(v):]
                matched = True
                break
        if not matched:
            return None
    return parts


def parse_word(text: str, hg) -> list:
    """
    Parse a word in A± into a sigma-lifted hyperword (list of singleton HyperLetters).

    Accepts space-separated tokens OR compact concatenated vertex strings.

    Space-separated token formats:
      x  x^-1  x^{-1}  x⁻¹  e_xy  e_xy^-1  e_{xy}  e_{x,y}

    Compact shorthand (no spaces, single-char or multi-char vertices):
      zyxzyx  →  z y x z y x (all positive)
      xyz^-1  →  x y z^-1 (exponent applies to the last symbol)

    Raises ValueError with a descriptive message on bad input.
    """
    tokens = text.strip().split()
    result = []
    for token in tokens:
        base_tok, exp = _strip_inverse_suffix(token)

        if base_tok.startswith('e_'):
            base = _parse_edge_base(base_tok[2:], hg)
            result.append(HyperLetter(frozenset({(base, exp)})))
            continue

        # Exact vertex match
        if base_tok in hg.vertices:
            result.append(HyperLetter(frozenset({(base_tok, exp)})))
            continue

        # Compact shorthand: greedily decompose into vertex names
        parts = _greedy_split_vertices(base_tok, hg)
        if parts is not None:
            for v in parts[:-1]:
                result.append(HyperLetter(frozenset({(v, +1)})))
            result.append(HyperLetter(frozenset({(parts[-1], exp)})))
            continue

        raise ValueError(
            f"Unknown symbol '{base_tok}'. "
            f"Vertices are {list(hg.vertices)}. "
            f"Use spaces to separate elements (e.g. 'z y x') or write edges as e_xy."
        )

    return result


def format_se(se: tuple, vertices: tuple) -> str:
    """Format a signed element as Unicode text."""
    base, exp = se
    if is_vertex(base):
        name = base
    else:
        v1, v2 = sorted(base, key=lambda v: vertices.index(v))
        sep = ',' if any(len(v) > 1 for v in vertices) else ''
        name = f'e_{{{v1}{sep}{v2}}}'
    return name + '⁻\xb9' if exp == -1 else name   # ⁻¹


def format_hyperword(word: list, vertices: tuple) -> str:
    """
    Project a hyperword back to A± text.
    Blocks separated by ' | '; empty block shown as '∅'.
    """
    parts = []
    for hl in word:
        if not hl.elements:
            parts.append('∅')  # ∅
        else:
            sorted_els = interpret(hl, vertices)
            parts.append(' '.join(format_se(se, vertices) for se in sorted_els))
    return ' | '.join(parts)
