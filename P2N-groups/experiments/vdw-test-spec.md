Follow-on to the previous experiment. The confluence failure from Test B means we're trying an alternative: a deterministic insertion algorithm instead of a confluent rewriting system, justified by van der Waerden's trick. This spec defines the insertion operator and the two conditions that need to hold. Condition (2) on non-flag hypergraphs is the decisive result — run that first and report it before anything else. Reuse the existing engine, mu_check, hypergraph_enum and word_gen.


# Spec: test the van der Waerden conditions for insertion-based normal forms

Follow-on to the previous spec. Much smaller: one new operator, two conditions, one decisive
verdict. Reuses the existing engine, `mu_check`, `hypergraph_enum`, and `word_gen`.

**Context.** Test B showed the rewriting system is not confluent on non-flag `χ` (the
`K_3`-with-no-triangle counterexample). Rather than assume flagness, we are testing whether
the group has a normal form obtained by a *deterministic left-to-right insertion algorithm*,
which needs no confluence at all. This spec decides whether that works.

---

## Part 1 — The insertion operator

### 1.1 Definition

For a hyperword `C` and a signed letter `a ∈ A^±`:

```
rho[a](C) := reduce( C ++ [ {a} ], strategy=S )
```

for a **fixed deterministic strategy `S`**. Any deterministic `S` is legitimate for what we
are testing — the point is that `rho[a]` is a function, not that it is canonical. Pin `S`
explicitly and record which one was used.

Run the whole suite under **three** strategies:

- `S1` = leftmost-innermost (leftmost applicable redex)
- `S2` = rightmost applicable redex
- `S3` = "push the newest letter first": always pick the redex involving the most recently
  inserted letter if one exists, else leftmost

`S3` is closest to a genuine collection process and is the one most likely to succeed. A
condition may hold under one strategy and fail under another; that is informative, not a bug.

### 1.2 The canonical set

```
N := { rho[a_m](...rho[a_1](λ)...)  :  a_1...a_m ∈ (A^±)^*,  m ≥ 0 }
```

i.e. the image of left-to-right insertion starting from the empty word. `N` is closed under
every `rho[a]` by construction.

### 1.3 Sampling `N`

Generate elements of `N` by taking random words in `(A^±)^*` of length `0..L` (`L ≈ 15`) and
folding `rho` over them. **Do not** generate hyperwords directly and filter — the whole point
is that `N` is strictly smaller than the set of irreducible hyperwords.

Sanity check to run first: on the Test B counterexample hypergraph (`v2,v3,v4`, all three
pairs edges, no triple), confirm that `[{v2,v4}][{v3,e34}]` is **irreducible but not in `N`**,
while `[{v2,v3}][{v4}]` **is** in `N`. If that fails, `rho` is not implementing insertion.

---

## Part 2 — The two conditions

### 2.1 CONDITION (1) — invertibility

For every sampled `C ∈ N` and every `a ∈ A^±`:

```
rho[a^{-1}]( rho[a](C) ) == C        and        rho[a]( rho[a^{-1}](C) ) == C
```

Both directions. Expected to hold; short to prove if it does. Report any failure with
`(χ, C, a, strategy)`.

### 2.2 CONDITION (2) — the relators act trivially

**This is the decisive test.** Define `rho_word(C, a_1...a_m) = rho[a_m](...rho[a_1](C)...)`
— insert left to right.

For every sampled `C ∈ N` and every defining relator `r` below, check

```
rho_word(C, r) == C
```

Relator words, as elements of `(A^±)^*`, for `{v_i,v_j} ∈ E_2` with `i < j`:

| name | word | range |
|---|---|---|
| `T_x` | `e_ij^{-1} v_i^{-1} e_ij v_i` | all `{v_i,v_j} ∈ E_2` |
| `T_y` | `e_ij^{-1} v_j^{-1} e_ij v_j` | all `{v_i,v_j} ∈ E_2` |
| `T_z` | `e_ij^{-1} v_k^{-1} e_ij v_k` | all `{v_i,v_j,v_k} ∈ E_3` |
| `D`   | `v_i^{-1} v_j^{-1} v_i v_j e_ij^{-1}` | all `{v_i,v_j} ∈ E_2` |

Inverse relators need not be tested separately: they follow from Condition (1) once the
forward ones hold.

Note `T_z` only ranges over **triples in `E_3`** — density then covers all larger hyperedges,
so do not enumerate 4-element edges separately.

### 2.3 Verdict

- **(1) and (2) both hold across all dense `χ`** → van der Waerden applies, the group has a
  unique insertion normal form, no flagness needed, and the confluence section can be
  deleted rather than repaired. This is the outcome we want.
- **(2) fails on some non-flag `χ`** → the normal form genuinely does not exist there and
  flagness was the real hypothesis all along. Report the minimal failing
  `(χ, relator, C, strategy)` — that quadruple settles the paper's direction.
- **(2) holds on flag `χ` but fails on non-flag `χ`** → same conclusion as above, but with a
  clean statement of exactly where the boundary lies.

---

## Part 3 — Follow-on tests, only if (1) and (2) pass

### 3.1 Agreement with the existing engine on flag `χ`

On flag `χ` (where the rewriting system *is* confluent), the insertion normal form must equal
the rewriting normal form for every sampled word. A mismatch means one of the two engines is
wrong. Flag `χ` = `E` is the clique complex of `Γ_2(χ)`: every pairwise-adjacent set of
vertices is an edge.

### 3.2 Re-run the centre test, confluence-independently

The previous Test C carried the caveat "fixed strategy, not confluence-independent". Under
insertion normal forms that caveat disappears. Re-run:

```
is_central(g)  :=  for all v_c ∈ V:  rho_word(g, v_c) == rho[v_c-inserted-on-the-left](g)
```

Left insertion is not primitive here, so implement it as: `g` is central iff for every
`v_c`, `rho_word(λ, w_g · v_c) == rho_word(λ, v_c · w_g)` where `w_g ∈ (A^±)^*` is any word
representing `g` (e.g. `F(g)` read off the normal form). Then check: **does any central
element have a vertex letter in its normal form?** This is the `thm:center` Step 3a question,
now on all dense `χ` rather than only flag ones.

### 3.3 Re-run clean append

Same as Test D previously, but with insertion normal forms and on all dense `χ`. Keep the
trigger-filter count in the report — a zero count still means the run is uninformative.

---

## Part 4 — Reporting

Per strategy `S1/S2/S3`, per condition, report: hypergraphs covered, samples, pass/fail
counts, and for every failure the minimal reproducing `(χ, C, relator or letter)`.

Priority: **Condition (2) first, on non-flag `χ` specifically** — that is the single number
that decides whether the paper needs flagness. Run `n=3` exhaustively (20 hypergraphs, 8 of
them flag) before anything larger; the `K_3` counterexample hypergraph from Test B is the
first place to look, and if (2) fails anywhere it will very likely fail there.

Do not run Part 3 until Part 2 has passed — the results would be uninterpretable.

---

## Appendix — what `rho` looks like structurally

Not needed for the tests, but useful for writing the proof afterwards, and worth checking
your `S3` implementation against.

Appending `z = x^ε` to a canonical `C = [u_0]...[u_{k-1}]`: `z` scans leftward from the right
end and stops at the first block `u_i` where either `x^{-ε} ∈ u_i` (cancel) or `z` is not
addable into `u_i` (blocked). Costs:

- each block `u_j` that `z` **passes through** contributes `l_z(u_j) · r_z(u_j)` immediately
  after `u_j`;
- the block `z` **lands in** contributes `r_z(u_i)` immediately after it;
- a cancelling block `u_i` contributes `r_z(u_i \ {x^{-ε}})` immediately after it.

All of these are pure-edge, so inserting them generates no further prices — the recursion has
depth 1. That is why the algorithm terminates trivially and why the termination measure from
the previous version becomes unnecessary.
