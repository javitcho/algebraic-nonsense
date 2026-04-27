"""
Shared test hypergraphs. Every other test imports from here.

Signed-element convention throughout this codebase:
  (base, exponent)  where base ∈ A = V ∪ E2
  - vertex base  : plain str, e.g. 'x'
  - edge base    : frozenset of exactly 2 vertex names, e.g. frozenset({'x','y'})
  exponent ∈ {+1, -1}

Ground-truth facts used as acceptance tests:
  HEISENBERG : σ(x⁻¹y⁻¹xy) normalises to [e_xy]
  PATH       : σ(xz) is already in normal form  →  [[x],[z]]
  TRIANGLE   : [[x,y],z] = 1  →  σ([e_xy,z]) normalises to []
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.core.hypergraph import Hypergraph


# ---------------------------------------------------------------------------
# HEISENBERG  χ = ({x,y}, {{x,y}})
# Dense closure of {{x,y}}: {∅, {x}, {y}, {x,y}}
# A = {x, y, e_xy};  maximal edge = {x,y}
# Ground truth: x⁻¹y⁻¹xy  →*  e_xy
# ---------------------------------------------------------------------------
HEISENBERG = Hypergraph(
    vertices=('x', 'y'),
    edges=frozenset({
        frozenset(),
        frozenset({'x'}),
        frozenset({'y'}),
        frozenset({'x', 'y'}),
    }),
)

# ---------------------------------------------------------------------------
# PATH  χ = ({x,y,z}, {{x,y},{y,z}})  —  {x,z} is NOT an edge
# Dense closure: {∅,{x},{y},{z},{x,y},{y,z}}  (no {x,z} or {x,y,z})
# E2 = {{x,y},{y,z}};  maximal edges = {{x,y},{y,z}}
# Ground truth: [x][z] is already in normal form
# ---------------------------------------------------------------------------
PATH = Hypergraph(
    vertices=('x', 'y', 'z'),
    edges=frozenset({
        frozenset(),
        frozenset({'x'}),
        frozenset({'y'}),
        frozenset({'z'}),
        frozenset({'x', 'y'}),
        frozenset({'y', 'z'}),
    }),
)

# ---------------------------------------------------------------------------
# TRIANGLE  χ = ({x,y,z}, {{x,y,z}})  —  all pairs are edges
# Dense closure: all non-empty subsets of {x,y,z}, plus ∅
# E2 = {{x,y},{x,z},{y,z}};  maximal edge = {x,y,z}
# Ground truth: [[x,y],z] = 1
# ---------------------------------------------------------------------------
TRIANGLE = Hypergraph(
    vertices=('x', 'y', 'z'),
    edges=frozenset({
        frozenset(),
        frozenset({'x'}),
        frozenset({'y'}),
        frozenset({'z'}),
        frozenset({'x', 'y'}),
        frozenset({'x', 'z'}),
        frozenset({'y', 'z'}),
        frozenset({'x', 'y', 'z'}),
    }),
)
