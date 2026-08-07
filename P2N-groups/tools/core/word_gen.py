"""
Word generation for the experiments (spec Part 3.1).

Two modes:
  random_words(hg, ...)      - sample random words in (A^±)*, lift via sigma
  exhaustive_normal_forms()  - all normal forms with <= k blocks, <= L letters
"""

import itertools
import random

from tools.core.alphabet import is_vertex
from tools.core.hyperletter import HyperLetter, sigma, is_addable
from tools.core.rewriter import normal_form, find_applicable_rules


def signed_alphabet(hg):
    """All signed elements a^eps for a in A = V ∪ E2, eps in {+1,-1}."""
    letters = list(hg.vertices) + list(hg.E2)
    return [(a, eps) for a in letters for eps in (+1, -1)]


def random_word(hg, length, rng: random.Random):
    """A uniformly random word in (A^±)^length, as a flat list of signed elements."""
    alphabet = signed_alphabet(hg)
    return [rng.choice(alphabet) for _ in range(length)]


def random_normal_forms(hg, count, max_length=20, seed=0):
    """
    Sample `count` random words of random length in [1, max_length], lift via
    sigma, reduce to normal form. Yields (flat_word, lifted, nf) triples.
    This is the mode that scales (spec: aim for 10^6+ samples) since it never
    enumerates hyper-letters.
    """
    rng = random.Random(seed)
    for _ in range(count):
        length = rng.randint(1, max_length)
        flat = random_word(hg, length, rng)
        lifted = sigma(flat, hg)
        nf = normal_form(lifted, hg)
        yield flat, lifted, nf


def _all_hyperletters(hg, max_letter_size=None):
    """
    All non-empty legal hyper-letters over hg: subsets u of A^± with no base
    repeated, no inverse pair, and support(u) contained in some maximal
    hyperedge's extended hyperedge. Exhaustive — blows up as 3^|Ebar|, so only
    usable for small hypergraphs (spec warns against this for headline runs).
    """
    letters = list(hg.vertices) + list(hg.E2)
    seen = set()
    for E in hg.maximal_edges:
        ext = sorted(hg.extended_hyperedge(E), key=lambda a: letters.index(a))
        n = len(ext)
        if max_letter_size is not None and n > 20:
            continue
        # each base element: absent, +1, or -1
        for choice in itertools.product((None, +1, -1), repeat=n):
            elements = frozenset(
                (base, eps) for base, eps in zip(ext, choice) if eps is not None
            )
            if not elements:
                continue
            if elements in seen:
                continue
            seen.add(elements)
            yield HyperLetter(elements)


def exhaustive_hyperwords(hg, max_blocks=5, max_letters=7):
    """
    All hyperwords with <= max_blocks blocks and <= max_letters total signed
    elements (spec 3.1 exhaustive mode). Filtering to normal forms is the
    caller's job (this just enumerates candidate hyperwords).
    """
    all_letters = list(_all_hyperletters(hg))

    def gen(remaining_blocks, remaining_letters):
        if remaining_blocks == 0:
            yield []
            return
        yield from gen(remaining_blocks - 1, remaining_letters)  # stop early: fewer blocks
        for hl in all_letters:
            size = len(hl.elements)
            if size > remaining_letters:
                continue
            for rest in gen(remaining_blocks - 1, remaining_letters - size):
                yield [hl] + rest

    seen = set()
    for k in range(0, max_blocks + 1):
        for word in gen(k, max_letters):
            key = tuple(hl.elements for hl in word)
            if key in seen:
                continue
            seen.add(key)
            yield word


def exhaustive_normal_forms(hg, max_blocks=5, max_letters=7):
    """All hyperwords from exhaustive_hyperwords that are already in normal form."""
    for word in exhaustive_hyperwords(hg, max_blocks, max_letters):
        if not find_applicable_rules(word, hg):
            yield word
