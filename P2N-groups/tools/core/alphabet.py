"""
Augmented alphabet A = V ∪ E2 and signed alphabet A±.

Representations
---------------
base element (unsigned, ∈ A):
  vertex   → plain str, e.g. 'x'
  E2 symbol → frozenset of exactly 2 vertex names, e.g. frozenset({'x','y'})

signed element (∈ A±):
  (base, exponent)  where exponent ∈ {+1, -1}

Total order on A± (from the paper, must be consistent everywhere):
  v1⁻¹ < v1 < v2⁻¹ < v2 < ... < vn⁻¹ < vn < e12⁻¹ < e12 < e13⁻¹ < e13 < ...
"""


def is_vertex(base):
    return isinstance(base, str)


def is_edge_symbol(base):
    return isinstance(base, frozenset)


def total_order_key(signed_element, vertices):
    """
    Return a sortable key for a signed element consistent with the paper's
    total order on A±.

    vertices: ordered tuple of vertex names (from Hypergraph.vertices)
    """
    base, exp = signed_element
    sign_key = 0 if exp == -1 else 1  # a⁻¹ < a

    if is_vertex(base):
        return (0, vertices.index(base), sign_key)
    else:
        # edge symbol: frozenset of two vertex names
        v1, v2 = sorted(base, key=lambda v: vertices.index(v))
        return (1, vertices.index(v1), vertices.index(v2), sign_key)


def c_function(a, b, hypergraph):
    """
    The commutator function c: A × A → A± ∪ {None}.

    a, b: base elements (unsigned) from A.
    Returns a signed element or None ('-' in the paper).

    Rules (paper Definition 4.3):
      c(a,b) = e_{ab}^{+1}  if a,b ∈ V and a < b and {a,b} ∈ E2
      c(a,b) = e_{ab}^{-1}  if a,b ∈ V and a > b and {a,b} ∈ E2  [= c(b,a)^{-1}]
      c(a,b) = None         if either a or b is in E2
      c(a,b) = None         if a == b or {a,b} ∉ E2
    """
    if not is_vertex(a) or not is_vertex(b):
        return None

    if a == b:
        return None

    edge = frozenset({a, b})
    if edge not in hypergraph.E2:
        return None

    # Both are distinct vertices sharing an edge
    a_idx = hypergraph.vertices.index(a)
    b_idx = hypergraph.vertices.index(b)

    if a_idx < b_idx:
        # c(a, b) = e_{ab}^{+1}
        return (edge, +1)
    else:
        # c(a, b) = c(b, a)^{-1} = e_{ba}^{-1} = e_{ab}^{-1}
        return (edge, -1)
