# Ember

Ember is a small, offline, non-LLM mathematical research agent under development,
directed by Seth. Its Theory Pyramid Mapping approach connects proposed
representations, their assumptions, counterexamples and checked reuse.

This source package runs with Python's standard library. It requires no model,
API key, downloaded weights, third-party package or source archive. Python itself
is an external prerequisite and is **not** included. The tested host is Windows
with Python 3.14.6; other Python versions, operating systems and devices remain
unverified. CPU, memory and storage are still required for each calculation.

Standing: **EXPERIMENTAL / SELF_ISOLATED**. Ember does not currently offer general
mathematical intelligence, unrestricted invention, or a solution to every open
problem. Its finite searches and exact checkers support the specific task types
below. Same-model development and review are not external scientific replication.

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

`--work` limits charged search and checking operations, not operating-system time,
memory or integer bit complexity. Input and instance state are bounded to 1 MiB;
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
These checks do not demonstrate another
operating system or enforced network isolation. There is no package installation
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
[CREDITS.md](CREDITS.md). Established mathematics is credited separately from the
implementation. Existing source families retain their attribution and rights.

The newly authored Ember code and public documentation in this package use the
[MIT License](LICENSE), whose standard text is published by the
[Open Source Initiative](https://opensource.org/license/mit). This license does
not relicense donor archives, third-party runtimes or private source materials.
Recursive examples adapt MIT-licensed PIE definition data; their original
copyright and license appear in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Donor archives and runtimes are not included. This artifact is a prepared source release. A local ZIP does
not itself establish that a public repository or hosted release has been published.
