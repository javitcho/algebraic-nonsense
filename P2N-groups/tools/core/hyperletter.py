"""
HyperLetter, addability, price functions, interpret, and sigma (lifting).

A HyperLetter [u] wraps a frozenset of signed elements.
[∅] = HyperLetter(frozenset()) is the empty hyper-letter.

A word (hyperword) in A* is a list[HyperLetter].
"""

from dataclasses import dataclass
from tools.core.alphabet import total_order_key, c_function, is_vertex


@dataclass(frozen=True)
class HyperLetter:
    """
    A hyper-letter [u] where u ⊆ A±.

    elements: frozenset of signed elements (base, exponent)
    """
    elements: frozenset

    @property
    def support(self):
        """The support |u| = {base | (base, exp) ∈ u}."""
        return frozenset(base for base, _ in self.elements)

    def __repr__(self):
        if not self.elements:
            return '[∅]'
        return f'[{set(self.elements)}]'


EMPTY_LETTER = HyperLetter(frozenset())


def is_addable(b_signed, u: HyperLetter, hypergraph):
    """
    True iff b^η is addable into [u] (paper Definition 4.1):
      1. b ∉ |u|
      2. ∃ maximal edge E with |u| ∪ {b} ⊆ Ē
    """
    b_base, _ = b_signed
    if b_base in u.support:
        return False
    target = u.support | {b_base}
    return any(
        target <= hypergraph.extended_hyperedge(E)
        for E in hypergraph.maximal_edges
    )


def left_price(b_signed, u: HyperLetter, hypergraph) -> HyperLetter:
    """
    l_{b^η}([u]) = [{c(a_i, b)^{η·ε_i} | a_i < b, c ≠ -}]

    Collects commutator symbols for elements of u that are less than b
    in the total order on A (unsigned comparison).
    """
    b_base, b_exp = b_signed
    vertices = hypergraph.vertices

    result = set()
    for a_base, a_exp in u.elements:
        # Check a < b in total order (unsigned: compare positions)
        a_key = total_order_key((a_base, +1), vertices)
        b_key = total_order_key((b_base, +1), vertices)
        if a_key >= b_key:
            continue  # only elements less than b contribute

        c = c_function(a_base, b_base, hypergraph)
        if c is None:
            continue  # "-" → skip

        c_base, c_exp = c
        # signed result: c(a_i, b)^{η · ε_i} = (c_base, c_exp * b_exp * a_exp)
        result.add((c_base, c_exp * b_exp * a_exp))

    return HyperLetter(frozenset(result))


def right_price(b_signed, u: HyperLetter, hypergraph) -> HyperLetter:
    """
    r_{b^η}([u]) = [{c(c_j, b)^{η·δ_j} | c_j > b, c ≠ -}]

    Collects commutator symbols for elements of u that are greater than b
    in the total order on A (unsigned comparison).
    """
    b_base, b_exp = b_signed
    vertices = hypergraph.vertices

    result = set()
    for c_base, c_exp_val in u.elements:
        # Check c_j > b in total order (unsigned comparison)
        cj_key = total_order_key((c_base, +1), vertices)
        b_key = total_order_key((b_base, +1), vertices)
        if cj_key <= b_key:
            continue  # only elements greater than b contribute

        c = c_function(c_base, b_base, hypergraph)
        if c is None:
            continue  # "-" → skip

        c_sym_base, c_sym_exp = c
        # signed result: c(c_j, b)^{η · δ_j}
        result.add((c_sym_base, c_sym_exp * b_exp * c_exp_val))

    return HyperLetter(frozenset(result))


def interpret(u: HyperLetter, vertices) -> tuple:
    """
    F([u]): return signed elements of u sorted by total_order_key.
    F([∅]) = () (empty tuple = identity word).
    """
    return tuple(sorted(u.elements, key=lambda se: total_order_key(se, vertices)))


def sigma(word_in_Apm, hypergraph) -> list:
    """
    Lifting map σ: (A±)* → A*.
    Each signed element becomes a singleton HyperLetter.
    """
    return [HyperLetter(frozenset({se})) for se in word_in_Apm]
