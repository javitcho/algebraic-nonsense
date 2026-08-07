"""
Tests for the rewriting rules R1, R2, R3 and normal_form.

Invariant: every rewriting step preserves the group element, verified
concretely in the Heisenberg matrix group.

Heisenberg matrix representations:
  x   ↦ [[1,1,0],[0,1,0],[0,0,1]]
  y   ↦ [[1,0,0],[0,1,1],[0,0,1]]
  e_xy↦ [[1,0,1],[0,1,0],[0,0,1]]

Ground-truth reductions:
  HEISENBERG: σ(x⁻¹y⁻¹xy) →* [e_xy]
  HEISENBERG: σ(e_xy⁻¹ x⁻¹ e_xy x) →* []         (Relator 1)
  PATH      : σ(xz) →* [[x],[z]]                  (already normal)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from tools.core.hyperletter import (
    HyperLetter, EMPTY_LETTER, interpret, sigma
)
from tools.core.rewriter import (
    apply_R1, apply_R2, apply_R3, find_applicable_rules, normal_form
)
from tests.fixtures import HEISENBERG, PATH, TRIANGLE

e_xy = frozenset({'x', 'y'})
e_xz = frozenset({'x', 'z'})
e_yz = frozenset({'y', 'z'})

# ---------------------------------------------------------------------------
# Heisenberg matrix group — invariant helper
# ---------------------------------------------------------------------------

_BASE_MATRICES = {
    'x':  np.array([[1, 1, 0], [0, 1, 0], [0, 0, 1]], dtype=int),
    'y':  np.array([[1, 0, 0], [0, 1, 1], [0, 0, 1]], dtype=int),
    e_xy: np.array([[1, 0, 1], [0, 1, 0], [0, 0, 1]], dtype=int),
}

_BASE_MATRICES_INV = {
    'x':  np.array([[1, -1, 0], [0, 1,  0], [0, 0, 1]], dtype=int),
    'y':  np.array([[1,  0, 0], [0, 1, -1], [0, 0, 1]], dtype=int),
    e_xy: np.array([[1,  0, -1], [0, 1,  0], [0, 0, 1]], dtype=int),
}


def _matrix_of_signed(base, exp):
    if exp == +1:
        return _BASE_MATRICES[base]
    return _BASE_MATRICES_INV[base]


def matrix_of_word(hyperword, hypergraph):
    """Compute the matrix product of F(w) in the Heisenberg group."""
    M = np.eye(3, dtype=int)
    for hl in hyperword:
        for base, exp in interpret(hl, hypergraph.vertices):
            M = M @ _matrix_of_signed(base, exp)
    return M


def assert_invariant(before, after, hypergraph):
    """Assert that two hyperwords represent the same group element."""
    m_before = matrix_of_word(before, hypergraph)
    m_after = matrix_of_word(after, hypergraph)
    assert np.array_equal(m_before, m_after), (
        f"Invariant violated!\n  before: {m_before}\n  after:  {m_after}"
    )


# ---------------------------------------------------------------------------
# apply_R3
# ---------------------------------------------------------------------------

class TestApplyR3:
    def test_removes_empty_block(self):
        word = [HyperLetter(frozenset({('x', +1)})), EMPTY_LETTER]
        result = apply_R3(word, 1)
        assert result == [HyperLetter(frozenset({('x', +1)}))]

    def test_removes_first_block(self):
        word = [EMPTY_LETTER, HyperLetter(frozenset({('y', +1)}))]
        result = apply_R3(word, 0)
        assert result == [HyperLetter(frozenset({('y', +1)}))]

    def test_reduces_length_by_one(self):
        word = [EMPTY_LETTER, EMPTY_LETTER, EMPTY_LETTER]
        assert len(apply_R3(word, 1)) == 2


# ---------------------------------------------------------------------------
# apply_R2
# ---------------------------------------------------------------------------

class TestApplyR2:
    def test_cancel_adjacent_inverse_pair(self):
        # [x^{-1}][x] → u=∅, v=∅, both prices ∅ → every block is empty and
        # is omitted (spec 0.1), so the result is the empty word.
        word = [
            HyperLetter(frozenset({('x', -1)})),
            HyperLetter(frozenset({('x', +1)})),
        ]
        result = apply_R2(word, 0, ('x', +1), HEISENBERG)
        assert result == []
        assert_invariant(word, result, HEISENBERG)

    def test_r2_preserves_group_element_x_inv_plus_exy_x(self):
        # First step of Relator 1: [e_xy^{-1}][x^{-1} + e_xy] → [x^{-1}]
        # This is a multi-step; just test the invariant on one R2 step
        u_block = HyperLetter(frozenset({('x', -1)}))
        v_block = HyperLetter(frozenset({(e_xy, +1)}))
        word = [HyperLetter(frozenset({(e_xy, -1)})), u_block, v_block]
        # apply R1 first to merge x^{-1} and e_xy, then R2...
        # instead just verify the pure step works:
        word2 = [
            HyperLetter(frozenset({(e_xy, -1)})),
            HyperLetter(frozenset({('x', -1), (e_xy, +1)})),
        ]
        result = apply_R2(word2, 0, (e_xy, +1), HEISENBERG)
        assert_invariant(word2, result, HEISENBERG)


# ---------------------------------------------------------------------------
# apply_R1
# ---------------------------------------------------------------------------

class TestApplyR1:
    def test_move_x_into_empty_block(self):
        # [∅][x] → [x] [∅] [∅] [∅]  (prices of empty block are all empty)
        word = [EMPTY_LETTER, HyperLetter(frozenset({('x', +1)}))]
        result = apply_R1(word, 0, 1, ('x', +1), HEISENBERG)
        assert HyperLetter(frozenset({('x', +1)})) in result
        assert_invariant(word, result, HEISENBERG)

    def test_r1_relator4_step1(self):
        """
        Relator 4 Step 1: [y^{-1}][x] → [x + y^{-1}] [e_xy]
        right_price(x, [y^{-1}]) = [e_xy]; v and left_price(x, [∅]) are both
        empty, so (spec 0.1) both are omitted rather than written as [∅].
        """
        word = [
            HyperLetter(frozenset({('y', -1)})),
            HyperLetter(frozenset({('x', +1)})),
        ]
        result = apply_R1(word, 0, 1, ('x', +1), HEISENBERG)
        assert len(result) == 2
        # Block 0 should be [x + y^{-1}]
        assert HyperLetter(frozenset({('x', +1), ('y', -1)})) == result[0]
        # Block 1 should be r_{x}([y^{-1}]) = [e_xy]
        assert HyperLetter(frozenset({(e_xy, +1)})) == result[1]
        assert_invariant(word, result, HEISENBERG)


# ---------------------------------------------------------------------------
# find_applicable_rules
# ---------------------------------------------------------------------------

class TestFindApplicableRules:
    def test_no_rules_on_single_block(self):
        word = [HyperLetter(frozenset({('x', +1)}))]
        assert find_applicable_rules(word, HEISENBERG) == []

    def test_finds_r3_for_empty_block(self):
        word = [EMPTY_LETTER]
        rules = find_applicable_rules(word, HEISENBERG)
        assert any(r[0] == 'R3' for r in rules)

    def test_finds_r2_for_inverse_pair(self):
        word = [
            HyperLetter(frozenset({('x', -1)})),
            HyperLetter(frozenset({('x', +1)})),
        ]
        rules = find_applicable_rules(word, HEISENBERG)
        assert any(r[0] == 'R2' for r in rules)

    def test_finds_r1_for_addable_element(self):
        # [∅][y^{-1}]: y is addable into [∅]
        word = [EMPTY_LETTER, HyperLetter(frozenset({('y', -1)}))]
        rules = find_applicable_rules(word, HEISENBERG)
        assert any(r[0] == 'R1' for r in rules)

    def test_path_xz_has_no_applicable_rules(self):
        # [x][z]: x and z don't share an edge in PATH
        word = [
            HyperLetter(frozenset({('x', +1)})),
            HyperLetter(frozenset({('z', +1)})),
        ]
        assert find_applicable_rules(word, PATH) == []


# ---------------------------------------------------------------------------
# normal_form — ground truth tests
# ---------------------------------------------------------------------------

class TestNormalForm:
    def test_heisenberg_commutator_reduces_to_exy(self):
        """
        σ(x⁻¹y⁻¹xy) →* [e_xy]
        Ground truth: the commutator [x,y] = e_xy in the Heisenberg group.
        """
        word = sigma([('x', -1), ('y', -1), ('x', +1), ('y', +1)], HEISENBERG)
        nf = normal_form(word, HEISENBERG)
        assert nf == [HyperLetter(frozenset({(e_xy, +1)}))]
        assert_invariant(word, nf, HEISENBERG)

    def test_heisenberg_relator1_reduces_to_identity(self):
        """
        σ(e_xy⁻¹ x⁻¹ e_xy x) →* []   (Relator 1: [[x,y],x] = 1)
        """
        word = sigma(
            [(e_xy, -1), ('x', -1), (e_xy, +1), ('x', +1)],
            HEISENBERG,
        )
        nf = normal_form(word, HEISENBERG)
        assert nf == []
        assert_invariant(word, nf, HEISENBERG)

    def test_path_xz_is_already_normal(self):
        """
        σ(xz) is already in normal form in PATH.
        x and z share no edge → neither R1 nor R2 applies.
        """
        word = sigma([('x', +1), ('z', +1)], PATH)
        nf = normal_form(word, PATH)
        assert nf == [
            HyperLetter(frozenset({('x', +1)})),
            HyperLetter(frozenset({('z', +1)})),
        ]
        # PATH has vertices {x,y,z}; the Heisenberg matrix map only covers {x,y}.
        # Structural equality above is the full correctness check here.

    def test_heisenberg_identity_word_reduces_to_empty(self):
        """σ(x x⁻¹) →* []"""
        word = sigma([('x', +1), ('x', -1)], HEISENBERG)
        nf = normal_form(word, HEISENBERG)
        assert nf == []
        assert_invariant(word, nf, HEISENBERG)

    def test_heisenberg_relator4_exy_reduces(self):
        """
        σ(x⁻¹ y⁻¹ x y e_xy⁻¹) →* []   (Relator 4: [x,y] e_xy⁻¹ = 1)
        """
        word = sigma(
            [('x', -1), ('y', -1), ('x', +1), ('y', +1), (e_xy, -1)],
            HEISENBERG,
        )
        nf = normal_form(word, HEISENBERG)
        assert nf == []
        assert_invariant(word, nf, HEISENBERG)

    def test_triangle_double_commutator_is_identity(self):
        """
        σ([[x,y],z]) = σ(e_xy⁻¹ z⁻¹ e_xy z) →* []
        In TRIANGLE, [[x,y],z] = 1 (Relator 3).
        """
        word = sigma(
            [(e_xy, -1), ('z', -1), (e_xy, +1), ('z', +1)],
            TRIANGLE,
        )
        nf = normal_form(word, TRIANGLE)
        assert nf == []

    def test_invariant_at_each_step_heisenberg_commutator(self):
        """
        For σ(x⁻¹y⁻¹xy), assert the invariant holds at EVERY intermediate step.
        """
        original = sigma([('x', -1), ('y', -1), ('x', +1), ('y', +1)], HEISENBERG)
        word = list(original)
        seen = [list(word)]
        max_steps = 200
        for _ in range(max_steps):
            rules = find_applicable_rules(word, HEISENBERG)
            if not rules:
                break
            rule = rules[0]
            if rule[0] == 'R3':
                word = apply_R3(word, rule[1])
            elif rule[0] == 'R2':
                word = apply_R2(word, rule[1], rule[2], HEISENBERG)
            elif rule[0] == 'R1':
                word = apply_R1(word, rule[1], rule[2], rule[3], HEISENBERG)
            # invariant: every intermediate word equals the original group element
            assert_invariant(original, word, HEISENBERG)
        assert word == [HyperLetter(frozenset({(e_xy, +1)}))]

    def test_invariant_at_each_step_relator1(self):
        """
        For σ(e_xy⁻¹ x⁻¹ e_xy x), assert invariant at every step.
        """
        original = sigma(
            [(e_xy, -1), ('x', -1), (e_xy, +1), ('x', +1)],
            HEISENBERG,
        )
        word = list(original)
        max_steps = 200
        for _ in range(max_steps):
            rules = find_applicable_rules(word, HEISENBERG)
            if not rules:
                break
            rule = rules[0]
            if rule[0] == 'R3':
                word = apply_R3(word, rule[1])
            elif rule[0] == 'R2':
                word = apply_R2(word, rule[1], rule[2], HEISENBERG)
            elif rule[0] == 'R1':
                word = apply_R1(word, rule[1], rule[2], rule[3], HEISENBERG)
            assert_invariant(original, word, HEISENBERG)
        assert word == []
