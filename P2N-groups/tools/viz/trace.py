"""
Step-trace recording and termination-measure computation.

Every rewriting step produces one RewritingStep containing:
  - the word AFTER the rule fires
  - which rule fired and its arguments
  - a human-readable description
  - the termination measure f(w) = (n_V, K, T, len(w))  (paper §2.4)
  - an annotations dict {block_index_in_new_word: kind_str}

Annotation kinds
----------------
  normal       – unchanged block
  r1_dest      – block that received the moved element  (R1)
  r1_src       – block that lost the moved element      (R1)
  r2_left      – left block, x^{-ε} removed            (R2)
  r2_right     – right block, x^ε removed              (R2)
  new_price_r  – newly inserted right-price block       (R1 / R2)
  new_price_l  – newly inserted left-price block        (R1 / R2)
  (R3 produces no annotations: the deleted block is described in text)
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dataclasses import dataclass
from typing import Optional

from tools.core.alphabet import is_vertex
from tools.core.hyperletter import HyperLetter, interpret, left_price, right_price
from tools.core.hypergraph import Hypergraph
from tools.core.rewriter import find_applicable_rules, apply_R1, apply_R2, apply_R3
import numpy as np

@dataclass
class RewritingStep:
    word: list                  # list[HyperLetter] — state AFTER the rule
    rule: Optional[str]         # 'R1' | 'R2' | 'R3' | None (initial step)
    description: str
    measure: tuple              # (n_V, K, T, len(w))
    annotations: dict           # {block_index: kind_str}


# ---------------------------------------------------------------------------
# Termination measure (spec Part 2.4 — replaces the old, incorrect §5.2 measure)
# ---------------------------------------------------------------------------

def compute_measure(word, vertices):
    """
    Compute f(w) = (n_V, K, T, len(w)) for a hyperword (spec Part 2.4).

      kappa(z)  = index (0-based) of the block containing letter occurrence z
      n_V(w)    = number of vertex letters in w
      K(w)      = tuple of kappa(z) over vertex letters z, left to right
                  (within a block, in the order F writes them)
      T(w)      = sum of kappa(z) over all EDGE letters z
      len(w)    = number of blocks

    Compared as (n_V, K, T, len) lexicographically; K only gets compared once
    n_V ties, so tuple lengths always match at that point.
    """
    n_V = 0
    K = []
    T = 0
    for k, hl in enumerate(word):
        for base, _ in interpret(hl, vertices):
            if is_vertex(base):
                n_V += 1
                K.append(k)
            else:
                T += k
    return (n_V, tuple(K), T, len(word))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fmt(se, vertices):
    """Format a signed element as plain Unicode for description strings."""
    base, exp = se
    if is_vertex(base):
        name = base
    else:
        v1, v2 = sorted(base, key=lambda v: vertices.index(v))
        sep = '' if all(len(v) == 1 for v in vertices) else ','
        name = f'e_{{{v1}{sep}{v2}}}'
    return name + '⁻\xb9' if exp == -1 else name  # ⁻¹


def _describe(rule, vertices):
    tag = rule[0]
    if tag == 'R1':
        _, i, j, x = rule
        return f'R1: move {_fmt(x, vertices)} from block {j + 1} into block {i + 1}'
    if tag == 'R2':
        _, i, x = rule
        return f'R2: cancel {_fmt(x, vertices)} between blocks {i + 1} and {i + 2}'
    # R3
    _, i = rule
    return f'R3: delete empty block at position {i + 1}'


def _annotate(rule, word, hg):
    """
    Return {new_block_index: kind} for the result word of this rule.

    Under spec 0.1, R1/R2 omit any block that comes out empty, so the number
    of blocks written is not fixed at 4 — it must be recomputed here from the
    same u/v/r/l values apply_R1/apply_R2 would produce, using their exact
    omission order, so annotation indices line up with the real output.
    """
    tag = rule[0]
    if tag == 'R1':
        i, j, x_signed = rule[1], rule[2], rule[3]
        u = word[i]
        v = HyperLetter(word[j].elements - {x_signed})
        u_plus_x = HyperLetter(u.elements | {x_signed})
        r = right_price(x_signed, u, hg)
        l = left_price(x_signed, v, hg)
        labeled = [(u_plus_x, 'r1_dest'), (r, 'new_price_r'),
                   (v, 'r1_src'), (l, 'new_price_l')]
    elif tag == 'R2':
        i, x_signed = rule[1], rule[2]
        x_base, x_exp = x_signed
        x_inv = (x_base, -x_exp)
        u = HyperLetter(word[i].elements - {x_inv})
        v = HyperLetter(word[i + 1].elements - {x_signed})
        r = right_price(x_signed, u, hg)
        l = left_price(x_signed, v, hg)
        labeled = [(u, 'r2_left'), (r, 'new_price_r'),
                   (v, 'r2_right'), (l, 'new_price_l')]
    else:  # R3
        return {}

    i = rule[1]
    annotations = {}
    offset = 0
    for block, kind in labeled:
        if block.elements:
            annotations[i + offset] = kind
            offset += 1
    return annotations


# ---------------------------------------------------------------------------
# Main trace function
# ---------------------------------------------------------------------------

def normal_form_with_trace(word, hg: Hypergraph):
    """
    Run the rewriting system exhaustively, collecting one RewritingStep per
    rule application.

    steps[0]  = initial word (rule=None)
    steps[-1] = normal form
    """
    word = list(word)
    vertices = hg.vertices

    steps = [RewritingStep(
        word=list(word),
        rule=None,
        description='Initial word (lifted via σ)',  # σ
        measure=compute_measure(word, vertices),
        annotations={},
    )]

    for _ in range(10_000):  # safety limit
        rules = find_applicable_rules(word, hg)
        if not rules:
            break
        np.random.shuffle(rules)  # randomize to avoid bias in the trace
        rule = rules[0]

        # _annotate needs the word BEFORE the rule fires (it recomputes u/v/r/l
        # itself to know which of the up-to-4 output blocks were omitted).
        annotations = _annotate(rule, word, hg)

        if rule[0] == 'R3':
            word = apply_R3(word, rule[1])
        elif rule[0] == 'R2':
            word = apply_R2(word, rule[1], rule[2], hg)
        else:  # R1
            word = apply_R1(word, rule[1], rule[2], rule[3], hg)

        steps.append(RewritingStep(
            word=list(word),
            rule=rule[0],
            description=_describe(rule, vertices),
            measure=compute_measure(word, vertices),
            annotations=annotations,
        ))

    return steps
