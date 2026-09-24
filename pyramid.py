"""Theory Pyramid Mapping of Ember's own reasoning: an audited catalog and synthesis lattice.

Directions: N proposes a representation, generalization or candidate; W refutes a
claim or candidate, or extracts a residual; S binds, specializes or checks against
the original task; E transfers checked knowledge between questions. The base
layer lists implemented moves. Synthesis nodes are the fifteen nonempty sets of
directions, from the four faces up to the apex {N,W,S,E}. A move sits at the node
of its own directions; a synthesis sits at the union of its steps' directions and
must chain produced types into consumed types. The audit binds every entry and
every explicit trace label to the source text. The map classifies operations; it
is a chosen description, not a proof, and a node is realized only by named code.
"""
import ast
from itertools import combinations
from pathlib import Path

VERSION = 'ember.tpm_pyramid.v1'
DIRECTIONS = ('N', 'W', 'S', 'E')
MEANING = {'N': 'propose a representation, generalization or candidate',
           'W': 'refute a claim or candidate, or extract a residual',
           'S': 'bind, specialize or check against the original task',
           'E': 'transfer checked knowledge between questions'}
NODE_ORDER = tuple(''.join(c) for k in range(1, 5) for c in combinations(DIRECTIONS, k))
NODE_NAMES = {
    'N': 'Propose', 'W': 'Refute and extract residuals', 'S': 'Specialize and check', 'E': 'Transfer',
    'NW': 'Counterexample-guided proposal', 'NS': 'Conjecture and verify', 'NE': 'Generalize for reuse',
    'WS': 'Falsify by specialization', 'WE': 'Residual-directed transfer', 'SE': 'Checked transfer',
    'NWS': 'Refinement loop', 'NWE': 'Unchecked repair and transfer', 'NSE': 'Law transport',
    'WSE': 'Refutation transport', 'NWSE': 'Apex research cycle'}
TYPES = ('original', 'candidate', 'certificate', 'counterexample', 'residual', 'law', 'library', 'derived',
         'answer', 'decision')
MODULES = ('ember.py', 'campaign.py', 'algebra.py', 'algebra_check.py', 'word_series.py', 'word_check.py',
           'recurrence.py', 'recurrence_check.py', 'invariant.py', 'invariant_map.py', 'invariant_check.py',
           'obligations.py', 'recursive.py', 'recursive_check.py', 'source_episode.py', 'apex.py', 'apex_check.py')


def move(id, module, entries, dirs, labels, consumes, produces, activation, summary):
    return dict(id=id, module=module, entries=entries, dirs=dirs, labels=labels, consumes=consumes,
                produces=produces, activation=activation, summary=summary)


# Base layer. dirs '' marks control moves: they schedule, persist or replay work
# and sit outside the direction lattice. Entries name functions in the move's
# module, or 'other.py:function' for a helper defined elsewhere.
MOVES = (
    # ---- ember.py: binding, exact counts, quotients, overlap refutation, memory
    move('original_binding', 'ember.py', ('load_json', 'bind', 'bind_discovery', 'digest'), 'S', (),
         ('original',), ('original',), 'every query',
         'Duplicate-key-free bounded JSON, exact field and bound checks, canonical SHA-256 task identity.'),
    move('exact_iteration', 'ember.py', ('direct', 'evaluate'), 'S', (), ('original',), ('answer',),
         'transition_count --strategy direct', 'Exact integer iteration of u*M**h*v; no separate certificate.'),
    move('quotient_refinement', 'ember.py', ('propose', 'solve_quotient', 'blocks_from'), 'NWS',
         ('N:propose_quotient', 'W:counterexample_to_current_merge', 'S:refine_failed_blocks',
          'S:check_original_matrix_equations'), ('original',), ('candidate', 'certificate', 'answer'),
         'transition_count --strategy quotient',
         'Refine terminal classes whenever a merge meets a counterexample row sum; evaluate the checked MP=PQ, v=Pw quotient.'),
    move('initial_partition_probe', 'ember.py', ('solve_matrix', 'initial_quotient'), 'NWS',
         ('N:propose_initial_terminal_partition', 'W:initial_partition_failed', 'S:check_original_matrix_equations'),
         ('original',), ('certificate', 'answer'), 'transition_count --strategy auto',
         'A fixed cost bound decides one terminal-partition probe before exact iteration.'),
    move('quotient_check', 'ember.py', ('check',), 'S', (), ('candidate',), ('certificate',), 'internal',
         'Recompute MP=PQ and v=Pw from the original matrix; producer signatures are not trusted.'),
    move('recipe_transfer', 'ember.py', ('solve_quotient',), 'WSE',
         ('E:transfer_single_block_recipe', 'W:transferred_recipe_refused'), ('library', 'original'), ('certificate',),
         'transition_count --strategy quotient with experience',
         'A remembered one-block success proposes a one-block quotient; the original equations decide.'),
    move('overlap_generalization_test', 'ember.py', ('discover', 'candidate_overlap', 'shortcut_coefficients',
         'original_count'), 'NWS', ('N:test_stated_structural_generalization',
         'S:bind_reduced_binary_words_and_column_premise', 'W:candidate_counterexample'), ('original',),
         ('counterexample',), 'test_overlap_shortcut',
         'Test a stated shortcut over a bounded binary-word grammar; return a checked original counterexample.'),
    move('overlap_counterexample_check', 'ember.py', ('check_discovery',), 'WS', (), ('counterexample',),
         ('counterexample',), 'internal', 'Rebuild overlap columns from strings and recount words by integer decoding.'),
    move('checked_replay', 'ember.py', ('read_state', 'retain', 'solve'), 'S', (), ('library',), ('certificate',),
         'every query with --state', 'Saved certificates are checked again on the original; saved flags never admit.'),
    move('lemma_memory', 'ember.py', ('remember_lemma', 'lemma_candidates'), 'NE', (), ('certificate',), ('library',),
         'polynomial proofs', 'Admitted flat or guarded proofs become at most eight proposals for other questions.'),
    move('invariant_memory', 'ember.py', ('remember_invariant', 'invariant_candidates'), 'NE', (), ('law',),
         ('library',), 'invariant proofs', 'Admitted conservation laws become at most eight proposals.'),
    # ---- campaign.py: durable research over original tasks
    move('repair_questions', 'campaign.py', ('routes',), 'NW', (), ('counterexample',), ('derived',),
         'research_campaign repairs', 'After a refutation, ask guard repairs or the full-overlap formula; added assumptions stay explicit.'),
    move('invariant_degree_expansion', 'campaign.py', ('routes', 'ready'), 'N', (), ('residual',), ('derived',),
         'research_campaign expansions', 'After bounded misses, ask a distinct higher-degree invariant question.'),
    move('generalization_questions', 'campaign.py', ('routes', 'ready'), 'N', (), ('certificate', 'answer'),
         ('derived',), 'discover_after_solving', 'After a settled finite original, ask an all-index question about its carrier.'),
    move('campaign_admission', 'campaign.py', ('admit', 'compact', 'terminal'), 'S', (),
         ('certificate', 'answer', 'counterexample'), ('certificate', 'answer', 'counterexample'), 'research_campaign',
         'Every saved or new outcome is replayed through its original checker before it counts.'),
    move('context_reentry', 'campaign.py', ('proposal_context', 'polynomial_candidates', 'supersede'), 'WE', (),
         ('residual', 'library'), ('derived',), 'research_campaign',
         'An unresolved knowledge-consuming attempt reopens only when its candidate fingerprint changes.'),
    move('campaign_schedule', 'campaign.py', ('score', 'record_sample', 'samples_read', 'run'), '', (),
         ('decision',), ('decision',), 'policy fixed, structure_first, learned',
         'Fair problem order; learned ranks by p=(1+S)/(2+S+F) over smoothed cost and reverses on every fifth unseen context.'),
    move('durable_checkpoint', 'campaign.py', ('checkpoint', 'binding', 'validate', 'context', 'generation'), '', (),
         ('decision',), ('library',), 'research_campaign', 'Atomic single-writer checkpoints of attempts, history and samples.'),
    # ---- algebra.py: rational polynomial consequences
    move('polynomial_expansion', 'algebra.py', ('expand', 'add', 'multiply', 'checked_size', 'evaluate', 'encoded'),
         'S', (), ('original',), ('candidate',), 'polynomial queries',
         'Expand bound expression trees into exact sparse polynomials under term and bit limits.'),
    move('affine_parameterization', 'algebra.py', ('affine_model',), 'N', (), ('original',), ('candidate',),
         'polynomial queries', 'Exact Gauss-Jordan on the affine assumptions parameterizes their solution set.'),
    move('rational_counterexample_search', 'algebra.py', ('consequence', 'probe_points'), 'WS', (),
         ('original', 'candidate'), ('counterexample',), 'polynomial_consequence',
         'Probe free parameters on a bounded integer grid for an admissible original point that violates the goal.'),
    move('support_witness', 'algebra.py', ('consequence',), 'S', (), ('original',), ('certificate',),
         'discover_guards and support_point', 'Attach the first admissible probe point; implications without one make no support claim.'),
    move('dense_degree_ladder', 'algebra.py', ('combination', 'monomials', 'consequence'), 'NS', (), ('original',),
         ('candidate', 'certificate'), '--proof-policy direct and fallbacks',
         'Solve goal = sum(m_i*g_i) exactly over all multiplier monomials, degree 0 up to the original bound.'),
    move('sparse_exponent_bases', 'algebra.py', ('sparse_basis', 'sparse_proposal'), 'N', (), ('original',),
         ('candidate',), '--proof-policy auto, target_sparse, cancellation_sparse',
         'Propose multiplier bases from goal-minus-assumption and cancellation exponent differences; dense search stays fallback.'),
    move('localized_guard_lift', 'algebra.py', ('localized_consequence', 'guarded_certificate'), 'NS',
         ('N:multiply_goal_by_original_nonzero', 'S:check_original_guarded_implication'), ('original',),
         ('certificate',), '--proof-policy localized_first',
         'Multiply the goal by one original nonzero guard U and prove U*goal from the original equations.'),
    move('lemma_binding_enumeration', 'algebra.py', ('lemma_bindings',), 'N', (), ('library',), ('candidate',),
         '--proof-policy lemma_first, obligations', 'Enumerate injective source-to-receiving variable maps, identity first.'),
    move('lemma_transport', 'algebra.py', ('transport_lemma', 'renamed_expression', 'flat_certificate'), 'SE', (),
         ('library', 'original', 'candidate'), ('certificate',), '--proof-policy lemma_first',
         'Recheck a stored source proof and rename its statement into the receiving variables.'),
    move('premise_discharge', 'algebra.py', ('transport_lemma',), 'S', (), ('candidate', 'certificate'), ('certificate',),
         '--proof-policy lemma_first', 'Prove every renamed source premise from the original receiving equations.'),
    move('multiplier_flattening', 'algebra.py', ('fits_certificate', 'reuse_lemma'), 'N', (), ('certificate',),
         ('candidate',), '--proof-policy lemma_first',
         'Compose L = sum h_i*A_i with A_i = sum k_ij*G_j into multipliers of the original generators.'),
    move('lemma_outer_target_search', 'algebra.py', ('reuse_lemma',), 'NS', (), ('candidate', 'certificate', 'original'),
         ('certificate',), '--proof-policy lemma_first', 'Solve the receiving goal over the checked lemma and original equations.'),
    move('guarded_transfer', 'algebra.py', ('receiving_guard_index', 'guarded_certificate', 'transport_lemma'), 'SE',
         (), ('library', 'original'), ('certificate',), '--proof-policy lemma_first, obligations',
         'Transfer a localized proof only when every source guard occurs as the same receiving expression.'),
    move('lemma_reuse_schedule', 'algebra.py', ('reuse_lemma', 'proof_with_lemmas'), 'WE', (), ('library', 'residual'),
         ('decision',), '--proof-policy auto, lemma_first', 'Bounded record-by-binding reuse attempts; misses fall back to direct search.'),
    move('pair_equality_guards', 'algebra.py', ('guard_candidates',), 'N', (), ('counterexample', 'original'),
         ('candidate',), 'discover_guards pair_equalities', 'Propose x_i - x_j repairs in declaration order.'),
    move('coefficient_slice_guards', 'algebra.py', ('guard_candidates', 'affine_key', 'affine_text'), 'N', (),
         ('counterexample', 'original'), ('candidate',), 'discover_guards coefficient_slices',
         'Propose affine coefficient slices of the goal over variable subsets of size one to three.'),
    move('assumption_residual_slice_guards', 'algebra.py', ('guard_candidates', 'affine_substitute'), 'NW', (),
         ('counterexample', 'original'), ('candidate',), 'discover_guards assumption_slices',
         'Substitute affine assumptions into the goal and slice the residual into guard proposals.'),
    move('guard_candidate_check', 'algebra.py', ('run',), 'WS', (), ('candidate',), ('certificate', 'counterexample'),
         'discover_guards', 'Append a candidate guard; require a support point and a proof, or keep its counterexample.'),
    move('witness_replay_filter', 'algebra.py', ('run',), 'W', (), ('counterexample', 'candidate'), ('counterexample',),
         'discover_guards residual_first', 'Stored checked counterexamples refute later guard candidates before search.'),
    move('guard_equivalence_merge', 'algebra.py', ('run',), 'NS', ('N:merge_mutually_proved_guard_forms',),
         ('certificate',), ('certificate',), 'discover_guards', 'Group accepted guards whose forms prove each other under the assumptions.'),
    move('guard_discovery_driver', 'algebra.py', ('run', 'guard_candidates'), 'NWS',
         ('W:reject_with_original_task_counterexamples', 'S:check_polynomial_combination_and_support'),
         ('counterexample', 'original'), ('certificate', 'derived'), 'discover_guards',
         'Refute the original, generate guards from its residual and admit supported repairs.'),
    move('sufficient_core_extraction', 'algebra.py', ('sufficient_core',), 'NS', (), ('library',), ('certificate',),
         '--proof-policy obligations', 'Keep only assumptions with nonzero multipliers: a checked lemma with fewer hypotheses.'),
    move('premise_plan_construction', 'algebra.py', ('prepare_premise_planner', 'plan_premises', 'premise_json',
         'plan_for'), 'NSE', (), ('library', 'original'), ('derived',), '--proof-policy obligations',
         'Map the checked core into the receiver and turn missing premises into child questions.'),
    move('premise_assembly', 'algebra.py', ('assemble_premises',), 'NSE',
         ('S:rebuild_checked_source_core_and_mapped_plan', 'S:check_premises_against_original_receiving_equations',
          'N:flatten_child_and_source_multipliers', 'S:check_original_parent_certificate'),
         ('certificate', 'derived'), ('certificate',), '--proof-policy obligations',
         'Rebuild the plan, recheck children and flatten them with the source into an original parent proof.'),
    move('algebra_budget_slices', 'algebra.py', ('LemmaBudget', 'SparseBudget', 'LocalizationBudget'), '', (),
         ('decision',), ('decision',), 'internal', 'Reserved sub-budgets keep fallback work available after a proposal stage.'),
    # ---- algebra_check.py: admission of polynomial certificates
    move('degree_grid_identity_check', 'algebra_check.py', ('check', 'monomial_value', 'value', 'multiplier_read'), 'S',
         (), ('candidate', 'certificate'), ('certificate',), 'internal',
         'Check goal = sum(m_i*g_i) on the complete original degree grid with the univariate root bound.'),
    move('localized_grid_check', 'algebra_check.py', ('check',), 'S', (), ('candidate', 'certificate'), ('certificate',),
         'internal', 'Check U*goal = sum(m_i*g_i) for an original guard U, which is nonzero at admissible points.'),
    move('counterexample_point_check', 'algebra_check.py', ('check', 'admissible', 'point_read'), 'WS', (),
         ('counterexample', 'candidate'), ('counterexample',), 'internal',
         'An exact rational point satisfies the original equations and guards and violates the goal.'),
    move('algebra_status_classification', 'algebra_check.py', ('result_status',), 'S', (), ('certificate',),
         ('certificate',), 'internal', 'Map a checked certificate kind to its exact result status.'),
    # ---- obligations.py: durable premise obligations
    move('obligation_graph', 'obligations.py', ('plan_graph', 'run', 'structure'), 'WSE', (), ('library', 'original'),
         ('derived', 'certificate'), '--proof-policy obligations',
         'Typed original, transfer, premise and direct nodes with dependencies and checked outcomes.'),
    move('child_question_creation', 'obligations.py', ('plan_graph', 'algebra.py:plan_for'), 'NWS', (),
         ('library', 'original'), ('derived',), '--proof-policy obligations',
         'Each mapped core premise becomes an exact child question under the original receiving assumptions.'),
    move('plan_dedup', 'obligations.py', ('plan_graph',), 'W', (), ('derived',), ('derived',), '--proof-policy obligations',
         'Byte-equal transfer plans share one plan; later duplicates are rejected.'),
    move('and_or_route_selection', 'obligations.py', ('run', 'choose'), 'WS', (), ('derived', 'counterexample'),
         ('decision',), '--proof-policy obligations', 'A child counterexample rejects its transfer route, never the parent.'),
    move('retry_on_changed_allowance', 'obligations.py', ('run', 'retryable'), 'W', (), ('residual',), ('decision',),
         '--proof-policy obligations', 'Retry an unresolved node only when its allowance grows or its context changes.'),
    move('child_checkpoint_replay', 'obligations.py', ('run', 'checked_result'), 'WS', (), ('library',), ('certificate',),
         '--proof-policy obligations', 'Saved child results are checked again; unsupported saved kinds are invalidated.'),
    move('leaf_child_solving', 'obligations.py', ('run',), 'SE', (), ('derived',), ('certificate',),
         '--proof-policy obligations', 'Solve a child question with the flat library under the default policy.'),
    move('obligation_control', 'obligations.py', ('checkpoint', 'PlanningBudget', 'generation', 'compact'), '', (),
         ('decision',), ('library',), '--proof-policy obligations', 'Planning slices, attempt log and atomic checkpoints.'),
    # ---- recursive.py: Nat/List identities
    move('recursive_theory', 'recursive.py', ('Theory', 'recursive_check.py:bind', 'recursive_check.py:_Theory'), 'S',
         (), ('original',), ('original',), 'prove_recursive_identity',
         'Validate structural definitions: immediate predecessor recursion and both constructor cases.'),
    move('dependency_closure', 'recursive.py', ('dependencies',), 'S', (), ('original',), ('original',),
         'prove_recursive_identity', 'Collect the goal functions and every function their definitions reach.'),
    move('lpo_orientation', 'recursive.py', ('greater',), 'NW', (), ('original',), ('candidate',),
         'prove_recursive_identity', 'Orient equations by a lexicographic path order; non-decreasing orientations are refused.'),
    move('rewrite_rule_assembly', 'recursive.py', ('rewrite_rules', 'match', 'successors'), 'S', (),
         ('original', 'library'), ('candidate',), 'prove_recursive_identity',
         'Forward definitions, oriented lemmas and induction hypotheses form the rewrite rules.'),
    move('normalize_and_join', 'recursive.py', ('join',), 'WS', (), ('original', 'library', 'candidate'),
         ('certificate', 'residual'), 'prove_recursive_identity',
         'Normalize both sides and search a bounded join; a failed join leaves the residual pair.'),
    move('structural_induction_search', 'recursive.py', ('attempt',), 'NWS', (), ('original', 'candidate'),
         ('certificate', 'residual'), '--recursive-policy direct',
         'Pick a recursion variable, split constructor cases and prove both with the hypothesis.'),
    move('typed_term_grammar', 'recursive.py', ('typed_terms',), 'N', (), ('original',), ('candidate',),
         'prove_recursive_identity', 'Enumerate well-sorted terms bottom-up by size.'),
    move('accumulator_generalization', 'recursive.py', ('candidates',), 'N', (), ('residual', 'original'),
         ('candidate',), '--recursive-policy residual', 'Generalize a ground accumulator argument into a fresh variable.'),
    move('shared_subterm_abstraction', 'recursive.py', ('shared', 'candidates'), 'N', (), ('residual',), ('candidate',),
         '--recursive-policy residual', 'Abstract subterms common to both residual sides into variables.'),
    move('typed_residual_frontier', 'recursive.py', ('patterns', 'candidates'), 'NW', (), ('residual',), ('candidate',),
         '--recursive-policy residual', 'Propose equations for the patterns actually blocking the residual.'),
    move('fixed_typed_enumeration', 'recursive.py', ('candidates',), 'N', (), ('original', 'decision'),
         ('candidate',), '--recursive-policy enumerate', 'A residual-independent stream of small well-sorted equations.'),
    move('candidate_admissibility', 'recursive.py', ('allowed', 'alpha', 'goal_id', 'emit'), 'NW', (), ('candidate',),
         ('candidate',), 'prove_recursive_identity', 'Rename, orient and deduplicate candidates; refuse trivial or oversized ones.'),
    move('root_finite_refutation', 'recursive.py', ('evaluate', 'ground_domains', 'run'), 'WS', (), ('original',),
         ('counterexample',), 'prove_recursive_identity', 'Evaluate the original on small ground domains for a counterexample.'),
    move('candidate_finite_filter', 'recursive.py', ('filter_candidate', 'candidate_task'), 'WS', (), ('candidate',),
         ('counterexample', 'candidate'), 'prove_recursive_identity',
         'Ground evaluation rejects false auxiliary candidates before any proof search.'),
    move('bundle_lemma_admission', 'recursive.py', ('check_bundle', 'candidate_task'), 'S', (),
         ('candidate', 'certificate'), ('certificate',), 'prove_recursive_identity',
         'A proved candidate enters the library only after the separate checker replays its bundle.'),
    move('parent_reentry', 'recursive.py', ('run', 'rewrite_rules'), 'SE', (), ('certificate', 'library'),
         ('certificate',), 'prove_recursive_identity', 'Checked auxiliary lemmas re-enter the blocked parent question.'),
    move('episode_replay_validation', 'recursive.py', ('_replay_record', 'validate_episode', 'generation'), 'S', (),
         ('library',), ('library',), 'prove_recursive_identity with --state',
         'A saved episode is revalidated node by node; changed theory, policy or runtime rejects it.'),
    move('checked_seed_transfer', 'recursive.py', ('prepare_seeds', '_proof_references', '_rebase_proof',
         '_seed_records'), 'SE', (), ('library', 'decision'), ('candidate',), 'source episodes, apex recursive_seeded',
         'Recheck a same-definition source proof and rebase selected lemmas with their dependency closure.'),
    move('residual_seed_matching', 'recursive.py', ('match_residual', 'residual_matches'), 'WE', (),
         ('residual', 'library'), ('decision',), '--source-policy gap_bridge',
         'Count checked seed orientations that match subterms of an actual residual.'),
    move('episode_inspection', 'recursive.py', ('inspect_episode',), 'WS', (), ('library',), ('residual',),
         '--source-policy gap_bridge', 'Replay a saved episode read-only to expose its current residual.'),
    move('recursive_episode_control', 'recursive.py', ('checkpoint', 'event', 'Slice', 'episode_id', 'seed_context',
         '_episode_key', 'progress_context'), '', (), ('decision',), ('library',), 'prove_recursive_identity',
         'Episode identities, stage slices, events, progress fingerprints and checkpoints.'),
    # ---- recursive_check.py: admission of recursive identities
    move('rewrite_step_replay', 'recursive_check.py', ('_rewrite', '_substitute', '_bounded', '_equal'), 'S', (),
         ('candidate',), ('certificate',), 'internal', 'Replay each rewrite step against definitions, earlier lemmas or the hypothesis.'),
    move('induction_replay', 'recursive_check.py', ('_verify',), 'S', (), ('candidate',), ('certificate',), 'internal',
         'Replay both constructor cases with a strictly smaller-argument hypothesis.'),
    move('recursive_identity_admission', 'recursive_check.py', ('check', 'result_status'), 'S', (),
         ('candidate', 'certificate'), ('certificate',), 'internal',
         'Admit an ordered lemma bundle and root proof against the complete original task.'),
    move('recursive_counterexample_admission', 'recursive_check.py', ('check', '_evaluate'), 'WS', (),
         ('counterexample', 'candidate'), ('counterexample',), 'internal',
         'Evaluate both sides at a concrete constructor assignment; different normal forms refute.'),
    # ---- source_episode.py: structured sources and checked bridges
    move('source_capsule_binding', 'source_episode.py', ('bind', 'decode', 'keys', 'charged_digest'), 'S', (),
         ('original',), ('original',), 'source_research_episode',
         'Literal SHA-256 source capsules and strict JSON; supplied proofs and answers are refused.'),
    move('source_format_adaptation', 'source_episode.py', ('bind',), 'NS', (), ('original',), ('original',),
         'source_research_episode', 'Adapt two declared formats into original recursive questions and stances.'),
    move('unsupported_format_gap', 'source_episode.py', ('bind', 'make_graph'), 'W', (), ('original',), ('residual',),
         'source_research_episode', 'An unsupported source stays visible as a gap and blocks a complete result.'),
    move('claim_question_extraction', 'source_episode.py', ('bind', 'make_graph'), 'N', (), ('original',),
         ('derived',), 'source_research_episode', 'Record each source stance as a question, holds or fails claim.'),
    move('root_dedup', 'source_episode.py', ('bind',), 'S', (), ('original',), ('original',), 'source_research_episode',
         'Identical questions share one root; copies add no truth weight.'),
    move('source_dependency_closure', 'source_episode.py', ('symbols', 'closure'), 'S', (), ('original',),
         ('original',), 'source_research_episode', 'Function closure of each root, used for seed relevance.'),
    move('source_tension', 'source_episode.py', ('make_graph', 'select_next'), 'W', (), ('original',), ('residual',),
         'source_research_episode', 'Opposite source assertions on one root create explicit tension.'),
    move('typed_source_graph', 'source_episode.py', ('make_graph', 'node', 'edge'), 'NWSE', (), ('original',),
         ('library',), 'source_research_episode',
         'A typed graph of sources, claims, originals, attempts, gaps and checked bridges.'),
    move('native_attempt_admission', 'source_episode.py', ('admit', 'run'), 'WS', (), ('original',),
         ('certificate', 'counterexample'), 'source_research_episode',
         'Each root is attempted natively and admitted only by its original checker.'),
    move('diagnostic_residual_probe', 'source_episode.py', ('select_next',), 'WS', (), ('original',), ('residual',),
         '--source-policy gap_bridge', 'One bounded native stage exposes each unresolved root residual.'),
    move('gap_inspection', 'source_episode.py', ('select_next', 'recursive.py:inspect_episode'), 'W', (),
         ('library',), ('residual',), '--source-policy gap_bridge', 'Read the saved residual of an unresolved root.'),
    move('gap_bridge_ranking', 'source_episode.py', ('select_next', 'recursive.py:match_residual'), 'WE', (),
         ('residual', 'library'), ('decision',), '--source-policy gap_bridge',
         'Rank roots by tension, residual matches, dependency count and source order.'),
    move('fixed_bridge_order', 'source_episode.py', ('select_next',), 'SE', (), ('library',), ('decision',),
         '--source-policy fixed_bridge', 'Seed every unresolved root in source order without residual inspection.'),
    move('isolated_policies', 'source_episode.py', ('select_next', 'make_graph'), 'S', (), ('original',),
         ('decision',), '--source-policy native_isolated, graph_isolated', 'Solve each root alone, with or without the graph.'),
    move('checked_seed_transport', 'source_episode.py', ('seed_records', 'bridge_rows', 'run'), 'SE', (),
         ('library', 'decision'), ('candidate',), 'source_research_episode',
         'Select checked same-definition proofs as seeds for a receiving root.'),
    move('eligibility_retry', 'source_episode.py', ('select_next',), 'W', (), ('residual',), ('decision',),
         'source_research_episode', 'A root waits until its phase, seed context or allowance changes.'),
    move('live_evidence_protection', 'source_episode.py', ('protected', 'merge_check'), 'S', (), ('library',),
         ('library',), 'source_research_episode', 'Refuse to overwrite other episodes whose evidence changed meanwhile.'),
    move('resume_readmission', 'source_episode.py', ('_record', '_validate', 'replay_contexts', 'generation'), 'S', (),
         ('library',), ('certificate',), 'source_research_episode', 'A saved episode must match its task, policy and generation; results replay.'),
    move('claim_assessment', 'source_episode.py', ('_answer',), 'WS', (), ('certificate', 'counterexample'),
         ('certificate',), 'source_research_episode', 'Mark each source ANSWERED, SUPPORTED or CONTRADICTED from checked results.'),
    move('source_control', 'source_episode.py', ('Account', 'checkpoint', 'native_summary'), '', (), ('decision',),
         ('library',), 'source_research_episode', 'Per-root work accounts and atomic outer checkpoints.'),
    # ---- word_series.py and word_check.py: forbidden-word generating functions
    move('word_overlap_formula', 'word_series.py', ('produce_formula', 'run'), 'S',
         ('S:bind_original_words_and_overlap_formula',), ('original',), ('candidate',), 'word_avoidance_identity',
         'Correlation polynomials give the requested column-shortcut or full-overlap formula.'),
    move('word_state_numerators', 'word_series.py', ('state_proposal', 'coefficients'), 'NS',
         ('N:propose_common_denominator_state_numerators', 'S:check_original_DFA_polynomial_equations'),
         ('candidate', 'original'), ('candidate',), 'word_avoidance_identity',
         'Propose automaton state numerators over one common denominator and check the state equations.'),
    move('word_counterexample_certificate', 'word_series.py', ('run', 'coefficients'), 'WS', (), ('candidate',),
         ('counterexample',), 'word_avoidance_identity', 'Expand the formula and count original words to a first differing length.'),
    move('word_automaton_producer', 'recurrence.py', ('word_system',), 'N', (), ('original',), ('candidate',),
         'discover_word_recurrence', 'Producer prefix automaton by suffix deletion, separate from the checker.'),
    move('word_automaton_checker', 'word_check.py', ('automaton', 'recurrence_check.py:original_word_system'), 'S', (),
         ('original',), ('original',), 'internal', 'Independent prefix automaton over both letters for admission.'),
    move('word_shortcut_classification', 'word_check.py', ('formula',), 'WS', (), ('original',), ('candidate',),
         'word_avoidance_identity', 'Verify the shortcut polynomial identity and its column premise algebraically.'),
    move('word_identity_check', 'word_check.py', ('check', 'bind', 'coefficients'), 'WS', (),
         ('candidate', 'counterexample'), ('certificate', 'counterexample'), 'internal',
         'Admit an all-length generating-function identity or a counted counterexample length.'),
    # ---- recurrence.py and recurrence_check.py: all-index scalar laws
    move('recurrence_prefix_observation', 'recurrence.py', ('run', 'row_step', 'scalar'), 'S',
         ('S:observe_original_system',), ('original',), ('candidate',), 'discover_recurrence, discover_word_recurrence',
         'Compute rows u*M**k and 2n+1 exact terms of the original sequence.'),
    move('recurrence_linear_solve', 'recurrence.py', ('solve_linear',), 'N', (), ('candidate',), ('candidate',),
         'internal', 'Incremental exact elimination; an inconsistent row refuses a width.'),
    move('row_span_closure_proposal', 'recurrence.py', ('run',), 'N', ('N:propose_closed_row_span',), ('candidate',),
         ('candidate',), 'discover_recurrence', 'The first solvable row width gives a closed row span.'),
    move('scalar_recurrence_fit', 'recurrence.py', ('run',), 'NWS', ('N:propose_scalar_recurrence',
         'W:refuse_candidate_on_original_system', 'S:check_entry_closure_and_residual'), ('candidate',), ('candidate',),
         'discover_recurrence', 'Fit the lowest consistent order on the prefix; the original system refuses or admits it.'),
    move('recurrence_binding', 'recurrence_check.py', ('bind', 'rational'), 'S', (), ('original',), ('original',),
         'discover_recurrence', 'Bounded integer carrier or two reduced patterns; canonical identity.'),
    move('entry_closure_residual_check', 'recurrence_check.py', ('check', 'dot', 'bounded'), 'WS', (),
         ('candidate', 'law'), ('law',), 'internal',
         'Original entry, row-span closure and residual orthogonality establish the law for every index.'),
    # ---- invariant.py, invariant_map.py and invariant_check.py: conservation laws
    move('invariant_binding', 'invariant_check.py', ('bind',), 'S', (), ('original',), ('original',),
         'discover_invariant', 'Parse bounded transition expressions, degree, focus and initial point; canonical identity.'),
    move('invariant_residual_operator', 'invariant.py', ('validate_basis', 'build_operator'), 'S',
         ('S:form_original_transition_residual_operator',), ('original',), ('candidate',), 'discover_invariant',
         'Columns m(F(x))-m(x) for every nonconstant monomial up to the degree bound.'),
    move('invariant_nullspace_candidate', 'invariant.py', ('search_operator', 'run'), 'NWS',
         ('N:propose_nullspace_polynomial', 'W:reject_invariant_candidate', 'S:check_original_transition_identity'),
         ('candidate',), ('candidate', 'residual'), 'discover_invariant',
         'Exact elimination proposes the first focus-relevant kernel basis vector.'),
    move('selector_kernel_search', 'invariant.py', ('search_operator',), 'N', (), ('candidate',), ('candidate',),
         'apex orbit_invariant', 'The same kernel enumeration with a caller-supplied linear selector.'),
    move('focus_relevance', 'invariant.py', ('search_operator', 'run'), 'WS', (), ('candidate',), ('candidate',),
         'discover_invariant focus', 'A candidate must involve a focus variable; others are skipped.'),
    move('dependency_map_components', 'invariant.py', ('run', 'invariant_map.py:build', 'invariant_map.py:components'),
         'N', ('N:partition_exact_residual_incidence',), ('candidate',), ('candidate',), '--invariant-policy mapped',
         'Split the operator along shared coefficient equations into independent components.'),
    move('map_validation_fallback', 'invariant.py', ('validated_components', 'run'), 'WS',
         ('W:reject_map_and_use_full_operator',), ('candidate',), ('candidate',), '--invariant-policy mapped',
         'A map must partition columns without splitting a shared row, or the full operator is used.'),
    move('invariant_initial_value', 'invariant.py', ('run', 'target_candidate'), 'S', (), ('candidate',),
         ('candidate',), 'discover_invariant with initial', 'Evaluate the candidate exactly at the original initial point.'),
    move('invariant_grid_check', 'invariant_check.py', ('check', 'polynomial'), 'WS', (), ('candidate', 'law'),
         ('law',), 'internal', 'P(F(x))=P(x) on the complete original-AST degree grid; initialized values by induction.'),
    move('invariant_renaming', 'invariant.py', ('reuse_bindings', 'renamed_invariant'), 'N', (), ('library',),
         ('candidate',), '--invariant-policy reuse_first, apex orbit_transfer',
         'Injective renamings of a stored law\'s active variables, preferred names first.'),
    move('invariant_reuse_first', 'invariant.py', ('run_reuse', 'ReuseBudget'), 'NWSE',
         ('S:freshly_check_source_invariant', 'N:rename_active_polynomial_candidate',
          'S:check_original_receiving_transition', 'W:reuse_unresolved_try_original_full_search'),
         ('library', 'original'), ('law',), '--invariant-policy reuse_first',
         'Recheck stored laws, rename and test them on the receiving transition, else search fully.'),
    # ---- apex.py and apex_check.py: the higher reasoning layer
    move('law_carrier', 'apex.py', ('law_instance',), 'WSE', ('S:check_quotient_carrier_on_original',
         'W:reject_law_carrier_outside_recurrence_bounds', 'E:transport_law_through_checked_quotient'),
         ('certificate', 'law'), ('derived', 'law'), 'apex law_instance',
         'Choose a checked quotient or the original as recurrence carrier; lift the law through MP=PQ.'),
    move('law_evaluation', 'apex_check.py', ('evaluate', 'check_law_instance', 'recurrence_task', 'check_quotient'),
         'S', (), ('law', 'original'), ('answer',), 'apex law_instance',
         'Evaluate a checked all-index recurrence at the original horizon by exact integer stepping.'),
    move('law_instance_report', 'apex.py', ('law_instance',), 'S', ('S:evaluate_checked_law_at_original_horizon',),
         ('law',), ('answer',), 'apex law_instance', 'Report the evaluated law as the original count.'),
    move('recursive_seed_selection', 'apex.py', ('recursive_seeds', 'recursive_seeded'), 'E', (), ('library',),
         ('decision',), 'apex recursive_seeded', 'Select remembered checked proofs sharing the complete definitions as seeds.'),
    move('orbit_prefix', 'apex.py', ('orbit_prefix',), 'WS', ('S:iterate_original_orbit_prefix',
         'W:refute_reachability_by_repeated_state', 'S:check_original_orbit_prefix_certificate'),
         ('original',), ('certificate', 'counterexample'), 'prove_orbit_exclusion',
         'Iterate the exact orbit; a target hit proves reachability, a repeated state bounds the orbit.'),
    move('orbit_kernel_separation', 'apex.py', ('orbit_invariant', 'separation_certificate', 'separates'), 'NWS',
         ('S:form_orbit_invariant_operator', 'N:propose_separating_kernel_invariant',
          'W:refute_reachability_by_invariant_value'), ('original', 'candidate'), ('law', 'counterexample'),
         'prove_orbit_exclusion', 'Select a kernel invariant whose value separates target and start.'),
    move('orbit_law_transfer', 'apex.py', ('orbit_transfer',), 'WSE', ('E:collect_stored_checked_laws',
         'S:freshly_check_stored_law_source', 'E:rename_stored_law_into_receiving_orbit',
         'W:refute_reachability_by_transferred_invariant'), ('library', 'original', 'candidate'),
         ('law', 'counterexample'), 'prove_orbit_exclusion', 'Recheck stored laws, rename them and admit only a receiving separation.'),
    move('orbit_check', 'apex_check.py', ('check_orbit', 'bind_orbit', 'orbit_prefix', 'orbit_step'), 'WS', (),
         ('candidate', 'certificate', 'counterexample', 'law'), ('certificate', 'counterexample'), 'internal',
         'Recompute witnesses and repeated states; check separating invariants on the complete original grid.'),
    move('apex_admission', 'apex.py', ('admit',), 'S', (), ('certificate', 'answer', 'counterexample'),
         ('certificate', 'answer', 'counterexample'), 'apex_research',
         'Synthesized results pass the apex checker; subreasoner results pass their original checkers.'),
    move('apex_memory', 'apex.py', ('remember', 'solve_orbit'), 'NE', (), ('law', 'certificate'), ('library',),
         'apex_research', 'Admitted separating invariants and recursive proofs become stored proposals.'),
    move('apex_face_schedule', 'apex.py', ('order', 'deferred', 'plan', 'face', 'face_counts'), '', (), ('decision',),
         ('decision',), 'apex_research',
         'Per obligation, the face with fewest executed attempts, then the best measured route; infeasible iteration waits.'),
)


def synthesis(id, status, steps, where, summary, form='chain', needs=(), node=None):
    return dict(id=id, status=status, steps=steps, where=where, summary=summary, form=form, needs=needs,
                declared=node)


# Compositions of base moves. EXISTING predates the apex; APEX is realized by
# the apex layer; PROPOSED is an open obligation with no implementation. A chain
# passes each step's produced type to the next step; faces ask one obligation
# from several directions. A proposed synthesis names the moves it still needs.
SYNTHESES = (
    synthesis('policy_direct', 'EXISTING', ('dense_degree_ladder', 'rational_counterexample_search',
              'degree_grid_identity_check'), 'algebra.proof_with_lemmas direct',
              'Dense multipliers or a counterexample, admitted on the original grid.', form='faces'),
    synthesis('policy_auto', 'EXISTING', ('sparse_exponent_bases', 'dense_degree_ladder',
              'rational_counterexample_search', 'lemma_reuse_schedule', 'lemma_transport'),
              'algebra.proof_with_lemmas auto', 'Sparse, then dense, then bounded lemma reuse.', form='faces'),
    synthesis('policy_localized', 'EXISTING', ('localized_guard_lift', 'localized_grid_check'),
              'algebra.localized_consequence', 'Cancel one original nonzero guard.'),
    synthesis('checked_lemma_transfer', 'EXISTING', ('lemma_memory', 'lemma_binding_enumeration', 'lemma_transport',
              'premise_discharge', 'multiplier_flattening', 'lemma_outer_target_search', 'degree_grid_identity_check'),
              'algebra.reuse_lemma', 'Rename a stored proof, discharge its premises and flatten into original multipliers.'),
    synthesis('durable_premise_transfer', 'EXISTING', ('lemma_memory', 'premise_plan_construction',
              'child_question_creation', 'leaf_child_solving', 'premise_assembly', 'degree_grid_identity_check'),
              'obligations.run', 'Missing premises become child questions whose checked proofs are flattened.'),
    synthesis('guard_repair', 'EXISTING', ('rational_counterexample_search', 'repair_questions',
              'assumption_residual_slice_guards', 'guard_candidate_check', 'guard_equivalence_merge'),
              'campaign repairs through algebra.run', 'A checked counterexample opens explicit supported guard repairs.'),
    synthesis('repair_then_reuse', 'EXISTING', ('rational_counterexample_search', 'guard_discovery_driver',
              'lemma_memory'), 'campaign.run remember_lemma for guards', 'Checked guard repairs become library lemmas.'),
    synthesis('word_formula_repair', 'EXISTING', ('word_counterexample_certificate', 'repair_questions',
              'word_state_numerators', 'word_identity_check'), 'campaign full_formula_repair',
              'A refuted shortcut formula opens the full-overlap question.'),
    synthesis('generalize_after_solving', 'EXISTING', ('exact_iteration', 'generalization_questions',
              'recurrence_prefix_observation', 'scalar_recurrence_fit', 'entry_closure_residual_check'),
              'campaign discover_after_solving', 'A settled finite count opens an all-index recurrence question.'),
    synthesis('invariant_degree_ladder', 'EXISTING', ('invariant_residual_operator', 'invariant_nullspace_candidate',
              'invariant_degree_expansion', 'invariant_residual_operator'), 'campaign expansions',
              'Bounded misses open a higher-degree question with its own identity.'),
    synthesis('mapped_invariant', 'EXISTING', ('invariant_residual_operator', 'dependency_map_components',
              'map_validation_fallback', 'invariant_nullspace_candidate', 'invariant_grid_check'),
              'invariant.run mapped', 'Coefficient dependencies split the operator; the original check admits.'),
    synthesis('law_reuse_reentry', 'EXISTING', ('invariant_memory', 'context_reentry', 'invariant_reuse_first',
              'invariant_grid_check'), 'campaign reuse_invariants', 'A later checked law reopens an earlier unresolved original.'),
    synthesis('residual_lemma_invention', 'EXISTING', ('normalize_and_join', 'typed_residual_frontier',
              'candidate_admissibility', 'candidate_finite_filter', 'structural_induction_search',
              'bundle_lemma_admission', 'parent_reentry'), 'recursive.run residual',
              'Residual terms condition lemmas; false ones are refuted; checked ones re-enter the parent.'),
    synthesis('source_gap_bridge', 'EXISTING', ('source_capsule_binding', 'source_tension', 'gap_bridge_ranking',
              'checked_seed_transport', 'recursive_identity_admission'), 'source_episode.run gap_bridge',
              'Tension and residual matches select checked same-definition bridges.'),
    synthesis('law_to_instance', 'APEX', ('recurrence_prefix_observation', 'scalar_recurrence_fit',
              'entry_closure_residual_check', 'law_evaluation'), 'apex.law_instance',
              'Go up to an all-index law, then come down to the requested horizon.'),
    synthesis('compress_discover_lift', 'APEX', ('quotient_refinement', 'law_carrier', 'recurrence_prefix_observation',
              'scalar_recurrence_fit', 'entry_closure_residual_check', 'law_evaluation'),
              'apex.law_instance with a compressing quotient', 'Discover the law on a checked quotient and lift it through MP=PQ.'),
    synthesis('orbit_periodic_refutation', 'APEX', ('orbit_prefix', 'orbit_check'), 'apex.orbit_prefix',
              'A repeated state bounds the orbit; the target is absent from its finite set.'),
    synthesis('orbit_invariant_separation', 'APEX', ('invariant_residual_operator', 'selector_kernel_search',
              'orbit_kernel_separation', 'invariant_grid_check', 'orbit_check'), 'apex.orbit_invariant',
              'A conserved value that differs at the target refutes reachability for every n.'),
    synthesis('orbit_transferred_separation', 'APEX', ('invariant_memory', 'invariant_renaming', 'orbit_law_transfer',
              'invariant_grid_check', 'orbit_check'), 'apex.orbit_transfer',
              'A law learned on another system, renamed and rechecked, separates.'),
    synthesis('recursive_memory_transfer', 'APEX', ('apex_memory', 'recursive_seed_selection', 'checked_seed_transfer',
              'recursive_identity_admission'), 'apex.recursive_seeded',
              'A proof admitted for one question seeds another with the same complete definitions.'),
    synthesis('four_face_orbit_question', 'APEX', ('orbit_prefix', 'orbit_law_transfer', 'orbit_kernel_separation',
              'apex_memory'), 'apex.solve_orbit', 'One orbit question asked from S, W, E and N; new laws are stored.',
              form='faces'),
    synthesis('apex_research_cycle', 'APEX', ('apex_face_schedule', 'campaign_admission', 'context_reentry',
              'generalization_questions', 'repair_questions', 'apex_admission', 'apex_memory'),
              'apex.Layer through campaign.run',
              'Every obligation cycles faces; knowledge changes reopen misses; only original checkers admit.',
              form='faces'),
    synthesis('word_count_law_instance', 'PROPOSED', ('recurrence_prefix_observation', 'scalar_recurrence_fit',
              'entry_closure_residual_check', 'law_evaluation'), 'none',
              'Count forbidden-word avoiders at a large length from a checked word recurrence.',
              needs=('word_count_original_query', 'word_carrier_evaluation'), node='NWS'),
    synthesis('ranking_exclusion', 'PROPOSED', ('orbit_prefix', 'orbit_check'), 'none',
              'Exclude a target by a polynomial that strictly increases along the orbit.',
              needs=('ranking_polynomial_proposal', 'ordered_field_monotonicity_check'), node='NWS'),
    synthesis('child_refutation_lift', 'PROPOSED', ('and_or_route_selection', 'counterexample_point_check'), 'none',
              'A child counterexample also refutes the parent when the parent goal is nonzero at that point.',
              needs=('parent_goal_evaluation_at_child_point',), node='WSE'),
    synthesis('recurrence_generating_function', 'PROPOSED', ('entry_closure_residual_check', 'word_identity_check'),
              'none', 'A checked recurrence and its initial terms give a rational generating function P/Q.',
              needs=('generating_function_certificate_kind',), node='NSE'),
    synthesis('invariant_level_set_lemma', 'PROPOSED', ('invariant_grid_check', 'lemma_memory'), 'none',
              'A checked invariant yields the lemma P(x)-c=0 implies P(F(x))-c=0 for polynomial transfer.',
              needs=('transition_substitution_lemma_record',), node='NSE'),
    synthesis('recurrence_minimality', 'PROPOSED', ('scalar_recurrence_fit', 'entry_closure_residual_check'), 'none',
              'Inconsistent Hankel systems below the checked order certify minimality.',
              needs=('hankel_inconsistency_checker',), node='WS'),
    synthesis('counterexample_instance_lifting', 'PROPOSED', ('native_attempt_admission',
              'recursive_counterexample_admission'), 'none',
              'A counterexample to an instance of a goal maps to a counterexample of the general goal.',
              needs=('goal_instance_matcher',), node='WSE'),
)

# Routes the apex can schedule, as the base moves each route executes.
ROUTES = {
    'auto': ('initial_partition_probe', 'exact_iteration'), 'direct': ('exact_iteration',),
    'quotient': ('quotient_refinement', 'recipe_transfer'),
    'law_instance': ('quotient_refinement', 'law_carrier', 'scalar_recurrence_fit', 'law_evaluation'),
    'discover_recurrence': ('recurrence_prefix_observation', 'scalar_recurrence_fit', 'entry_closure_residual_check'),
    'discover_word_recurrence': ('word_automaton_producer', 'scalar_recurrence_fit', 'entry_closure_residual_check'),
    'original': ('original_binding', 'checked_replay'),
    'full_formula_repair': ('repair_questions', 'word_state_numerators', 'word_identity_check'),
    'original_implication': ('sparse_exponent_bases', 'dense_degree_ladder', 'rational_counterexample_search',
                             'lemma_reuse_schedule', 'degree_grid_identity_check'),
    'localized_implication': ('localized_guard_lift', 'localized_grid_check'),
    'guarded_lemma_first': ('lemma_reuse_schedule', 'guarded_transfer', 'degree_grid_identity_check'),
    'pair_equalities': ('pair_equality_guards', 'guard_discovery_driver'),
    'coefficient_slices': ('coefficient_slice_guards', 'guard_discovery_driver'),
    'assumption_slices': ('assumption_residual_slice_guards', 'guard_discovery_driver'),
    'invariant_full': ('invariant_residual_operator', 'invariant_nullspace_candidate', 'invariant_grid_check'),
    'invariant_mapped': ('dependency_map_components', 'map_validation_fallback', 'invariant_nullspace_candidate'),
    'invariant_reuse_first': ('invariant_reuse_first', 'invariant_grid_check'),
    'invariant_degree': ('invariant_degree_expansion', 'invariant_nullspace_candidate', 'invariant_grid_check'),
    'recursive_direct': ('normalize_and_join', 'structural_induction_search', 'root_finite_refutation'),
    'recursive_residual': ('typed_residual_frontier', 'accumulator_generalization', 'candidate_finite_filter',
                           'structural_induction_search', 'parent_reentry'),
    'recursive_enumerate': ('fixed_typed_enumeration', 'candidate_finite_filter', 'structural_induction_search'),
    'recursive_seeded': ('recursive_seed_selection', 'checked_seed_transfer', 'structural_induction_search',
                         'parent_reentry'),
    'orbit_prefix': ('orbit_prefix', 'orbit_check'), 'orbit_transfer': ('orbit_law_transfer', 'orbit_check'),
    'orbit_invariant': ('orbit_kernel_separation', 'orbit_check'),
}
QUERY_ROUTES = {'test_overlap_shortcut': ('overlap_generalization_test', 'overlap_counterexample_check'),
                'word_avoidance_identity': ('word_overlap_formula', 'word_state_numerators', 'word_identity_check'),
                'discover_recurrence': ('recurrence_prefix_observation', 'scalar_recurrence_fit'),
                'discover_word_recurrence': ('word_automaton_producer', 'scalar_recurrence_fit')}


def node(directions):
    return ''.join(d for d in DIRECTIONS if d in directions)


WIDER = {'derived': ('original',), 'law': ('certificate',), 'counterexample': ('certificate',)}


def satisfies(produced, consumed):
    """A derived question is an original question; laws and refutations are checked certificates."""
    return produced == consumed or consumed in WIDER.get(produced, ())


def synthesis_node(s):
    return s['declared'] or union(s['steps'])


def _moves():
    return {m['id']: m for m in MOVES}


def union(ids):
    table = _moves()
    return node(''.join(table[i]['dirs'] for i in ids))


def route_node(strategy, role, query=None):
    """The lattice node of a scheduled route: the union of its moves' directions."""
    if strategy.startswith('invariant_degree_'): strategy = 'invariant_degree'
    steps = ROUTES.get(strategy) or QUERY_ROUTES.get(query, ('original_binding',))
    if role == 'repair' and strategy in ('pair_equalities', 'coefficient_slices', 'assumption_slices'):
        steps = ('repair_questions',) + steps
    return union(steps)


def _source_facts(path):
    """Definitions and explicit direction/operation trace labels in one module."""
    tree = ast.parse(path.read_bytes(), filename=path.name)
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    labels = set()
    for n in ast.walk(tree):
        pairs = {}
        if isinstance(n, ast.Dict):
            pairs = {k.value: v for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant)}
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'dict':
            pairs = {k.arg: k.value for k in n.keywords if k.arg}
        d, o = pairs.get('direction'), pairs.get('operation')
        if (isinstance(d, ast.Constant) and d.value in DIRECTIONS and isinstance(o, ast.Constant)
                and type(o.value) is str):
            labels.add(d.value + ':' + o.value)
    return names, labels


def audit(root):
    """Bind the catalog to source text: entries exist, labels are claimed, syntheses chain."""
    root = Path(root); problems = []; table = _moves(); facts = {}
    for name in MODULES:
        try: facts[name] = _source_facts(root / name)
        except (OSError, SyntaxError) as exc: problems.append(name + ': unreadable module: ' + str(exc))
    if len(table) != len(MOVES): problems.append('duplicate move identifiers')
    claimed = {name: set() for name in MODULES}
    for m in MOVES:
        if m['module'] not in facts: problems.append(m['id'] + ': module not audited'); continue
        names, labels = facts[m['module']]
        if node(m['dirs']) != m['dirs']: problems.append(m['id'] + ': directions not in N,W,S,E order')
        if not set(m['consumes']) | set(m['produces']) <= set(TYPES): problems.append(m['id'] + ': unknown type')
        for entry in m['entries']:
            module, _, name = entry.rpartition(':')
            defined = facts.get(module or m['module'], (set(), set()))[0]
            if name not in defined: problems.append(m['id'] + ': missing entry ' + (module or m['module']) + ':' + name)
        for label in m['labels']:
            if label not in labels: problems.append(m['id'] + ': label not in source ' + label)
            if label[0] not in m['dirs']: problems.append(m['id'] + ': label direction outside move ' + label)
            claimed[m['module']].add(label)
    for name, (_, labels) in facts.items():
        for label in sorted(labels - claimed[name]): problems.append(name + ': uncatalogued trace label ' + label)
    for s in SYNTHESES:
        missing = [i for i in s['steps'] if i not in table]
        if missing: problems.append(s['id'] + ': unknown steps ' + ','.join(missing)); continue
        if s['status'] not in ('EXISTING', 'APEX', 'PROPOSED'): problems.append(s['id'] + ': status')
        if (s['status'] == 'PROPOSED') != bool(s['needs']) or (s['status'] == 'PROPOSED') != bool(s['declared']):
            problems.append(s['id'] + ': only proposed syntheses declare missing moves and a node')
        if s['form'] == 'faces':
            if len({d for i in s['steps'] for d in table[i]['dirs']}) < 2: problems.append(s['id'] + ': one face')
        elif s['form'] != 'chain': problems.append(s['id'] + ': unknown form')
        elif s['status'] != 'PROPOSED':
            for a, b in zip(s['steps'], s['steps'][1:]):
                if not any(satisfies(p, c) for p in table[a]['produces'] for c in table[b]['consumes']):
                    problems.append(s['id'] + ': ' + a + ' produces nothing ' + b + ' consumes')
    for strategy, steps in list(ROUTES.items()) + list(QUERY_ROUTES.items()):
        if any(i not in table for i in steps): problems.append('route ' + strategy + ': unknown move')
    labels_in_code = sum(len(v[1]) for v in facts.values())
    return dict(ok=not problems, problems=problems, modules=len(facts), moves=len(MOVES),
                trace_labels=labels_in_code, syntheses=len(SYNTHESES))


def lattice():
    """Fifteen nodes, level by level, with the moves and syntheses realizing each."""
    rows = []
    for key in NODE_ORDER:
        moves = [m['id'] for m in MOVES if m['dirs'] == key]
        built = [s['id'] for s in SYNTHESES if s['status'] != 'PROPOSED' and synthesis_node(s) == key]
        open_ = [s['id'] for s in SYNTHESES if s['status'] == 'PROPOSED' and synthesis_node(s) == key]
        rows.append(dict(node=key, level=len(key), name=NODE_NAMES[key], moves=moves, syntheses=built,
                         proposed=open_, realized=bool(moves or built)))
    return rows


def report(root):
    checked = audit(root)
    faces = {d: [m['id'] for m in MOVES if d in m['dirs']] for d in DIRECTIONS}
    return dict(status='PYRAMID', schema=VERSION, directions=MEANING, faces=faces,
                base=[dict(m, node=m['dirs'] or 'control') for m in MOVES],
                syntheses=[dict(s, node=synthesis_node(s)) for s in SYNTHESES],
                lattice=lattice(), apex=[s['id'] for s in SYNTHESES if s['status'] != 'PROPOSED'
                                         and synthesis_node(s) == 'NWSE'],
                audit=checked,
                limits='A classification of implemented operations bound to source text; not evidence that any claim holds.')
