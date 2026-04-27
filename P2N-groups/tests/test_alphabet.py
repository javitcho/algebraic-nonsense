"""Tests for tools/core/alphabet.py."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.core.alphabet import total_order_key, c_function, is_vertex, is_edge_symbol
from tests.fixtures import HEISENBERG, PATH, TRIANGLE

e_xy = frozenset({'x', 'y'})
e_xz = frozenset({'x', 'z'})
e_yz = frozenset({'y', 'z'})


class TestTotalOrderKey:
    """Verify the order v1⁻¹ < v1 < v2⁻¹ < v2 < ... < eij⁻¹ < eij < ..."""

    def test_vertex_inverse_before_vertex(self):
        v = HEISENBERG.vertices
        assert total_order_key(('x', -1), v) < total_order_key(('x', +1), v)
        assert total_order_key(('y', -1), v) < total_order_key(('y', +1), v)

    def test_vertex_order_follows_vertex_list(self):
        v = HEISENBERG.vertices   # ('x', 'y')
        # x⁻¹ < x < y⁻¹ < y
        keys = [total_order_key(se, v) for se in [
            ('x', -1), ('x', +1), ('y', -1), ('y', +1)
        ]]
        assert keys == sorted(keys)

    def test_vertices_before_edge_symbols(self):
        v = HEISENBERG.vertices
        assert total_order_key(('y', +1), v) < total_order_key((e_xy, -1), v)

    def test_edge_inverse_before_edge(self):
        v = HEISENBERG.vertices
        assert total_order_key((e_xy, -1), v) < total_order_key((e_xy, +1), v)

    def test_three_vertex_order(self):
        v = TRIANGLE.vertices   # ('x', 'y', 'z')
        # Expected: x⁻¹ < x < y⁻¹ < y < z⁻¹ < z < e_xy⁻¹ < e_xy < e_xz⁻¹ < e_xz < e_yz⁻¹ < e_yz
        signed_elements = [
            ('x', -1), ('x', +1),
            ('y', -1), ('y', +1),
            ('z', -1), ('z', +1),
            (e_xy, -1), (e_xy, +1),
            (e_xz, -1), (e_xz, +1),
            (e_yz, -1), (e_yz, +1),
        ]
        keys = [total_order_key(se, v) for se in signed_elements]
        assert keys == sorted(keys), f"Order mismatch: {keys}"

    def test_edge_ordering_respects_vertex_indices(self):
        v = TRIANGLE.vertices   # ('x', 'y', 'z')
        # e_xy < e_xz < e_yz
        assert total_order_key((e_xy, +1), v) < total_order_key((e_xz, +1), v)
        assert total_order_key((e_xz, +1), v) < total_order_key((e_yz, +1), v)


class TestCFunction:

    def test_c_two_vertices_x_before_y(self):
        result = c_function('x', 'y', HEISENBERG)
        assert result == (e_xy, +1), f"Expected e_xy^+1, got {result}"

    def test_c_two_vertices_y_before_x_inverts(self):
        result = c_function('y', 'x', HEISENBERG)
        assert result == (e_xy, -1), f"Expected e_xy^-1, got {result}"

    def test_c_vertex_and_edge_symbol_is_none(self):
        assert c_function(e_xy, 'x', HEISENBERG) is None
        assert c_function('x', e_xy, HEISENBERG) is None

    def test_c_two_edge_symbols_is_none(self):
        assert c_function(e_xy, e_xy, HEISENBERG) is None

    def test_c_vertices_not_sharing_edge_is_none(self):
        # In PATH, x and z do not share an edge
        assert c_function('x', 'z', PATH) is None

    def test_c_triangle_all_pairs(self):
        # In TRIANGLE, all pairs of vertices share an edge
        assert c_function('x', 'y', TRIANGLE) == (e_xy, +1)
        assert c_function('x', 'z', TRIANGLE) == (e_xz, +1)
        assert c_function('y', 'z', TRIANGLE) == (e_yz, +1)
        # Reversed
        assert c_function('y', 'x', TRIANGLE) == (e_xy, -1)
        assert c_function('z', 'x', TRIANGLE) == (e_xz, -1)
        assert c_function('z', 'y', TRIANGLE) == (e_yz, -1)

    def test_c_same_vertex_is_none(self):
        assert c_function('x', 'x', HEISENBERG) is None
