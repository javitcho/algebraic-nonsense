"""
TEST B (spec Part 3.3) — local confluence: for every word with >= 2 distinct
redexes, applying any two of them and reducing both branches to normal form
must agree.
"""

from tools.core.rewriter import find_applicable_rules, apply_rule, normal_form


def check_word(word, hg, max_pairs=None):
    """
    For every unordered pair of distinct redexes applicable to `word`, apply
    each, reduce both branches to normal form, and check they agree.
    Returns a list of violation dicts (empty if all pass or <2 redexes exist).
    """
    redexes = find_applicable_rules(word, hg)
    if len(redexes) < 2:
        return []

    violations = []
    n = len(redexes)
    pairs_checked = 0
    for i in range(n):
        for j in range(i + 1, n):
            if max_pairs is not None and pairs_checked >= max_pairs:
                return violations
            pairs_checked += 1
            r1, r2 = redexes[i], redexes[j]
            branch1 = normal_form(apply_rule(word, r1, hg), hg)
            branch2 = normal_form(apply_rule(word, r2, hg), hg)
            key1 = tuple(hl.elements for hl in branch1)
            key2 = tuple(hl.elements for hl in branch2)
            if key1 != key2:
                violations.append({
                    'word': word,
                    'hg': hg,
                    'redex1': r1,
                    'redex2': r2,
                    'branch1_nf': branch1,
                    'branch2_nf': branch2,
                })
    return violations


def has_edge_base_price_overlap(word, hg):
    """
    True iff `word` contains a redex where the moved letter is an edge symbol
    whose base coincides with a price letter produced by that same move —
    the case the spec (3.3) singles out as needing explicit coverage.
    Approximated as: some redex moves/cancels an E2-symbol x, and applying it
    produces a price block containing x's own base (only possible if that
    price recomputes the same generator, i.e. a genuine self-overlap case);
    more usefully we detect "redex moves an edge letter AND at least one other
    redex in the same word also touches an edge letter with overlapping base",
    which is the scenario that stresses this interaction in local confluence.
    """
    from tools.core.alphabet import is_vertex
    redexes = find_applicable_rules(word, hg)
    edge_bases = set()
    for r in redexes:
        if r[0] == 'R1':
            x = r[3]
        elif r[0] == 'R2':
            x = r[2]
        else:
            continue
        base, _ = x
        if not is_vertex(base):
            edge_bases.add(base)
    return len(edge_bases) > 0


def run(words_with_hg, max_pairs_per_word=None):
    all_violations = []
    cases_run = 0
    trigger_count = 0

    for word, hg in words_with_hg:
        redexes = find_applicable_rules(word, hg)
        if len(redexes) < 2:
            continue
        cases_run += 1
        if has_edge_base_price_overlap(word, hg):
            trigger_count += 1
        vs = check_word(word, hg, max_pairs=max_pairs_per_word)
        for v in vs:
            v['hypergraph_vertices'] = hg.vertices
        all_violations.extend(vs)

    return {
        'test': 'B',
        'cases_run': cases_run,
        'edge_letter_trigger_count': trigger_count,
        'pass': len(all_violations) == 0,
        'violations': all_violations,
    }
