"""
TEST E (spec Part 3.6) — the wall lemma.

A block u_m is a wall for v iff v not in |u_m| and v is not addable into u_m.

  W1: if u_m contains any letter with base e_{a,v} for some a, then u_m is
      NOT a wall for v.
  W2: a letter with base e_{a,v} is never addable into a wall for v.

Both are theorems (no confluence dependency — these are pointwise addability
facts about individual blocks), so a failure means is_addable/extended
hyperedge code is wrong.
"""

from tools.core.hyperletter import is_addable


def _edge_bases_touching(v, hg):
    """All edge symbols e_{a,v} (any a != v) that exist in hg.E2."""
    return frozenset(edge for edge in hg.E2 if v in edge)


def is_wall_for(block, v, hg):
    if v in block.support:
        return False
    return not is_addable((v, +1), block, hg)


def check_block(block, hg):
    """
    For every vertex v in hg, check W1 and W2 against this single block.
    Returns list of violation dicts (empty if none).
    """
    violations = []
    for v in hg.vertices:
        wall = is_wall_for(block, v, hg)
        touching_edges = _edge_bases_touching(v, hg)

        # W1: if block contains e_{a,v} for some a, block is not a wall for v.
        contains_touching_edge = any(edge in block.support for edge in touching_edges)
        if contains_touching_edge and wall:
            violations.append({
                'law': 'W1', 'block': block, 'v': v, 'hg': hg,
            })

        # W2: a letter with base e_{a,v} is never addable into a wall for v.
        if wall:
            for edge in touching_edges:
                if is_addable((edge, +1), block, hg):
                    violations.append({
                        'law': 'W2', 'block': block, 'v': v, 'edge': edge, 'hg': hg,
                    })

    return violations


def run(blocks_with_hg):
    """blocks_with_hg: iterable of (HyperLetter, hg) pairs (e.g. every block
    from every generated normal form)."""
    cases_run = 0
    violations = []
    for block, hg in blocks_with_hg:
        cases_run += 1
        violations.extend(check_block(block, hg))

    return {
        'test': 'E',
        'cases_run': cases_run,
        'pass': len(violations) == 0,
        'violations': violations[:10],
        'total_violations': len(violations),
    }
