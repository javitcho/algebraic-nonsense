"""
TEST D (spec Part 3.5) — clean append. For every normal form g^ containing
at least one vertex letter:

  v_j = the LARGEST vertex occurring as a vertex letter in g^
  b   = index of the LAST block containing a v_j-letter
  eps = the sign of that letter
  N   = number of v_j-letters in g^
  h   = NF(g^ . [{v_j^eps}])
  N'  = number of v_j-letters in h

Assert N' == N + 1.

Same confluence caveat as Test C: normal_form is computed with a fixed
strategy ('leftmost') throughout so a given input always maps to the same
value within this test, but is not guaranteed unique across strategies on
hypergraphs where local confluence fails (see Test B).
"""

from tools.core.alphabet import is_vertex
from tools.core.hyperletter import HyperLetter
from tools.core.rewriter import normal_form

STRATEGY = 'leftmost'


def _vertex_letters(word, hg):
    """List of (block_index, base, exp) for every vertex letter in word, left to right."""
    out = []
    for i, hl in enumerate(word):
        for base, exp in hl.elements:
            if is_vertex(base):
                out.append((i, base, exp))
    return out


def analyze(g_hat, hg):
    """
    Returns None if g_hat has no vertex letter (not applicable), else a dict
    with the computed v_j, b, eps, N, N', pass/fail, and the auto-clean /
    trigger filter flags (spec 3.5).
    """
    v_letters = _vertex_letters(g_hat, hg)
    if not v_letters:
        return None

    vertices = hg.vertices
    v_j = max((base for _, base, _ in v_letters), key=lambda v: vertices.index(v))

    j_occurrences = [(i, exp) for i, base, exp in v_letters if base == v_j]
    b = max(i for i, _ in j_occurrences)
    eps = next(exp for i, exp in j_occurrences if i == b)
    N = len(j_occurrences)

    auto_clean = b >= len(g_hat) - 1

    trigger = False
    if not auto_clean:
        for i in range(b + 2, len(g_hat)):
            block = g_hat[i]
            for a_base, a_eps in block.elements:
                if not is_vertex(a_base):
                    continue
                if vertices.index(a_base) >= vertices.index(v_j):
                    continue
                # c(a, v_j): a < v_j (vertex order) -> e_{a,v_j}, +1
                if a_base not in hg.vertices:
                    continue
                edge = frozenset({a_base, v_j})
                if edge not in hg.E2:
                    continue
                needed_edge_exp = -eps * a_eps
                if (edge, needed_edge_exp) in block.elements:
                    trigger = True
                    break
            if trigger:
                break

    vj_letter = HyperLetter(frozenset({(v_j, eps)}))
    h = normal_form(list(g_hat) + [vj_letter], hg, strategy=STRATEGY)
    N_prime = sum(1 for hl in h for base, _ in hl.elements if base == v_j)

    return {
        'g_hat': g_hat,
        'hg': hg,
        'v_j': v_j,
        'b': b,
        'eps': eps,
        'N': N,
        'N_prime': N_prime,
        'auto_clean': auto_clean,
        'trigger': trigger,
        'passed': (N_prime == N + 1),
        'h': h,
    }


def run(normal_forms_with_hg):
    cases_run = 0
    trigger_count = 0
    auto_clean_count = 0
    failures = []

    for word, hg in normal_forms_with_hg:
        result = analyze(word, hg)
        if result is None:
            continue
        cases_run += 1
        if result['auto_clean']:
            auto_clean_count += 1
            if not result['passed']:
                failures.append(result)  # spec: auto-clean must pass trivially
            continue
        if result['trigger']:
            trigger_count += 1
        if not result['passed']:
            failures.append(result)

    return {
        'test': 'D',
        'cases_run': cases_run,
        'auto_clean_count': auto_clean_count,
        'trigger_count': trigger_count,
        'uninformative': trigger_count == 0,
        'pass': len(failures) == 0,
        'failures': failures[:10],
        'total_failures': len(failures),
    }
