"""
TEST A (spec Part 3.2) — the termination measure f(w) = (n_V, K, T, len(w))
is strictly monotone decreasing under every redex.

Python tuple comparison already implements the required lexicographic order:
n_V compares first; if it ties, K (same length on both sides, since |K| = n_V
on both) compares elementwise; only if that ties too do T and len(w) break
the tie. So `after < before` on the raw compute_measure() tuples is exactly
the check the spec asks for — no custom comparator needed.
"""

from tools.core.rewriter import find_applicable_rules, apply_rule
from tools.viz.trace import compute_measure


def check_word(word, hg):
    """
    For every redex applicable to `word`, apply it and check f strictly
    decreases. Returns a list of violation dicts (empty if all pass).
    """
    violations = []
    vertices = hg.vertices
    before_f = compute_measure(word, vertices)
    for rule in find_applicable_rules(word, hg):
        after = apply_rule(word, rule, hg)
        after_f = compute_measure(after, vertices)
        if not (after_f < before_f):
            violations.append({
                'word': word,
                'redex': rule,
                'f_before': before_f,
                'f_after': after_f,
            })
    return violations


def known_bad_fixture():
    """
    Spec's regression fixture: v1..v4 in a common maximal hyperedge,
    [{e12}][{v3,v4}] -> [{e12,v3}][{v4}] must give K: (1,1) -> (0,1).
    Returns (hg, word, expected_rule_tag).
    """
    from tools.core.hypergraph import Hypergraph
    from tools.core.hyperletter import HyperLetter

    vertices = ('v1', 'v2', 'v3', 'v4')
    full = frozenset(vertices)
    edges = frozenset(
        frozenset(c) for k in range(len(vertices) + 1)
        for c in __import__('itertools').combinations(vertices, k)
    )
    hg = Hypergraph(vertices=vertices, edges=edges)
    e12 = frozenset({'v1', 'v2'})

    word = [
        HyperLetter(frozenset({(e12, +1)})),
        HyperLetter(frozenset({('v3', +1), ('v4', +1)})),
    ]
    return hg, word


def run(words_with_hg):
    """
    words_with_hg: iterable of (word, hg) pairs.
    Returns dict with cases_run, violations (list), and a pass/fail summary,
    always including the known-bad fixture check first.
    """
    all_violations = []
    cases_run = 0

    hg0, fixture_word = known_bad_fixture()
    fixture_violations = check_word(fixture_word, hg0)
    cases_run += 1
    if fixture_violations:
        for v in fixture_violations:
            v['source'] = 'known_bad_fixture'
        all_violations.extend(fixture_violations)

    for word, hg in words_with_hg:
        cases_run += 1
        vs = check_word(word, hg)
        for v in vs:
            v['source'] = 'generated'
            v['hypergraph_vertices'] = hg.vertices
        all_violations.extend(vs)

    return {
        'test': 'A',
        'cases_run': cases_run,
        'pass': len(all_violations) == 0,
        'violations': all_violations,
    }
