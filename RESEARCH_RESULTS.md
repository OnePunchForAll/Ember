# Research results received: Ember's end-to-end targets

Provenance. The document below was written by a separate research session on
25 September 2026 in answer to RESEARCH_INQUIRY.md, and handed to this
repository by its owner on 26 September 2026 as a file. It is reproduced
unchanged below the rule. It is source-reported material: nothing in it is
evidence Ember uses, its claims carry the markers its author gave them ([P]
published, [V] verified, [R] reported, [U] unverified), and its citations were
not all reachable from this session (arxiv.org is blocked here), so a claim
marked [R] stays reported. What was done with it is recorded in CAMPAIGNS.md
under the entries that cite it: certified exception sets (the `exceptions`
claim kind, the scan operator and the window `window-schinzel-beyond-bounds`),
and the exact-certificate search kinds it ranks first.

Two readings made while installing the first of them. The obstruction lemma her
Erdős–Straus campaign proved is Schinzel's theorem (Funct. Approx. 28, 2000)
with Elsholtz and Tao's Proposition 1.6 (2013), as README.md now says. The
Pomerance and Weingartner calculations the document quotes support an
exceptional prime in (a^2, 2a^2) for every a >= 20; they do not bound the
exceptions above, and her certified sets show exceptions at 2a^2 + 1 itself
for a = 24, 32, 33, 36 and 42, while the library's earlier search recorded
90,001 for a = 20.

---

# Ember's end-to-end targets: what one exact-checking machine can finish (status as of 25 September 2026)

The best targets for Ember are finite constructions whose records were set by symmetric or local search and have not been exhaustively searched. Ranked by chance of success: 2n-point no-three-in-line configurations for n = 61 and up, multicolour 3-AP van der Waerden lower bounds, mid-range Ramsey lower bounds R(3,k) and R(4,k), minimum-lcm and other finite covering-system extremal values, and certified exception sets for Schinzel's unit-fraction numerators. Her current unit-fraction programme cannot close Erdős–Straus. Her obstruction lemma is a known theorem (Mordell, Schinzel, Yamamoto; restated by Elsholtz–Tao 2013), and pushing verification past 10^18 has no research value on her hardware. Several records the inquiry treats as open have fallen: the Hadamard orders 668, 716 and 892 (reported August 2026), no-three-in-line n = 47 (settled 2026), and OGR-28 (completed 2022).

**Status legend used throughout:** [P] proved (peer-reviewed or standard); [V] verified computationally (by a stated computation); [R] reported but not peer-reviewed, or only secondarily sourced; [C] conjectured; [U] unknown / open; "no source found" = I could not locate a source in this research session.

## TL;DR

- **Where to start:** begin with the no-three-in-line problem at n ≥ 61. Prellberg (arXiv:2602.07751, 2026) settled every n ≤ 60 by symmetric constraint programming, adding the new cases n = 47, 49, 51 and 53–60, so "the smallest n for which it is unknown whether D(n) = 2n increases from 47 to 61". The check is trivial. Be warned that his solver found nothing for n = 61 or 62 within 10^7 seconds. Next are the multicolour van der Waerden bounds W(r,3); the last published increments were small and cheap. Then the R(3,k)/R(4,k) lower bounds in Radziszowski's Table IIa, which DS1 itself calls "not that hard to improve" and which moved again in 2026. [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) Then covering-system minimum-lcm problems. Last is certified Schinzel exception data, which is her native territory.
- **Unit fractions:** residue-class families provably cannot cover the square classes. Schinzel's theorem says that if 4/(at+b) is polynomially 3-Egyptian then b is a quadratic non-residue mod a. Elsholtz–Tao Prop. 1.6 says odd squares have no Type I/II solutions. So Erdős–Straus is out of reach of any cover-based certificate [P]. The frontier is 10^17 (Salez 2014, [V]) and 10^18 (Spiridon Mihnea and Dumitru C. Bogdan, arXiv:2509.00128, submitted 29 August 2025, [R], with a flagged gap). For large numerators, Schinzel's N(a), if it exists, must be at least exp(a^{1/3+o(1)}) (Pomerance–Weingartner, arXiv:2511.16817).
- **What "end to end" means today:** a construction checked by exact arithmetic, or an LRAT/DRAT refutation checked by a verified checker (cake_lpr, ACL2check). Recent landmark proofs are 34 TB to 2 PB. Ember should emit LRAT (hint-annotated, linear-time checkable) for small negative results, and treat positive constructions as her main product.

## Key Findings

1. **Records that have moved (2022–2026) and change the inquiry's premises:**
   - **Hadamard:** on 12 August 2026 Levent Alpöge announced on X, with P. Voinov and S. Reynolds-Haertle, constructions obtained with Claude for all twelve previously open orders below 2000: 668, 716, 892, 1132, 1244, 1388, 1436, 1676, 1772, 1916, 1948 and 1964 [R]. MathWorld states that "Epoch AI (2026) reported that L. Alpöge, P. Voinov, and S. Reynolds-Haertle had announced constructions obtained with Claude". Order 668 had been the smallest open order since Kharaghani–Tayfeh-Rezaie constructed H(428) (J. Combin. Des. 13, 2005).
     - Epoch AI marks order 668 "Solved (human + AI)", provisionally. [epoch](https://epoch.ai/frontiermath/open-problems/hadamard)
     - No peer-reviewed paper was found.
   - **No-three-in-line:** Prellberg (arXiv:2602.07751, 2026) exhibits 2n-point configurations for all n ≤ 60, so the smallest open n is 61 [V]. [arxiv](https://www.arxiv.org/pdf/2602.07751)
   - **Golomb rulers:** distributed.net completed OGR-28 on 23 November 2022 (length 585) [V]. [distributed](https://blogs.distributed.net/) [distributed](https://www.distributed.net/News)
   - **Erdős–Straus verification:** extended to 10^18 by Spiridon Mihnea and Dumitru C. Bogdan (arXiv:2509.00128, August 2025; abstract: "improving computational bounds to 10^18") [R].
   - **R(5,5) ≤ 46:** Angeltveit–McKay, arXiv:2409.15709, J. Graph Theory 2026, doi:10.1002/jgt.70029 [P, computer-assisted]. [arxiv](https://arxiv.org/abs/2409.15709) [arxiv](https://arxiv.org/pdf/2604.21187)
   - **Radziszowski's DS1:** now at revision #18 (24 April 2026). [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
2. **Records that have not moved:**
   - Least modulus of a distinct covering system: 42 (Owens 2014). Still cited as the record in July 2026 (arXiv:2607.19029). [arxiv](https://arxiv.org/html/2607.19029)
   - Cap set in F_3^7: 236. [tudelft](https://repository.tudelft.nl/file/File_03ab6991-f67e-48c7-87cd-bf4f2a0237d4) [cmu](https://www.math.cmu.edu/~mtait/caps.pdf)
   - S(6) ≥ 536 (2000). [wolfram](https://mathworld.wolfram.com/SchurNumber.html)
   - W(2,7) > 3703. [arxiv](https://arxiv.org/pdf/1601.04697)
   - Costas arrays: none known at orders 32 and 33. [arxiv](https://arxiv.org/pdf/1102.5727)
   - R(5,5) ≥ 43 (Exoo 1989). [arxiv](https://www.arxiv.org/pdf/2409.15709)
3. **Heuristic scarcity:** DS1.18 records Harborth–Krause's result that no lower bound in Table Ia can be improved by a cyclic graph on fewer than 102 vertices, except possibly R(3,k) for k ≥ 13. [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) Circulant search on small classical Ramsey numbers is therefore exhausted. Ember must go to larger parameters or non-cyclic Cayley graphs.

## Deliverable 1 — Ranked table of open problems

Chance ratings are qualitative judgments from the evidence cited (how recently the record moved, by what method, and whether exhaustive search within the natural symmetry class has been published). They are not measured probabilities.

| # | Problem | Open case | Certificate & check | Best known (source) | Object size | Record method / space searched | Chance on 1 machine, days | First strategy | Checker rule needed |
|---|---|---|---|---|---|---|---|---|---|
| 1 | No-three-in-line | 2n points, no 3 collinear, on n×n grid, n = 61 (or any n ≥ 61) [U] | Point list; check that no triple is collinear (integer cross product) | All n ≤ 60 (Prellberg, arXiv:2602.07751, 2026) [V] [arxiv](https://www.arxiv.org/pdf/2602.07751) | 122 points | Constraint programming restricted to 90° rotational symmetry (even n) or rotation-except-diagonal plus 2 diagonal points (odd n) [arxiv](https://www.arxiv.org/pdf/2602.07751) | **Moderate.** The frontier moved 47→60 in one paper using symmetry; odd n is harder; no exhaustive result on the symmetric class at 61 found | Symmetric (rot4 / rct4) backtracking with slope-blocking bitsets; try n = 62 (even, rot4) in parallel | `nothree`: O(k²) slope-class hashing per point |
| 2 | Multicolour vdW, 3-APs | W(r,3) lower bounds, r = 7…17 [U] | r-colouring of [1,N]; no monochromatic 3-AP | Alexey V. Komkov, "New Lower Bounds for Van der Waerden Numbers" (arXiv:1701.05603, 2017, SAT-solver certificates): W(7,3) >342→>343, W(8,3) >511→>515, W(10,3) >889→>892, W(11,3) >1183→>1187, W(17,3) >3546→>3549, improving Heule (J. Comb. 8(3), 2017) [V]; no later source found | N ≤ ~3600 | Modular/cyclic colourings plus SAT-based extension | **Moderate.** The last gains were +1 to +4 from modest compute, so the frontier is soft; they may already have been beaten (no source found) | Colour by i mod p over power-residue classes; then local SAT/tabu extension at both ends | `apfree(k=3)`: O(N²) pair check |
| 3 | Ramsey lower bounds, mid range | R(3,k), 16 ≤ k ≤ 23; R(4,k), 16 ≤ k ≤ 22 [U] | Graph; check ω < s and α < t exactly | R(3,16) ≥ 82 … R(3,23) ≥ 139; R(4,16) ≥ 170 … R(4,22) ≥ 314 (DS1.18 Table IIa, 2026) [V]; [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) R(4,20) ≥ 252 claimed (arXiv:2608.18169, 2026) [R] [arxiv](https://arxiv.org/pdf/2608.18169) | 80–320 vertices | Circulant/Cayley constructions (Exoo, Kolodyazhny, Kuznetsov); RL-guided (Nagda–Raghavan–Thakurta 2026) [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | **Low–moderate.** DS1 2.2.i expects these bounds are weaker than Table Ia; 2026 papers improved several [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | Circulant on Z_n: tabu over connection set S = −S, exploiting vertex-transitivity | `ramseygraph(s,t)`: branch-and-bound clique search, rooted at vertex 0 for circulants |
| 4 | Covering systems, finite extremal values | Min lcm of a distinct covering with min modulus m = 8, 9, …; stretch goal: min modulus ≥ 43 [U] | Congruence list; coverage of every residue mod lcm, or a CRT-tree check | Min modulus 42 (Owens 2014); min lcm 10080 for m = 7 (arXiv:2607.19029, 2026) [V]; [arxiv](https://arxiv.org/html/2607.19029) upper bounds 616,000 (BBMST, Invent. Math. 228, 2022) and 118 for squarefree moduli (Cummings–Filaseta–Trifonov, Acta Math. Hungar. 2024) [P] [arxiv](https://arxiv.org/pdf/2208.09720) [researchgate](https://www.researchgate.net/publication/356265374_On_the_Erdos_covering_problem_the_density_of_the_uncovered_set) | lcm 10^4–10^6 (min-lcm problems); astronomically large for m = 42 | Nielsen's recursive construction (2009), refined by Owens [uwaterloo](https://cs.uwaterloo.ca/journals/JIS/VOL25/Trifonov/trif3.pdf) | **Moderate** for min-lcm at m = 8 (small, active area); **very low** for 43 (12 years without progress) | Integer programming or DFS over divisors of a candidate L with greedy residue choice | `cover`: sieve over Z_L; for large L, a recursive prime-by-prime tree |
| 5 | Schinzel exceptions | Exact sets E_a(X) = {n ≤ X : a/n not a sum of 3 unit fractions}, a = 7…30 [U, as certified data] | Witness triple for every n ∉ E; exhaustive bounded search for every n ∈ E | Pomerance–Weingartner (arXiv:2511.16817, v2 15 Jan 2026) report "extensive numerical calculations that support this assertion with the much smaller bound m≥20" (exceptional primes p ∈ (a², 2a²)) [V/R] | per-n search of about p²/a² steps | Direct search by the authors | **High** for certified data; **novelty uncertain** | Reuse her witness and family pipeline; add a `nonrep` refutation | `nonrep(a,n)`: enumerate x ≤ 3n/a, then y, with exact rationals |
| 6 | Erdős–Straus audit | Independently certify the Salez filter structure and audit the 10^18 claim | Filter = residue set with identity per class | 10^17 (Salez, arXiv:1406.6307, 2014) [V]; 10^18 [R] | 147,348 classes mod 892,371,480 | [arxiv](https://arxiv.org/abs/1406.6307) [arxiv](https://arxiv.org/pdf/1406.6307) Modular filters on n ≡ 1 mod 24 | **High** for reproducing the filters; **zero** for a new range | Encode Salez's 7 modular equations as `gfam` rules | existing `cover`/`gfam`, plus a `filter` rule |
| 7 | Weak Schur | WS(6) ≥ 647 [U] | 6-colouring of [1,N], each class weakly sum-free (x + y = z, x ≠ y, forbidden) | WS(6) ≥ 646 (Ageron et al., arXiv:2112.03175) [V] [arxiv](https://arxiv.org/abs/2112.03175) | N = 647 | Templates plus ad hoc search | **Low–moderate** | Extend the 646 partition by local search / SAT at the tail | `weaksumfree`: O(N²) |
| 8 | Schur S(6) | S(6) ≥ 537 [U] | 6-colouring of [1,537], sum-free | S(6) ≥ 536 (Fredricksen–Sweet, EJC 17 R32, 2000) [V]; [arxiv](https://arxiv.org/pdf/1711.08076) templates build larger n from it (arXiv:2607.15034, 2026) [arxiv](https://arxiv.org/abs/2607.15034) [wolfram](https://mathworld.wolfram.com/SchurNumber.html) | N = 537 | Symmetric (palindromic) sum-free partitions | **Low.** 26 years unchanged despite template campaigns | Symmetric SAT over palindromic colourings | `sumfree`: O(N²) |
| 9 | vdW W(2,7) | 2-colouring of [1,3704] with no mono 7-AP [U] | Colouring; AP check | > 3703 (Rabung–Lotts 2012) [V] [arxiv](https://arxiv.org/pdf/1601.04697) | N = 3704 | Cyclic zipper over prime/primitive-root colourings [researchgate](https://www.researchgate.net/publication/267190465_Improving_the_Use_of_Cyclic_Zippers_in_Finding_Lower_Bounds_for_van_der_Waerden_Numbers) | **Low** | Zipped Rabung colourings for primes near 3700; local repair | `apfree(k=7)`: O(N²/6) |
| 10 | Cap set n = 7 | Cap of size 237 in F_3^7 [U] | Point set; for each pair, the third point −(x+y) is absent | 236 (Calderbank–Fishburn 1994; recorded by Edel) [V]; upper bound 291 [P] [tudelft](https://repository.tudelft.nl/file/File_03ab6991-f67e-48c7-87cd-bf4f2a0237d4) | 237 points | Product/lifting constructions | **Low.** FunSearch (Nature 625, 2024) improved n = 8 [nature](https://www.nature.com/articles/s41586-023-06924-6) but not n = 7 | Search caps invariant under a chosen subgroup of AGL(7,3) | `capset`: O(k²) hash lookup |
| 11 | Cap set n = 8 | ≥ 513 [U] | same | 512 (FunSearch, Romera-Paredes et al., Nature 625, 2024) [V] [nyu](https://cs.nyu.edu/~davise/papers/FunSearch.pdf) [nature](https://www.nature.com/articles/s41586-023-06924-6) | 513 points | Evolved greedy priority functions (4 of 140 runs reached 512) [researchgate](https://www.researchgate.net/publication/376546904_Mathematical_discoveries_from_program_search_with_large_language_models) | **Low** | Greedy with symmetry (reflection i ↔ −i) plus tabu | `capset` |
| 12 | Structured multicolour Ramsey | e.g. R(K4, K4−e, K4−e) ≥ 36 [U] | Edge colouring; forbidden-subgraph check | ≥ 35 (Wesley, arXiv:2509.03784, 2025) [V] [arxiv](https://arxiv.org/html/2509.03784) | ~35 vertices | SAT on structured (circulant/block) colourings [arxiv](https://arxiv.org/html/2509.03784) | **Low–moderate** | Circulant SAT encoding using her SAT tool | `ramseycolour` |
| 13 | Costas arrays | Order 32 or 33 [U] | Permutation; all displacement vectors distinct | None known; complete enumeration to n = 29 (Drakakis et al., Adv. Math. Commun. 5, 2011) [V] [arxiv](https://arxiv.org/pdf/1102.5727) [arxiv](https://arxiv.org/pdf/2608.28690) | 32×32 | Welch/Lempel–Golomb constructions miss 32 and 33; exhaustive search to 29 | **Very low**; density arguments predict near-extinction | Not recommended beyond a calibration run | `costas`: O(n²) |
| 14 | R(5,5) lower bound | 43-vertex (5,5)-graph [U] | Graph; ω, α < 5 | ≥ 43 (Exoo 1989); ≤ 46 [P] [arxiv](https://www.arxiv.org/pdf/2409.15709) | 43 vertices | Exoo heuristics; McKay–Radziszowski gluing | **Negligible.** Strong evidence that R(5,5) = 43 (McKay–Radziszowski, per DS1.18 2.1.e) [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | Do not attempt | — |
| 15 | OGR-29 | Optimality of a 29-mark ruler [U] | Exhaustive-search certificate | OGR-28 = 585 (distributed.net, 2022) [distributed](https://blogs.distributed.net/) [V] [distributed](https://blogs.distributed.net/) [distributed](https://www.distributed.net/News) | ~10^40 raw space (arXiv:2609.05421) [arxiv](https://arxiv.org/pdf/2609.05421) | Distributed branch and bound; ~5×10^6 core-hours for OGR-28 (per arXiv:2609.05421) [arxiv](https://arxiv.org/pdf/2609.05421) | **None** | — | — |
| 16 | Three cubes | 114 (smallest open n) [U] | Integer triple, checked exactly | Open; frontier d ≤ 1.85×10^17 for 114 (Charity Engine 2020, per a 2026 GPU project) [R] [github](https://github.com/Elfsong/find114) | 20-digit integers | Booker–Sutherland algorithm on a global grid | **None** | — | `cubes`: trivial |
| 17 | Erdős–Straus range | Verify beyond 10^18 [U] | chunks | 10^18 [R] | — | C++ sieves | **None of value.** Python is ~50–100× slower than Salez's 16-hour C++ run for 10^17 (my estimate) | Do not do this | — |

## Deliverable 2 — Exact status of the unit-fraction conjectures

### 2.1 Erdős–Straus, 4/n = 1/x + 1/y + 1/z

- **Residue classes [P].** Mordell's identities (Mordell, *Diophantine Equations*, 1969) settle every residue class mod 840 except the six quadratic-residue classes 1, 121, 169, 289, 361, 529. [arxiv](https://arxiv.org/html/2609.29250) Salez lists R₂ = {1, 121, 169, 289, 361, 529} mod 840 and notes that Swett also used this reduction. [arxiv](https://arxiv.org/pdf/1406.6307)
- **Refinements.**
  - Terzi's computation mod 120,120 is reported as leaving 198 classes (arXiv:2609.29250) [R]. [arxiv](https://arxiv.org/html/2609.29250)
  - Salez's sieve leaves 192 residues at G₄ = 120,120. The two counts conflict; the difference may come from Salez restricting to n ≡ 1 mod 24 and his filters (not resolved).
  - Salez (arXiv:1406.6307, 2014) derives a complete set of seven modular equations and refines successive moduli: 120 (2 residues), 840 (6), 9,240 (34), 120,120 (192), 2,042,040 (1,507), 38,798,760 (13,380), and finally **G₇ = 892,371,480 with 147,348 residues** [V]. [arxiv](https://arxiv.org/pdf/1406.6307)
- **Verified range.**
  - 10^14: Swett 1999, 150 hours. [arxiv](https://arxiv.org/abs/1406.6307) [researchgate](https://www.researchgate.net/publication/395214305_Further_verification_and_empirical_evidence_for_the_Erdos-Straus_conjecture)
  - **10^17: Salez 2014** [V]. [arxiv](https://arxiv.org/pdf/2508.07367) Second stage: every n ∈ N₇ below 10^17 that is not a square has a "modular certificate" with an odd modulus below 5000. This took about 16 hours in C++ on an AMD Turion II M250. [arxiv](https://arxiv.org/pdf/1406.6307)
  - **10^18: Spiridon Mihnea and Dumitru C. Bogdan, arXiv:2509.00128 (submitted 29 August 2025; abstract: "improving computational bounds to 10^18 and by evaluating the solution-counting function f(p)")** [R]. They add a filter S29, giving 2,101,514 residues mod 25,878,772,920, per a secondary review. [pith](https://pith.science/paper/2509.00128)
    - A public review (pith.science) flags that the load-bearing step is the unproved assertion that no unfiltered survivor was prime ("found that none of them were prime"). [pith](https://pith.science/paper/2509.00128)
    - Treat 10^18 as [R] and 10^17 as the last fully documented bound.
- **Density [P].** Vaughan (Mathematika 17, 1970): the exceptions up to N number at most N exp(−c(log N)^{2/3}). [arxiv](https://arxiv.org/pdf/1107.1010) [erdosproblems](https://www.erdosproblems.com/tags/unit%20fractions)
- **Elsholtz–Tao** (J. Aust. Math. Soc. 94 (2013) 50–105; arXiv:1107.1010) [P]:
  - Definitions: a solution is *Type I* if n | x and n is coprime to y and z; *Type II* if n | y, z and n is coprime to x. f(p) = 3f_I(p) + 3f_II(p) for odd primes p. [arxiv](https://arxiv.org/pdf/1107.1010)
  - N log²N ≪ Σ_{p≤N} f(p) ≪ N log²N log log N. [arxiv](https://arxiv.org/abs/1107.1010) [researchgate](https://www.researchgate.net/publication/395214305_Further_verification_and_empirical_evidence_for_the_Erdos-Straus_conjecture)
  - Pointwise, f(p) ≪ p^{3/5+O(1/log log p)}. [arxiv](https://arxiv.org/abs/1107.1010)
  - f(n) ≫ (log n)^{0.549} on a density-1 set of n and on a relative-density-1 set of primes. [arxiv](https://arxiv.org/pdf/1107.1010) There is **no pointwise lower bound for every p** (such a bound would prove the conjecture).
  - Prop. 1.6: for any odd perfect square n, f_I(n) = f_II(n) = 0. [arxiv](https://arxiv.org/pdf/1107.1010)
  - They state: "a primitive congruence class n = r mod q which is a perfect square, cannot be solved by polynomials". They cite this as known and note it also follows from Prop. 1.6. Prop. 1.9 lists all Type I and Type II polynomially solvable families. [arxiv](https://arxiv.org/pdf/1107.1010)
  - Their citations [44] and [68] are presumably Mordell and Schinzel; I did not check their bibliography.
- **Schinzel's theorem [P]** (A. Schinzel, "On sums of three unit fractions with polynomial denominators", Funct. Approx. Comment. Math. 28 (2000) 187–194). As restated by Salez, Prop. 2: if 4/(at + b) is 3-Egyptian as a polynomial identity then b is a quadratic non-residue mod a. [arxiv](https://arxiv.org/pdf/1406.6307)
  - **Ember's obstruction lemma is therefore a rediscovery of this theorem.** Her `obstruction` claim is sound, but it should be cited, not presented as new.

### 2.2 Sierpiński (5/n) and Schinzel (a/n)

- **Existence of N(a):** unknown for every a ≥ 4 [U/C]. The conjecture is not proved outright for any a ≥ 4. No source found for any a with a published complete proof.
- **Lower bound on N(a)** (Carl Pomerance and Andreas Weingartner, "Exceptions to the Erdős–Straus–Schinzel conjecture", arXiv:2511.16817 v2 15 January 2026; Ramanujan J., 2025) [P]:
  - If n_m exists it must be at least exp(m^{1/3+o(1)}). [arxiv](https://arxiv.org/abs/2511.16817v1) [springer](https://link.springer.com/article/10.1007/s11139-025-01312-2)
  - For m ≥ 6.52×10^9 there is a prime p ∈ (m², 2m²) with m/p not a sum of 3 unit fractions. [arxiv](https://arxiv.org/abs/2511.16817v1) [arxiv](https://arxiv.org/abs/2511.16817)
  - Their abstract reports "extensive numerical calculations that support this assertion with the much smaller bound m≥20". The PDF text says m ≥ 19; this discrepancy is unresolved.
  - They also make Vaughan's density bound explicit in m: exceptions ≤ N/exp(C(log²N/φ(m))^{1/3}). [arxiv](https://arxiv.org/pdf/2511.16817)
  - **Consequence for Ember:** for numerators near 19–21 she should expect genuine exceptional primes in (a², 2a²). Her reduction theorems for a = 19 and 21 should record such n as certified exceptions, not as open classes.
- **Residue-class reductions and verified ranges for 5/n and general a:**
  - 5/n: the hard class is n ≡ 1 mod 5; a 2026 divisor-parametrization preprint (arXiv:2606.10922) develops a "fabfive" analogue [R]. [arxiv](https://arxiv.org/pdf/2606.10922)
  - arXiv:2602.20036 reports small thresholds for k = 5 (N₀ = 2, N₁ = 11) [R]. [arxiv](https://arxiv.org/html/2602.20036)
  - No authoritative source found for the current verified range of 5/n.
- **Four terms vs three:** the four-term (distinct) representation of 4/n follows from the greedy algorithm (erdosproblems.com, tag "unit fractions") [P]. [erdosproblems](https://www.erdosproblems.com/tags/unit%20fractions) The difficulty is entirely in three terms.

### 2.3 What Ember can certify, and the classification question

- **(a) Class identities:** certifiable. The complete classification of polynomially solvable Type I/II families is Elsholtz–Tao Prop. 1.9. Salez's seven modular equations (14a–c, 15a–d) are "complete" in the sense that a linear class not equivalent to one of them is not polynomially 3-Egyptian [P]. [arxiv](https://arxiv.org/pdf/1406.6307)
  - Recommended test: check her `gfam` space against Salez's seven equations and Elsholtz–Tao Prop. 1.9. Anything they contain that `gfam` cannot express is a gap.
  - I cannot verify from sources whether d = h1 n^i e^j / h2 exhausts Type I with one divisor condition: **no source found**.
- **(b) Finite ranges:** certifiable, but not a research frontier.
- **(c) Closure under divisors [P]:** if 4/p is solvable, so is 4/(kp). [arxiv](https://arxiv.org/pdf/1406.6307) [arxiv](https://arxiv.org/pdf/2509.00128) Hence **"every n with a prime factor outside the six square classes mod 840 is representable" is a theorem**: Mordell's identities plus multiplicativity. This is the strongest simple divisor-condition statement, and it is certifiable as a `theorem_multiples` claim over `cover`.
  - The residual is the set of n all of whose prime factors lie in the square classes. Those classes are 6 of the 192 coprime classes mod 840, i.e. a proportion of 1/32.
  - By standard Landau–Wirsing-type counting, that residual set has density zero. This is standard, but I did not retrieve a source stating it for this set.
- **(d) Divisor of a linear form with a congruence condition:** Salez's "modular equations" and the 2026 preprints (arXiv:2606.10922; arXiv:2605.23601 on "tame solutions") are of this type [R]. [arxiv](https://arxiv.org/pdf/2608.24035)

### 2.4 Route to a single square class

No known route reduces a full coprime square class to a finite computation: **no source found**. The two results that come closest are these.
- **Elsholtz–Tao:** almost all primes have at least (log p)^{0.549} solutions. This is an averaging result and not certifiable by families.
- **Salez's filters:** a certificate per n, not per class.

A 2026 preprint on n ≡ 1 mod 24 (arXiv:2608.24035, "Sieve dimension and search depth") appears to quantify search depth [R; not read].

### 2.5 Verification methods and value

- Salez's two-stage method (filters, then per-n modular certificates with odd m < 5000) is the model to copy.
- Ember's chunk method would need to process about 1.65×10^13 integers to reproduce 10^17: Salez's "16 512 783 482 880 integers including 51 732 427 squares". [arxiv](https://arxiv.org/pdf/1406.6307)
- That is months to years in standard-library Python on 4 cores (my estimate). **Extending the range is not worth doing.**
- Certifying the *structure* is worth doing:
  - reproduce R₇ exactly;
  - characterise which square-class n lack Type I solutions with small parameters;
  - publish the list with `nonrep`-style bounded certificates.

### 2.6 Beyond three terms

- **Bloom (2021):** solved the density version of Erdős's question. Any A with Σ_{n∈A} 1/n ≫ (log log log N / log log N) log N contains a solution of 1 = Σ 1/n_i. **Liu–Sawhney (2024)** improved the threshold to (log N)^{4/5+o(1)} [P] (erdosproblems.com). [erdosproblems](https://www.erdosproblems.com/tags/unit%20fractions)
- Finite open instances (Znám's problem, denominators in an interval, prescribed-form denominators): **not researched in this session; no source found.**

## Deliverable 3 — Calibration: certificate-checked computer results

| Result | Search / size | Certificate | Checker | Compute |
|---|---|---|---|---|
| Boolean Pythagorean triples: [1,7824] 2-colourable, [1,7825] not (Heule–Kullmann–Marek, SAT 2016, arXiv:1605.00723) | cube-and-conquer | DRAT, "almost 200 terabytes"; 68 GB compressed certificate | DRAT-trim; later a formally verified chain (Cruz-Filipe et al., arXiv:1610.06984) | 800 cores, ~2 days; 37,100 CPU-h solve and ~16,000 CPU-h verify [R, from Buss's slides] [ucsd](https://mathweb.ucsd.edu/~sbuss/ResearchWeb/Orevkov80_DRAT_2021/talkslides.pdf) |
| S(5) = 160 (Heule, AAAI 2018, arXiv:1711.08076) | 2,447,113,088 extreme colourings | DRAT/LRAT, "two petabytes" | ACL2-verified checker | >14 CPU-years solving; ~36 CPU-years checking | [arxiv](https://arxiv.org/pdf/1711.08076)
| Keller's conjecture, dim 7 (Brakensiek–Heule–Mackey–Narváez, IJCAR 2020; JAR 66, 2022) [nsf](https://par.nsf.gov/biblio/10188353-resolution-kellers-conjecture) | s = 6 case | DRAT, 224 GB | DRAT-trim, then **ACL2check** (not cake_lpr) | 43.27 / 77.00 / 81.85 CPU-h for s = 3, 4, 6 | [arxiv](https://arxiv.org/pdf/1910.03740)
| Packing chromatic number of Z² = 15 (Subercaseaux–Heule, TACAS 2023, arXiv:2301.09757) [researchgate](https://www.researchgate.net/publication/382587014_CaDiCaL_20) | D_{15,14,6} encoding [springer](https://link.springer.com/chapter/10.1007/978-3-031-30823-9_20) | DRAT 34 TB compressed; LRAT 122 TB | drat-trim, then **cake_lpr** [arxiv](https://arxiv.org/pdf/2301.09757) [springer](https://link.springer.com/chapter/10.1007/978-3-031-30823-9_20) | 4,851 CPU-h solving; 4,337 CPU-h checking | [arxiv](https://arxiv.org/pdf/2301.09757)
| h(6) = 30, empty hexagon (Heule–Scheucher, TACAS 2024, arXiv:2403.00737) [researchgate](https://www.researchgate.net/publication/379562604_Happy_Ending_An_Empty_Hexagon_in_Every_Set_of_30_Points) | O(n⁴)-clause CNF [cmu](https://www.cs.cmu.edu/~mheule/publications/ITP24.pdf) | LRAT, 180 TB [arxiv](https://arxiv.org/pdf/2403.00737) | **cakeLPR** concurrent with solving (CaDiCaL); encoding verified in Lean (Subercaseaux et al., ITP 2024, arXiv:2403.17370) [arxiv](https://arxiv.org/pdf/2403.00737) [arxiv](https://arxiv.org/pdf/2403.17370) | 17,300 CPU-h [cmu](https://www.cs.cmu.edu/~mheule/publications/ITP24.pdf) |
| Same, re-run with certificates streamed into Lean (arXiv:2607.00815, 2026) [arxiv](https://arxiv.org/pdf/2607.00815) | 312,418 cubes [arxiv](https://arxiv.org/pdf/2607.00815) | 174 TB LRAT streamed [arxiv](https://arxiv.org/pdf/2607.00815) | Lean kernel | cluster |
| R(3,8) = 28, R(3,9) = 36 [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | SAT+CAS | DRAT | per DS1.18 2.1.g [DuLBG] [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | not found |
| R(4,5) = 25 [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | — | HOL4 proof [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | HOL4 [GauB], per DS1.18 [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) | not found |
| R(5,5) ≤ 46 (Angeltveit–McKay 2024/26) [arxiv](https://arxiv.org/abs/2409.15709) | LP + large case check [arxiv](https://arxiv.org/abs/2409.15709) | none; "independently implemented by both authors" [arxiv](https://arxiv.org/abs/2409.15709) [researchgate](https://www.researchgate.net/scientific-contributions/Vigleik-Angeltveit-14990295) | two independent programs | not found |
| OGR-28 = 585 (distributed.net, 2022) | 524,091,443 stubs, each computed twice with identical node counts [distributed](https://blogs.distributed.net/) | no machine-checkable proof [arxiv](https://arxiv.org/pdf/2609.05421) | redundancy | ~8.5 years of volunteer compute [distributed](https://blogs.distributed.net/) |
| Hadamard orders 668…1964 (Aug 2026) [R] [wolfram](https://mathworld.wolfram.com/HadamardMatrix.html) | — | explicit ±1 matrices | HH^T = nI; checked by third parties per public repositories [R] [proof-watch](https://proof-watch.com/problems/hadamard) | not found |
| Lam's plane of order 10 (1989; SAT+CAS recertification by Bright et al.) | — | — | not re-verified in this session | not found |

**What an "end to end" result means today:** either an explicit object plus an exact check, or a refutation in LRAT checked by a verified checker (CakeML-based cake_lpr, ACL2) with the *encoding* verified in a proof assistant (Lean, as for h(6)). The encoding is now the weakest link; the solver is not. [dagstuhl](https://drops.dagstuhl.de/storage/00lipics/lipics-vol309-itp2024/LIPIcs.ITP.2024.35/LIPIcs.ITP.2024.35.pdf) [arxiv](https://arxiv.org/pdf/2403.17370)

## Deliverable 4 — The top five, one page each

### 4.1 No-three-in-line, n = 61

- **Search space:** 2n = 122 points, exactly 2 per row and 2 per column, on a 61×61 grid.
  - Under rct4 (90° rotation, with the diagonal handled separately) the free choices drop to about one quarter.
  - Prellberg notes that known large solutions have 90° rotational symmetry for even n, or 90° symmetry "except for the diagonal" plus two symmetric diagonal points for odd n. [arxiv](https://www.arxiv.org/pdf/2602.07751)
- **Symmetry classes:** Flammenkamp's classes (rot2, rot4, rct4, dia1, dia2, ort1, ort2). His pages list all solutions for n = 43, 45, 47 in rct4 and one n = 47 solution in dia2, alongside the rot4 solutions for 48, 50 and 52. [uni-bielefeld](https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html)
- **Checker:**
```
check_nothree(n, P):
  assert len(P)==2n, all 0<=x,y<n, distinct
  for each p in P:
    seen = set()
    for q in P, q != p:
      dx,dy = q-p; g = gcd(|dx|,|dy|); d = (dx/g, dy/g) normalised with sign
      if d in seen: return FAIL
      seen.add(d)
  return OK        # 122*121 ≈ 15k operations
```
- **Prior reach:**
  - Flammenkamp (JCTA 1992, 1998): all n ≤ 46, plus 48, 50, 52. [arxiv](https://arxiv.org/pdf/1406.6713) [arxiv](https://www.arxiv.org/pdf/2602.07751)
  - Prellberg (arXiv:2602.07751, QMUL, 2026): all n ≤ 60, by CP-SAT constraint programming, using 384 parallel runs on an AMD EPYC 9965 (192 cores) with a 10-day job cap. He reports: "We attempted n = 61 and n = 62 with the current method; however, no solution was found within 10^7 seconds, so we are leaving this as an open case." Ember therefore needs a better symmetry class or encoding, not just more time.
- **Day one:**
  1. Implement rct4 backtracking with row/column counters and incremental slope-blocking bitmasks (Python ints).
  2. Validate by reproducing n = 47 and 52.
  3. Run n = 61 (rct4) and n = 62 (rot4) on separate cores with randomised value ordering and restarts.
  4. Add a `nothree` claim kind with verdict re-check.

### 4.2 Multicolour 3-AP van der Waerden lower bounds W(r,3)

- **Search space:** r^N colourings. Restrict to colourings periodic mod a prime p, coloured by the class of i in the multiplicative group modulo index-r (Rabung-style power residues), then extend the ends.
- **Symmetry:** the reflection i ↦ N+1−i, and the multiplier group of Z_p.
- **Checker:**
```
check_ap3(N, col):  # col[1..N] in 0..r-1
  for a in 1..N: for d in 1..(N-a)//2:
     if col[a]==col[a+d]==col[a+2d]: FAIL
  OK   # N=3550: ~3.2M checks
```
- **Prior reach:** Heule (2017), then Alexey V. Komkov's note (arXiv:1701.05603, 2017), which used SAT-solver certificates to gain +1 to +4 over Heule (e.g. W(7,3) >342→>343, W(17,3) >3546→>3549). No later update found.
- **Day one:**
  1. Reproduce W(7,3) > 343 from a cyclic colouring.
  2. Run a tabu/SAT extension at both ends for r = 7, 8, 10, 11.
  3. Report any N beyond the record with an `apfree` certificate.
  4. Before claiming a record, check the current tables by hand: no 2018–2026 source was found in this session.

### 4.3 Ramsey lower bounds R(3,k), R(4,k), mid range

- **Search space:**
  - Circulant graphs on Z_n: connection sets S = −S ⊆ Z_n \ {0}, about 2^{n/2} of them.
  - For R(3,k), S must be sum-free mod n (triangle-free).
  - Target the DS1.18 Table IIa entries: R(3,16) ≥ 82, R(3,17) ≥ 92, R(3,19) ≥ 106, R(3,20) ≥ 111, R(3,21) ≥ 122, R(3,22) ≥ 131. [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
- **Symmetry:** multipliers u ∈ Z_n^* act on S, so search one orbit representative each. Beyond circulants, use Cayley graphs on non-cyclic groups (Exoo's Cayley colourings, DS1.18 2.2.d). [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
- **Checker:**
```
check_ramsey_circulant(n,S,s,t):
  adj = bitmask per vertex
  # by vertex transitivity, only cliques/independent sets containing 0 matter
  if max_clique_containing(0, adj) >= s: FAIL
  if max_clique_containing(0, complement) >= t: FAIL
  OK
```
  Use Östergård-style branch and bound on bitsets. Non-circulant graphs need a full search over all vertices.
- **Prior reach:**
  - Circulant constructions (Exoo; Kolodyazhny 2015–16; Kuznetsov 2016). [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
  - RL: Nagda–Raghavan–Thakurta 2026 improved R(3,13), R(3,18) and R(4,13–15). [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
  - R(4,20) ≥ 252 claimed (arXiv:2608.18169, 2026) [R]. [arxiv](https://arxiv.org/pdf/2608.18169)
- **Day one:**
  1. Reproduce R(3,16) ≥ 82 with an 81-vertex triangle-free circulant with α ≤ 15.
  2. Tabu over S for n = 82, 83.
  3. Then move to R(3,20) (n = 111).

### 4.4 Covering systems: minimum lcm for a given minimum modulus

- **Search space:**
  - For a candidate L, choose distinct divisors m > m₀ of L and residues r_m so the union covers Z_L.
  - A necessary condition is Σ 1/m ≥ 1.
  - arXiv:2607.19029 (2026) proves 10080 is the minimal lcm for minimum modulus 7. [arxiv](https://arxiv.org/html/2607.19029) The natural next case is m₀ = 8.
- **Symmetry:** translation (shift all residues) and the CRT product structure.
- **Checker:**
```
check_cover(L, [(r_i,m_i)]):
  assert all m_i | L, m_i distinct, m_i >= m0
  mark = bytearray(L)
  for (r,m): for x in range(r%m, L, m): mark[x]=1
  assert all(mark)      # L ≤ ~10^7 fine in Python
```
  For large L, check recursively along primes: the uncovered set within each class mod p must be covered by the moduli divisible by p.
- **Prior reach:**
  - Min modulus 42 (Owens 2014, master's thesis). Hough–Nielsen's journal version calls it a "Ph.D. dissertation" and gives BYU; arXiv:2607.19029 gives Wake Forest. [stonybrook +2](https://www.math.stonybrook.edu/~rdhough/covering_restricted.pdf) This conflict is unresolved.
  - Classification of distinct coverings with ≤ 10 moduli (arXiv:2208.09720, Integers 24A, 2024): all have minimum modulus 2. [colgate](https://math.colgate.edu/~integers/a1Proc23/a1Proc23.pdf) [arxiv](https://arxiv.org/pdf/2208.09720)
- **Day one:**
  1. Reproduce 10080 for m₀ = 7.
  2. Enumerate candidate L for m₀ = 8 by Σ_{d|L, d≥8} 1/d ≥ 1.
  3. Run a greedy + DFS residue assignment with the exact sieve as oracle.
- **Odd covering problem (context):** open [U]. Every distinct covering has a modulus divisible by 2 or 3 (Hough–Nielsen). A covering by odd squarefree distinct moduli is impossible (BBMST, Algebra Number Theory 15 (2021) 609–626). An odd covering's lcm must be divisible by 9 or 15 [P]. [scispace](https://scispace.com/pdf/the-erdos-selfridge-problem-with-square-free-moduli-3xh6gytk2u.pdf) [erdosproblems](https://www.erdosproblems.com/history/7)

### 4.5 Certified Schinzel exception sets

- **Search space:** for a/n = 1/x + 1/y + 1/z with x ≤ y ≤ z:
  - n/a < x ≤ 3n/a;
  - then for fixed x, y ≤ 2/(a/n − 1/x);
  - z is determined and must be an integer.
- **Checker:**
```
nonrep(a,n):
  for x in ceil_div(n+1,a) .. floor(3n/a):
    r1 = Fraction(a,n) - Fraction(1,x); if r1<=0: continue
    for y in max(x, ceil(1/r1)) .. floor(2/r1):
      r2 = r1 - Fraction(1,y)
      if r2>0 and r2.numerator==1 and r2.denominator>=y: return FALSE  # representable
  return TRUE   # certified: no representation
```
  Cost is roughly Σ_x 2/r1, about O(n log n / a); primes near 2a² are trivial.
- **Prior reach:** the numerics of Pomerance–Weingartner (arXiv:2511.16817), whose abstract reports calculations supporting exceptional primes in (m², 2m²) "with the much smaller bound m≥20".
- **Day one:**
  1. Add `nonrep` with an independent verdict implementation.
  2. For a = 7…30, compute E_a(10^6) and certify every member.
  3. Cross-check against her existing open classes.
  4. Publish the table as a data artefact.

## Deliverable 5 — Claims in the inquiry that are wrong or outdated

1. **"Smallest orders with no known Hadamard matrix (668, 716, 892…)":** outdated. On 12 August 2026 Levent Alpöge announced on X constructions for all 12 open orders below 2000, made with P. Voinov, S. Reynolds-Haertle and Claude. MathWorld: "Epoch AI (2026) reported that L. Alpöge, P. Voinov, and S. Reynolds-Haertle had announced constructions obtained with Claude". Epoch's attribution is "provisional" [R]. Order 668 had been the smallest open order since Kharaghani–Tayfeh-Rezaie's H(428) (J. Combin. Des. 13, 2005). The Eliahou 64-modular 668 matrix (AJC 93(2), 2025) [uq](https://ajc.maths.uq.edu.au/pdf/93/ajc_v93_p422.pdf) is superseded. The next open order is ≥ 2000; no source found for which one.
2. **"No-three-in-line: is n = 47 still open":** no. Prellberg (arXiv:2602.07751) gives all n ≤ 60; smallest open n = 61. [arxiv](https://www.arxiv.org/pdf/2602.07751)
3. **"OGR-28 (verify; completed?)":** completed 23 November 2022; length 585; marks 0 3 15 41 66 95 97 106 142 152 220 221 225 242 295 330 338 354 382 388 402 415 486 504 523 546 553 585 (distributed.net). [distributed](https://blogs.distributed.net/)
4. **"R(3,10) (36 ≤ …)":** wrong. 40 ≤ R(3,10) ≤ 41 (Angeltveit improved the upper bound from 42 to 41; DS1.18). [researchgate](https://www.researchgate.net/scientific-contributions/Vigleik-Angeltveit-14990295)
5. **"R(5,5) ≤ 46, Angeltveit–McKay 2024":** correct. arXiv:2409.15709 (v2, September 2025); J. Graph Theory 2026, doi:10.1002/jgt.70029. [arxiv](https://arxiv.org/abs/2409.15709) [arxiv](https://arxiv.org/pdf/2604.21187) DS1.18 dates the result to 2023. [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
6. **"Cap 236 (Edel)":** the 236-cap is due to Calderbank–Fishburn (1994) and is tabulated by Edel. Upper bound 291 (2018 tables; ILP). [tudelft](https://repository.tudelft.nl/file/File_03ab6991-f67e-48c7-87cd-bf4f2a0237d4)
7. **Erdős–Straus range "to 10^17":** superseded by a 10^18 claim from Spiridon Mihnea and Dumitru C. Bogdan (arXiv:2509.00128, August 2025) [R, with a flagged gap].
8. **Obstruction lemma as Ember's own result:** it is Schinzel's theorem (Funct. Approx. 28, 2000) and Elsholtz–Tao Prop. 1.6. [arxiv](https://arxiv.org/pdf/1406.6307) [arxiv](https://arxiv.org/pdf/1107.1010)
9. **"Elsholtz–Tao lower bounds for f(p)":** these are lower bounds on average and for almost all p; there is none for every p. [arxiv](https://arxiv.org/pdf/1107.1010)
10. **Keller dim 7 checker:** ACL2check, not cake_lpr. cake_lpr was used for packing chromatic Z² and h(6). [arxiv +3](https://arxiv.org/pdf/2301.09757)
11. **Owens (2014):** thesis type and institution are inconsistent across sources (master's/BYU vs Ph.D.; Wake Forest in arXiv:2607.19029). [stonybrook +2](https://www.math.stonybrook.edu/~rdhough/covering_restricted.pdf)
12. **R(4,6) ∈ [36,40]:** correct (DS1.18 Table Ib). **R(4,7):** [49,58]. **R(5,6):** [59,85]; Exoo improved the lower bound in 2023. [rit](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
13. **Three cubes below 1000:** 114, 390, 627, 633, 732, 921 and 975 remain open (secondary sources; no primary list retrieved) [R]. [handwiki](https://handwiki.org/wiki/Sums_of_three_cubes) [grokipedia](https://grokipedia.com/page/Sums_of_three_cubes)
14. **S(6) upper bound 1836:** not re-verified in this session. It is consistent with S(n) ≤ R_n(3) − 2 (Eliahou, arXiv:1912.05353), [arxiv](https://arxiv.org/pdf/1912.05353) but I did not confirm the current R_6(3) upper bound.

## Caveats

- Items not researched in this session carry "no source found": R(3,3,4) = 30, R(3,3,5), R(4,4,4), WS(5), W(2,6), W(3,4), Heilbronn optima, kissing numbers in dimensions 5–7, odd perfect numbers, Lehmer's totient problem, Erdős–Moser, Sierpiński/Riesel candidates, Lean Mathlib coverage of unit fractions and covering systems, and Lam's plane recertification. I have not asserted values for these.
- The August 2026 Hadamard constructions, the 10^18 Erdős–Straus verification and several 2026 arXiv preprints are unrefereed.
- **Hardware limit:** Ember's standard-library Python sets a hard ceiling. Any negative result with a proof above ~10^7 LRAT lines (very roughly) is beyond her independent checker. Her realistic product is positive constructions and small certified refutations.