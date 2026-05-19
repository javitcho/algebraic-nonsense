"""
Parsing and formatting for words in A±.

Supported token formats:
  Vertex positive : x  y  z
  Vertex inverse  : X  x^-1  x^{-1}  x⁻¹   (uppercase = inverse)
  Edge positive   : e_xy  e_{xy}  e_x,y
  Edge inverse    : e_xy^-1  e_{xy}^{-1}  e_xy⁻¹

Compact shorthand (no spaces):
  XYZ   →  x⁻¹ y⁻¹ z⁻¹
  xYz   →  x y⁻¹ z
  XYZxyz → x⁻¹ y⁻¹ z⁻¹ x y z
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


def _match_vertex(s: str, hg) -> tuple | None:
    """
    Try to consume one vertex name from the start of s.
    Returns (vertex, exp, remaining) or None.
    Uppercase variant → exp=-1; lowercase → exp=+1.
    Tries longer names first to avoid ambiguous partial matches.
    """
    ordered = sorted(hg.vertices, key=len, reverse=True)
    for v in ordered:
        if s.startswith(v):
            return (v, +1, s[len(v):])
        v_up = v.upper()
        if v_up != v and s.startswith(v_up):
            return (v, -1, s[len(v_up):])
    return None


def _greedy_split_vertices(s: str, hg) -> list | None:
    """
    Greedily consume vertex names (lowercase=positive, uppercase=inverse).
    Returns list of (vertex, exp) pairs, or None if s cannot be fully consumed.
    """
    parts = []
    remaining = s
    while remaining:
        m = _match_vertex(remaining, hg)
        if m is None:
            return None
        v, exp, remaining = m
        parts.append((v, exp))
    return parts


def parse_word(text: str, hg) -> list:
    """
    Parse a word in A± into a sigma-lifted hyperword (list of singleton HyperLetters).

    Accepts space-separated tokens OR compact concatenated strings.

    Space-separated tokens:
      x  X  x^-1  x^{-1}  x⁻¹  e_xy  e_xy^-1  e_{xy}  e_{x,y}

    Compact shorthand (no spaces):
      XYZxyz  →  x⁻¹ y⁻¹ z⁻¹ x y z
      xYz^-1  →  x  y⁻¹  z⁻¹   (suffix applies to last symbol)

    Raises ValueError with a descriptive message on bad input.
    """
    tokens = text.strip().split()
    result = []
    for token in tokens:
        base_tok, suffix_exp = _strip_inverse_suffix(token)

        # Edge symbol (uppercase has no meaning for edges)
        if base_tok.startswith('e_') or base_tok.lower().startswith('e_'):
            body = base_tok[2:] if base_tok.lower().startswith('e_') else base_tok[2:]
            base = _parse_edge_base(body, hg)
            result.append(HyperLetter(frozenset({(base, suffix_exp)})))
            continue

        # Exact vertex match (lowercase = positive)
        if base_tok in hg.vertices:
            result.append(HyperLetter(frozenset({(base_tok, suffix_exp)})))
            continue

        # Single uppercase token = inverse of the lowercase vertex
        if base_tok.lower() in hg.vertices and base_tok != base_tok.lower():
            # Combine: uppercase (-1) * suffix_exp
            result.append(HyperLetter(frozenset({(base_tok.lower(), -suffix_exp)})))
            continue

        # Compact shorthand: greedily decompose into (vertex, exp) pairs
        parts = _greedy_split_vertices(base_tok, hg)
        if parts is not None:
            for v, exp in parts[:-1]:
                result.append(HyperLetter(frozenset({(v, exp)})))
            last_v, last_exp = parts[-1]
            # suffix_exp combines with the case-derived exp: X^-1 → x^{-(-1)} = x
            result.append(HyperLetter(frozenset({(last_v, last_exp * suffix_exp)})))
            continue

        raise ValueError(
            f"Unknown symbol '{base_tok}'. "
            f"Vertices: {list(hg.vertices)}. "
            f"Use spaces between elements or write edges as e_xy."
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
