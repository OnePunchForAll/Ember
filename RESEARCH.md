# Reasoning abilities she could hold next

A research note, written on 25 September 2026 after the third round of
instruments (commit 83acffa, fingerprint e05a320c). It asks what *reasoning*
Ember lacks, as distinct from what mathematics she lacks, and how each ability
would be installed in her language, checked by her checker and by the
independent verdict, and measured. The evidence is her own records: the scans,
the two contests and their transfers, the profiles of her rounds, and the
preregistered rounds of the third family tier, which found a defect she could
not see. CAMPAIGNS.md holds the record; this note holds the reading of it.

## 1. How the reading was done

Three sources were read against each other. First, her records: which moves
her rounds spend their time on (profiles of a 13/n and a Collatz round), what
her chunk proofs carry (family entries against witnesses, by problem), what her
reports show and what they hide (a refused claim is a `success: false` row with
no reason), and what her ranking chose (the gain rule and its rounds). Second,
the mathematics of the problems she holds: every solution of a/n = 1/x + 1/y +
1/z with n prime is of Type I (n | x) or Type II (n | x and n | y), and her
family grammar now spans both up to a search bound, so what remains for her on
these problems is measured below rather than guessed. Third, the reasoning
methods the literature names, mapped onto what she has: Pólya's plan, auxiliary
problem, working backwards and looking back; Lakatos's lemma incorporation;
clause learning, abstraction refinement and anytime search from automated
reasoning; and the bandit view of strategy choice. For each method the question
was whether she has it, in what form, and what its absence costs her by her
own records.

## 2. What she reasons with now

Her language has 219 typed operators over four directions (propose, refute,
bind, transfer) and 376 moves in the pyramid; a doctrine scheduler that ranks
strategies by measured success and cost, retires the ones that only fail,
proposes compositions from signatures, and chooses problems by the size and
speed of recent gains; anytime moves that breathe, wait, resume and, since the
third round, finish with what they have; residuals that record attempts;
derivations (union, extension, extension with a computed part, closure under
multiples, composition with families, the square of a range); covers,
theorems, walls, the square-class lemma, patterns; windows (finite exact
questions about catalog problems) and her own widening of settled ones;
relevant fingerprints, a forgetting order, and her own loop. The reasoning
methods this amounts to: case analysis by residue class with refinement by
measured yield (abstraction refinement); learned nogoods (walls) with implied
ones (the lemma); generalization of witnesses into families and of families
into divisor families; bounded search with anytime interruption; scheduling
under uncertainty; and inductive statements over ranges with certified
composition. What she does not have is listed in section 4.

## 3. The frontier of her mathematics on unit fractions

For n prime, a solution of a/n = 1/x + 1/y + 1/z has n dividing at least one
denominator; with n | x only it is Type I, x = ne, y = (ne + f)/q, z = ney/f
with q = ae - 1 and f | e^2; with n | x and n | y it is Type II, which the pair
families state. Her classical families fix e and f; her divisor families leave
q free with f = he, e/h or e^2/h, and with plus, times and pair the one-divisor
grammar is complete: for f | e^2 the condition q | ne + f is a divisibility of
n + h, hn + 1 or ahn + 1. So a prime she still witnesses is one for which no
family up to her h bound applies, and a prime she cannot witness either would
be a counterexample to the conjecture. Her residual is therefore the frontier
of the conjecture at a bounded search depth, and the question is how the
residual shrinks with depth. Measured on the primes her rerun still witnessed
(state of the fourteen rounds, fingerprint e05a320c, the chunks past one
million), with my own code, the least h at which any family takes them:

| a | witnessed | by h <= 7 | <= 15 | <= 30 | <= 60 | beyond 60 |
|---|---|---|---|---|---|---|
| 13 | 6,108 | 5,704 | 5,999 | 6,067 | 6,090 | 18 |
| 19 | 9,321 | 7,166 | 8,405 | 8,840 | 9,025 | 296 |
| 21 | 2,637 | 731 | 1,622 | 2,024 | 2,208 | 429 |
| 18 | 3,269 | 687 | 1,787 | 2,341 | 2,608 | 661 |

Each doubling of h takes a few percent more; on 21/n and 18/n a fifth of the
residual lies past h = 60. Their residues modulo a and modulo 8 are spread
over the classes (for 21/n: 881 of 2,637 are 1 mod 21, then 496, 464, 321),
so no congruence predicate characterizes the residual: it is a sieve set,
what is left when every divisor condition fails. Two conclusions. Search depth
has diminishing returns and is a computation she already regulates by yield;
it is not a reasoning ability. And nothing in the residual's shape suggests a
new family; what would move the conjecture is analytic (the density bounds of
Elsholtz and Tao) and outside a language of checked finite claims. Her next
gains on these problems are range and depth, both hers to spend; the reasoning
abilities below are about what she can see, state and decide, not about a
method she is missing here.

## 4. Abilities to install, in order

Each entry names the gap and its evidence, the design in her language, how it
is checked, what it should gain, and what it costs.

### 4.1 Refusal accounting and self-diagnosis

*Gap.* A claim her checker refuses leaves a `success: false` row with no
reason and no count. The preregistered rounds of the third tier found that on
five problems every chunk proof after the twenty-fifth family was refused
whole (the bound on the shapes a proof may name), and her rounds ended with
"no untried move" as if nothing were wrong; the defect was visible only to my
check outside her. She has failure mining in the loop's sense (I read her
profiles); she does not mine her own refusals.

*Design.* The runtime keeps, per round, a table of refused claims by
(strategy, claim kind, refusal reason), with the first refused object's
identity; the report carries it (`refusals`) and the rounds ledger keeps the
counts per round. A strategy whose claims are refused at a rate above a bound
over a window of rounds is retired for the problem like one that only fails,
with the reason kept, and the scan's ranking treats a problem whose last round
refused more than it admitted as a problem waiting for an instrument (like an
exhausted one), naming the reason. A `diagnosis` section of the report, for a
round without gain, states what was exhausted, what was refused and why, the
residual's size, and which instrument a fixed table names for that reason.

*Check.* A package check plants a refusal (a proof past the shapes bound) and
finds it in the report and the ledger with its reason; the retirement fires
on a synthetic history. No claim is involved, so no verdict rule.

*Gain.* The defect class the rounds found becomes visible in her own report
on the round it happens; a strategy that cannot get its claims admitted stops
spending. *Cost.* Small: the checker already raises the reason; the runtime
already sees every refusal.

### 4.2 Residual mining: inductive statements over her own residual, with falsifiers

*Gap.* She cannot say what her residual looks like. The witnessed numbers in
her proofs are a set she computed; a statement about that set (every one of
them satisfies P) is a finite exact claim her checker can decide, and the
conjecture that P characterizes the residual on the next range is a window
she can pose. Section 3 shows the residual is a sieve set; predicates worth
testing are sieve predicates (on the factorizations of n + h, hn + 1 and
ahn + 1), not congruences.

*Design.* A predicate grammar over n: the residue of n modulo m for m | M; for
each linear form L in {n + h, hn + 1, ahn + 1} and modulus t in {a, ah}, the
residues modulo t of the prime factors of L(n), and whether L(n) is smooth or
rough at a bound. An operator `egypt_residual_profile` evaluates the grammar
over the witnessed numbers of the admitted proofs and over an equal sample of
represented numbers, and states as a `pattern` claim (a new pattern rule,
`residual_predicate`) every predicate the residual satisfies entirely and the
sample satisfies rarely; the claim names the proofs by identity, the checker
rebuilds the witnessed set from them and evaluates the predicate. A falsifier
window (`residual_predicate` family of the window tools) asks whether the
predicate holds for the witnessed numbers of the next chunk; a failure refutes
the pattern claim and the refutation is kept. Predicates that survive are what
she can offer to a reader as the shape of the residual, and what a new family
shape would have to reach.

*Check.* The checker's pattern rule and a verdict rule of its own; a package
check with a planted residual whose predicate is known, and a planted
counterexample refuting it.

*Gain.* Her residual becomes a stated object with tested properties; a
scheduling signal too (a predicate that fails is a sign a family may apply).
*Cost.* Medium: a predicate grammar, one pattern rule, one window family,
their verdict rules.

### 4.3 Goal-directed family search: aim where the witnesses are

*Gap.* Her family searches on a level are ordered by the doctrine score over
classes, not by where the numbers she had to witness lie. On 19/n her rerun
witnessed 944 numbers in ten chunks; the classes modulo 27,720 they fall in
are known from the proofs and are not used.

*Design.* The `eclass` targets of the open level get a weight from the count
of witnessed numbers in their class over the admitted proofs (the residual's
mass), and the scheduler's tie-breaking among fresh moves on classes uses it;
`egypt_choose_lift` already chooses the next prime by exact yield, and the
same mass decides which refined classes are swept first.

*Check.* A package check with two open classes of unequal witnessed mass:
the heavier is swept first. *Gain.* Family searches spend where a family would
save the most witnesses. *Cost.* Small.

### 4.4 Search depth as her own parameter, by yield

*Gap.* The witness search's bound (`max_excess`, four times 256a) and the
family list's extension rule are fixed policies; the depth curve of section 3
says each doubling of h buys a few percent, and the witness bound decides
when a number goes to a residual instead. She extends h by yield already; the
witness bound is mine.

*Design.* Per problem, the witness search bound rises by a factor when a
round's residual (numbers with no witness within the bound) is nonempty and
the previous rise paid (the residual shrank by more than a fraction), and
falls when a round finds every witness well within it. Recorded per problem
in the rounds ledger with the yields, like the family extension. *Check.* A
package check on a synthetic history. *Gain.* Fewer residuals from bound
exhaustion on problems like 18/n; no wasted depth on 4/n. *Cost.* Small.

### 4.5 Adaptive chunk size from the measured cost per number

*Gap.* A chunk is as long as the base range; with the re-priced units and the
checkpoints a chunk that outruns its slice now states a prefix, but the
prefix and the rest are two claims where one would do.

*Design.* The chunk length is the base range length scaled so that, at the
seconds per number of the last admitted chunk of the problem, a chunk fits
in a slice; bounded by the checker's range bound. *Check.* A bench fixture
with a measured cost. *Gain.* Fewer settled prefixes, fewer derivation rows.
*Cost.* Small.

### 4.6 Lemma import across problems

*Gap.* The square-class lemma (no classical family reaches a coprime square
class) is derived per problem; the divisor families are stated per problem;
the composition rules are shared code but the claims are not shared. Doctrine
5 (reuse A => C where B supplies A) is what an E move across records would
do: import an admitted claim from another problem's record, re-checked here.

*Design.* An operator that, for a claim kind with a question-independent
statement (the lemma with its modulus, a divisor family with its a), reads
the other live records for admitted claims that bind to this question and
proposes them; the checker admits them as any claim. *Check.* A package check
with two problems sharing a lemma. *Gain.* The re-check wave after a code
change spends less on what another problem already holds; a lemma found once
is held everywhere it applies. *Cost.* Medium (records are read by the goal,
not the runtime, today).

### 4.7 Budget allocation across problems by predicted marginal yield

*Gap.* Every call gives a problem the same allowance (10,000 moves, the work
bound). Her rounds on 5/n gain thousands in a thousand seconds; her rounds on
11/n gain a hundred in fifty. She chooses the problem; she does not choose
how long to stay.

*Design.* The scan's allowance for a call becomes a function of the chosen
problem's recent yield curve (gains per second over the last rounds, and
whether the last round ended by its allowance or by exhaustion): a problem
that ended by its allowance with gains still rising gets more; one that
exhausts its moves early gets less. Recorded in the ledger as a policy with
its samples, per the doctrine's scheduling rules. *Check.* A package check on
a synthetic history. *Gain.* Time follows yield within a scan, not only across
problems. *Cost.* Small.

### 4.8 What not to install

Density estimates as claims (the residual is of density zero among the primes
by the usual sieve heuristic): not checkable in her language, so not a claim;
stated in prose with its attribution, never used. Source claims as evidence
(the conjecture is verified to 10^17 in the literature): her theorems are
about what she verified; a source could only tell her scheduler where not to
spend, and the loop keeps statuses and prose out of her reading on purpose.
Anything that reads a language model: outside the loop by construction.

## 5. Order and measure

Install 4.1 first: it is small, it closes the class of defect the preregistered
rounds found, and every later ability depends on seeing refusals. Then 4.3 and
4.4, measured on the fourteen theorem problems by the number of witnesses per
chunk and the residuals from bound exhaustion, against the rerun above as the
baseline. Then 4.2, measured by the number of surviving predicates per problem
after two ranges and by whether any names a new family (none is expected on
these problems; the measure is honest either way). Then 4.5, 4.7 and 4.6.
Each is preregistered in CAMPAIGNS.md before it runs: the baseline, the
fourteen-round schedule, what is recorded, and what counts as a defect.

Status. 4.1 is installed (commit 3ae3cae): the package check plants the
refusal, the defect of the third tier's first run reproduces with the
diagnosis naming its bound, and two ordinary rounds show refusals that name
no instrument. Read against her records, 4.3 has no outcome measure while
every theorem round ends by exhaustion (it changes the order of moves that
all run), and 4.4's case, a chunk abandoned for want of a witness within the
bound, has not occurred in her state; both wait for evidence. 4.2 is
installed as two derivation rules and two operators (the entry in
CAMPAIGNS.md has the preregistration and the fourteen rounds): on her
theorem problems no predicate of the grammar is selective at the
preregistered tenth, the best being satisfied by two thirds to four fifths
of the represented sample, so the grammar of residues and prime-factor
classes does not tell her residual from what the families take. The
ability is in place with its checks; what it found is a limitation of the
grammar, recorded, not a description of the residual.

Beyond the note's list, the ability that answers the residual is the one I
used against her by hand: finding family shapes. The four shapes are points
of a parametrized space (d = h1 n^i e^j / h2 in the Type I identity), and
she now searches that space herself, verifies each family exactly and adopts
by measured yield on her own residual (`gfam` claims, `egypt_shape_search`);
CAMPAIGNS.md records the probe, the preregistration and the rounds.

## 6. Limits of this note

The depth table is one state and four problems; the residues were counted,
not modeled. The mapping of methods to her abilities is a reading, not a
measurement. Nothing here proves that an ability, once installed, gains what
its entry expects; that is what the preregistered rounds are for.
