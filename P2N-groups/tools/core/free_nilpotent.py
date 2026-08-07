"""
The free 2-nilpotent group F_{2,n} on vertices V, used as an independent
correctness oracle (spec Part 2.3): mu_2(w) = mu_2(w') is checked by a route
that shares no code with the hyperletter rewriter (no is_addable, no price
functions) — only vertex indices and edge-symbol parsing.

Representation: an element is a pair (a, B) with
  a in Z^n           — the abelianisation Z^n
  B in Lambda^2 Z^n  — the weight-2 part, stored as {(p,q): int} for p<q
in the normal form x_1^{a_1} ... x_n^{a_n} * prod_{p<q} [x_p,x_q]^{B_pq}.

Group law (derived from the class-2 identity uv = vu[u,v]): to append a
signed vertex letter x_k^eps to a state (a,B), x_k^eps must move left past
x_j^{a_j} for every j > k, each swap paying commutator [x_j,x_k]^{a_j*eps}
= [x_k,x_j]^{-a_j*eps}, i.e. contributing -a_j*eps to B_{k,j} (using the
OLD a_j, before this step updates a_k). An edge letter e_pq^eps is already
central in F_{2,n}, so it just adds eps to B_{p,q} directly.
"""

from tools.core.alphabet import is_vertex


def mu2_image(flat_word, hypergraph):
    """
    flat_word: iterable of signed elements (base, exp) in A^± (NOT a hyperword —
    callers pass tools.core.hyperletter.interpret()'d/concatenated output).

    Returns (a, B) with a: tuple of n ints, B: frozenset of (p, q, value)
    for p < q with value != 0 (so equal images compare equal regardless of
    how sparsely B was populated).
    """
    vertices = hypergraph.vertices
    n = len(vertices)
    a = [0] * n
    B = {}

    for base, eps in flat_word:
        if is_vertex(base):
            k = vertices.index(base)
            for j in range(k + 1, n):
                if a[j] == 0:
                    continue
                key = (k, j)
                B[key] = B.get(key, 0) - a[j] * eps
            a[k] += eps
        else:
            v1, v2 = sorted(base, key=lambda v: vertices.index(v))
            p, q = vertices.index(v1), vertices.index(v2)
            key = (p, q)
            B[key] = B.get(key, 0) + eps

    B_clean = frozenset((p, q, val) for (p, q), val in B.items() if val != 0)
    return tuple(a), B_clean


def mu_check(word1, word2, hypergraph) -> bool:
    """
    True iff hyperwords word1, word2 (list[HyperLetter]) represent the same
    element of G(chi), verified by an independent route: map F(word1),
    F(word2) into F_{2,n} and compare images.

    This catches sign errors in the price functions (spec Part 2.3) because
    it never calls left_price/right_price/is_addable itself.
    """
    from tools.core.hyperletter import interpret

    flat1 = [se for hl in word1 for se in interpret(hl, hypergraph.vertices)]
    flat2 = [se for hl in word2 for se in interpret(hl, hypergraph.vertices)]
    return mu2_image(flat1, hypergraph) == mu2_image(flat2, hypergraph)
