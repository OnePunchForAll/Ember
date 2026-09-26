# Deep research inquiry: what open problems can Ember solve end to end, and how

*Give this whole document to Claude Fable 5.1 (chat) as a deep-research task. It
is written by the Claude Code session that builds Ember, for a research
session that has web access and time. Ember herself never reads it: she is a
non-LLM, offline research agent, and everything that reaches her must arrive
as code, a claim kind with a checker rule, or a stated problem in her
library. The answers wanted are facts with sources, rankings with reasons,
and encodings concrete enough to implement. Where a fact cannot be
established, say so; a wrong citation costs more than a gap.*

## 0. The request in one paragraph

Find the open mathematical problems that a machine like Ember, described
below, could actually settle or measurably advance end to end, in the only
way she can: by producing a finite certificate that an exact, independent
checker admits. Rank them by the likelihood that bounded structured search
plus exact checking on one machine, over days, beats the current record, and
for each give the statement, the certificate, the best known result with its
source, the reasons prior attempts stopped where they did, a concrete
encoding or construction strategy, and the compute it would take. Separately,
settle the exact status of the unit-fraction conjectures she already works on
(Erdős–Straus, Sierpiński, Schinzel), what is provable by her means and what
is provably not, and what the frontier of computer-assisted, certificate-
checked results in combinatorics and number theory looks like today, so that
her next instruments are built toward problems she can finish.

## 1. What Ember is, precisely

Ember is a Python program (about 30 modules, standard library only, no
network, no model) that runs one call at a time on a JSON instance state and
a task, and writes the state back. She has:

- **A typed move language of 222 operators** in ten modules (sequences,
  polynomials, orbits, unit fractions, Collatz-type maps, matrices,
  arithmetic, words, and two families of "window" tools over discrete and
  real mathematics), each declared with the kinds it consumes and produces
  and its directions among N (propose), W (refute or extract a residual), S
  (bind or check against the original question), E (transfer between
  questions). A bench executes every operator on fixtures and records the
  directions observed.
- **A separate checker** (`lexicon_check.py`, exact rational arithmetic) that
  admits or refuses every claim kind. Nothing enters her state as a result
  unless the checker admits it; operators only propose. Claim kinds that
  matter here: `cover` (a covering of residue classes modulo M by polynomial
  families for a/n = 1/x + 1/y + 1/z, each family an identity in n placed on
  a class, verified as a polynomial identity), `finite` (an exact
  verification of every n in a range, by cover class, family divisor,
  witness, or divisor), `theorem` (a reduction: every n not in the open
  classes and below the range is done), derivations (`range_extend` chunks
  past the checker's range bound, `range_union`, `theorem_range`,
  `theorem_multiples` closing a theorem under multiplication of n by
  divisors, `theorem_families`, `composite_range`, `residual_predicate`,
  `residual_break`), `dfam` and `gfam` (divisor families: for every n with a
  divisor q of a linear form A n + B in a residue class, a/n is the sum of
  three unit fractions with denominators given by an identity; `gfam` is the
  general family d = h1 n^i e^j / h2 in the Type I identity with x = n e,
  e = (q + 1)/a, y = (n e + d)/q, z = n e y/d, of which plus, times, pair and
  square are four points), `nofamily` walls (a certificate that no
  polynomial family of bounded parameters covers a class), `obstruction` (a
  lemma that no polynomial family reaches a coprime square class), `descent`
  and `dcover` for Collatz-type maps, `cycle`, `exclusion`, `invariant`, SAT
  and set-system window claims (`value`, `witness`, `proof`) and others.
- **An independent verdict** (`tools/verdict.py`) that re-verifies every saved
  claim with its own code and returns one bit to her.
- **An autonomous agent** that chooses moves by observed success and cost
  (a scheduling policy, never a belief), runs anytime moves in slices,
  retires strategies that fail, accounts every refusal by reason, mines its
  own residuals, and invents macros. **Her own loop** runs a library of 148
  stated problems (18 open, 5 closed calibrations, 125 windows) call after
  call, choosing by her own records.
- **What she has proved**, all verified independently: for Erdős–Straus
  (4/n) and Schinzel's numerators 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18,
  19, 21 and Sierpiński's 5/n, reduction theorems to finitely many open
  residue classes at moduli up to 83,160, every open class a coprime square
  class where her obstruction lemma shows no polynomial family exists;
  verified ranges to about four million with the range closed under
  multiples; divisor families, now found by her own search over the general
  family space, that represent 62 to 90 percent of the numbers she
  otherwise had to witness; descent covers for the Collatz map to 2^18; and
  windows (exact finite computations) on every catalog problem.
- **What she cannot do**: read prose, use a model, prove anything her checker
  has no rule for, or state an infinite claim without a finite certificate
  whose rule the checker has. Every new claim kind needs (a) a checker rule,
  (b) a verdict rule written independently, (c) a package check, and each is
  a few hundred lines. She runs on one machine (four cores), a call in
  seconds to minutes; a scan of her library is a few hours.

The consequence for open problems: she can settle a problem end to end only
when the answer is a finite object an exact checker can verify (a
construction, a coloring, a matrix, a covering system, a counterexample, a
certificate of a search's completeness in a form like a DRAT proof), or when
an infinite statement reduces by a rule she has to such an object. She
cannot finish Erdős–Straus by families: her own lemma says the square classes
are out of reach of polynomial identities, and a cover of all classes is
exactly what the conjecture needs.

## 2. Questions on the unit-fraction problems she already holds

Answer each with sources (DOI or arXiv identifier, author, year).

2.1 State exactly what is proved for 4/n = 1/x + 1/y + 1/z (Erdős–Straus):
the residue-class results (Mordell's classes modulo 840; later refinements),
the verified numerical range (the largest N with a published verification,
and by whom), the density results (Vaughan 1970; Elsholtz–Tao 2013 on the
number of solutions f(n), including their statements about solutions of Type
I and Type II, their lower bounds for f(p), and what they prove about
polynomial families: is it a theorem that no polynomial identity covers the
quadratic-residue classes modulo 840, and where is that stated?).

2.2 The same for 5/n (Sierpiński) and for Schinzel's conjecture that a/n is
a sum of three unit fractions for all n beyond some N(a): which a have
published residue-class reductions, which have verified ranges, and what is
known about N(a) (is it known that N(a) exists for every a? For which a is
the conjecture proved outright?). Distinguish the three-term problem from
the four-term one (for which results are complete or nearly so).

2.3 Which *partial* theorems about these conjectures are of the form Ember
can state and certify: (a) "for every n in residue class r modulo m, a/n has
a representation", by a polynomial identity or a divisor family; (b) "every
n below N has one", by exact computation; (c) "every n with a divisor in a
class", by closure; (d) statements involving a divisor of a linear form in n
with a congruence condition on the divisor (her general families). Is there
a published classification of all families of type (d), or of all "Type I"
and "Type II" parametrizations with a free parameter (Mordell's book,
Schinzel, Elsholtz–Tao section on parametrizations)? Does her general family
space (d = h1 n^i e^j / h2) exhaust the Type I parametrizations with one
divisor condition, and what lies outside it (two divisor conditions, Type
II with a common factor, families indexed by a divisor of a quadratic form)?

2.4 Is there any known route to a *complete* proof for a single open
residue class (a coprime square class) that reduces to finite computation?
For example, results of the form "if n ≡ 1 (mod 840) and n has a prime
factor in a set S then 4/n is representable", so that the residual is the n
all of whose prime factors avoid S; sieve statements bounding such n; the
Elsholtz–Tao observation that a positive proportion of primes in the square
classes are handled by which families. What is the strongest statement of
the form "every n in class r with a prime factor p ≡ c (mod t) is
representable" in the literature, and is it certifiable as a divisor family
in her sense?

2.5 Where do the numerical verifications stand, with the method: Swett's
verification (to 10^14), Salez (to 10^17 in 2014, on the arXiv), and any
later; what representation search did they use (the "first divisor"
methods), and would her chunk method (cover class, then divisor family, then
witness) reproduce their range at what cost? Is there value in her
extending a verified range past 10^17 (no, if it is only more of the same;
say so if that is the honest answer) versus certifying the *structure* of
the residual (which n in the square classes have no Type I representation
with small parameters, and are these characterized)?

2.6 Beyond three terms: which unit-fraction problems have an open case that a
finite certificate settles, for example the Erdős–Graham questions on
denominators in a set, the "Egyptian fraction with denominators of a given
form" problems, the problem of 1 = Σ 1/x_i with x_i in a prescribed set
(Bloom 2021 settled the density version; what finite instances remain),
the "sum of unit fractions with distinct denominators in an interval"
problems, and the Znám and Sierpiński-type problems. For each open finite
instance: statement, best known bound, source.

## 3. Open problems whose constructive side is a finite certificate

This is the heart of the inquiry. For each family below, establish the
current record with a source, whether the next case is open, the size of the
object, the method that set the record, why it stopped there, and whether an
exact checker in Ember's style (rational arithmetic, no floating point, a
few hundred lines per rule) can verify a candidate. Then rank all candidates
across families by the chance that structured search on one machine over
days finds a new object. Be concrete about search: symmetry classes to
restrict to (cyclic, circulant, two-circulant, difference-set based, group
developed), local search versus SAT versus algebraic construction, known
heuristics that produced the current records, and the fraction of the space
they explored.

3.1 **Covering systems of congruences.** Minimum modulus: Nielsen's covering
with least modulus 40 (2009), Owens's with 42 (2014); the upper bounds of
Hough (2015) and Balister–Bollobás–Morris–Sahasrabudhe–Tiba (2022, minimum
modulus at most 616,000). Is a distinct covering system with least modulus
43 or more known today? What is the structure of the record constructions
(which moduli, how the residues were chosen, computer search over what
space)? The odd covering problem (Erdős–Selfridge: a covering with distinct
odd moduli, all greater than 1) and the squarefree variant: status, partial
results (coverings with odd moduli that are not distinct, or with one
modulus repeated), and the best obstruction results. A covering system is a
certificate Ember can check exactly (she has a coverings window); is a search
for least modulus 43 realistic, and how did Owens search?

3.2 **Cap sets.** The exact maximum size of a cap in F_3^n is known for
n ≤ 6 (20, 45, 112 for n = 4, 5, 6); for n = 7 the best lower bound was 236
(Edel) and the upper bounds have been lowered (state the current values with
sources, including any 2023–2025 results by Tyrrell or others and any SAT-
or search-based improvements). A cap of size 237 in F_3^7 is a finite object
checked exactly (no three points on a line: for each pair, the third point
on their line is not in the set). What search found 236, what symmetry did it
assume, and is a larger cap plausible by local search, SAT, or lifting from
n = 6 and n = 5 caps with product constructions?

3.3 **Schur numbers.** S(5) = 160 (Heule 2017, SAT with a 2-petabyte proof);
S(6) bounds (lower 536 by Fredricksen–Sweet 2000, upper 1836 or better;
verify). A sum-free 6-coloring of [1, 537] would be a new lower bound, a
finite object checked exactly. How were the lower bounds found, what
structure do the record colorings have (palindromic, built from S(5)
colorings), and what would a search for 537 look like? Weak Schur numbers
and the state of WS(6), WS(7).

3.4 **Van der Waerden numbers.** W(2,6) = 1132 (Kouril–Paul 2008), the
lower bound for W(2,7) (3703, Rabung's cyclic zero-sum construction; any
improvement), W(3,4) = 293 (Kouril), the small mixed cases still open, and
the general lower-bound constructions (Rabung, Blankenship–Cummings–Taranchuk
2018 for W(2,k)). A 2-coloring of [1, N] with no monochromatic 7-term
arithmetic progression for N ≥ 3704 would be a new lower bound. Which cases
are within reach of SAT or structured search on one machine?

3.5 **Ramsey numbers, lower-bound side.** R(5,5) ∈ [43, 46] (Angeltveit–
McKay 2024 upper bound; verify), R(4,6) ∈ [36, 40], R(3,10) (36 ≤ ... state
current), R(4,7), R(5,6), the multicolor R(3,3,4) = 30 (Codish et al. 2016)
and R(3,3,5), R(4,4,4) bounds. A graph on 43 vertices with no K5 and no
independent 5-set would raise R(5,5)'s lower bound: is that plausible by
search (Exoo's methods, circulant and Cayley graph searches, simulated
annealing), and which cases had the least search effort?

3.6 **Hadamard matrices.** The smallest orders with no known Hadamard matrix
(668, 716, 892, ... verify the current list after the 428 construction of
Kharaghani–Tayfeh-Rezaie 2005 and later work); the constructions used
(Williamson, Turyn type, two-circulant core, Goethals–Seidel), their search
spaces, and what an exact checker verifies (HH^T = nI over the integers).
Also skew-Hadamard orders still open, the smallest, and D-optimal designs.

3.7 **Costas arrays.** Orders with no known Costas array (32 and 33 the
smallest; verify), the exhaustive results (all Costas arrays enumerated up to
order 29 or 30 by Drakakis et al.), the algebraic constructions (Welch,
Lempel–Golomb) and why they miss 32 and 33, and the chance of a heuristic
search finding one (with the estimated density arguments).

3.8 **Golomb rulers and difference sets.** Optimal Golomb rulers known to 27
marks (distributed.net, 2014) and 28 (verify; OGR-28 completed?), the
projective-plane constructions, and open cyclic difference set existence
questions with small parameters (the Lander conjecture cases, the smallest
open (v, k, λ)); planar difference sets of non-prime-power order (the prime
power conjecture) and the smallest orders where existence is open after
exhaustive searches.

3.9 **Geometric and combinatorial small cases.** The no-three-in-line
problem: 2n points known for n ≤ 46 and n = 48, 50, 52 (Flammenkamp); is
n = 47 still open, and how large were the searches? The empty hexagon number
h(6) = 30 (Heule–Scheucher 2024, SAT) and what remains open in Erdős–
Szekeres-type finite cases; the happy ending problem's small cases; the
Heilbronn triangle problem for small n (exact optima known up to n = 7 or
8; state); the kissing number in dimensions 5, 6, 7 (bounds); packing and
covering small cases with verified certificates (the packing chromatic number
of Z^2, Subercaseaux–Heule 2023).

3.10 **Number-theoretic finite searches with certificates.** Lehmer's
totient problem bounds; the search for odd perfect numbers (bounds and the
"web of conditions"); Erdős–Moser; the Erdős–Selfridge–Sierpiński prime
searches (the remaining Sierpiński and Riesel candidates, and why a single
machine cannot compete with PrimeGrid); Egyptian-fraction denominator
problems; the smallest open cases of Waring-type problems with exact
certificates; sums of three cubes (the remaining n below 1000 after 42 and
114 were found; the search is a lattice sieve, not a certificate problem,
but a found solution is a certificate). For each, the honest verdict on
whether one machine over days has any chance.

3.11 **Problems recently settled by exact computer search with independently
checked certificates**, as calibration: the Pythagorean triples problem
(Heule–Kullmann–Marek 2016), Schur number five (2017), Keller's conjecture in
dimension 7 (Brakensiek–Heule–Mackey–Narváez 2020), the packing chromatic
number of the square grid (2023), the empty hexagon number (2024), the
Ramsey number R(3,3,4), R(5,5) ≤ 46, the Collatz-type or covering-system
results, Lam's projective plane of order 10 (1989, and its later
certification). For each: the size of the search, the certificate format
(DRAT, LRAT, a construction), the checker that verified it (drat-trim,
cake_lpr, a formally verified checker), and the compute used. This tells us
what "end to end" means today and what a checker must accept.

## 4. Questions on method: certificates, encodings, checkers

4.1 For search problems whose *negative* answer matters (no object exists),
what certificate formats let an independent checker verify completeness of
a search: DRAT and LRAT proofs for SAT, their sizes for problems of the
scale above, verified checkers (cake_lpr, the Isabelle and Coq checkers),
and the cube-and-conquer method. Could Ember emit a DRAT proof from a SAT
tool she already has, and check it with an independent checker in her
verdict, and how big are proofs for the smallest open cases in section 3?

4.2 For the *positive* side (a construction), what exact checks are
standard, how small are they, and which are already in her language (sum-free
coloring: every x + y = z check; cap set: line check; Hadamard: integer
matrix product; covering system: residue coverage up to the lcm; Costas
array: distinct difference vectors; Ramsey graph: clique and independent
set search of bounded size, which is itself a small exhaustive search the
checker must do exactly).

4.3 Symmetry and structure: for each candidate in section 3, the algebraic
constructions that produced records (cyclotomic classes, difference sets,
Paley-type graphs, circulant matrices, group-developed designs,
Rabung/Blankenship-type zero-sum colorings) and how far exhaustive or
heuristic search within those classes has gone, so Ember's search can start
where the literature stopped rather than where it began.

4.4 Local search and SAT practice: which solvers and encodings set the
recent records (CaDiCaL, Kissat, the SAT encodings of Heule for Schur and
van der Waerden, tabu search for Ramsey graphs by Exoo, simulated annealing
for Costas), typical wall-clock times, and the encoding tricks that made the
difference (symmetry breaking, incremental extension, restriction to
palindromic or cyclic solutions).

4.5 Formal proof: the state of Lean's Mathlib for unit fractions and
covering systems, whether a checker's soundness of Ember's size has been
formalized anywhere (verified checkers for specific certificate formats),
and what it would take to certify one of her claim kinds in Lean so that an
end-to-end result is a theorem accepted outside her.

## 5. What to return

1. A ranked table of at most twenty open problems (from sections 2 and 3)
   with columns: problem, exact statement of the open case, the certificate
   (what finite object and what check), best known result with source, size
   of the object, method that set the record and the space it searched,
   estimated chance that one machine over days improves it (with the
   reasoning, not a number alone), the encoding or construction strategy
   to try first, and what checker rule Ember would need.
2. The exact status of the unit-fraction conjectures (section 2) with
   sources, including a plain statement of what is provable by residue
   classes and families and what is not, and the strongest divisor-condition
   theorems in the literature in a form she could certify.
3. The calibration list of certificate-checked computer results (3.11) with
   sizes and checkers.
4. For the top five problems of the table, a page each: the search space,
   the symmetry classes, the exact checker in pseudocode, prior attempts
   with their reach, and a day-one plan.
5. A list of the claims in this document you found to be wrong or outdated,
   with the correction and its source.

Style: dense, factual, sourced. Prefer primary sources (arXiv, journals,
the OEIS with sequence numbers, the authors' pages). Mark every statement as
proved, verified computationally, conjectured, or unknown. Where the
literature is silent, say "no source found" rather than guessing. Numbers
with their year: records move.
