# Ember

Ember is a small, offline, non-LLM mathematical research agent under development,
directed by Seth. Its Theory Pyramid Mapping approach connects proposed
representations, their assumptions, counterexamples and checked reuse.

This source package runs with Python's standard library. It requires no model,
API key, downloaded weights, third-party package or source archive. Python itself
is an external prerequisite and is **not** included. Generations through
`ember-pyramid-15` were tested on Windows with Python 3.14.6. Generation
`ember-pyramid-16` added the apex layer; this generation, `ember-pyramid-17`,
adds a typed operator language (now 219 executed operators), a move bench, an
autonomous research agent, an open-problem library and 29 window tools that give
her a finite exact view of 125 catalogued open problems. Both were verified on Linux x86_64 with Python 3.11.15
only; they have not been rerun on the Windows host. Other Python versions,
operating systems and devices remain unverified. CPU, memory and storage are still
required for each calculation.

Standing: **EXPERIMENTAL / SELF_ISOLATED**. Ember does not currently offer general
mathematical intelligence, unrestricted invention, or a solution to every open
problem. Its finite searches and exact checkers support the specific task types
below. Its autonomous agent works only on problems stated in its typed language;
an open problem stays open unless the checker settles it, and none has been
settled. A window computes or verifies a finite exact view of an open problem and
settles nothing about it. Same-model development and review are not external
scientific replication.

## Start locally

Extract the ZIP into an ordinary folder, open a terminal there, and run:

```text
python -I -B -X utf8 ember.py examples/graph_count.json --state my-instance.json
python -I -B -X utf8 ember.py examples/polynomial_consequence.json --state my-instance.json
python -I -B -X utf8 ember.py examples/rational_repair.json --state my-instance.json
python -I -B -X utf8 ember.py examples/word_identity.json --state my-instance.json
python -I -B -X utf8 ember.py examples/discover_word_recurrence.json --state my-instance.json
```

The graph example returns the integer `18446744073709551616`. The polynomial
example checks an implication against its supplied equations. The rational-repair
example explores a condition requiring a fractional witness. The word example
checks a generating-function identity for every nonnegative length for the two
supplied forbidden words, using a finite exact polynomial certificate.

The higher reasoning layer described in
[Apex: the higher reasoning layer](#apex-the-higher-reasoning-layer) plans any
supported original from four directions:

```text
python -I -B -X utf8 ember.py --pyramid
python -I -B -X utf8 ember.py examples/apex_research.json --state apex-instance.json
python -I -B -X utf8 ember.py examples/hidden_rank_count.json --layer apex --state apex-instance.json
```

Each invocation prints one JSON result. The files in `examples/` contain the full
task inputs. They can be inspected or modified with a text editor. State paths
identify separate instances; each state file supports one writer at a time.

## Research campaigns

```text
python -I -B -X utf8 ember.py examples/campaign_research.json --state campaign-instance.json
python -I -B -X utf8 ember.py examples/campaign_research.json --state campaign-instance.json
```

A campaign keeps a bounded record of attempted routes and continues remaining
work on later calls. Saved mathematical outcomes are checked again. An unchanged
unsuccessful attempt remains a no-result observation; it cannot become a proof.
Successful repairs retain their added assumptions and remain distinct from the
original claim. The default campaign policy, `structure_first`, tries the
assumption-aware route before broader search when applicable. The optional
`fixed` policy keeps the original route order; `learned` ranks available routes
from measured outcomes and costs. Learned scheduling has no demonstrated
advantage over the stronger fixed ordering in the selected comparisons and
remains experimental. Scheduling scores never establish mathematical truth.

The input supplies the original questions and resource bounds. Campaigns select
among explicitly implemented routes and repair grammars; they do not invent an
unrestricted research agenda or resume arbitrary partial solver internals. An
exhausted route list can still leave an original question unresolved.

`examples/campaign_discovery.json` enables `discover_after_solving: true`. Run it
twice with the same state path: the first call answers a finite transition-count
question; the next call automatically proposes an all-index recurrence question
from that same original system. Original forbidden-word formula tasks can likewise
lead to recurrence discovery. The generated question has role `generalization`,
distinct from both the original claim and any repair. This option is disabled by
default and does not invent an unrestricted agenda. Inspect every returned result:
a completed campaign can retain an `UNKNOWN` generalization while its original
obligations have checked outcomes.

## Discover an exact recurrence

```text
python -I -B -X utf8 ember.py examples/discover_recurrence.json --state recurrence-instance.json
python -I -B -X utf8 ember.py examples/hidden_mode_recurrence.json --state recurrence-instance.json
python -I -B -X utf8 ember.py examples/discover_word_recurrence.json --state recurrence-instance.json
```

The first two tasks supply an integer transition matrix `M`, an initial row `u`
and a terminal column `v`. Ember proposes recurrence coefficients for the sequence
`a(h) = u M**h v`; the caller does not supply those coefficients. The first example
discovers the Fibonacci recurrence. The second observes the `2**h` mode while
preserving the original matrix's unobserved `3**h` mode.

A finite prefix supplies candidates, never the all-index proof. A separate checker
reconstructs a closed row space containing the original `u` and verifies that the
recurrence residual is invisible throughout that space. Exact rational arithmetic
and induction then establish the recurrence for every nonnegative integer index.
The checker also reconstructs the initial terms from the original system.

The word task supplies two distinct forbidden binary patterns, each of length at
most seven and neither contained in the other. Producer and checker separately
build the prefix automaton, including both binary letters. The checked recurrence
therefore counts original words of every nonnegative length avoiding those patterns.
The patterns remain the original input; a supplied replacement matrix cannot stand
in for them.

Both queries return `CHECKED_RECURRENCE` with exact coefficient pairs `[numerator,
denominator]`. Coefficients are in ascending order: `a(h+r) = sum(c[j]*a(h+j))`
for `j=0..r-1`. An order-zero certificate states that every term is zero.
`max_order` bounds the proposed recurrence; matrix dimension is at most 64 and
matrix/vector entries are integers of absolute value at most one million.
Arithmetic has an 8192-bit bound. Insufficient search or arithmetic resources leave
the task `UNKNOWN`. Stored certificates are freshly checked after restart.

This is autonomous coefficient discovery in a fixed, established mathematical
grammar. It does not infer a guaranteed law from measurements whose generating
system is unknown, certify minimal recurrence order, invent arbitrary methods,
or claim a newly solved open problem. A recurrence campaign can resume these same
tasks alongside the other supported queries.

## Discover a polynomial conservation law

```text
python -I -B -X utf8 ember.py examples/discover_invariant.json --state invariant-instance.json
python -I -B -X utf8 ember.py examples/nonlinear_invariant.json --state invariant-instance.json
python -I -B -X utf8 ember.py examples/invariant_cancellation.json --invariant-policy mapped
python -I -B -X utf8 tools/helper_client.py examples/discover_invariant.json --state helper-instance.json
```

An invariant task supplies variables and their simultaneous polynomial update
`F`, an optional rational initial point, and a maximum degree. Ember generates a
nonconstant polynomial `P` and checks `P(F(x)) = P(x)` for every rational state.
For a quarter turn, it discovers `x*x + y*y`; from the initial point `(3,4)` the
value is always 25. The nonlinear example updates `x` to `x+1` and `y` to
`y+3*x*x+3*x+1`; it discovers `y-x**3`, whose initial value is 3.

The producer proposes coefficients by exact linear algebra. The distinct checker
evaluates the original transition expressions on a complete grid determined by
rigorous individual degree bounds. Polynomial root bounds establish the identity;
agreement on a few sampled trajectories would not suffice. When an initial point
is supplied, the checker also reconstructs the initial value, which is preserved
at every nonnegative iterate by induction. The approach draws on established
[linear-algebraic invariant generation](https://arxiv.org/abs/1611.07726); that
background does not validate this implementation or replace its checks.

`--invariant-policy full` is the default. The experimental `mapped` policy applies
TPM to concrete coefficient dependencies: candidate monomials connect to the exact
coefficient equations they contribute to in `P(F)-P`. Shared equations, including
constant terms, join candidates that must be solved together. In the cancellation
example, `x+1` and `y-1` share a constant equation and yield `x+y`. Every proposed
map partition is validated against the full operator; final admission still checks
the original transition. The policy has no general speed or intelligence claim.

The returned map is inspectable proposal data. A saved map cannot authorize a
proof. Restart freshly checks the saved polynomial certificate; it does not replay
or return the saved map as new evidence. Stored maps retained alongside a replayed
proof are explicitly marked as proposals that were not replayed.

Tasks allow one to six variables and `max_degree` from one to three. `focus`, if
provided, is a nonempty subset of declared variable names; at least one must occur
in the discovered polynomial. Each transition has a conservative individual-degree
sum at most four. Complete checking is limited to 50,000 grid points and 8192-bit
exact arithmetic. Rational values use reduced `[numerator, denominator]` pairs.
Certificates have sorted, nonzero monomials, no constant term, and first coefficient
one. `UNKNOWN` does not prove that no invariant exists.

Run `examples/campaign_invariant.json` repeatedly with one state path to see degree
expansion. Two bounded linear searches remain unresolved; the campaign then asks
a distinct quadratic question and checks its answer. The original degree-one
request remains `UNKNOWN`, so the campaign legitimately exits with code 3 even
while reporting a checked quadratic expansion. Restart rechecks that proof and
avoids unnecessary higher-degree searches. This is bounded question generation,
not an unrestricted research agenda.

## Reuse a discovered invariant

```text
python -I -B -X utf8 ember.py examples/invariant_reuse_source.json --state law-instance.json
python -I -B -X utf8 ember.py examples/invariant_reuse_receiving.json --state law-instance.json --invariant-policy reuse_first
python -I -B -X utf8 ember.py examples/invariant_reuse_receiving.json --state law-instance.json --invariant-policy reuse_first
```

The source task discovers the cubic law `y-x**3`. The receiving task changes both
variable names and update step. With the optional `reuse_first` policy, Ember can
freshly check the source proof, rename the polynomial's active variables, and
test that candidate against the **original receiving transition**. It recomputes
the receiving initial value; the source's value does not transfer unchanged.
The example's new value is `53/24`. The final certificate stands on its own and
is checked again after restart.

A source law supplies a candidate, never a new assumption or a guarantee about
different dynamics. Reuse considers at most eight recent source observations and
sixteen injective variable bindings per source, within a reserved budget slice.
The receiving focus and degree limits still apply. Failed reuse falls back to
the full original search. `full` remains the default; rechecking and binding can
cost more than solving directly. No universal transfer or speed claim follows.

```text
python -I -B -X utf8 ember.py examples/campaign_reuse_reentry.json --state research-instance.json --work 200000
python -I -B -X utf8 ember.py examples/campaign_reuse_reentry.json --state research-instance.json --work 200000
```

This campaign opts into `reuse_invariants: true`. Its first bounded call cannot
settle the earlier six-variable question but discovers a useful law in a later
two-variable question. On restart, the changed candidate library makes the prior
reuse attempt worth trying again. A fresh receiving proof then settles the same
original question, without relaxing its bounds. The superseded `UNKNOWN` attempt
remains inspectable. Library fingerprints only decide when to retry; they never
establish a theorem. Observations outside the candidate library do not trigger this retry, and already
checked outcomes are replayed instead of searched again.

## Checked lemma reuse

```text
python -I -B -X utf8 ember.py examples/lemma_source.json --state lemma-instance.json
python -I -B -X utf8 ember.py examples/lemma_receiving.json --state lemma-instance.json --proof-policy lemma_first
python -I -B -X utf8 ember.py examples/lemma_receiving.json --state lemma-instance.json --proof-policy lemma_first
```

The first task proves `a-b=0 => a*a-b*b=0` and stores its original statement and
flat certificate. The receiving task asks whether `u-v=0, v-w=0 => u**3-w**3=0`.
Ember can propose a variable renaming, freshly check the source proof, establish
each renamed source premise from the receiving equations, and use the checked
intermediate result. It then expands the composition back into multipliers of
the **original receiving equations** and checks that final certificate. The
repeated receiving call rechecks the stored final proof.

A stored lemma is never a trusted extra assumption. Missing premises, altered
bindings, nonzero conditions and the original certificate degree limits still
apply. This bounded implementation considers up to eight recent flat proof
observations and up to sixteen candidate bindings. It does not provide arbitrary
substitution, cyclic proof graphs or unrestricted theorem-library search.

`--proof-policy auto` is the default: try a bounded basis with target and
assumption-cancellation candidates, followed by full polynomial search; then try
bounded lemma reuse if the result remains unresolved and budget remains. `direct`
uses the full basis and disables cross-task lemma search; `lemma_first` tries the
bounded reuse stage before full direct fallback. A previously saved proof of the exact same task can still
be freshly checked under any policy. Reuse can cost more than direct search; it
does not establish general acceleration, new trusted axioms or solved open problems.

The explicit `target_sparse` policy first proposes a smaller multiplier basis from
monomials already present in the target and assumptions. `cancellation_sparse`
also proposes differences between assumption monomials. Both retain the full
bounded polynomial search as fallback and check the same original certificate;
neither treats missing candidates as a refutation. These two explicit policies
do not consult other tasks' stored lemmas.

## Cancel an original nonzero condition

```text
python -I -B -X utf8 ember.py examples/localized_cancellation.json --state cancellation-instance.json --proof-policy localized_first
python -I -B -X utf8 ember.py examples/localized_consequence.json --state cancellation-instance.json --proof-policy localized_first
python -I -B -X utf8 tools/helper_client.py examples/localized_cancellation.json --state cancellation-instance.json --proof-policy localized_first
```

The first task asks whether `x*y=0` and `x!=0` imply `y=0`. The experimental
`localized_first` policy selects one of the **original** nonzero guards `U`
and proposes an identity `U*goal = sum(multiplier[i]*assumption[i])`. A separate
checker verifies that polynomial identity against the original expressions.
Since `U` is nonzero at every admissible original rational point, cancellation
proves the original goal. The larger example is the generic algebraic converse
arising from the reviewed Organon column-shortcut question.

The certificate is `localized_polynomial_combination` and names the selected
original `nonzero_index`; it supplies no new guard or cancellation factor.
Exactly one guard with exponent one is supported. Original multiplier-degree
limits remain binding. The checker uses the complete original degree grid,
including points where the guard vanishes, without dividing at those points.
The existing 50,000-point and 8192-bit bounds still apply. Changed or reordered
guards require a fresh original-task check.

The fixed policy tries guards in their declared order, then degrees zero through
the original bound, using at most 100,000 counted units and one quarter of the
remaining work. Unsuccessful search falls back to `auto`. This ordering can miss
a known proof within its allowance. Guard powers/products, inferred nonzero
conditions and arbitrary rational-expression proofs remain unsupported. `auto`
remains the default; it can replay a saved original proof but does not search
this new certificate grammar on a fresh task.

On the selected twelve-task development comparison, this policy and a fixed
controller with the same grammar each settled eight tasks; the old default
settled four. Four tasks remained unresolved, including a variant with a known
certificate that bounded search did not find. The two capable controllers used
the same counted work and each was faster on six individual tasks. These results
support the added proof capability, not a general speed or intelligence claim.

A checked implication does not establish that its assumptions have a solution.
For example, an original condition `0!=0` makes every implication vacuously true.
`support_checked` is true only when the certificate supplies an admissible
original point that the checker validates. Guard-repair discovery retains its
support requirement. This policy does not search for a support point during its
localization prepass. Localized proofs are stored for fresh same-task replay and
excluded from the default flat lemma library. The explicit receiving policies
described below can now propose guarded cross-task composition.

```text
python -I -B -X utf8 ember.py examples/campaign_localization.json --state cancellation-campaign.json
python -I -B -X utf8 ember.py examples/campaign_localization.json --state cancellation-campaign.json
```

The explicit campaign flag `localize_polynomials: true` adds a localized original
route before its existing polynomial route. The first call settles the supplied
example, and the next checks its evidence again. An absent or false flag keeps
the existing campaign routes. The helper exposes the same explicit policy and
original-proof statuses. These are bounded polynomial consequences, not newly
solved open problems or a general discovery method.

## Reuse a guarded proof in a different question

```text
python -I -B -X utf8 ember.py examples/localized_cancellation.json --state guarded-instance.json --proof-policy localized_first
python -I -B -X utf8 ember.py examples/guarded_receiving.json --state guarded-instance.json --proof-policy lemma_first
python -I -B -X utf8 tools/helper_client.py examples/guarded_receiving.json --state guarded-instance.json --proof-policy lemma_first
```

The learned source establishes `x*y=0, x!=0 => y=0`. The receiving task asks
whether `u*v-w=0, w=0, u!=0` imply `v+w=0`. Ember first proves the renamed source
premise `u*v=0` from both receiving equations. It then composes the learned
consequence with the original equation `w=0` and checks the original identity
`u*(v+w) = (u*v-w) + (1+u)*w`. The final certificate names the receiver's original
guard and can be checked later without the source library.

Every source nonzero condition must occur in the receiver as the same parsed
expression, including conditions unused by the source certificate. A different
guard order reconstructs the correct receiving index. Algebraically equivalent
but differently written guards are not inferred. Bindings rename every source
variable injectively; substitutions and variable elimination remain unsupported.
Required source equations must receive flat proofs from the original receiving
equations. A child that needs another localized cancellation is not supported by
this composition. Source support is never copied as a receiving support witness.

Only explicit `lemma_first` and `obligations` select guarded source records.
`auto` and `localized_first`'s ordinary fallback retain their flat source library.
Stateless reuse keeps its 50,000-unit/fifth-of-remaining-work allowance and its
intermediate receiving-lemma degree bound. Durable assembly may cancel exact
coefficients before checking the final target degree. These are distinct bounded
search policies; neither guarantees that an available proof will be found.

For a child checkpoint followed by fresh assembly, use a separate instance:

```text
python -I -B -X utf8 ember.py examples/localized_cancellation.json --state guarded-premises.json --proof-policy localized_first
python -I -B -X utf8 ember.py examples/guarded_receiving.json --state guarded-premises.json --proof-policy obligations --obligation-steps 1
python -I -B -X utf8 ember.py examples/guarded_receiving.json --state guarded-premises.json --proof-policy obligations --obligation-steps 1
```

The first receiving call returns `UNKNOWN` after saving the checked child. The
next rechecks it and assembles the original guarded result. Unsupported saved
localized child evidence is invalidated and retried as a flat child, never
accepted merely because it carried a successful status.

```text
python -I -B -X utf8 ember.py examples/campaign_guarded_transfer.json --state guarded-campaign.json
```

Repeat that campaign command to advance its one-attempt checkpoints. It opts into
both `localize_polynomials` and `reuse_guarded_polynomials`: it learns the source,
then attempts the changed receiving question. The latter Boolean adds an original
`lemma_first` route; absent or false preserves the prior routes and identity.
Changed candidate contents can reopen an unresolved attempt, but only a fresh
original proof closes it. This is bounded reuse of checked knowledge, not a
general scientific discovery or speed guarantee.

On the selected seventeen-task development bank, a cold sparse controller
settled fifteen tasks; explicit lemma reuse settled eleven and durable reuse
settled thirteen. Reuse helped one wider task, but the complete episodes paid
source generation, checking and persistence, and were more expensive overall.
The examples demonstrate valid knowledge transfer and continuation, not a reason
to replace the default with reuse on every task.

## Resume missing-premise proofs

```text
python -I -B -X utf8 ember.py examples/obligation_source.json --state premise-instance.json --proof-policy direct
python -I -B -X utf8 ember.py examples/obligation_receiving.json --state premise-instance.json --proof-policy obligations --obligation-steps 1
python -I -B -X utf8 ember.py examples/obligation_receiving.json --state premise-instance.json --proof-policy obligations --obligation-steps 1
python -I -B -X utf8 tools/helper_client.py examples/obligation_receiving.json --state premise-instance.json --proof-policy obligations --obligation-steps 1
```

The source proves `a=0, b=0 => a*a=0`. Its checked certificate uses only `a=0`.
The optional `obligations` policy extracts that sufficient equation subset,
retains every source variable and nonzero guard, and proposes a variable binding.
It turns the receiving prerequisite `x=0` into an exact child question under
the original assumptions `x-z=0, z=0`. The first receiving call proves and saves
that child, leaving the parent `UNKNOWN` with exit code 3. The next call rebuilds
the plan, checks the saved child afresh, and composes a flat proof of `x*x=0`
against the original receiving equations. The helper then rechecks the final
proof; the source library and graph are no longer required for that replay.

The state contains typed original, transfer, required-premise and direct nodes,
their dependencies, checked outcomes and actual work allocations. Alternative
plans can share an exact child. A child counterexample rejects that transfer
route; it cannot refute the parent. Only the original certificate checker
can admit the parent; this route assembles flat or single-guard proofs against
the original receiving equations. Original assumptions, nonzero guards and multiplier-degree
limits remain binding. A sufficient subset is not claimed to be a minimum.

Within one planning call, Ember checks each source and its sufficient core once.
Each variable binding still receives its own mapped-proof check. Exactly equal
mapped tasks, certificates and ordered child questions share one complete plan.
Plans own their evidence separately, and the next call reconstructs and checks
its evidence again. A stored successful flag cannot authorize a new proof.

`--obligation-steps` accepts 1 through 64 and defaults to 4. A step solves one
child, attempts one ready assembly, or runs direct fallback. Planning and saved
proof checking also consume the call's `--work` budget. The graph has at most
64 nodes and 128 edges, considers eight recent source proofs and sixteen variable
bindings in total, and retains 64 attempt records. Stage work is capped at
200,000 and at half the remaining allowance. Saved no-results are retried only
when their actual stage allowance grows or their code/proposal context changes.
Changing descriptive task metadata rebuilds its plan context without changing
the mathematical task. State paths still require a single writer.

This is an explicit standalone polynomial policy. Research campaigns retain
their existing routes. `auto` remains the default: on the selected ten-task
comparison, both durable modes settled the same nine tasks as the alternatives
and lost to `auto` on every receiving-time comparison. Repeated single-step
calls also paid more planning and replay work than one call. The current planner
reduced time and stored duplicate plans compared with its previous implementation,
while its additional counted deduplication work increased the mixed work total.
It still lost every receiving-time comparison against `auto`. The feature offers
inspectable continuation of supported child proofs; it establishes no general
speed advantage, unrestricted theorem search or newly solved open problem.

## Recursive identities and bounded lemma invention

```text
python -I -B -X utf8 ember.py examples/recursive_add_right_zero.json --state recursive-instance.json --recursive-policy direct
python -I -B -X utf8 ember.py examples/recursive_reverse_involution.json --state recursive-instance.json --recursive-steps 1
python -I -B -X utf8 ember.py examples/recursive_reverse_involution.json --state recursive-instance.json --recursive-steps 1
python -I -B -X utf8 ember.py examples/recursive_qrev.json --state recursive-instance.json
python -I -B -X utf8 tools/helper_client.py examples/recursive_wrong_order.json --state recursive-instance.json
```

A `prove_recursive_identity` task asks whether its equation holds for every
natural number and finite list of natural numbers. It contains exactly `query`,
`domain: "NatList"`, `definitions` and `goal`. Variables carry an explicit `Nat`
or `List` sort. Applications are arrays such as `["succ", {"v":"n","sort":"Nat"}]`.
The free constructors are `zero`, `succ`, `nil` and `cons`. All original ordered
definitions belong to the task, including functions unused by the goal. The
examples contain original definitions and questions, without supplied helper
lemmas, proofs or expected answers.

Every declared function selects a recursive argument and defines both of its
constructor cases. A self call must use the literal immediate predecessor or
list tail in that position. Other arguments may change, allowing accumulators.
Calls to earlier validated definitions are supported; arbitrary recursion,
mutual recursion, constructor redefinitions, overlapping cases and unbound
variables are refused. Function names have no built-in theorem meaning.

`--recursive-policy direct` attempts rewriting and structural induction without
inventing lemmas. `enumerate` and the default `residual` can propose bounded
auxiliary equations, reject concrete counterexamples, try structural proofs and
retry the original question with checked lemmas. Residual guidance conditions
proposals on unresolved proof steps; it is an experimental ordering policy,
without a general speed claim. Finite test survival never establishes an identity.

The separate checker reconstructs each explicit rewrite, both induction cases,
the strict smaller-argument hypothesis and every earlier auxiliary proof. Other
goal variables remain universally quantified in the induction hypothesis, so
changing an accumulator requires a valid typed specialization. Fresh case
variables cannot escape their scope. Only one induction level per theorem is
supported; each auxiliary theorem can have its own induction proof. A final
`recursive_identity` certificate includes the ordered lemma proofs and the
original proof, so admission needs no trusted saved theorem library.

`CHECKED_RECURSIVE_IDENTITY` reports such a proof. A
`CHECKED_RECURSIVE_COUNTEREXAMPLE` includes a concrete original assignment whose
two values the checker independently evaluates. The wrong-order reversal example
asks a false identity; reversing concatenated lists changes their order. A false
auxiliary candidate does not refute its parent question. `UNKNOWN` can mean that
the chosen proof grammar or allowance could not settle a true or false statement.
These examples concern established identities, not newly solved open problems.

Use the same state path to continue a bounded episode. `--recursive-steps` limits
stages per invocation to 1..64, default 4; each stage has a counted-work cap of
200,000 within the supplied `--work`. Pending proposals and checked lemma evidence
remain instance data. Reuse requires fresh proof replay; a changed theory,
policy or runtime cannot turn a saved success label into evidence. A saved final
certificate is freshly checked against the complete original task on restart.

```text
python -I -B -X utf8 ember.py examples/campaign_recursive_identity.json --state recursive-campaign.json
python -I -B -X utf8 ember.py examples/campaign_recursive_identity.json --state recursive-campaign.json
```

This campaign keeps the same original reverse-involution question while trying
the supported recursive policies. Repeat calls to continue within the fixed
bounds; an unfinished campaign may return `UNKNOWN`. It commits recursive
progress together with the outer campaign record. It does not import another
instance's unchecked auxiliary lemmas. This example completed after nine calls
in the tested configuration; the two commands above illustrate continuation.

The checker allows at most 16 functions of arity 1..4, 16 variables per equation,
16 proved lemmas and a 256 KiB certificate. Input terms have at most 1,024 nodes
and depth 64; intermediate terms have at most 4,096 nodes and depth 128. The
search has additional fixed proposal, attempt and episode limits. These bounds
constrain computation and supported proof forms, not the universal domain of
an admitted identity. The custom checker is not a formally verified proof kernel.

In the selected thirteen-task development comparison, residual invention and
its resumed form each settled all thirteen tasks: nine proofs and four concrete
counterexamples. Direct search and fixed enumeration each settled nine. Starting
with empty libraries, reverse involution used three generated, checked lemmas;
the accumulator-reversal question used two. The bank includes original questions,
renamings and basic controls and was exposed during development. These outcomes
are bounded implementation evidence, not a held-out intelligence evaluation.
Residual invention cost more than direct search, which left four tasks unresolved;
resuming single stages added replay and checkpoint costs. Neither faster unresolved
calls nor this small comparison establish a general speed advantage.

## Research related questions from structured sources

```text
python -I -B -X utf8 ember.py examples/source_research_episode.json --state source-instance.json --source-steps 64 --work 4000000
python -I -B -X utf8 tools/helper_client.py examples/source_research_episode.json --state source-instance.json --source-steps 64 --work 4000000
```

The example contains two original questions: reverse involution and accumulator
reversal. A `source_research_episode` task contains exactly `query` and `sources`.
Each source supplies an `id`, the SHA-256 of its literal UTF-8 text, and that text
in `utf8`. The runtime interprets bounded JSON data; it does not execute source
code or open a supplied path. The supported formats are `pie-problem-v1` and
`ember.recursive_claim.v1`. The latter contains exactly `format`, an original
recursive `task`, and `claim`, which is `question`, `holds` or `fails`. Neither
format accepts supplied proofs or an authoritative expected answer.

The controller preserves every source association and all original definitions.
Identical mathematical questions share one root. Opposite source assertions
create an explicit tension; extra copies add no truth weight. Its typed graph
connects sources, claims, original questions, attempts, gaps and checked bridges.
Unsupported source formats remain visible and prevent a complete outer result.

A proof produced within the episode can supply auxiliary statements to another
question with exactly the same complete ordered definitions. Ember rechecks the
source proof, retains every needed earlier lemma, and checks the assembled
receiving prefix. The final receiving certificate includes its own proof
dependencies and replays against the original question without the source graph.
Changed unused definitions still prevent transfer. Reused lemmas are counted
separately from newly generated lemmas.

`--source-policy native_isolated` solves each original without the graph or
cross-question transfer. `graph_isolated` adds the graph. `fixed_bridge` proposes
checked transfers in original source order. The default `gap_bridge` first
inspects a bounded proof attempt for each original, then ranks unresolved
questions by source tension, actual typed matches to the remaining proof terms,
function-dependency count and source order. Ranking selects work; it does not
prove a statement. This implements a bounded part of Theory Pyramid Mapping,
with no claim that the full source collection or general scientific method has
been absorbed.

`--source-steps` is 1..64, default 8. Use the same task, policy and state path to
resume. The episode permits eight sources, 64 KiB per source, four distinct
originals, eight selected seed entries, 64 graph nodes, 128 edges and 64 actions.
Each original has a cumulative two-million-unit allowance, and the complete
episode shares at most two million times its number of distinct originals.
Parsing, checking, graph construction and persistence consume work. Returned
`work_accounts` separate common work from work charged to each original.
Callers enforcing a total allowance across calls must subtract every returned
`work`, including a failed call whose previous checkpoint was preserved.

`CHECKED_SOURCE_EPISODE` means every supplied source was adapted and every
distinct original received a freshly checked proof or counterexample. It can
therefore include a source assertion marked `CONTRADICTED`. Inspect each source's
assessment and each original result. `UNKNOWN` retains gaps or exhausted work;
malformed source hashes, invalid proof evidence and incompatible state are
refused. This interface currently handles the declared recursive JSON grammar,
not arbitrary papers, prose or scientific subjects.

On the exposed eight-episode development bank, all five compared configurations
settled every episode: sixteen known identity-proof occurrences and one original
counterexample per bank traversal. Across three rotated repetitions, median
complete time for the whole bank was 2.969 seconds for `native_isolated`, 2.985
for `graph_isolated`, 3.268 for `fixed_bridge`, 3.706 for `gap_bridge`, and 4.877
for one-stage gap-guided resumption. The gap-guided policy was slower on every
individual case median and charged about 69% more total work than isolation.
These are one-host development measurements including original proof replay;
they do not justify a performance promotion. The default remains an experimental
research policy; `native_isolated` is the cheaper measured option on this bank.

A separate constructed control kept two receiving questions and their actual
unresolved proof terms fixed. Changing the checked source lemma changed the
gap-guided choice from one receiver to the other. Disabling residual scoring
kept the same choice. This verifies a causal selection mechanism, not better
subsequent progress, generalization or speed. The eight-episode bank does not
provide a competing-receiver experiment for measuring that score's benefit.

## Apex: the higher reasoning layer

```text
python -I -B -X utf8 ember.py --pyramid
python -I -B -X utf8 ember.py examples/apex_research.json --state apex-instance.json
python -I -B -X utf8 ember.py examples/apex_research.json --state apex-instance.json
python -I -B -X utf8 ember.py examples/hidden_rank_count.json --layer apex --state rank-instance.json
python -I -B -X utf8 ember.py examples/orbit_exclusion.json --state orbit-instance.json
python -I -B -X utf8 ember.py examples/orbit_drift.json
python -I -B -X utf8 ember.py examples/orbit_ranking.json
python -I -B -X utf8 ember.py examples/word_count.json
python -I -B -X utf8 ember.py examples/generating_function.json
python -I -B -X utf8 ember.py examples/minimal_recurrence.json
python -I -B -X utf8 ember.py examples/eventual_recurrence.json
python -I -B -X utf8 ember.py examples/recursive_lift.json --state lift-instance.json
python -I -B -X utf8 tools/helper_client.py examples/orbit_exclusion.json --layer apex
```

The apex sits above the subreasoners described earlier in this README. It keeps
a map of Ember's own reasoning and plans every original question from four
Theory Pyramid Mapping directions:

- **S** attacks the question as stated with its native routes.
- **W** refutes it, extracts a residual, or repairs it with explicit added assumptions.
- **N** generalizes it or changes its representation: a quotient, an all-index
  law, a higher degree or a lemma grammar.
- **E** transfers checked knowledge from other questions.

### The reasoning pyramid

`--pyramid` prints the map. Its base is a catalog of 384 implemented moves across
34 modules: 157 subreasoner moves (9 of them control moves that schedule, persist
or replay work) and the 227 operators of the typed language described below. The
base holds 169 moves with an N component, 118 with W, 313 with S and 105 with E.
Each move names its functions, directions, the evidence types it
consumes and produces, and how its output is admitted. The layers above are the
fifteen nonempty direction sets, from the four faces up to the apex {N,W,S,E}. A
move sits at its own directions. A synthesis, a composition of moves, sits at
the union of its steps' directions, and a chained synthesis must pass each
step's produced type to the next step.

An audit binds the catalog to the source text. Every named function must exist,
every explicit `direction`/`operation` trace label in the code must be claimed by
a move with that direction, and every chain must type-check. `--pyramid` exits 2
when the audit fails. Fourteen of the fifteen nodes are realized by code. The
unrealized node, NWE, would transfer a repair without checking it on an
original; every admitted Ember result passes through S. The map records 14
syntheses that predate the apex and 20 that the apex and the agent realize. The
first audit listed seven proposed syntheses. Six were implemented next, together
with exact drift, a special case of the seventh. This generation implements the
seventh, exclusion by a ranking polynomial, and the one proposal added after it,
a reduced generating function that certifies the least eventual recurrence. No
proposed synthesis remains. Directions classify operations; the map is a
description bound to source text, not evidence that any claim holds.

### Scheduling

`apex_research` accepts one to sixteen original questions of the campaign kinds,
plus `prove_orbit_exclusion`, `count_word_avoiders`, `discover_generating_function`,
`certify_minimal_recurrence` and `certify_eventual_recurrence`. `--layer apex` sends
a single original through the
same layer. The apex reuses the campaign's durable executor: saved outcomes are
checked again on restart, and an unchanged miss is not searched again. It enables
the campaign's optional generalization, localization and reuse routes.

For each obligation the apex chooses the face with the fewest executed attempts,
counting stages that a resumed episode superseded. Ties go to the face holding
the best measured route score, then to the order S, E, W, N. Inside a face,
routes are ranked by the campaign's measured success and cost score. Exact
iteration waits behind other faces when its edge-count bound exceeds the attempt
allocation; a quotient cannot compress when every terminal weight differs.
Results report each attempt's face and pyramid node, face counts, node coverage
and the synthesized-route trace. Faces and scores schedule work; they never
admit an answer. Synthesized results are admitted by `apex_check.py`, and every
other result by its original checker.

### Synthesized routes

- `law_instance` (N, then S) answers a transition count from an all-index law.
  When partition refinement compresses the system to at most 64 states, the law
  is discovered on the checked quotient and lifted through MP=PQ and v=Pw.
  Otherwise the original carrier is used when it has at most 64 states. The
  checker rechecks the quotient equations and the recurrence on the carrier and
  recomputes the answer; the producer's value is not trusted.
- `prove_orbit_exclusion` asks whether an exact rational orbit x(n+1)=F(x(n))
  ever reaches a target point. The S face iterates a bounded prefix and returns
  a witness index (`CHECKED_ORBIT_REACHES`). In the same pass, the W face returns
  a repeated state, which confines the orbit to a finite set that avoids the
  target. The N face selects, among all polynomial invariants within the degree
  bound, one whose value differs at the start and the target. The E face renames
  checked laws stored by other questions and admits only a receiving separation.
  Separating invariants are admitted by the existing complete-grid invariant
  checker against the original transition, and the target value is recomputed.
- `recursive_seeded` (E) uses proofs admitted for other questions with the same
  complete definitions as checked seeds for a residual episode, through the
  source-episode seed transport. Seeds are rechecked under the receiving
  definitions, and the final certificate is checked against the receiving original.

- `orbit_drift` (N, then W or S) searches the kernel of a clocked system for a
  law R(x)+kappa*clock with kappa nonzero. Such a law gives R(x(n))=R(x(0))-kappa*n,
  so n=(R(x(0))-R(target))/kappa is the only index at which the target can occur.
  A nonintegral or negative index excludes the target. Otherwise the checker
  iterates to that index, which must lie within `max_steps`, and reports
  exclusion or reachability. The clocked law is checked on the complete grid.
- `orbit_ranking` (N, then W or S) generalizes exact drift to a ranking polynomial
  R whose rise R(F(x))-R(x) equals a floor c >= 0 plus a sum of positively
  weighted squares. Then R(x(n)) >= R(x(0))+n*c for every n. A target of lower
  rank than the start is excluded at once. Otherwise, with c > 0, only indices up to
  (R(target)-R(x(0)))/c can meet it, and the checker iterates those exactly. The
  producer tries every signed monomial and signed pair within the degree bound.
  It recognizes two positive forms: even monomials with positive coefficients, and
  quadratics completed to squares by an exact LDL^T decomposition. The checker
  verifies the identity on the complete original degree grid, recomputes the rank
  gap and the bound, and iterates the prefix. Nonnegative rises of other shapes
  are missed, not refused.
- `word_count_direct` (S) and `word_count_law` (N, then S) answer
  `count_word_avoiders`, the number of binary words of a given length up to 20,000
  avoiding two patterns. The law route discovers the all-length word recurrence
  and evaluates it at the length. A standalone call tries the law first when the
  length exceeds four times the squared automaton size; the apex schedules both
  by face and defers direct iteration beyond the attempt allocation.
- `generating_function` (N, then S) turns a checked all-index recurrence and its
  initial terms into P(x)/Q(x) with Q(x)=1-sum c_j x^(r-j) and
  P=(Q*sum a_h x^h) mod x^r. The checker rechecks the recurrence on the original
  word or matrix carrier and recomputes P and Q. The fraction is not necessarily
  reduced.
- `recurrence_minimality` (W, then S) certifies that no linear recurrence of lower
  order holds for every index. A lower-order recurrence would make the columns of
  the r-by-r Hankel matrix [a(i+j)] dependent. The checker recomputes 2r-1 terms
  from the original carrier and requires a nonzero fraction-free determinant.
- `reduced_generating_function` (N, W, then S) answers
  `certify_eventual_recurrence`. It forms P/Q from a checked recurrence, removes
  gcd(P,Q) by Euclid's algorithm over QQ, and keeps the Bezout cofactors U, V with
  U*P'+V*Q'=1. The checker rechecks the recurrence, verifies P=g*P', Q=g*Q',
  Q'(0)=1 and the Bezout identity. The reduced denominator of degree d then gives
  a recurrence that holds from index max(d, deg P'+1). No recurrence of order
  below d holds for all large indices. If R(0)=1 and R*A is a polynomial, then Q'
  divides R*P' and so divides R.
- `recursive_lifted_counterexample` (E, N, W, then S) matches a remembered refuted
  instance into the general equation. When the instance is the general goal under
  a substitution, the refuting values are pushed through that substitution and
  evaluated, and the receiving checker decides.
- In `--proof-policy obligations`, a required premise child keeps the original
  assumptions and guards. When its checked counterexample point also violates the
  original goal, the original checker admits it as the parent's refutation.
  Otherwise the point only closes that transfer route.

Admitted separating invariants, recursive proofs and recursive refutations are
remembered for later E routes. Every admitted conservation law is also stored as
the checked polynomial lemma P(x)-level=0 implies P(F(x))-level=0, with
multiplier 1, for later lemma transfer. Direct search also proves such lemmas when
their degree fits; the stored form is memory for renamed transfer, not a new
proving capability. A kernel selector that vanishes on every kernel basis vector vanishes on
the whole kernel, so an N-face miss is complete for its monomial grammar, but it
remains `UNKNOWN`: it does not show that the target is reachable.

`examples/orbit_exclusion.json` asks whether the orbit of (0,3) under
x -> x+1, y -> y+3*x*x+3*x+1 reaches (2,10). No prefix repeats, and none hits the
target. The N face finds y-x**3, which is 3 at the start and 2 at the target. For
the quarter turn from (3,4) to (5,0), x*x+y*y takes the value 25 at both points,
so no invariant of degree two separates them; the orbit instead repeats after
four steps.

`examples/hidden_rank_count.json` is a constructed control: a dense 56-state
system with distinct terminal weights and hidden rank-two dynamics. Exact
iteration exceeds the default ten-million-unit budget, and no quotient
compresses. The apex's N face settles it with the checked law
`a(h+3) = 4*a(h+1)`, using 887,534 work units for that route. A package check
compares the 1,236-digit answer with exact iteration under a larger budget.

`examples/apex_research.json` contains five questions:

1. an invariant question;
2. a renamed orbit question that the S face cannot settle, but the E face settles
   with the first question's law;
3. the quarter-turn orbit;
4. a false polynomial claim, refuted and then repaired with the guard `2*y-1`;
5. the hidden rank-two count.

One call settles all five across the four faces. A second call rechecks the
saved evidence without searching.

`examples/orbit_drift.json` asks whether the orbit of (x+1, 2y) from (0,1)
reaches (40,7). The map has no nonconstant polynomial invariant, and the orbit
never repeats. The clocked law clock-x fixes n=40 as the only candidate index, and
iterating to it excludes the target. `examples/word_count.json` counts the
1,046-digit number of binary words of length 5,000 avoiding 0110 and 111 from an
order-six law. A package check compares it with an independent dynamic program.
`examples/generating_function.json` gives
(1+x+x^2+x^3+x^4+x^5)/(1-x-x^2) for the same words.
`examples/minimal_recurrence.json` certifies that a three-state carrier's counts
2*2^h+3^h obey a recurrence of order two and no lower.
`examples/orbit_ranking.json` asks whether the orbit of (x+y^2+1, y^2) from (0,2)
reaches (10,3). The prefix exceeds the 8,192-bit exact-arithmetic bound at step
13, no stored law transfers, and the invariant and drift searches find no law of
degree at most two that decides it: four routes return `UNKNOWN`. The ranking R=x
rises by 1+y^2 >= 1, so only the first ten indices can meet a target of rank 10,
and none does.
`examples/eventual_recurrence.json` has counts 5, 1, 2, 4, 8, ...: every
recurrence valid from the start has order two, but a(h)=2a(h-1) holds from h=2,
and the Bezout certificate rules out order zero. Applied to the words avoiding
0110 and 111, the same route shows that the counts 1, 2, 4, 7, 12, 20, 32, 52, ...
obey the Fibonacci recurrence a(h)=a(h-1)+a(h-2) from h=6, although no recurrence
of order below six holds from h=0. A package check confirms both against
independent counts. In
`examples/recursive_lift.json`, the claim sub(sub(x,2),y)=0 holds on every value
that bounded testing tries (numbers up to 2), and the recursive routes leave it
`UNKNOWN`. The refuted instance sub(sub(3,2),y)=0 lifts to the counterexample
x=3, y=0.

### Measured comparison

The comparison used 27 original tasks: 23 shared example questions, the hidden
rank-two count and three orbit questions. Each task started from a fresh state
with 1,000,000 work units per attempt, 64 attempts and 10,000,000 units per call,
and calls were repeated until the result closed or a call executed nothing. The
host was Linux x86_64 with Python 3.11.15, in one run of each configuration, on
the code of this generation.

| Configuration | Originals settled (27) | Shared settled (23) | Shared work | Shared wall time |
|---|---|---|---|---|
| campaign `fixed` | 20 | 20 | 3,707,545 | 7.87 s |
| campaign `structure_first` | 20 | 20 | 3,713,815 | 7.67 s |
| campaign `learned` | 20 | 20 | 4,273,617 | 8.20 s |
| campaign `fixed`, all optional routes | 23 | 23 | 1,822,529 | 4.19 s |
| apex | 27 | 23 | 2,153,380 | 5.32 s |

The apex's gain on the shared tasks comes from the optional routes it enables;
a campaign with the same routes settles the same 23 tasks with about 15% less
work (the apex spends about 18% more). The four extra settlements are the hidden
rank-two count and the three orbit questions, which the campaigns refuse. On the
two resumed recursive identities, rotating faces spent 642,946 and 194,044 units,
against 424,925 and 129,172 for the fixed campaign order. The `learned` policy
scores routes by measured time, so its work can vary between runs.

Two scheduling details were changed after inspecting these development tasks.
Superseded attempts now count toward their face; without that, a resumed
recursive episode kept reopening one face and spent 19.6 million units on one
task. The tie order also places W before N. The bank is exposed development
data, not a held-out evaluation, and it establishes no general speed or
intelligence claim.

### Limits

The apex plans only over implemented routes and bounded grammars. It does not
invent subreasoners or proof systems; the agent below invents macros and templates
within the typed language, not new kinds of evidence. The orbit question
allows one to six variables, transitions of conservative degree at most four,
invariant degree one to three and at most 1,024 prefix steps, with exact
arithmetic up to 8192 bits. `UNKNOWN` never means that the target is reachable.
The law route needs a carrier of at most 64 states whose entries fit the
recurrence checker. Recurrence discovery cost grows roughly with the fourth power
of the carrier dimension, so the route pays off when the hidden law has low order
relative to the horizon. The checkers are custom code, not a formally verified
kernel.

## Typed language and move bench

```text
python -I -B -X utf8 ember.py --move-bench
```

Generation 17 gives Ember a typed mathematical language. Objects are a kind plus
exact JSON data: questions (a sequence definition, a polynomial map and orbit, a
residue class of a unit-fraction question, an integer polynomial, a residue-class
map, and the 29 window questions described under "Window tools") and claims (a
linear recurrence for every index, a rational generating function, a closed form,
a period modulo m, a polynomial identity, an invariant or semi-invariant, an orbit
exclusion, a unit-fraction family polynomial in the class parameter, a
residue-class cover, a checked finite range, a modular root or its absence, a
descent certificate, a cycle, a window's value, witness or proof, and a
derivation: a claim that follows from admitted claims by a named rule).
`lexicon_check.py` is the only way a claim becomes checked. It imports no operator
code, has its own exact arithmetic (its window checkers live in `window_check.py`,
`window_real.py` and `window_discrete.py`), and binds every claim to the question
stated in its own data.

227 operators in ten modules (`ops_seq`, `ops_poly`, `ops_orbit`, `ops_egypt`,
`ops_arith`, `ops_word`, `ops_matrix`, `ops_collatz`, `ops_wnum`, `ops_wdisc`)
consume and produce objects.
Each output is created through one runtime event with a checkable precondition:

- **N** a new candidate;
- **W** a checked refutation, orbit exclusion, modular non-existence proof,
  cycle or certified wall (no classical family reaches a class), or a residual
  naming the open part;
- **S** an admission by the checker;
- **E** a claim about another question derived from a checked claim.

Examples: the law of a+b multiplies characteristic polynomials; the binomial
transform shifts every root by one; decimation takes a power of the companion
matrix; a checked invariant of F is an invariant of F∘F, of a conjugate map, of
a product system and, in its lowest degree, of the linearization; an exclusion
for F transfers to F∘F, a conjugate, the inverse map and an enclosing system; a
root modulo p lifts to p² by Hensel's lemma; roots combine by the Chinese
remainder theorem; a representation of a/p gives the family x_i·k for the class
0 mod p.

The move bench runs every operator on its fixtures in a fresh runtime. It counts
only the events that produced the objects the operator returned. An operator
passes when its declared directions equal the union observed over its fixtures,
every returned checked object is admitted again by a fresh checker call, and its
argument and output kinds match its signature. All 219 pass: 118 have an N
component, 53 W, 211 S and 79 E. Together with the subreasoner moves, every
direction of the pyramid now has more than one hundred moves. A package check
changes one operator's declared directions and requires the bench to fail.
Directions are observed on fixtures, not proved for every input. Five operators
are anytime moves (below); the bench runs them whole and counts their breaths.

### Derivations

A `derived` claim names a rule, the identities of its premises (the digest of
each premise's kind and data) and the statement that follows. The checker takes
one more thing for this kind only: a way to look up an admitted claim by its
identity, which the runtime supplies from its own workspace. The checker never
verifies the premises again; it verifies that the statement is exactly what the
rule gives from what the premises state. Four rules exist. `range_union`: two
admitted ranges of one question that touch or overlap give the range from the
lower start to the further end. `theorem_range`: a theorem whose range ends at
h, and an admitted range that starts at or before h and reaches past it, give
the same theorem with the further range end. `range_extend` is a derivation
with a computed part: from an admitted range [lo, h) it states [lo, hi), and
the checker verifies only the new numbers, each by a cover class at or above
its family threshold, by a witness the proof carries, or by a proper divisor
d >= lo of n, which the checker finds itself by trial division (a/(t d) follows
from a/d, and d lies in the premise or earlier in the new part). So a proof
part carries witnesses only for the primes and the few numbers whose divisors
lie below lo; on Schinzel's 11/n, where the cover leaves 34,611 of 83,160
residues open, a plain chunk claim had to witness 42 percent of its numbers
and took twenty minutes, and the extension takes seconds. `theorem_multiples`
closes a theorem under divisors: a/(p n') follows from a/n', so a residue the
cover leaves open is still represented when a prime p of the modulus divides it
and the residue x/p modulo M/p is reached (or reduces further), as long as the
factor taken out keeps n/t >= lo for every n past the checked range. The
premises are the theorem and its cover, named by identity; the statement
carries the open counts after closure and the range end it was closed at
(`closed_at`), which the checker and the independent verdict recount. The
closure follows the range: the counts depend on how far the range reaches, so
once the closed theorem is extended over a new chunk its closure at the wider
range is derived again, and a theorem already closed at its range is refused.
A closure that reduces nothing is derived all the same, as the record that it
was tried at that range. A derivation is sound in a workspace whose admissions
are sound; on a resume every derivation is admitted again after its premises,
and one whose premise is gone is refused.

The closure rule came from a contest. Asked to compete against her and hand
over whatever I used, I took her fifteen saved theorems and applied, with my
own code, the first thing a mathematician reaches for that her language could
not state: the set of n with a representation is closed under multiples. It
leaves the coprime open classes untouched (for 4/n and 7/n every open class is
coprime, the quadratic-residue wall) but cuts the rest: 10/n from 40,047 open
residues of 83,160 to 18,724, 21/n from 44,220 to 21,936, 11/n from 34,611 to
26,969. The rule is that method in her language; `egypt_theorem_multiples`
derives it from her own theorem and cover, and the verdict recounts it.

The divisor families came from the second contest. The primes her theorems
leave in open classes are the numbers her range chunks must witness one by one.
With my own code, over the ranges she had verified, 257,837 such primes across
thirteen problems had each been witnessed; twelve divisor families (h up to 6)
represent all but 15,474 of them, and all but 13,392 of the 294,755 in the
next million. For Erdős–Straus that is all but 2 of the 260 below a million
and all but 5 of the 229 in the next; for 7/n all 19. So the families are the
statement, for all n at once, of what her witnesses said number by number, and
they leave the search to a residual of a few percent of the open-class primes.

The rules let her verified range grow past the checker's bound on one claim
(2,000,000 numbers). `egypt_range_chunk` extends the admitted range from the
least n past its frontier, by a chunk as long as the base range and up to forty
times `verify_to` (ten at first, raised as her rounds reached each frontier);
`egypt_theorem_range` extends her theorem over the result;
`egypt_range_union` joins two separately verified ranges. Each is tried once
per state of what it reads. `egypt_theorem_multiples` closes the theorem whose
closure is due: one that names its cover while no theorem on that cover is
closed at its range, the widest range first, then the fewest open residues;
so a finer cover found later gets its own closure, extension and closure again.
`egypt_theorem_range` does not extend a theorem past one that already reaches
as far and is closed when it is, on the same cover or leaving fewer residues
open when both were closed at the same range (counts closed at different
ranges are not compared: the wider range may reduce more). Every base range,
one per cover it was verified with, is persisted with its theorems, so a finer
theorem survives a resume. The independent verdict checks derivations with its
own reading of the rules, after the claims they rest on, and the chunk proofs
number by number.

A `dfam` claim is a divisor family: a Type I solution of a/n = 1/x + 1/y + 1/z
with its parameter left free. Her classical families fix the parameters and
cover one residue class each; a divisor family ties q = ae - 1 to a divisor of
a linear form in n and so is a classical family for every q at once. `plus h`
represents every n such that n + h has a divisor q = -1 (mod ah), with
denominators ne, e(n + h)/q and n(e/h)(n + h)/q where e = (q + 1)/a; `times h`
every n such that hn + 1 has such a divisor; `square` every n such that an + 1
has a divisor q = -1 (mod a). The checker verifies the identity as a polynomial
identity in n and q on a grid larger than its degree, states the integrality
lemma (a | q + 1, h | e, and the divisor condition), and computes and sums the
first instances exactly. `egypt_divisor_families` states twelve of them (h up
to 6). A range chunk then represents a number by a divisor of its linear form
before it searches for a witness; its proof names the shapes it uses and, per
number, the shape and the divisor, and the checker and the verdict recompute
the denominators and the sum exactly, so a chunk proof stands on its own even
where the family claim is not in the workspace. With her theorem the families
say where the hard cases are: n is unresolved only if it lies in an open class
and none of n + h, hn + 1 (h <= 6) and an + 1 has a divisor in the family's
class. By the usual sieve estimate that is a set of density zero among the
primes; her language does not state that, and nothing here proves it.

The third tier of families is the `pair` shape, the Type II solutions with a
common factor h: a h n + 1 = q q' with q, q' = -1 (mod a), e = (q + 1)/a,
f = (q' + 1)/a, h | ef, and a/n = 1/(ne) + 1/(nf) + h/(ef). With `plus`,
`times` and `pair` the one-divisor grammar of Type I solutions is complete: for
f | e^2 the condition q | ne + f is always a divisibility of n + h, hn + 1 or
ahn + 1 by some q = -1 modulo a or ah. She states plus, times and pair for h
up to 6 and the square, and then extends a shape kind one step at a time while
its last two steps each carried at least sixteen numbers in her admitted
proofs: a family that pays earns its successor, up to the checker's bound of
64. Base ranges use the families as the chunks do (a `finite` claim may carry a
family table, verified the same way), so a base range verified again with a
finer cover no longer witnesses tens of thousands of numbers one by one.

Two more derivation rules compose what she has. `theorem_families` takes a
theorem and admitted divisor families of its question and states the theorem
with the list of families: an unresolved n lies in an open class of the cover,
is at or past the range end, and meets none of the families' divisor
conditions. `composite_range` takes an admitted range [lo, hi) and states that
every n below hi^2 with a divisor in [lo, hi) is represented (a/(td) is a sum
of unit fractions whenever a/d is); for a question from 2 that is every
composite below hi^2, so a range verified to two million settles the
composites to four million million. `egypt_theorem_families` derives the
first again when the families grow; `egypt_range_square` the second when the
range grows. A theorem composed with its families is terminal: it is not
extended, closed or composed again.

Two rules let her describe her residual, the numbers her chunk proofs had to
witness after the cover and the families. A `residual_predicate` derivation
names chunk proofs (range extensions with a family part) and a predicate of
a small grammar: the residue classes of n modulo a divisor of the level
modulus; the classes the prime factors of n + h, hn + 1 or ahn + 1 (h up to 6)
may take modulo a or ah; or a bound below or above every prime factor of one
of those forms. It states that every number the named proofs witnessed
satisfies the predicate and that, of a same-size sample of the numbers they
represent by a family divisor (evenly spaced through them), fewer than a tenth
do; the checker rebuilds both sets from the named proofs and evaluates the
predicate on every number, and a claim needs at least ten numbers on each
side. A `residual_break` derivation names one chunk proof and a witnessed
number of it that fails the predicate. `egypt_residual_profile` states, over
the chunk proofs a call carried in, the selective predicates of the grammar
(at most sixteen, the most selective first), leaving out one that only
restates an admitted plus or times family; `egypt_residual_falsify` tests
every surviving predicate on each chunk the call adds, stating the break at
the first witnessed number that fails it, or the predicate again over the
wider set of proofs while it stays selective. On her theorem problems no
predicate of this grammar is selective: the most selective candidate is
satisfied by two thirds to four fifths of the represented sample, so her
residual, seen through residues and the classes of prime factors of these
forms, is not told apart from what the families take (CAMPAIGNS.md records
the measurement). The fixture that exercises the rules is 4/n with the
families plus 1 and times 2 only, where the fifteen numbers witnessed in
[300, 3000) are all 1 modulo 24 and a forced witness at 3011 breaks that.

The four shapes are points of a space she can search herself. Every Type I
solution with x = n e, e = (q + 1)/a, comes from a divisor d of (n e)^2 with
y = (n e + d)/q and z = n e y/d, since then 1/y + 1/z = q/(n e) and the three
fractions sum to (1 + q)/(n e) = a/n. With d = h1 n^i e^j / h2 (i in {0, 2}, j
in {0, 1, 2}, h1 and h2 coprime), the divisibility q | n e + d is the
divisibility of one linear form A n + B by q once q = -1 (mod a h2): plus h is
(0, 1, h, 1), times h is (0, 1, 1, h), a pair h is (2, 0, h, 1) and the square
is (0, 2, 1, 1), and the rest of the space, such as n + a (0, 0, 1, 1) or
h1 n + a h2 (2, 2, h1, h2), was never given to her. A `gfam` claim names the
four parameters and instances; the checker verifies the identity as a
polynomial identity on a 12 by 12 grid and every instance exactly (y is an
integer whenever q divides the form, z when d | n e y, a condition of the
instance as h | e f is for a pair), and a chunk proof's family table may name
a general family by its parameters. `egypt_shape_search` enumerates the space
up to a level of h1, h2 (8 first, doubling while a level pays, up to 32),
measures each candidate on a sample of the numbers her carried chunk proofs
had to witness, and states, greedily by what each adds, the families that
represent at least four of them and one in sixty-four; her ranges then use
them after the four shapes, and her composed theorem names them with the
rest. On her fifth-scan residuals the families she found represent 61 to
88 percent of the sampled witnessed numbers on the four problems probed
first (CAMPAIGNS.md records the preregistered rounds).

Her language also states what a numerator's question leaves out. An
`exceptions` claim lists, for a/n with 2 <= a <= 64, every n up to a bound (at
most 4,000) for which a/n is not a sum of three unit fractions, with a witness
for every other n: two denominators leaving a unit fraction, or a proper
divisor represented earlier (a/(k d) scales from a/d). The checker certifies
each listed exception by a complete search: with x the least denominator, x
lies in (n/a, 3n/a], and 1/y + 1/z = e/(n x) with e = a x - n exactly when
(e y - n x)(e z - n x) = (n x)^2, so y and z come from the divisors u <= n x of
(n x)^2 with e | u + n x and e | (n x)^2/u + n x, and no such divisor for any x
means no representation. The verdict tool repeats the search in its own code,
and the package build checks the search against a brute force on every a <=
12, n <= 40. `egypt_exception_scan` states the set up to 2a^2 + 1 (4,000 from
a = 45) for a stated question, once per question; a refused set leaves a
residual naming the count. The library's window of Schinzel's conjecture for
the numerators she does not state (`window-schinzel-beyond-bounds`) asks for
the sets of a = 20 and 22 to 28, and each takes her well under a second. A set
says nothing beyond its bound: exceptions continue past 2a^2 (for a = 24 the
bound 1,153 is itself one), and her sets for every a from 20 to 44 hold a
prime exception in (a^2, 2a^2), as the calculations Pomerance and Weingartner
report (arXiv 2511.16817) support.

## Autonomous research agent

```text
python -I -B -X utf8 ember.py examples/agent_decide.json
python -I -B -X utf8 ember.py examples/agent_explore.json
python -I -B -X utf8 ember.py examples/agent_unit_fraction_small.json --state small-instance.json
python -I -B -X utf8 ember.py examples/agent_choose_lift.json --state lift-instance.json
python -I -B -X utf8 tools/verdict.py lift-instance.json
python -I -B -X utf8 ember.py examples/agent_collatz.json --work 2000000000
python -I -B -X utf8 ember.py examples/agent_erdos_straus.json --state es-instance.json --work 20000000000
python -I -B -X utf8 ember.py examples/open_problems.json --state her-instance.json --work 5000000000
```

`autonomous_research` states a problem in the typed language:

- `decide`: admit a claim or refute it with a checked refutation;
- `explore`: find checked facts of the requested kinds about given objects;
- `unit_fraction_cover`: cover the residue classes of a/n = 1/x + 1/y + 1/z by
  checked polynomial families, refine what stays open, and verify a finite range;
- `descent_cover`: certify T^j(n) < n class by class for a residue-class map
  such as 3n+1, refine what does not contract, verify a range and search cycles.

A run settles its problem only through checked claims, and then returns
`CHECKED_RESEARCH` with `settled`. A decide goal is proved or refuted by its
claim. A cover goal is proved when a checked theorem leaves no residue open
from the problem's least n. A descent goal is refuted by a checked cycle that
avoids 1, since the cycle's least member never falls below itself, and proved
by a descent cover that reaches every class of its modulus together with a
checked range from 2 to the cover's bound. Every other run returns `UNKNOWN`.

Each step the agent lists the open targets of its goal. It forms candidate moves
from every operator whose signature accepts a target or an object derived from
it, and ranks them by the doctrine score p=(1+S)/(2+S+F) over the smoothed mean
cost (0.01 + sum w t)/(1+S+F). A success is a checked result that changes the
goal's progress. Samples are kept per context, strategy and task, at most 128.
Reported samples from another run weigh min(0.25, 1/R), and every fifth unseen
task reverses the order. Each strategy is tried once per target (the level steps
described below once per workspace state), and a target gets at most 24 moves. A move that fails only because its work allocation ran
out is retried once with four times the allocation. A class is refined toward
the next modulus only after all three family generators have missed it. With
`extra_lifts`, she may add up to four refinement primes of her own choosing: for
each candidate prime she counts exactly how many coprime lifts of her open
classes a classical family reaches, and refines every open class by the prime
that leaves the smallest fraction of residues open. A family class q that
divides M·p but not M reaches the lifts of x whose residue modulo
p^(v_p(M)+1) equals its own, for the entries congruent to x mod q/p, so the
count needs one lookup per table modulus for each open class, not one per lift.
These are scheduling policies, not evidence.

For unit fractions she has three family generators. Two are divisor grammars:
x = (s n + c)/a with every divisor shape of N², base and extended. The third
gives the two classical fixed-parameter solution types, for any numerator a:
- Type II: x = u v d, y = u w d n, z = v w d n, with a u v d = n + e and
  e w = u + v. It is complete over every modulus a u v that divides the class
  modulus.
- Type I: x = u v d n, y = u w d, z = v w d, with (u+v) n + w = a u v w d. It
  is enumerated completely: with u = d' u', v = d' v' and u', v' coprime, u' v'
  divides the modulus and d' w divides (u'+v') m / (a u' v'), a finite set.

Each family is stated on the coarsest class its parameters need. Where the
classical generator misses at the finest level, she can claim a wall
(`nofamily`). The checker admits that claim only after enumerating every
classical parameter set for the class and finding none. She can also state
two patterns about a cover, each checked exhaustively over the coprime
residues:
- the least set of primes outside which every open class is a local square;
- the residues the open classes reduce to modulo each prime power.

From a checked finite range and the cover inside it she can state a whole
reduction theorem (`theorem`): every n >= 2 whose residue is covered has a
representation. The checker admits it only after checking each part of the
chain again. Every family of the cover holds from its threshold, the range
checks every n below its bound, and the cover's bound lies inside the range.
The theorem names what stays open: the residues no family reaches. Nothing is
claimed for those above the range.

She can also state an obstruction lemma (`obstruction`): no classical
fixed-parameter family, with any parameters and a class modulus dividing m,
reaches a coprime square class mod m. The checker enumerates every reached
class, since both parameter sets are finite at a fixed modulus. A reached
square class, named with its family's parameters, refutes the lemma. For 4/n
she proves it. For 5/n her checker refutes it. Once the lemma holds at her
finest level, square classes need no walls of their own.

Covers and descent covers may carry their chain of levels. Coverage,
patterns, density and the theorem are then decided by a sieve that lifts
only the classes no family reaches. The theorem is checked class by class:
each covered residue needs a family whose threshold is at most the
residue's first member past the checked range. Classical families may be
stated by their parameters. Every other family is saved in a compact form: a
family on n = m k + r is an identity in n placed on a class, x(k) = X(m k + r),
so a cover or a batch of families writes each identity once, as its
denominators in n, and names each family by its class, threshold and identity.
Her round-5 covers held 1,910 and 2,185 families but only 111 and 130
identities. The checker and the independent verdict each rebuild the
polynomials with their own arithmetic and check every family as if it were
written out. Strategies that fail 64 times without a success in
one context (class kind and local squareness) and one refinement level are
retired there for the rest of the run. The classical generator and the
wall certificates are never retired.

A claim the checker refuses is counted. The runtime keeps, per call, the
refused claims by move, kind and the checker's own reason, with the first
refused identity; the report carries the table (`refusals`), the total
(`refused`) and, for a round that gained nothing or refused more than it
admitted, a `diagnosis`: what was exhausted, what was refused and why, the
residual's size, and the bound each reason names from a fixed table (the
shapes a proof's family part may name, the finite range bound, the closure
residue bound, the premises a derivation may name, and the rest). A strategy
whose claims are refused eight times in a context and scope with none admitted
is retired there with the reason, whatever its context. The rounds ledger keeps
each round's refusals and its most frequent reason, and her scan treats a
problem whose last round refused at least eight claims and more than it
admitted as waiting for an instrument, naming the reason, until the code
changes. The defect the third tier's first run found (every chunk refused past
the shapes bound, the rounds ending as if exhausted) is now named in her own
report and ledger on the round it happens.

She prepares her finest level before its classes: her obstruction lemma first,
then a classical sweep that runs the generator over every class still without a
classical outcome in one move, then one batch wall claim for the classes it
missed (square classes a checked lemma settles are left out). Each level step is
tried once per workspace state, and a step already tried in the current state no
longer holds the level's other questions back. A class target with no fresh move
is looked at again only when something that can give it one changes: its own
derived objects, a new level, a lemma, the kinds available as companions, or,
above the finest level, a retirement in its own context and level. Her library
also shortens retirement: a strategy it has seen fail at least 64 times, with no
success, in a context gets 8 tries per level there before it retires. That is a
scheduling prior, not evidence. Contexts saved before the numerator was part of
their name are read as the current numerator only when every saved record has
it. Walls carried over from a related problem wait until her lemma at their
level is settled. The walls it implies are not checked again, and a saved state
keeps the lemma instead of them. When the state reaches its bound, the
scheduling memory of other records is trimmed first, then the evidence of
records whose claims she carried over and checked again, and her own new
evidence last.

Every report mines its own failures. It lists the open targets, the moves each
received and the residuals they left, and a profile of what stayed open (for
unit fractions, the primes at which each open class is a non-residue). Measured
strategy outcomes are kept in a bounded library in the state file, and later
problems read them as discounted reports. Each goal names its closest related
problems; for 4/n these are 5/n and 6/n with the same statement.

The agent invents moves in three ways:

- when a checked result's derivation chains two to four operators, the chain
  becomes a macro that replays it on new targets;
- every 25 moves, a pair of operators with at least one success each, where the
  first produces the kind the second consumes, is proposed as a composition and
  promoted when it first produces a checked result;
- the extended unit-fraction ansatz turns a family found outside the base grammar
  into a reusable template object.

Invented moves are reported with their origin, uses and successes. Saved objects,
including pattern, density and wall claims stored with a digest reference to
their cover, are proposals until the checker admits them again on resume. If a saved object is
refused, the scheduling memory built on it is discarded and the search is redone.
The report lists only checked results, residuals, invented moves, the scheduler's
ranking, the directions observed and the refusals with their reasons.

### Moves she can leave and come back to

Five operators are anytime moves: the base and extended divisor searches, the
classical sweep, the range verification and the range chunk. Each is written
as a generator that breathes at natural points (after a parameter pair, a
class, or 64 numbers). A move runs in slices: at the first breath past the
slice (half its work bound, at most 4,000,000 units) it waits with its own
budget and its place in the search. Each step she chooses again between the
best fresh move of the first open target and the waiting moves, by the same
doctrine score, a waiting move's divided by one plus the slices it has run
without progress. So a long search that keeps producing keeps its place, a
search that stalls yields to other moves and resumes when nothing better is
left, and she can switch at any breath. At most eight moves wait; with the
table full she resumes one rather than starting another, so every search she
starts runs to its end within the call or to its work bound, which is four
times its allocation over all its slices (what an escalated plain move gets).
A move still waiting when the call ends no longer starts over. The scheduler
asks it to finish with what it has: at its next breath the operator receives
the word `checkpoint` and states the part it verified (a base range or a chunk
states its prefix, a sweep the classes swept, a divisor search nothing and no
miss), with a quarter of its allocation to state it, and the checker admits
the part like any other claim. The same happens to a move that reaches its
total work bound. The report counts slices, resumes, switches, the moves
settled this way and the objects they stated.

### What counts as attempted

Her memory of tried moves is bounded (6,000 keys per problem), and a resume
can forget attempts. A residual is now the record of an attempt: the runtime
stamps every residual with the move that left it, restored refinement trees
stamp theirs with the generator whose miss they record, and a deterministic
one-argument move is never proposed again on an object that carries its
residual. Her Collatz search at 2^20 stalled on exactly this before the rule
existed (see `CAMPAIGNS.md`).

## Launch: two open problems

Both runs used this package with Python 3.11.15 on Linux x86_64, from a fresh state, in one run each.

### The Erdős–Straus conjecture

The conjecture (Erdős and Straus, 1948) states that 4/n = 1/x + 1/y + 1/z has a
solution in positive integers for every n >= 2. It is open. It has been verified
far beyond any bound used here, and Mordell showed polynomial identities for every
residue class modulo 840 except 1, 121, 169, 289, 361 and 529. Polynomial
identities cannot cover classes that are quadratic residues: Schinzel's theorem
(Funct. Approx. Comment. Math. 28, 2000) says that if 4/(at + b) is a sum of
three unit fractions with polynomial denominators then b is a quadratic
non-residue modulo a, and Elsholtz and Tao (J. Aust. Math. Soc. 94, 2013,
Prop. 1.6) show odd squares have no Type I or Type II solutions. Her
`obstruction` lemma below is a checked rediscovery of that theorem, not a new
result. The verified range stands at 10^17 (Salez, 2014), with a 10^18 claim
of 2025 not yet refereed. Ember was given only the problem statement
`examples/agent_erdos_straus.json`: numerator 4, three terms, n >= 2, base modulus
840, refinement primes 11, 3 and 3 (moduli 840, 9,240, 27,720 and 83,160), and a
checked range below 100,000.

Ember ran 4,289 moves in 159 s (185,105,722 work units) and ended when no open
target had an untried move. Its status is `UNKNOWN`.

| Modulus | Covered residues | Open squares | Open non-squares | Square-class pattern |
|---|---|---|---|---|
| 840 | 834 of 840 | 6 | 0 | checked |
| 9,240 | 9,206 of 9,240 | 30 | 4 | refuted at 2041 |
| 27,720 | 27,624 of 27,720 | 90 | 6 | refuted at 2521 |
| 83,160 | 82,876 of 83,160 | 270 | 14 | refuted at 2521 |

- **Mordell's classes rediscovered.** Modulo 840 her 190 checked families cover
  every class except exactly 1, 121, 169, 289, 361 and 529. She proposed, and the
  checker admitted, the claim that for this cover the uncovered coprime classes
  are exactly the coprime squares.
- **Refinement.** She refined the six classes by 11, then by 3 twice, and found 37
  more families. At every level the open square classes are exactly all coprime
  squares: 6, 30, 90 and 270. Her own square-class conjecture was refuted by the
  checker at 9,240, 27,720 and 83,160, where 4, 6 and 14 non-square classes stayed
  open under her grammar. Refining by 3 closed 6 of the 12 lifts of the four open
  non-square classes mod 9,240: a limitation she found and partly removed.
- **Finite range.** Every n with 2 <= n < 100,000 has a checked representation:
  99,656 by a family at or above its threshold, 135 by explicit witnesses and 207
  by scaling a checked divisor.
- **Invention.** She invented 16 templates outside the base grammar and 16
  macros. Two type-directed compositions were promoted after their first checked
  success. The derivation macro for zero classes (greedy witness, then the class
  0 mod p) was reused successfully.
- **Independent check.** An independent script, outside Ember, evaluated all 227
  saved families at 50 class members each (11,350 instances, none wrong). It also
  replayed the finite range for all 99,998 values of n.

What this establishes: every family, cover, density, pattern and finite range in
the report was admitted by `lexicon_check.py`, and the saved cover and range
replay with only the checker present. Every n below 100,000 has a checked
representation, and every n in a covered class has one at or above its family's
threshold. What it does not establish: anything about the uncovered classes. The
square classes are the known obstruction to polynomial identities, and the
non-square classes left open are limits of this grammar and depth, not
counterexamples. The conjecture remains open. Rediscovering Mordell's classes and
observing the square-class pattern are results for this program, not new
mathematics.

### The Collatz stopping-time sieve

The Collatz conjecture states that iterating T(n) = n/2 or (3n+1)/2 reaches 1 from
every positive integer. It is open. The stopping-time sieve (Terras; Everett)
certifies residue classes modulo 2^k on which some iterate falls below n.

`examples/agent_collatz.json` certifies descent to modulus 2^10. The report run
below used depth 12 and a finite check to 10^6. Ember ran 849 moves in 2.0 s
(3,591,929 work units):

- the open classes modulo 2^k for k = 1..12 are 1, 1, 2, 3, 4, 8, 13, 19, 38, 64, 128
  and 226;
- 57 checked descent certificates lift to a checked cover of 3,870 of the 4,096
  classes modulo 4,096;
- every n with 2 <= n < 1,000,000 falls below itself, so every n below 10^6 reaches
  1 by induction from n = 1;
- the cycle search found no cycle avoiding 1 from starts below 2,000. The same
  search on the map 5n+1 finds the cycle through 13 in the move bench.

A package check recomputes the open counts independently, by exact parity
simulation of every residue.

As with Erdős–Straus, the surviving classes are where the problem stays open.
Descent on a class says nothing about its survivors, and verification below a
bound is not a proof.

## Campaigns: problems given, walls mined, instruments built

After the launch, Ember works in campaigns. `CAMPAIGNS.md` is the ledger: for
every round it records the task, the fingerprint of the code she ran, the
moves and time, what she proved, the verdict, and the failures mined.

The loop:

1. Claude supplies only the problem, as a task in her typed language, with
   no answer and no hint.
2. She works alone, offline and without a language model. She chooses her
   own moves, her own refinement primes, and which patterns and lemmas to
   state.
3. Her checker admits each claim. Then `tools/verdict.py`, which shares no
   code with her, tests itself on known-true and known-false claims and
   recomputes every saved claim. Each claim is VERIFIED, REFUTED or
   UNRESOLVED. One bit goes back to her: "verified", or "no, keep thinking".
4. Her failures are mined from her reports and from live profiles.
5. When she failed because of her own limits, Claude builds the general
   instrument she lacked and never the answer. The instrument passes the
   move bench and the package checks, and she runs again.
6. Strategy outcomes carry over to later problems as discounted reports.
   Checked families, covers, walls and lemmas carry over to problems about
   the same equation. Each report names the closest related problems, and
   5/n was the one her first campaign offered.

Results so far. Each is admitted by her checker and VERIFIED by the
independent verdict. None settles an open problem. The Collatz campaign is a
closed check against known counts, compared with an independent parity
simulation she never sees.

- **Erdős–Straus, 4/n.** In round 5 she chose the primes 13, 17 and 2
  herself, counting every lift exactly, and proved that every n >= 2
  outside 26,262 residue classes mod 36,756,720 has a representation (an
  open fraction of 7.14 × 10^-4). Of the open classes, 25,920 are coprime
  squares, the known obstruction, which her own lemma shows no classical
  fixed-parameter family reaches. The other 342 are non-residues at 11, 13
  or 17, where she certified walls. The round took 370 s; the same round
  on the code before the upgrade took 4,852 s.
- **Sierpiński, 5/n.** In round 6 she chose 13, 19, 23 and 17, counting
  every lift exactly, and proved that every n >= 2 outside 821 residue
  classes mod 8,031,343,320 has a representation: about one open class in
  ten million (1.02 × 10^-7), against 1.04 × 10^-6 in round 5, when a cover
  at that level did not fit her checker's bounds. The round took 738 s. At
  472,431,960 every open class is 1 mod 5, 7 and 13, 1 mod 9, and 1 mod 4.
  For 5/n the square classes are not the obstruction. She stated the obstruction lemma that holds for
  4/n, and her checker refuted it with her own witness: Type II (1, 1, 1)
  reaches the square class 4 mod 5.
- **Collatz sieve to 2^18 (closed).** In a first run her open counts
  matched the known counts at 16 of 18 levels. The two misses exposed a
  defect: an invented macro could refine a class without trying to
  certify it. After the fix, all 18 levels match (7,495 open classes mod
  2^18), and her sieved descent cover at 2^18 covers exactly
  254,649 classes.

The instruments built from her failures, in order: a classical Type I and
Type II family generator; wall certificates; signature and local-image
patterns; her own choice of refinement prime; failure mining, a strategy
library and the independent verdict; a reduction theorem checked as a chain;
a compact family encoding; a theorem checked class by class; sieve
certificates that lift only open classes; learned retirement of futile
strategies per context and level; a warm start for new problem statements;
complete Type I enumeration (the bound of 120 had hidden 26 reachable
classes at 1,580,040); an obstruction lemma that replaces thousands of
square walls, provable for 4/n and refuted for 5/n; incremental bookkeeping;
Pollard-rho factoring; shorter certificates (families named by their
parameters, wall batches, ranges saved by cover reference); saved and
independently verified refutations; macros that obey the goal's policy at
every step; sieved descent covers; and, from her round-5 profile, her lemma
first with whole-level sweeps, rescans only when a class can gain a move,
priors from her own library, a refinement prime chosen on exact counts,
carried walls settled by her lemma, a Type II index in the checker, and a
state bound that keeps her newest results; then a compact proof format (each
identity written once, families named by class, threshold and identity) and
a larger state, 8 MiB, since raised to 24 MiB. Each is described, with the
failure that prompted it, in `CAMPAIGNS.md`.

## The open-problem library

```text
python -I -B -X utf8 ember.py examples/open_problems.json --state her-instance.json --work 5000000000
```

`problems.json` is her library. It has two tiers.

- **Stated problems** (148). Each is a task in her language that she can run.
  - *Open* (25): the Erdős–Straus conjecture, Sierpiński's 5/n, Schinzel's
    conjecture for a/n with a = 6 to 19 and 21, and the Collatz conjecture
    (descent classes to 2^20). The numerators 12, 15 to 19 and 21 became
    stateable when her statement bounds widened (numerators up to 64, least n up
    to 100,000); each starts above every exception an exhaustive search here
    found below 100,000 (for 16/n that search found exceptions at 78,721 and
    83,449, past an earlier search to 40,000), and her certified exception sets
    confirm each least n (the number below it has no representation by the
    complete search). Seven state a record one step past its frontier, as an
    explore task her searches resume across calls: 122 points of the 61 grid
    with no three in a line, colorings of 1..344, 1..516, 1..893 and 1..1188
    in 7, 8, 10 and 11 colors without a monochromatic 3-term progression, a
    circulant graph on 82 vertices for R(3, 16), and a covering system with
    least modulus 8.
  - *Closed* (5) calibrate her: the Collatz sieve to 2^18, whose counts are
    known; 3/n and the halving map, which are true; and the 3n − 1 and 5n + 1
    maps, which are false because each has a cycle.
  - *Windows* (126): a finite exact view of a catalog problem, one per problem
    that has one (below). A window never settles its problem. One window asks
    for certified exception sets (`exceptions` claims) instead of a window
    tool's answer.

  A task states the part of its problem her checker can decide, and each entry's
  `scope` says what a result means for the problem.
- **The catalog** (135 entries). These are open problems she cannot state as
  questions, from the Riemann hypothesis to the Hadamard conjecture. Each entry
  names what her language lacks (`needs`, 30 kinds described in the file) and
  points to its window when it has one; 125 do. The ten without one are named in
  CAMPAIGNS.md. It is a start, not every open problem.
- **Resolved** (6): problems that left the catalog when the literature settled
  them in 2024–2026 (the moving sofa, the cycle double cover, Chvátal's
  conjecture, Sendov's conjecture, Schiffer's conjecture and the irrationality of
  zeta(5)), with sources. A status check of every entry by web search on
  2026-09-25 also restated six entries to their still-open form (the unit
  distance growth order, the Jacobian conjecture in dimension 2, Borsuk's
  problem in dimensions 4 to 62, hot spots for convex planar domains, Kakeya
  from dimension 4, and unforced Navier-Stokes).

`open_problems` scans the library, chooses one stated problem and runs one
round on it. Her choice reads only each stated problem's id, status and
task, together with her own records in the instance state. Titles,
statements, known results, sources and the catalog are for people, and a
package check rewrites them to confirm they change nothing. The rule is the
doctrine score over her last four rounds on each problem: a round that gained
g new checked results is a success of weight g / (g + 64) and a failure of
the remaining weight, and its seconds are its cost, so a round that gains
little counts little and a problem whose recent rounds gain nothing falls
back. An untried problem scores p = 1/2 over m = 0.01, so every problem gets a
first round. After that, the problems where her rounds keep producing checked
results cheaply come first. Ties go to open problems, then windows, then closed
problems, then to the problem type her strategy library has the most successes
with, then to the id.

She also proposes problems of her own. A settled window is offered again with
larger bounds (the widening rule of its family, the one `window_widen` uses),
up to three times over, each level only once the level below it is settled.
A widening stays within the family's own bounds, so nothing is proposed that
the checker would refuse on sight. It is ranked by the rounds of the window it
widens until it has its own, keeps its rounds in the ledger under its own task
like any problem, and appears in the scan's ranking with `proposed_by: ember`. So her frontier on a
catalog problem grows as far as her rounds keep succeeding, without a new
library entry.

Her rounds are kept in one ledger record per instance state: for each problem,
the generation, status, checked results gained, moves and seconds of each round.
The ledger sits beside her strategy library and is never evicted. When her records
outgrow the 24 MiB instance state, the evidence of her largest other records moves
into files beside the state, one per record (`<state>.evidence/`, each named by
its content's digest and bounded like a state); a record keeps its file's name,
digest and object count. When the 128-record bound evicts her oldest record, its
evidence moves to such a file as well and the ledger keeps the reference, so a
library larger than the bound loses no checked result. A later round on the
problem reads its evidence back when the digest matches, the independent verdict
does the same with its own code, and a missing or altered file is refused: the
problem's search is then simply done again. Files the state no longer names are
removed after it is written. A problem she settled, or left with no
untried move, waits until her code changes: not any change, but a change of
what a round on it can depend on. Each round records, beside the whole
fingerprint, the fingerprint of the core (scheduler, runtime, checker) and of
the operator modules whose moves can apply to the problem, found by closure
over the language's signatures from the problem's own object kinds (a window's
question kinds bring the window tools). A change to the Collatz operators
leaves a unit-fraction problem's rounds valid, and it is not checked again. A window settles when every one of its objects has a checked
answer. `"run": false` returns her ranking and her choice without running. When
nothing is left, the scan returns `UNKNOWN` with the backlog, which now also
counts, for each missing kind, how many of its catalog problems have a window.
When the record bound is reached she forgets the records of settled problems
first (their evidence stays on file and their problem waits for new
instruments), then the oldest of the rest, so an open problem's record stays
as long as it can. She runs her own loop: `--calls N` runs the task N times in
one process, each call reading and writing the state as a separate call would,
`--out DIR` writes each call's result, the seconds and a log line to the files
a shell loop would write, and `--seconds S` stops starting calls after S wall
seconds; a scan that finds every problem waiting for new instruments stops.
The library's statuses and prose are not evidence, and she never reads them.

Her first scan of the whole library took 202 calls on one instance state.
Every problem got a first round, the open ones first. All 125 windows settled
in their first round, and the closed calibrations came out as known. No open
problem was settled. The independent verdict, archived evidence included, found
33,890 of her saved claims VERIFIED, none refuted and 23 UNRESOLVED (21 window
values in families it has no rule for, and two theorems an older save had cut
from their ranges). The scan exposed the byte bound, the record bound and a
slow save at the bound; CAMPAIGNS.md records each wall and its instrument.

Her second scan (29 calls, her own choices among the 18 problems still open to
her) proved first theorems for Erdős–Straus at 4/n and for Schinzel's 7/n, 18/n
and 21/n. It narrowed three others and proved the two cut theorems again. Its
verdict found 92,316 claims VERIFIED, none refuted, and only the 21 window
values unresolved. It also exposed a Collatz stall: her rounds re-tried failures
they had forgotten. A saved residual now counts as the record of an attempt.

An independent verdict's result can be recorded in her state with
`tools/ingest_verdict.py <state> <verdict.json>`: the bit, the counts, the
verdict's digest and the state's go into the rounds ledger record, which her
calls carry forward. That is the one bit that goes back, kept where it can be
inspected beside her rounds; she never reads the counts. Work units on the
prover's side are priced at about a microsecond of the machine they were
measured on (the witness search's price): a cover-loop step costs one unit a
number plus one per ten moduli, a factor check half the bit length of the
number, a family step half the bit length of its linear form. The checker's
charges are its own and unchanged.

Her later scans (calls 232 to 1,709, at seven fingerprints) ran with the
instruments of the sections above: anytime moves, derivations, attempt records,
gain-weighted choice, self-widened windows, the closure of a theorem under
multiples, the divisor families, and from call 1,270 the pair families, her
own extension of the family list, the compositions, checkpointed moves and her
own loop, and from call 1,485 the refusal accounting, the residual mining and
her own shape search over the general family space, with the frontier at forty
chunks. Each change of her core makes every settled problem eligible again,
so each of those scans began with a re-check wave of about two hundred calls
of a few seconds. Her theorems now cover Erdős–Straus at 4/n, Sierpiński's 5/n
and thirteen of Schinzel's numerators; their verified ranges grew from 100,000
to about four million, each closed under multiples at
its range, and from
call 1,063 each theorem round states its divisor families (17 to 30 shapes
from call 1,270) and represents by them all but a few percent of the primes
its chunks reach in open classes. The verdict on her state after call 646
found 116,552 claims VERIFIED, none refuted and 27 UNRESOLVED (the window
values without an independent rule); after call 1,269, 124,455 VERIFIED
(101,320 of them walls), none refuted, 27 UNRESOLVED, 37 self-test cases, in
4,232 s. The verdict on her final state after call 1,484 (215 calls of the fifth scan) found 126,483 claims VERIFIED (101,968 of them walls), 0 refuted, 27 UNRESOLVED (the window values without an independent rule), 45 self-test cases passing, in 3,916 s; the bit returned to her is `no, keep thinking`.
The verdict on her final state after call 1,709 found 112,847 claims VERIFIED (102,544 of them walls), 0 refuted, 27 UNRESOLVED (the window values without an independent rule), 57 self-test cases passing, in 5,208 s; the bit returned to her is `no, keep thinking`.
CAMPAIGNS.md records each contest and what it transferred; RESEARCH_INQUIRY.md is
the research brief written for a research session on which open problems a
finite certificate can settle.

The library grows by editing `problems.json`. A stated problem needs a
unique id, a status (`open`, `closed` or `window`) and a task that
`autonomous_research` accepts; a window also names its catalog problem
(`window_of`). A catalog entry needs a unique id and at least one `needs` kind
named in the file. The package checks refuse a library that breaks either rule.
Editing the library does not change her fingerprint, so it does not make an
exhausted problem eligible again. Only a change to her code does that.

## Window tools

```text
python -I -B -X utf8 ember.py window-task.json --state her-instance.json --work 2000000000
```

The catalog named 30 kinds of mathematics her language lacked. Each now has a
tool: 29 window question kinds, one per kind of view, and wider statement
bounds for unit-fraction problems. A window question names a family and its
parameters, for example

```json
{"kind": "primes_q", "data": {"family": "tally", "params": {"pred": ["and", ["prime", "n"], ["prime", ["add", "n", 2]]], "lo": 2, "bounds": [1000, 10000, 100000, 1000000]}}}
```

and its answer is a claim of one of three kinds: a **value** the checker
recomputes, a **witness** it verifies, or a **proof** it replays. The 123
families (81 value, 40 witness, 2 proof) include:

| tool | families (examples) |
| --- | --- |
| `census_q`, `primes_q`, `arith_q`, `dioph_q`, `bigint_q`, `field_q` | tallies and member lists over a typed predicate language (primes, divisor functions, Fibonacci numbers, factorials); record prime gaps, Goldbach tables, Gilbreath rows; totient fibres, odd weird numbers; Euler bricks, power sums, abc triples, Pascal multiplicities, three cubes, congruent numbers; Lucas-Lehmer, Pepin, Wall-Sun-Sun, Proth and N+1 tests, Pratt certificates; irregular pairs, class numbers, small Mahler measures |
| `orbit_q`, `covering_q`, `dynamics_q` | reverse-and-add, residue-class maps, Conway's amusical permutation, aliquot sequences; covering systems and covering sets; certified Mandelbrot grids, x2 x3 orbits, averaged Liénard zeros |
| `zeta_q`, `const_q`, `digits_q`, `interval_q`, `approx_q` | interval arithmetic: signs of Hardy's Z and of L(s, chi_4) on the critical line, zero-count bounds, certified sizes of zeta, lattice-point and divisor errors; enclosures, continued fractions, excluded rationals, relations and polynomials for constants; digits of pi; Mahler's Z-number sets; Littlewood products, lonely runner times |
| `graph_q`, `setsys_q`, `additive_q`, `design_q`, `sat_q`, `circuit_q` | colorings, Hamiltonian paths, graceful labelings, cycle double covers, Ramsey graphs, strongly regular parameters, small censuses (reconstruction, Hadwiger, Sidorenko, Erdős-Hajnal, oriented graphs); union-closed and sunflower-free families, balanced pairs, Rota's bases; prime progressions, Sidon sets, four cubes, sums and products; Hadamard matrices, projective planes, orthogonal Latin squares; SAT witnesses and RUP-checked refutations; exact circuit sizes, isomorphism, unique games |
| `config_q`, `kakeya_q`, `knot_q`, `algebra_q`, `group_q`, `variety_q`, `spectrum_q`, `lattice_q`, `operator_q` | unit distances, Heilbronn sets, no three in line, convex-free sets, kissing arrangements, rational distances, unit-distance graphs in Q(sqrt a, sqrt b), Mahler volumes, illumination, Borsuk partitions, lattice packings, points on the sphere with bounded energy; finite-field Kakeya sets; Jones polynomials, the Kashaev invariant, inscribed squares; Galois groups, plane polynomial inverses, matrix multiplication schemes, Casas-Alvero searches; coset enumeration, Andrews-Curtis trivializations; point counts and rational points; Laplacian eigenvalue counts; Ising and Galerkin identities; invariant subspaces |

Her 51 window operators (`ops_wnum.py`, `ops_wdisc.py`) propose answers: one
compute move per tool asks the checker's family for a value; search moves find
witnesses with her own code (circulant Ramsey graphs, flip graphs over GF(2)
with a sign lift for matrix multiplication, best-first Andrews-Curtis moves,
hill climbing for Heilbronn sets, projected gradient descent moved to exact
rational points of the sphere, a CDCL solver that logs RUP proofs, Proth bases
and Lucas parameters, Pratt certificates); `window_widen` restates a checked
window with larger bounds, and `window_refute` refutes a value that does not
recompute. The explore goal `window` asks, for each object, for the answer
kind its family gives.

Four of the search moves work at records the research brief ranked
(RESEARCH_RESULTS.md) and resume across calls: each runs within its move's
work bound and, when it finds nothing, leaves a residual carrying its state
(a coloring and its conflicts, a restart count and seed, the next candidate
lcm, a connection set), from which its next call continues; the explore goal
proposes it once per call on each target. `waerden_search` colors 1..n with r
colors and no monochromatic k-term progression (`waerden_coloring`): by
backtracking for n <= 30, else by Rabung's power-residue colorings for primes
p = 1 (mod r) near n/(k-1), cut to their longest progression-free prefix and
extended at either end by backtracking, then by a tabu search on colorings of
Z_m (m the least period at least n/(k-1) with no prime factor below k, so
that a periodic extension is safe) whose period escalates when it stalls.
`nothree_search` places 2n points of the n x n grid with no three in a line
(`no_three_in_line`, now to n = 64): exhaustive for n <= 12, else symmetric
backtracking with randomized restarts, most constrained row first, under a
90 degree rotation for even n and, for odd n, the rotation except one pair
of points on the main diagonal (the symmetry of the known large odd
solutions). `covering_lcm_search` finds a covering system with distinct
moduli at least m0 (`min_modulus_covering`) over 13-smooth candidate lcms in
increasing order, choosing residues greedily for the smaller moduli and
completing with a depth-first search over the larger ones. `circulant_search`
finds a circulant graph with no clique of size s and no independent set of
size t (`circulant_ramsey`, checked through vertex 0 by vertex transitivity,
a branch and bound with a greedy coloring bound in the checker and, in its
own code, the verdict) by a tabu search over connection sets scored by the
triangles and the independent t-sets through vertex 0. Calibrations the
package checks: W(3, 3) > 26 and, in the ledger, W(4, 3) > 75; the 16 grid
under rot4 and the 17 grid under rct4 (and 18, 20, 24, 25 in the ledger);
the least lcm 12 for least modulus 2 and 120 for least modulus 3; the
circulant (3, 5)-, (3, 6)- and (3, 9)-graphs on 13, 16 and 35 vertices. Seven
open problems state the records themselves: the 61 grid, W(7, 3), W(8, 3),
W(10, 3) and W(11, 3) one past their records, R(3, 16) on 82 vertices, and
a covering with least modulus 8; what her loop reaches on them is in
CAMPAIGNS.md, and each problem's scope says what not finding a witness
shows, which is nothing.

Every one of the 125 windows settles under her agent in seconds (most below
five). The values that published tables also list agree with them: twin prime
pairs below 10^3..10^6 (35, 205, 1224, 8169), Sophie Germain primes (37, 190,
1171, 7746), prime quadruplets (5, 12, 38, 166), primes n^2 + 1 (112, 841,
6656), the 22 record prime gaps below 10^7, the Mersenne exponents below 3000,
the ten zeros of zeta below height 50, the Pascal multiplicities up to 10^9
(3003 eight times; 120, 210, 1540, 7140, 11628 and 24310 six times), the
13 amicable pairs below 10^5, M(1000) = 248,083 distinct products, Brocard's
4, 5 and 7, and Lehmer's polynomial as the only reciprocal degree-10 measure
below 1.18 (with its reflection). What a window shows is exactly its scope: a
finite range, a box, one construction. It settles nothing about its problem.

`tools/verdict.py` now also judges window claims with `tools/verdict_windows.py`,
which shares no code with her producers or checkers. It recomputes 59 value
families and rechecks 37 witness and 2 proof families with its own code (98 of
the 115 family names), among them its own Todd-Coxeter enumeration, its own
class numbers of real quadratic fields (reduced-form cycles, with the unit's norm
from a continued fraction period), exact Laplacian inertia by congruence with
symmetric pivoting, and its own digits of pi. For the other 17 it answers
UNRESOLVED and names the family: the interval-arithmetic families (zeta,
constants, Littlewood, Mandelbrot, Kashaev, divisor errors), Galois groups,
Mahler measures, Jones polynomials and pebbling numbers. So a window verdict's
one bit is "verified" only when every family it holds has a rule. On the 125
windows it verified 137 claims, refuted none and left 21 unresolved, so its bit
is "verified" for 110 windows.
Building the tools found four defects that her checks then caught or that the
package now tests: the N+1 test for k·2^n − 1 was wrong (it would have refused
every true prime above the Miller-Rabin range); the RUP checker missed unit
steps in clauses with a repeated literal; the Jones polynomial had the writhe
sign reversed; and a flip in the matrix multiplication search changed the tensor
for negatively shared factors.

## Task and result interface

The CLI accepts a JSON task filename, optional `--state`, and optional `--work`.
`python -I -B -X utf8 ember.py --capabilities` returns the supported interface.
The Python entry point `ember.solve(...)` is available to an application embedding
the owned code; the CLI is the simplest separate-process interface for other AIs
or local programs. It never needs an LLM call to execute a task.

The included process client validates the runtime capability version and checks
that each returned status agrees with its exit code:

```text
python -I -B -X utf8 tools/helper_client.py --capabilities
python -I -B -X utf8 tools/helper_client.py examples/word_identity.json --state helper-instance.json
python -I -B -X utf8 tools/helper_client.py examples/discover_word_recurrence.json --state helper-instance.json
```

The client returns an `ember.helper.v1` JSON envelope containing the original
result. Reuse the same state path to preserve the instance across calls. A client
failure, such as a timeout or incompatible response, returns `CLIENT_ERROR` and
exit code `4`; it does not invent a mathematical outcome. Its timeout limits how
long the client waits, not operating-system CPU or memory usage. Its response-read
bound does not impose a child-process disk quota.

| Query | Operation |
|---|---|
| `transition_count` | Exact integer weighted walks, with direct iteration or a checked quotient transformation. |
| `test_overlap_shortcut` | Search a bounded binary-word grammar for a counterexample to the supplied shortcut claim. |
| `polynomial_consequence` | Find a flat or explicitly requested single-guard rational polynomial certificate, or an original-task counterexample. |
| `discover_guards` | Generate and check sufficient equality conditions and group proven equivalent forms. |
| `word_avoidance_identity` | Check a rational generating function against the original pair of forbidden binary words. |
| `discover_recurrence` | Propose and check an all-index scalar recurrence from the original integer transition system. |
| `discover_word_recurrence` | Discover an all-length recurrence for counts avoiding two original binary patterns. |
| `discover_invariant` | Generate a nonconstant polynomial conserved by the original polynomial transition, with optional initial orbit value. |
| `prove_recursive_identity` | Attempt an original Nat/List equation using explicit rewriting, structural induction and bounded checked lemma invention, or return an original counterexample. |
| `source_research_episode` | Interpret bounded structured sources, preserve original claims and questions, and attempt checked same-definition proof transfer. |
| `research_campaign` | Persist a bounded sequence of original-task and repair attempts across calls. |
| `apex_research` | Plan one to sixteen originals from the four TPM faces, with synthesized law, orbit and memory-transfer routes; admit only original-task certificates. |
| `prove_orbit_exclusion` | Decide whether an exact rational polynomial orbit reaches a target: witness, repeated state, checked separating invariant, clocked drift law or ranking polynomial. |
| `count_word_avoiders` | Count binary words of a given length avoiding two patterns, by exact automaton iteration or a checked all-length law. |
| `discover_generating_function` | Return a checked rational generating function for a word or matrix carrier. |
| `certify_minimal_recurrence` | Return a checked all-index recurrence with a nonzero Hankel determinant excluding every lower order. |
| `certify_eventual_recurrence` | Return a reduced generating function with a Bezout coprimality certificate: the least order of a recurrence valid for all large indices, and where it starts. |
| `autonomous_research` | Run the offline agent on a problem stated in the typed language: decide, explore, cover unit-fraction classes or certify descent; report only checked results. |
| `open_problems` | Scan the problem library (open, closed and window problems), choose one by her own records, and run one round on it; report her ranking and the instrument backlog. |

Exit code `0` means the returned result is closed within its stated scope. Exit
code `3` with `status: "UNKNOWN"` means the evidence did not settle the request
within its bounds. Exit code `2` with `status: "REFUSED"` means a task or state was
invalid or unsupported. Argument-parser errors also exit with code `2` but may
print usage text instead of JSON. Callers must examine the status and mathematical
scope, not equate all exit-zero results with proofs of the same claim.

For matrix tasks, `--strategy auto`, `direct` and `quotient` choose an existing
route. Direct numerical answers use exact arithmetic; quotient transformations
also receive a distinct equation check. The algebra and word certificates are
checked by separate exact code against the original task. These checkers are
custom software, not a formally verified proof-assistant kernel.

Exact answers can exceed Python's default 4,300-digit limit for converting an
integer to text. The CLI and helper raise that limit to 100,000 digits, so such
answers print as JSON; earlier generations exited with a traceback instead of a
result. `--layer apex` wraps a single original as the only obligation of an
`apex_research` task; policy flags for individual subreasoners then stay at their
defaults because the apex chooses routes itself.

`--work` limits charged search and checking operations, not operating-system time,
memory or integer bit complexity. A task file is bounded to 1 MiB, one claim to
4 MiB and an instance state to 24 MiB (her evidence beyond it moves to files of at
most 24 MiB each beside the state, and her ledger keeps the files of up to 1,024
agent records the observation bound evicted);
at most 128 observations and bounded scheduling samples are retained. These limits
make incomplete work explicit. Do not let two processes write the same instance
file simultaneously. Changing a task can invalidate reuse; a saved status flag
cannot authorize acceptance of new mathematics.

The polynomial grammar and search bounds are finite. A failed witness search
does not prove that no rational witness exists. A finite coefficient match does
not establish an identity at all lengths. Unsupported domains remain unsupported;
the result JSON reports the narrower certificate or unresolved outcome.

For algebra tasks, `counterexample_radius` bounds sampled free-variable values.
Coordinates solved from affine assumptions may be rational or outside that
interval. This field controls the search; it does not add an assumption limiting
the original rational domain.

## Inspect and reproduce this package

`PUBLIC_MANIFEST.json` lists every payload file with its size and SHA-256. Its
own bytes are excluded from that list to avoid a circular hash. The ZIP contains
only owned runtime files, public examples, documentation, credit, license,
manifest and the packaging tool. Private source collections, personal transcripts,
research databases and instance state are excluded by an explicit allowlist.

To rebuild the deterministic source ZIP and run its relocation checks:

```text
python -I -B -X utf8 tools/build_public_package.py --verify
```

The builder fixes member order and metadata. It verifies payload hashes, starts
the actual CLI from a temporary relocated package, exercises fresh state and
restart, checks source-to-receiving lemma transfer and the default polynomial policy, and
rebuilds there to compare archive bytes. These are local portability
checks using the same Python interpreter. It also checks recurrence discovery,
helper and campaign restarts, and rejection of a forged stored recurrence proof.
Invariant checks cover full and mapped policies, original nonlinear conservation, untrusted
stored maps, forged certificates, helper calls and campaigns whose original
degree bound remains unresolved despite a checked expansion.
They also check cross-system invariant candidate reuse, changed dynamics, forged
source evidence, and a campaign that revisits an earlier question after learning.
Apex checks cover the audited pyramid, including a
tampered trace label that the audit must reject. They also cover orbit witnesses,
repeated states and separating invariants with forged saved evidence, the law
answer against exact iteration, forged apex checkpoints, recursive memory transfer,
standalone replay of apex certificates with only the checkers present, helper
calls and a large exact answer. Language checks run the move bench, require at
least 100 moves per pyramid direction, and reject a tampered operator whose declared
directions it does not observe. Agent checks cover the square-class residue of a
small unit-fraction cover, resume replay, a forged saved cover, standalone replay of
saved agent evidence with only the checker present, Collatz open-class counts
against an independent count, and decide and explore problems. These checks do not
demonstrate another operating system or enforced network isolation. There is no package installation
step and no background service.

The checks also exercise original nonzero cancellation, fresh default/helper/
obligation replay, changed guards, vacuity without support, forged saved evidence
and explicit localization campaign restarts. Guarded-transfer checks cover actual
source learning, changed receiving premises and goal, flat-child checkpoints,
unsupported saved child evidence, default-policy boundaries and campaign replay.
Recursive checks cover original induction, an actual false original equation,
helper status handling, forged saved evidence, zero-work replay and campaign
restart. They also exercise original reverse-involution proposal progress across
processes, checked auxiliary proofs, parent re-entry and a standalone final replay.
Source-episode checks cover literal capsule hashes, actual checked seed use,
CLI/helper continuation, preserved checkpoints on refusal or exhaustion, and
original certificate replay with only the checker present. The public example
also executes under the same network/external-file audit hook. That hook is a
development observation, not operating-system sandboxing.

## Credit and license

Seth supplied the project direction and original TPM approach. OpenAI Codex and
earlier AI collaborators contributed the research and engineering described in
[CREDITS.md](CREDITS.md). Anthropic's Claude contributed the apex layer and the
reasoning pyramid in this generation. Established mathematics is credited separately from the
implementation. Existing source families retain their attribution and rights.

The newly authored Ember code and public documentation in this package use the
[MIT License](LICENSE), whose standard text is published by the
[Open Source Initiative](https://opensource.org/license/mit). This license does
not relicense donor archives, third-party runtimes or private source materials.
Recursive examples adapt MIT-licensed PIE definition data; their original
copyright and license appear in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Donor archives and runtimes are not included. This artifact is a prepared source release. A local ZIP does
not itself establish that a public repository or hosted release has been published.
