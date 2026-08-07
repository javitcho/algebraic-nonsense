"""
Master experiment runner (spec Part 3, reported per Part 4).

Usage:
    python3 -m tools.experiments.run_all
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import time

from tools.core.hypergraph_enum import hypergraphs_for, sampled_hypergraphs_for
from tools.core.word_gen import random_normal_forms, random_word
from tools.core.hyperletter import sigma, interpret
from tools.core.rewriter import find_applicable_rules, apply_rule, normal_form
from tools.core.free_nilpotent import mu_check

from tools.experiments import test_a_termination as A
from tools.experiments import test_b_confluence as B
from tools.experiments import test_c_centre as C
from tools.experiments import test_d_clean_append as D
from tools.experiments import test_e_wall as E


def fmt_hl(hl, vertices):
    if not hl.elements:
        return '[?]'
    parts = []
    for base, exp in interpret(hl, vertices):
        if isinstance(base, str):
            s = base
        else:
            v1, v2 = sorted(base, key=lambda v: vertices.index(v))
            s = f'e{v1}{v2}'
        parts.append(s + ('^-1' if exp == -1 else ''))
    return '[' + ' '.join(parts) + ']'


def fmt_word(word, vertices):
    return ' '.join(fmt_hl(hl, vertices) for hl in word)


def walk_all_steps(hgs, n_per_hg, max_length, seed):
    """Yield every intermediate word state (using leftmost strategy) for
    random words over each hg, for Test A (every redex at every step)."""
    for hg in hgs:
        for flat, lifted, _ in random_normal_forms(hg, n_per_hg, max_length=max_length, seed=seed):
            w = list(lifted)
            yield w, hg
            for _ in range(300):
                rules = find_applicable_rules(w, hg)
                if not rules:
                    break
                w = apply_rule(w, rules[0], hg)
                yield w, hg


def run_test_a(hgs, n_per_hg, max_length, seed):
    t0 = time.time()
    result = A.run(walk_all_steps(hgs, n_per_hg, max_length, seed))
    result['elapsed_s'] = time.time() - t0
    return result


def run_test_b(hgs, n_per_hg, max_length, seed, max_pairs_per_word):
    t0 = time.time()
    words = list(walk_all_steps(hgs, n_per_hg, max_length, seed))
    result = B.run(words, max_pairs_per_word=max_pairs_per_word)
    result['elapsed_s'] = time.time() - t0
    return result


def run_test_c(hgs, n_per_hg, max_length, seed):
    def gen():
        for hg in hgs:
            for _, _, nf in random_normal_forms(hg, n_per_hg, max_length=max_length, seed=seed):
                yield nf, hg
    t0 = time.time()
    result = C.run(gen())
    result['elapsed_s'] = time.time() - t0
    return result


def run_test_d(hgs, n_per_hg, max_length, seed):
    def gen():
        for hg in hgs:
            for _, _, nf in random_normal_forms(hg, n_per_hg, max_length=max_length, seed=seed):
                yield nf, hg
    t0 = time.time()
    result = D.run(gen())
    result['elapsed_s'] = time.time() - t0
    return result


def run_test_e(hgs, n_per_hg, max_length, seed):
    def gen():
        for hg in hgs:
            for _, _, nf in random_normal_forms(hg, n_per_hg, max_length=max_length, seed=seed):
                for hl in nf:
                    yield hl, hg
    t0 = time.time()
    result = E.run(gen())
    result['elapsed_s'] = time.time() - t0
    return result


def run_mu_check_sanity(hgs, n_per_hg, max_length, seed):
    """Part 2.3: independent group-element check on every generated word."""
    t0 = time.time()
    failures = []
    cases = 0
    for hg in hgs:
        for flat, lifted, nf in random_normal_forms(hg, n_per_hg, max_length=max_length, seed=seed):
            cases += 1
            if not mu_check(lifted, nf, hg):
                failures.append((hg.vertices, flat, nf))
    return {
        'test': 'mu_check',
        'cases_run': cases,
        'pass': len(failures) == 0,
        'failures': failures[:10],
        'elapsed_s': time.time() - t0,
    }


def print_report(results, n4_centre_table):
    print('=' * 78)
    print('P2N REWRITING SYSTEM — EXPERIMENT REPORT')
    print('=' * 78)

    for r in results:
        name = r['test']
        print(f"\n--- Test {name} ---")
        for k, v in r.items():
            if k in ('test', 'violations', 'failures', 'counterexamples', 'centre_table'):
                continue
            print(f"  {k}: {v}")
        for key in ('violations', 'failures', 'counterexamples'):
            if key in r and r[key]:
                print(f"  first {key} (up to 10):")
                for item in r[key][:10]:
                    print(f"    {item}")

    print(f"\n--- Test C: centre table (n=4 sweep) ---")
    print(f"  {'vertices':<20} {'predicted':<30} {'found':<30} {'match'}")
    for row in n4_centre_table:
        pred = sorted(tuple(sorted(e)) for e in row['predicted_centre_edges'])
        found = sorted(tuple(sorted(e)) for e in row['found_in_central_elements'])
        print(f"  {str(row['hg_vertices']):<20} {str(pred):<30} {str(found):<30} {row['matches_prediction']}")


if __name__ == '__main__':
    SEED = 12345

    print('Enumerating hypergraphs...')
    hgs3 = hypergraphs_for(3)
    hgs4 = hypergraphs_for(4)
    hgs5_sample = sampled_hypergraphs_for(5, 200, seed=SEED)
    print(f'n=3: {len(hgs3)}, n=4: {len(hgs4)}, n=5 sample: {len(hgs5_sample)}')

    all_hgs = hgs3 + hgs4 + hgs5_sample

    print('Running mu_check sanity...')
    mu_result = run_mu_check_sanity(all_hgs, 60, 16, SEED)

    print('Running Test A...')
    a_result = run_test_a(all_hgs, 60, 14, SEED)

    print('Running Test B...')
    b_result = run_test_b(hgs3 + hgs4, 30, 12, SEED, max_pairs_per_word=6)

    print('Running Test C...')
    c_result = run_test_c(all_hgs, 60, 14, SEED)

    print('Running Test D...')
    d_result = run_test_d(all_hgs, 60, 14, SEED)

    print('Running Test E...')
    e_result = run_test_e(all_hgs, 60, 14, SEED)

    print('Running Test C n=4 centre table...')
    c4_result = run_test_c(hgs4, 60, 14, SEED)

    print_report(
        [mu_result, a_result, b_result, c_result, d_result, e_result],
        c4_result['centre_table'],
    )
