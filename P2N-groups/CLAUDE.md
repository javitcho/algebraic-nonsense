# Partially 2-Nilpotent Groups — Code & Visualization Tools

## Project purpose
This repo implements computational tools and visualizations for the rewriting
system that solves the word problem for partially 2-nilpotent groups G(χ).
The mathematics is fully defined in `word-problem.tex`. This file is the authoritative
reference for all implementation decisions.

---

## Mathematical objects (implement exactly as defined here)

### Hypergraph χ = (V, E)
- V = finite ordered set of vertices {v1, ..., vn}, always with a fixed total order
- E ⊆ P(V) = set of hyperedges, **must be dense (downward-closed)**:
  if e ∈ E and e' ⊆ e then e' ∈ E
- Decompose E = E1 ⊔ E2 ⊔ ... ⊔ E|V| where Ek = hyperedges of size k
- E1 (singletons) can always be omitted — they produce only trivial relations

### Augmented alphabet A
- A = V ∪ E2
- E2 elements are commutator symbols e_ij with i < j, one per 2-element hyperedge {vi, vj}
- A± = {a^+1, a^-1 | a ∈ A} = signed alphabet
- **Total order on A±** (this exact order must be used everywhere):
  v1⁻¹ < v1 < v2⁻¹ < v2 < ... < vn⁻¹ < vn < e12⁻¹ < e12 < e13⁻¹ < e13 < ... < eij⁻¹ < eij < ...
  Rule: a⁻¹ < a for all a, and a⁻¹ < b⁻¹ iff a < b

### Extended hyperedge Ē
For hyperedge E = {vi1, ..., vir} (i1 < ... < ir):
  Ē = {vi1,...,vir} ∪ {e_ij | {vi, vj} ∈ E2, i < j}
This is the set of symbols that can "interact" with each other.

### Hyper-letter [u]
- u ⊆ A± is a finite set satisfying:
  1. |u| = {a | a^ε ∈ u} ⊆ Ē for some maximal hyperedge E
  2. No inverse pairs: x^ε ∈ u ⟹ x^{-ε} ∉ u
- [∅] is a valid hyper-letter (used by R3)
- Hyperword: finite sequence of hyper-letters, i.e. element of A*

### Interpretation map F: A* → (A±)*
F([u]) = a1^ε1 · a2^ε2 · ... · ak^εk
where u = {a1^ε1,...,ak^εk} sorted by the total order on A (positive part only for sorting).
F([∅]) = empty word.
F extends to a monoid homomorphism on A* by concatenation.

### c function: A × A → A± ∪ {-}
For a < b sharing a hyperedge:
  c(a,b) = e_ab   if a,b ∈ V
  c(a,b) = -      if a ∈ E2 or b ∈ E2  (contributes nothing)
  c(b,a) = c(a,b)^{-1}
The "-" return value means "no commutator generated, skip this term".

### Price functions (core of the rewriting system)
Given [u] ∈ A with elements straddling b (b ∉ |u|), b^η addable into u:
  - Elements of u less than b: a1^ε1,...,ar^εr  (left side)
  - Elements of u greater than b: c1^δ1,...,cs^δs (right side)

Left price:  l_{b^η}([u]) = [{ c(ai,b)^{η·εi} | i=1..r, c≠- }]
Right price: r_{b^η}([u]) = [{ c(cj,b)^{η·δj} | j=1..s, c≠- }]

Both return hyper-letters containing only E2± elements.
If b^η is not addable into u, these are undefined — treat as an error.

### Addability
b^η is addable into [u] iff:
  1. b ∉ |u|
  2. ∃ maximal hyperedge E such that |u| ∪ {b} ⊆ Ē

### Rewriting rules on A*
**R1 (Movement):** w1[u][v+x^ε]w2 → w1[u+x^ε] r_{x^ε}(u) [v] l_{x^ε}(v) w2
  condition: x^ε addable into both u and v

**R2 (Cancellation):** w1[u+x^{-ε}][v+x^ε]w2 → w1[u] r_{x^ε}(u) [v] l_{x^ε}(v) w2
  condition: x^ε addable into u and v

**R3 (Empty deletion):** w1[∅]w2 → w1 w2

A word is in **normal form** iff no rule applies:
  - No [∅] present
  - No x^ε in block j that is addable into any earlier block i < j
  - No x^{-ε} in block i with x^ε in block i+1

### Correctness invariant
Every rewriting step preserves the group element:
  μ(F(w)) = μ(F(w'))  whenever  w → w'
This is the check for every test.

### Key examples to use as ground truth
1. **Heisenberg group** (two vertices, one edge):
   χ = ({x,y}, {{x,y}}), A = {x, y, e_xy}
   Relations: [[x,y],x]=1, [[x,y],y]=1, [x,y]=e_xy
   Word [x^{-1}][y^{-1}][x][y] should reduce to [e_xy] (normal form)

2. **Path graph** (three vertices, edges {1,2} and {2,3} but NOT {1,3}):
   x and z do not share an edge — they cannot interact
   Normal form of [x][z] is just [x][z] (already reduced)

3. **Triangle** (three vertices, all edges including {1,2,3}):
   All three vertices interact, e12, e13, e23 all exist
   [[x,y],z] = 1 in this group

---

## Repository layout

```
/
├── CLAUDE.md              ← this file
├── paper.tex              ← source of mathematical truth
├── tools/
│   ├── core/
│   │   ├── hypergraph.py      ← Hypergraph, vertex/edge data structures
│   │   ├── alphabet.py        ← A, A±, total order, c function
│   │   ├── hyperletter.py     ← HyperLetter, addability, price functions
│   │   └── rewriter.py        ← R1/R2/R3, normal_form(), rewrite_step()
│   ├── viz/
│   │   └── (visualization tools, one file per tool)
│   └── __init__.py
├── tests/
│   ├── test_hypergraph.py
│   ├── test_alphabet.py
│   ├── test_prices.py
│   ├── test_rewriting.py
│   └── fixtures.py            ← shared test hypergraphs (Heisenberg, path, triangle)
└── examples/
    └── heisenberg.py          ← runnable demo
```

---

## Implementation rules

1. **Never approximate the math.** If a definition says "there exists a maximal
   hyperedge E such that...", check all maximal hyperedges, not just one.

2. **The total order on A± is fixed and must be consistent everywhere.**
   Sorting a hyper-letter, computing F, and comparing elements must all use
   the same order function. Implement it once in `alphabet.py` and import it.

3. **c(a,b) returning "-" means skip, not error.** Price functions silently
   drop terms where c returns "-". This is correct behavior, not a bug.

4. **[∅] is a valid hyper-letter.** Do not special-case it away before R3
   has a chance to fire. F([∅]) = empty word = identity in the group.

5. **Rewriting is nondeterministic** (multiple rules may apply). For normal
   form computation, apply rules exhaustively in any order — confluence
   guarantees the result is unique. For visualization, show the choices.

6. **Tests must check the invariant**, not just the output shape:
   assert group_element(before) == group_element(after) for every step.
   For the Heisenberg group this is checkable concretely.

---

## Current status

- [x] Core data structures (hypergraph, alphabet, hyper-letter)
- [x] Price functions l, r
- [x] Rewriting rules R1, R2, R3
- [x] Normal form algorithm
- [x] Test suite with Heisenberg, path, triangle fixtures
- [ ] Visualization: rewriting step animator
- [ ] Visualization: hypergraph viewer
- [ ] Visualization: normal form explorer