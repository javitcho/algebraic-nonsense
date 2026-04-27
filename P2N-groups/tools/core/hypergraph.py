from dataclasses import dataclass


@dataclass(frozen=True)
class Hypergraph:
    """
    Dense hypergraph χ = (V, E) where E is downward-closed.

    vertices: ordered tuple of vertex names (strings) — fixes the total order on V
    edges: frozenset of frozensets of vertex names (all hyperedges, including empty)
    """
    vertices: tuple
    edges: frozenset

    def __post_init__(self):
        object.__setattr__(self, 'edges', frozenset(frozenset(e) for e in self.edges))

    @property
    def E2(self):
        """All 2-element hyperedges."""
        return frozenset(e for e in self.edges if len(e) == 2)

    @property
    def maximal_edges(self):
        """Edges not strictly contained in any other edge."""
        return frozenset(
            e for e in self.edges
            if not any(e < e2 for e2 in self.edges)
        )

    def extended_hyperedge(self, e):
        """
        Ē = e ∪ {frozenset({vi,vj}) | {vi,vj} ∈ E2, vi ∈ e, vj ∈ e}
        The set of symbols (vertices + edge symbols) that can interact within e.
        """
        e = frozenset(e)
        edge_symbols = frozenset(
            edge for edge in self.E2
            if edge <= e
        )
        return e | edge_symbols
