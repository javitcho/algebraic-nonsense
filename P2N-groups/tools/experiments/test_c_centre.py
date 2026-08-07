"""
TEST C (spec Part 3.4) — the centre test. The claim under test: every central
element's normal form contains no vertex letter (it's a product of edge
generators only).

Caveat (see Test B): local confluence was found to fail on some hypergraphs,
so normal_form(w) is not always well-defined as a function of w alone — it
can depend on rewrite order. We fix strategy='leftmost' for every call here
(including both sides of the is_central comparison) so a single word always
maps to the same computed value across this test, but a is_central verdict
computed this way is not guaranteed to match what a different strategy would
report on a hypergraph where confluence fails. Results should be read with
that caveat; it does not by itself change the interpretation of a vertex
letter appearing in a "central" g's normal form under a fixed strategy.
"""

from tools.core.alphabet import is_vertex
from tools.core.hyperletter import sigma, HyperLetter
from tools.core.rewriter import normal_form

STRATEGY = 'leftmost'


def _key(word):
    return tuple(hl.elements for hl in word)


def is_central(g_hat, hg):
    """
    is_central(g^) := for all v_c in V: NF(g^ . [{v_c}]) == NF([{v_c}] . g^)
    """
    for vc in hg.vertices:
        vc_letter = HyperLetter(frozenset({(vc, +1)}))
        right = normal_form(list(g_hat) + [vc_letter], hg, strategy=STRATEGY)
        left = normal_form([vc_letter] + list(g_hat), hg, strategy=STRATEGY)
        if _key(right) != _key(left):
            return False
    return True


def has_vertex_letter(word):
    return any(is_vertex(base) for hl in word for base, _ in hl.elements)


def fully_extended_edges(hg):
    """
    {v_p,v_q} in E2 is fully-extended iff {v_p,v_q,v_c} in E3 for every
    v_c in V \\ {v_p,v_q} (spec 3.4). Predicted centre generators.
    """
    result = set()
    for edge in hg.E2:
        v_p, v_q = tuple(edge)
        others = [v for v in hg.vertices if v not in edge]
        if all(frozenset({v_p, v_q, vc}) in hg.edges for vc in others):
            result.add(edge)
    return frozenset(result)


def run(normal_forms_with_hg):
    """
    normal_forms_with_hg: iterable of (word, hg) pairs, each word ALREADY a
    normal form (callers should pass generated normal forms, e.g. from
    exhaustive_normal_forms or normal_form(random_word...)).

    Returns per-case central/vertex-letter records plus a counterexample flag,
    and per-hg predicted-vs-found centre generator comparison.
    """
    cases_run = 0
    central_records = []
    counterexamples = []
    centre_by_hg = {}  # id(hg) -> (hg, set of edge symbols seen alone in a central word)

    for word, hg in normal_forms_with_hg:
        cases_run += 1
        central = is_central(word, hg)
        contains_vertex = has_vertex_letter(word)
        record = {
            'word': word,
            'hg': hg,
            'central': central,
            'contains_vertex_letter': contains_vertex,
        }
        if central:
            central_records.append(record)
            if contains_vertex:
                counterexamples.append(record)
            key = id(hg)
            if key not in centre_by_hg:
                centre_by_hg[key] = (hg, set())
            edge_bases = {base for hl in word for base, _ in hl.elements if not is_vertex(base)}
            centre_by_hg[key][1].update(edge_bases)

    centre_table = []
    for hg, found_edges in centre_by_hg.values():
        predicted = fully_extended_edges(hg)
        centre_table.append({
            'hg_vertices': hg.vertices,
            'predicted_centre_edges': predicted,
            'found_in_central_elements': frozenset(found_edges),
            'matches_prediction': frozenset(found_edges) <= predicted,
        })

    return {
        'test': 'C',
        'cases_run': cases_run,
        'central_count': len(central_records),
        'counterexample_count': len(counterexamples),
        'counterexamples': counterexamples,
        'centre_table': centre_table,
    }
