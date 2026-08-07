"""
Rewriting rules R1, R2, R3 and normal form algorithm.

A word (hyperword) is a list[HyperLetter].

R1 (Movement):
  [u][v+x^ε] → [u+x^ε] r_{x^ε}([u]) [v] l_{x^ε}([v])
  condition: x^ε addable into u (addable into v is automatic for well-formed letters)
  A price hyper-letter equal to [∅] is omitted from the output, and [v] itself is
  omitted if it becomes empty. R1 never produces an empty block that R3 would later
  need to clean up.

R2 (Cancellation):
  [u+x^{-ε}][v+x^ε] → [u] r_{x^ε}([u]) [v] l_{x^ε}([v])
  condition: x^ε in right block, x^{-ε} in left block
  Same omission convention as R1 — this includes [u] itself if removing x^{-ε}
  empties it.

R3 (Empty deletion):
  [∅] → (removed)
  R3 only ever fires on an empty block already present in the input; R1/R2 never
  write one.
"""

from tools.core.hyperletter import (
    HyperLetter, EMPTY_LETTER, is_addable, left_price, right_price
)
import numpy as np


def apply_R3(word: list, i: int) -> list:
    """Delete empty hyper-letter at position i."""
    return word[:i] + word[i + 1:]


def apply_R2(word: list, i: int, x_signed: tuple, hypergraph) -> list:
    """
    Cancel x^{-ε} from block i and x^ε from block i+1.

    word[i]   = [u + x^{-ε}]
    word[i+1] = [v + x^ε]
    Result: [u] r_{x^ε}([u]) [v] l_{x^ε}([v]), with every empty block omitted.
    """
    x_base, x_exp = x_signed
    x_inv = (x_base, -x_exp)

    u = HyperLetter(word[i].elements - {x_inv})
    v = HyperLetter(word[i + 1].elements - {x_signed})

    r = right_price(x_signed, u, hypergraph)
    l = left_price(x_signed, v, hypergraph)

    new_blocks = [b for b in (u, r, v, l) if b.elements]
    return word[:i] + new_blocks + word[i + 2:]


def apply_R1(word: list, i: int, j: int, x_signed: tuple, hypergraph) -> list:
    """
    Move x^ε from block j into block i  (j = i+1).

    word[i] = [u]
    word[j] = [v + x^ε]
    Result: [u+x^ε] r_{x^ε}([u]) [v] l_{x^ε}([v]), with every empty block omitted.
    [u+x^ε] is never empty (it contains x), so only r, [v], l can be dropped.
    """
    u = word[i]
    v = HyperLetter(word[j].elements - {x_signed})

    u_plus_x = HyperLetter(u.elements | {x_signed})
    r = right_price(x_signed, u, hypergraph)
    l = left_price(x_signed, v, hypergraph)

    new_blocks = [b for b in (u_plus_x, r, v, l) if b.elements]
    assert new_blocks[0] is u_plus_x  # [u+x] is never empty
    return word[:i] + new_blocks + word[j + 1:]


def find_applicable_rules(word: list, hypergraph) -> list:
    """
    Return all applicable (rule, args) pairs, scanning left to right.

    Priority: R3 > R2 > R1  (R2 checked before R1 for same pair).
    Returns a list of tuples:
      ('R3', i)
      ('R2', i, x_signed)
      ('R1', i, i+1, x_signed)
    """
    rules = []
    for i in range(len(word)):
        if not word[i].elements:
            rules.append(('R3', i))
            # still check R1/R2 for pair (i, i+1): [∅][v+x] → R1 may apply

        if i + 1 >= len(word):
            continue

        next_block = word[i + 1]
        for x_signed in next_block.elements:
            x_base, x_exp = x_signed
            x_inv = (x_base, -x_exp)

            if x_inv in word[i].elements:
                # R2: x^{-ε} in block i, x^ε in block i+1
                rules.append(('R2', i, x_signed))
            elif is_addable(x_signed, word[i], hypergraph):
                # R1: x^ε in block i+1 is addable into block i
                rules.append(('R1', i, i + 1, x_signed))

    return rules


def apply_rule(word: list, rule: tuple, hypergraph) -> list:
    """Dispatch a redex tuple from find_applicable_rules to the matching apply_R*."""
    tag = rule[0]
    if tag == 'R3':
        return apply_R3(word, rule[1])
    if tag == 'R2':
        return apply_R2(word, rule[1], rule[2], hypergraph)
    return apply_R1(word, rule[1], rule[2], rule[3], hypergraph)


def normal_form(word: list, hypergraph, strategy='random') -> list:
    """
    Apply rewriting rules exhaustively until no rule applies.
    Confluence (proved in the paper) guarantees a unique result regardless
    of strategy: 'random' (default), 'leftmost' (first redex found), or
    'rightmost' (last redex found).
    """
    word = list(word)
    while True:
        rules = find_applicable_rules(word, hypergraph)
        if not rules:
            break
        if strategy == 'random':
            rule = rules[np.random.randint(len(rules))]
        elif strategy == 'leftmost':
            rule = rules[0]
        elif strategy == 'rightmost':
            rule = rules[-1]
        else:
            raise ValueError(f"Unknown strategy '{strategy}'")
        word = apply_rule(word, rule, hypergraph)
    return word
