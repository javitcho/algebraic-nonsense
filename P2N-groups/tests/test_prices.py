"""
Tests for HyperLetter, is_addable, left_price, right_price, and interpret.

Key test cases (ground truth from the paper):
  HEISENBERG: left_price(e_xy^{+1}, {x^{-1}}) = [∅]
  HEISENBERG: right_price(x^{+1}, {y^{-1}})   = [e_xy]  (Relator 4, Step 1)
  TRIANGLE  : right_price(y^{+1}, {x, z^{-1}, e_xz}) = [e_yz]  (Section 4 example)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from tools.core.hyperletter import (
    HyperLetter, EMPTY_LETTER, is_addable, left_price, right_price, interpret, sigma
)
from tools.core.alphabet import total_order_key
from tests.fixtures import HEISENBERG, PATH, TRIANGLE

e_xy = frozenset({'x', 'y'})
e_xz = frozenset({'x', 'z'})
e_yz = frozenset({'y', 'z'})


# ---------------------------------------------------------------------------
# HyperLetter basics
# ---------------------------------------------------------------------------

class TestHyperLetter:
    def test_empty_letter(self):
        assert EMPTY_LETTER.elements == frozenset()
        assert EMPTY_LETTER.support == frozenset()

    def test_support(self):
        hl = HyperLetter(frozenset({('x', +1), ('y', -1)}))
        assert hl.support == {'x', 'y'}

    def test_equality_is_by_elements(self):
        a = HyperLetter(frozenset({('x', +1)}))
        b = HyperLetter(frozenset({('x', +1)}))
        assert a == b


# ---------------------------------------------------------------------------
# is_addable
# ---------------------------------------------------------------------------

class TestIsAddable:
    def test_vertex_addable_into_empty(self):
        assert is_addable(('x', +1), EMPTY_LETTER, HEISENBERG)

    def test_vertex_not_addable_if_already_in_support(self):
        u = HyperLetter(frozenset({('x', +1)}))
        assert not is_addable(('x', -1), u, HEISENBERG)  # x already in support

    def test_vertex_addable_into_singleton_sharing_edge(self):
        u = HyperLetter(frozenset({('x', +1)}))
        assert is_addable(('y', +1), u, HEISENBERG)

    def test_vertex_not_addable_if_no_shared_edge(self):
        # x and z don't share an edge in PATH
        u = HyperLetter(frozenset({('x', +1)}))
        assert not is_addable(('z', +1), u, PATH)

    def test_edge_symbol_addable_with_vertices_in_same_edge(self):
        # e_xy is addable into [x] in HEISENBERG
        u = HyperLetter(frozenset({('x', +1)}))
        assert is_addable((e_xy, +1), u, HEISENBERG)

    def test_element_not_addable_if_no_maximal_edge_covers(self):
        # In PATH, z is not addable into [x] since {x,z} is not an edge
        u = HyperLetter(frozenset({('x', +1)}))
        assert not is_addable(('z', +1), u, PATH)


# ---------------------------------------------------------------------------
# left_price (paper Definition 4.4)
# ---------------------------------------------------------------------------

class TestLeftPrice:
    def test_left_price_empty_letter_is_empty(self):
        # l_{x^1}([∅]) = [∅]  (no elements less than x)
        result = left_price(('x', +1), EMPTY_LETTER, HEISENBERG)
        assert result == EMPTY_LETTER

    def test_left_price_exy_into_x_inv_is_empty(self):
        """
        Key observation from paper:
        l_{e_xy^{+1}}([x^{-1}]) = [∅]
        because c(x, e_xy) = None (e_xy ∈ E2)
        """
        u = HyperLetter(frozenset({('x', -1)}))
        b = (e_xy, +1)
        result = left_price(b, u, HEISENBERG)
        assert result == EMPTY_LETTER

    def test_left_price_y_into_x_is_empty(self):
        # x < y, so no element in [x^{+1}] is less than y... wait, x < y
        # l_{y^{+1}}([x^{+1}]) = [{c(x,y)^{+1·+1}}] = [{e_xy}]
        u = HyperLetter(frozenset({('x', +1)}))
        b = ('y', +1)
        result = left_price(b, u, HEISENBERG)
        assert result == HyperLetter(frozenset({(e_xy, +1)}))

    def test_left_price_y_into_x_inv_negates(self):
        # l_{y^{+1}}([x^{-1}]) = [{c(x,y)^{+1·-1}}] = [{e_xy^{-1}}]
        u = HyperLetter(frozenset({('x', -1)}))
        b = ('y', +1)
        result = left_price(b, u, HEISENBERG)
        assert result == HyperLetter(frozenset({(e_xy, -1)}))

    def test_left_price_no_elements_greater_contribute(self):
        # l_{x^{+1}}([y^{+1}]) = [∅] since y > x, nothing less than x in {y}
        u = HyperLetter(frozenset({('y', +1)}))
        b = ('x', +1)
        result = left_price(b, u, HEISENBERG)
        assert result == EMPTY_LETTER


# ---------------------------------------------------------------------------
# right_price (paper Definition 4.4)
# ---------------------------------------------------------------------------

class TestRightPrice:
    def test_right_price_empty_letter_is_empty(self):
        result = right_price(('x', +1), EMPTY_LETTER, HEISENBERG)
        assert result == EMPTY_LETTER

    def test_right_price_x_into_y_inv_gives_exy(self):
        """
        From paper Relator 4, Step 1:
        r_{x^{+1}}([y^{-1}]) = [e_xy]

        Derivation:
          y > x; c(y, x) = e_xy^{-1}  (since y > x, c(y,x) = c(x,y)^{-1} = e_xy^{-1})
          signed result: c(y,x)^{η·δ} = (e_xy^{-1})^{+1·(-1)} = e_xy^{+1}
        """
        u = HyperLetter(frozenset({('y', -1)}))
        b = ('x', +1)
        result = right_price(b, u, HEISENBERG)
        assert result == HyperLetter(frozenset({(e_xy, +1)}))

    def test_right_price_no_elements_less_contribute(self):
        # r_{y^{+1}}([x^{+1}]) = [∅] since x < y, nothing greater than y in {x}
        u = HyperLetter(frozenset({('x', +1)}))
        b = ('y', +1)
        result = right_price(b, u, HEISENBERG)
        assert result == EMPTY_LETTER

    def test_right_price_triangle_example(self):
        """
        Section 4 example from the paper:
        u = {x^{+1}, z^{-1}, e_xz^{+1}},  b = y^{+1}
        right_price = [e_yz]

        Derivation (x < y < z, e_xy < e_xz < e_yz):
          Elements > y in unsigned order: z^{-1}, e_xz^{+1}
          For z^{-1}: c(z, y) = c(y,z)^{-1} = e_yz^{-1}
            signed: (e_yz^{-1})^{+1·(-1)} = e_yz^{+1}
          For e_xz^{+1}: c(e_xz, y) = None (e_xz ∈ E2) → skip
        Result: [e_yz]
        """
        u = HyperLetter(frozenset({('x', +1), ('z', -1), (e_xz, +1)}))
        b = ('y', +1)
        result = right_price(b, u, TRIANGLE)
        assert result == HyperLetter(frozenset({(e_yz, +1)}))

    def test_right_price_exy_into_x_inv_is_empty(self):
        # r_{e_xy^{+1}}([x^{-1}]) = [∅]
        # x < e_xy, so x is NOT greater than e_xy → nothing contributes
        u = HyperLetter(frozenset({('x', -1)}))
        b = (e_xy, +1)
        result = right_price(b, u, HEISENBERG)
        assert result == EMPTY_LETTER


# ---------------------------------------------------------------------------
# interpret (F on a single hyper-letter)
# ---------------------------------------------------------------------------

class TestInterpret:
    def test_interpret_empty_is_empty_tuple(self):
        assert interpret(EMPTY_LETTER, HEISENBERG.vertices) == ()

    def test_interpret_singleton(self):
        hl = HyperLetter(frozenset({('x', +1)}))
        assert interpret(hl, HEISENBERG.vertices) == (('x', +1),)

    def test_interpret_order_is_total_order(self):
        # {y^{-1}, x^{+1}, e_xy^{+1}} should sort to (x^{+1}, y^{-1}, e_xy^{+1})
        hl = HyperLetter(frozenset({('y', -1), ('x', +1), (e_xy, +1)}))
        result = interpret(hl, HEISENBERG.vertices)
        assert result == (('x', +1), ('y', -1), (e_xy, +1))

    def test_interpret_with_inverses_sorted_correctly(self):
        # x⁻¹ < x < y⁻¹ < y < e_xy⁻¹ < e_xy
        hl = HyperLetter(frozenset({('x', -1), ('y', +1)}))
        result = interpret(hl, HEISENBERG.vertices)
        assert result == (('x', -1), ('y', +1))


# ---------------------------------------------------------------------------
# sigma (lifting)
# ---------------------------------------------------------------------------

class TestSigma:
    def test_sigma_produces_singletons(self):
        word = sigma([('x', -1), ('y', +1)], HEISENBERG)
        assert len(word) == 2
        assert word[0] == HyperLetter(frozenset({('x', -1)}))
        assert word[1] == HyperLetter(frozenset({('y', +1)}))

    def test_sigma_empty_word(self):
        assert sigma([], HEISENBERG) == []
