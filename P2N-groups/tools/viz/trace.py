"""
Step-trace recording and termination-measure computation.

Every rewriting step produces one RewritingStep containing:
  - the word AFTER the rule fires
  - which rule fired and its arguments
  - a human-readable description
  - the termination measure (f1, f2, f3)
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
from tools.core.hyperletter import HyperLetter
from tools.core.hypergraph import Hypergraph
from tools.core.rewriter import find_applicable_rules, apply_R1, apply_R2, apply_R3
import numpy as np

@dataclass
class RewritingStep:
    word: list                  # list[HyperLetter] — state AFTER the rule
    rule: Optional[str]         # 'R1' | 'R2' | 'R3' | None (initial step)
    description: str
    measure: tuple              # (f1, f2, f3)
    annotations: dict           # {block_index: kind_str}


# ---------------------------------------------------------------------------
# Termination measure (paper §5.2)
# ---------------------------------------------------------------------------

def compute_measure(word):
    """
    Compute (f1, f2, f3) for a hyperword.

      w|V  = mixed blocks  (≥1 vertex element), re-indexed 1..p
      w|E  = pure-edge non-empty blocks, re-indexed 1..q
      f1   = Σ k · |{vertex elements in k-th mixed block}|
      f2   = Σ k · |{all elements in k-th pure-edge block}|
      f3   = total block count
    """
    mixed = []
    edge_only = []
    for hl in word:
        if not hl.elements:
            continue
        if any(is_vertex(b) for b, _ in hl.elements):
            mixed.append(hl)
        else:
            edge_only.append(hl)

    f1 = sum(
        (k + 1) * sum(1 for b, _ in hl.elements if is_vertex(b))
        for k, hl in enumerate(mixed)
    )
    f2 = sum((k + 1) * len(hl.elements) for k, hl in enumerate(edge_only))
    f3 = len(word)
    return (f1, f2, f3)


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


def _annotate(rule):
    """Return {new_block_index: kind} for the result word of this rule."""
    tag = rule[0]
    if tag == 'R1':
        i = rule[1]
        return {i: 'r1_dest', i + 1: 'new_price_r', i + 2: 'r1_src', i + 3: 'new_price_l'}
    if tag == 'R2':
        i = rule[1]
        return {i: 'r2_left', i + 1: 'new_price_r', i + 2: 'r2_right', i + 3: 'new_price_l'}
    return {}  # R3


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
        measure=compute_measure(word),
        annotations={},
    )]

    for _ in range(10_000):  # safety limit
        rules = find_applicable_rules(word, hg)
        if not rules:
            break
        np.random.shuffle(rules)  # randomize to avoid bias in the trace
        rule = rules[0]

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
            measure=compute_measure(word),
            annotations=_annotate(rule),
        ))

    return steps
