"""
Enumeration of dense (downward-closed) hypergraphs (spec Part 3.0).

A downward-closed family E ⊆ P(V) is uniquely determined by an antichain (its
maximal elements); enumerating all such E is equivalent to enumerating all
order ideals of the Boolean lattice 2^V, whose count is the Dedekind number
M(n): M(3)=20, M(4)=168, M(5)=7581. We enumerate by DFS over subsets in
decreasing size order (supersets decided before subsets), propagating forced
inclusion downward — this avoids ever materializing 2^(2^n) candidates.
"""

import itertools
import random

from tools.core.hypergraph import Hypergraph


def _all_subsets_of(s: frozenset):
    """All subsets of s (including s itself and the empty set)."""
    items = list(s)
    return frozenset(
        frozenset(c)
        for k in range(len(items) + 1)
        for c in itertools.combinations(items, k)
    )


def _ordered_subsets(n):
    """All subsets of range(n), largest first (ties broken arbitrarily)."""
    universe = list(range(n))
    subsets = []
    for size in range(n, -1, -1):
        for combo in itertools.combinations(universe, size):
            subsets.append(frozenset(combo))
    return subsets


def enumerate_downward_closed(n):
    """
    Yield every downward-closed E ⊆ P([n]) as a frozenset of frozensets of
    ints in range(n). DFS over subsets in decreasing size order; at each
    subset, if some already-included superset forces it, it is included
    with no choice, else we branch on include/exclude.
    """
    subsets = _ordered_subsets(n)

    def backtrack(idx, forced, chosen):
        if idx == len(subsets):
            yield frozenset(chosen)
            return
        s = subsets[idx]
        if s in forced:
            yield from backtrack(idx + 1, forced, chosen | {s})
        else:
            yield from backtrack(idx + 1, forced, chosen)
            yield from backtrack(idx + 1, forced | _all_subsets_of(s), chosen | {s})

    yield from backtrack(0, frozenset(), frozenset())


def sample_downward_closed(n, count, rng: random.Random):
    """
    Randomly sample `count` downward-closed E ⊆ P([n]) by making a random
    include/exclude choice at every free (unforced) decision point in the
    same decreasing-size DFS used by enumerate_downward_closed. Used for
    n too large to enumerate exhaustively (spec: n=5 "on a sample").
    """
    subsets = _ordered_subsets(n)
    results = []
    for _ in range(count):
        forced = frozenset()
        chosen = set()
        for s in subsets:
            if s in forced:
                chosen.add(s)
            elif rng.random() < 0.5:
                chosen.add(s)
                forced = forced | _all_subsets_of(s)
        results.append(frozenset(chosen))
    return results


def to_hypergraph(edge_family, n) -> Hypergraph:
    """Convert a frozenset-of-int-frozensets family into a Hypergraph with
    vertices labelled 'v1'..'vn'."""
    labels = tuple(f'v{i + 1}' for i in range(n))
    edges = frozenset(
        frozenset(labels[i] for i in e) for e in edge_family
    )
    return Hypergraph(vertices=labels, edges=edges)


def hypergraphs_for(n):
    """All dense hypergraphs on n vertices, as Hypergraph objects."""
    return [to_hypergraph(fam, n) for fam in enumerate_downward_closed(n)]


def sampled_hypergraphs_for(n, count, seed=0):
    """`count` random dense hypergraphs on n vertices (for large n)."""
    rng = random.Random(seed)
    return [to_hypergraph(fam, n) for fam in sample_downward_closed(n, count, rng)]
