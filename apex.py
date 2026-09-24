"""Ember's apex: the higher reasoning layer above her subreasoners.

The apex plans every original obligation from four Theory Pyramid Mapping faces:
S attacks the question as stated, W refutes or repairs it, N generalizes it or
changes its representation, and E transfers checked knowledge. For each
obligation it schedules the face with the fewest attempts, ranks routes inside
a face by measured outcomes and costs, and admits results only through
original-task checkers. It also owns synthesized routes that compose existing
subreasoners. Directions and scores schedule work; they never establish truth.
"""
import copy
import hashlib
import json
from pathlib import Path
import time

# Tie order: the question as stated, checked memory, failure-directed work, then
# broader generalization. A chosen scheduling policy, not a claim about truth.
FACE_ORDER = ('S', 'E', 'W', 'N')
ORBIT_ROUTES = ('orbit_prefix', 'orbit_transfer', 'orbit_invariant', 'orbit_drift')
SINGLE_ROUTES = {'prove_orbit_exclusion': ORBIT_ROUTES,
                 'count_word_avoiders': ('word_count_law', 'word_count_direct'),
                 'discover_generating_function': ('generating_function',),
                 'certify_minimal_recurrence': ('recurrence_minimality',)}
SYNTHESES = (('law_instance', 'recursive_seeded', 'recursive_lifted_counterexample', 'word_count_direct', 'word_count_law',
              'generating_function', 'recurrence_minimality') + ORBIT_ROUTES)
CHECKED_BY_APEX = ('law_instance', 'word_count_direct', 'word_count_law', 'generating_function',
                   'recurrence_minimality') + ORBIT_ROUTES
ROLE_FACES = {'repair': 'W', 'generalization': 'N', 'expansion': 'N'}
STRATEGY_FACES = {'quotient': 'N', 'law_instance': 'N', 'invariant_mapped': 'N', 'localized_implication': 'N',
                  'recursive_enumerate': 'N', 'orbit_invariant': 'N', 'orbit_drift': 'N', 'invariant_reuse_first': 'E',
                  'guarded_lemma_first': 'E', 'orbit_transfer': 'E', 'recursive_seeded': 'E', 'recursive_residual': 'W',
                  'recursive_lifted_counterexample': 'E', 'word_count_law': 'N', 'generating_function': 'N',
                  'recurrence_minimality': 'W'}
LAW_CARRIER_STATES = 64
TRANSFER_RECORDS = 8
SEED_ENTRIES = 8


class _Uncharged:
    """Proposal-context bookkeeping outside any work budget, as campaign contexts are."""
    def use(self, amount=1): pass


def face(route):
    return ROLE_FACES.get(route['role']) or STRATEGY_FACES.get(route['strategy'], 'S')


def face_counts(record, byid, problem):
    """Executed attempts per face for one obligation, superseded stages included."""
    counts = dict.fromkeys(FACE_ORDER, 0)
    for attempt in record['attempts'] + record['superseded_attempts']:
        route = byid.get(attempt['route_id'])
        if route is not None and route['problem'] == problem: counts[route['face']] += 1
    return counts


def generation():
    """Fingerprint the apex layer and every module it can route through."""
    root = Path(__file__).resolve().parent
    names = ('ember.py', 'campaign.py', 'apex.py', 'apex_check.py', 'pyramid.py', 'algebra.py', 'algebra_check.py',
             'word_series.py', 'word_check.py', 'recurrence.py', 'recurrence_check.py', 'invariant.py',
             'invariant_check.py', 'invariant_map.py', 'recursive.py', 'recursive_check.py', 'obligations.py',
             'source_episode.py')
    return hashlib.sha256(b''.join((root / name).read_bytes() for name in names)).hexdigest()


def _limits(host):
    return (host.Exhausted, host.local_module('apex_check').Limit, host.local_module('invariant_check').Limit,
            host.local_module('recurrence_check').Limit)


def _invalid(host):
    return (host.local_module('apex_check').Invalid, host.local_module('invariant_check').Invalid,
            host.local_module('recurrence_check').Invalid)


def encoded(q):
    return [q.numerator, q.denominator]


# ---------------------------------------------------------------- syntheses

def law_instance(task, budget, host):
    """N then S (and E through a quotient): answer one horizon from an all-index law."""
    checker = host.local_module('apex_check'); rcheck = host.local_module('recurrence_check')
    engine = host.local_module('recurrence')
    M, u, v, h, identity = host.bind(task); n = len(M); trace = []; carriers = []
    quotient = host.propose(M, v, identity, budget, trace)
    if len(quotient['blocks']) < n:
        Qm, a, w = checker.check_quotient(M, u, v, identity, quotient, budget)
        trace.append(dict(direction='S', operation='check_quotient_carrier_on_original', states=len(Qm)))
        if len(Qm) <= LAW_CARRIER_STATES: carriers.append((quotient, (Qm, a, w)))
    if n <= LAW_CARRIER_STATES: carriers.append((None, (M, u, v)))
    reasons = []
    for quotient_certificate, carrier in carriers:
        derived = checker.recurrence_task(*carrier)
        try: rcheck.bind(derived)
        except rcheck.Invalid as exc:
            reasons.append('carrier outside recurrence bounds: ' + str(exc))
            trace.append(dict(direction='W', operation='reject_law_carrier_outside_recurrence_bounds', reason=str(exc)))
            continue
        found = engine.run(derived, budget, rcheck)
        trace.extend(found.get('trace', []))
        if found['status'] != 'CHECKED_RECURRENCE':
            reasons.append(found.get('reason', 'no checked recurrence')); continue
        certificate = dict(kind='law_instance', task_id=identity, recurrence=found['certificate'])
        if quotient_certificate is not None:
            certificate['quotient'] = quotient_certificate
            trace.append(dict(direction='E', operation='transport_law_through_checked_quotient', states=len(carrier[0])))
        checked = checker.check_law_instance(task, certificate, budget)
        trace.append(dict(direction='S', operation='evaluate_checked_law_at_original_horizon', horizon=h,
                          order=checked['order'], accepted=True))
        return dict(status='CHECKED_EXACT', answer=checked['answer'], task_id=identity, route='law_instance',
                    certificate=certificate, check=checked, trace=trace, original_states=n,
                    carrier_states=checked['carrier_states'],
                    limits='A checked all-index recurrence evaluated at one horizon; no minimality, speed or novelty claim.')
    if not carriers: reasons.append('no carrier with at most 64 states')
    return dict(status='UNKNOWN', reason='; '.join(reasons), trace=trace)


def orbit_prefix(task, budget, host):
    """S with W: iterate the original orbit; stop at the target or at a repeated state."""
    checker = host.local_module('apex_check'); b = checker.bind_orbit(task)
    trace = [dict(direction='S', operation='iterate_original_orbit_prefix', max_steps=b['max_steps'])]
    key = lambda point: tuple((q.numerator, q.denominator) for q in point)
    state = list(b['initial']); seen = {key(state): 0}; certificate = None
    if state == b['target']: certificate = dict(kind='orbit_witness', task_id=b['identity'], index=0)
    for index in range(1, b['max_steps'] + 1):
        if certificate is not None: break
        state = checker.orbit_step(b, state, budget); budget.use(len(state))
        if state == b['target']:
            certificate = dict(kind='orbit_witness', task_id=b['identity'], index=index)
        elif key(state) in seen:
            start = seen[key(state)]
            certificate = dict(kind='periodic_orbit', task_id=b['identity'], start=start, period=index - start)
            trace.append(dict(direction='W', operation='refute_reachability_by_repeated_state', start=start,
                              period=index - start))
        else: seen[key(state)] = index
    if certificate is None:
        return dict(status='UNKNOWN', reason='no target hit or repeated state within max_steps', trace=trace)
    checked = checker.check_orbit(task, certificate, budget)
    trace.append(dict(direction='S', operation='check_original_orbit_prefix_certificate', accepted=True))
    return dict(status=checker.orbit_status(checked), certificate=certificate, check=checked, trace=trace)


def separation_certificate(b, receiving, poly, budget, host):
    algebra = host.local_module('algebra'); invariant = host.local_module('invariant_check')
    initial = algebra.evaluate(poly, receiving['initial'], budget, invariant)
    target = algebra.evaluate(poly, b['target'], budget, invariant)
    if initial == target: return None
    law = dict(kind='polynomial_invariant', task_id=receiving['identity'], polynomial=algebra.encoded(poly),
               initial_value=encoded(initial))
    return dict(kind='invariant_separation', task_id=b['identity'], invariant=law, target_value=encoded(target))


def orbit_invariant(task, budget, host):
    """N then S and W: find a kernel invariant whose value separates target and start."""
    checker = host.local_module('apex_check'); invariant = host.local_module('invariant_check')
    engine = host.local_module('invariant'); algebra = host.local_module('algebra')
    b = checker.bind_orbit(task); receiving = invariant.bind(b['derived'])
    basis = algebra.monomials(len(receiving['names']), receiving['degree'])[1:]
    columns = engine.build_operator(receiving, basis, budget, invariant, algebra)
    trace = [dict(direction='S', operation='form_orbit_invariant_operator', columns=len(columns))]
    differences = [algebra.evaluate({powers: 1}, receiving['initial'], budget, invariant)
                   - algebra.evaluate({powers: 1}, b['target'], budget, invariant) for powers in basis]

    def separates(vector):
        budget.use(2 * len(vector))
        return sum(q * d for q, d in zip(vector, differences) if q and d) != 0

    diagnostics = {}
    poly = engine.search_operator(receiving, basis, columns, budget, invariant, diagnostics, select=separates)
    if poly is None:
        # A linear functional vanishing on every kernel basis vector vanishes on the kernel.
        return dict(status='UNKNOWN', trace=trace, invariant_search=diagnostics,
                    reason='no polynomial invariant within the degree bound separates target and initial point')
    trace.append(dict(direction='N', operation='propose_separating_kernel_invariant', terms=len(poly)))
    certificate = separation_certificate(b, receiving, poly, budget, host)
    checked = checker.check_orbit(task, certificate, budget)
    trace.append(dict(direction='W', operation='refute_reachability_by_invariant_value', accepted=True))
    return dict(status=checker.orbit_status(checked), certificate=certificate, check=checked, trace=trace,
                invariant_search=diagnostics)


def orbit_transfer(task, budget, host, records):
    """E then S and W: rename stored checked laws; admit only a receiving separation."""
    checker = host.local_module('apex_check'); invariant = host.local_module('invariant_check')
    engine = host.local_module('invariant')
    b = checker.bind_orbit(task); receiving = invariant.bind(b['derived'])
    diagnostics = dict(records_considered=0, sources_checked=0, source_failures=0, bindings_considered=0,
                       nonseparating=0, target_failures=0, used=False)
    trace = [dict(direction='E', operation='collect_stored_checked_laws', records=min(len(records), TRANSFER_RECORDS))]
    for index, record in enumerate(list(records)[:TRANSFER_RECORDS]):
        diagnostics['records_considered'] += 1
        try:
            source = invariant.bind(record['task'])
            invariant.check(record['task'], record['certificate'], budget)
            terms = invariant.polynomial(record['certificate']['polynomial'], source)
            active = [i for i in range(len(source['names'])) if any(powers[i] for powers, _ in terms)]
            mappings = engine.reuse_bindings(active, source['names'], receiving['names'], budget)
        except (invariant.Invalid, invariant.Limit, TypeError, KeyError, ValueError):
            diagnostics['source_failures'] += 1; continue
        diagnostics['sources_checked'] += 1
        for mapping in mappings:
            diagnostics['bindings_considered'] += 1
            poly = engine.renamed_invariant(terms, active, mapping, len(receiving['names']), budget, invariant)
            if any(sum(powers) > receiving['degree'] for powers in poly):
                diagnostics['nonseparating'] += 1; continue
            certificate = separation_certificate(b, receiving, poly, budget, host)
            if certificate is None:
                diagnostics['nonseparating'] += 1; continue
            try: checked = checker.check_orbit(task, certificate, budget)
            except (checker.Invalid, checker.Limit):
                diagnostics['target_failures'] += 1; continue
            names = {source['names'][i]: receiving['names'][j] for i, j in zip(active, mapping)}
            diagnostics.update(used=True, source_task_id=source['identity'], binding=names)
            trace += [dict(direction='S', operation='freshly_check_stored_law_source', source_task_id=source['identity']),
                      dict(direction='E', operation='rename_stored_law_into_receiving_orbit', binding=names),
                      dict(direction='W', operation='refute_reachability_by_transferred_invariant', accepted=True)]
            return dict(status=checker.orbit_status(checked), certificate=certificate, check=checked, trace=trace,
                        law_transfer=diagnostics)
    return dict(status='UNKNOWN', reason='no stored checked law separates this orbit', trace=trace,
                law_transfer=diagnostics)


def recursive_seeds(task, state, host, budget):
    """Remembered checked proofs of other questions with the same complete definitions.

    Selection follows source-episode seeding: statements touching the receiver's
    function closure, at most eight entries. Seeds are proposals; prepare_seeds
    rechecks every source proof under the receiving original definitions.
    """
    checker = host.local_module('recursive_check'); source = host.local_module('source_episode')
    receiving = checker.bind(task, budget)['identity']; relevant = source.closure(task, budget)
    seeds = []; count = 0; seen = set()
    for row in reversed(state['observations']):
        if count >= SEED_ENTRIES or len(seeds) >= 8: break
        if (row.get('kind') != 'prove_recursive_identity' or row.get('status') != 'CHECKED_RECURSIVE_IDENTITY'
                or row.get('task_id') == receiving or type(row.get('task')) is not dict
                or type(row.get('certificate')) is not dict): continue
        original, certificate = row['task'], row['certificate']
        budget.use(len(host.canonical(original).encode()))
        if original.get('domain') != task['domain'] or original.get('definitions') != task['definitions']: continue
        key = host.digest(certificate)
        if key in seen: continue
        seen.add(key); selected = []
        try:
            entries = [item['goal'] for item in certificate['lemmas']] + [original['goal']]
            for index, goal in enumerate(entries[:17]):
                if count >= SEED_ENTRIES: break
                if (source.symbols(goal['lhs'], budget) | source.symbols(goal['rhs'], budget)) & relevant:
                    selected.append(index); count += 1
        except (TypeError, KeyError): continue
        if selected:
            seeds.append(dict(source_task=copy.deepcopy(original), source_certificate=copy.deepcopy(certificate),
                              selected_indices=selected, source_id='memory_' + str(len(seeds)), source_commit_id=key))
    return seeds


def recursive_seeded(task, state, limit, host):
    """E: resume a residual episode seeded with remembered same-definition proofs."""
    budget = host.Budget(limit); candidate = copy.deepcopy(state); checker = host.local_module('recursive_check')
    try:
        seeds = recursive_seeds(task, state, host, budget)
        if not seeds:
            result = dict(status='UNKNOWN', reason='no remembered checked proof shares these definitions'); candidate = None
        else:
            result = host.local_module('recursive').run(task, candidate, None, budget, host, policy='residual', steps=4,
                                                        seed_records=seeds)
            result['seeds'] = [dict(source_commit_id=s['source_commit_id'], selected_indices=s['selected_indices'])
                               for s in seeds]
    except (host.Exhausted, checker.Limit, checker.Invalid) as exc:
        result = dict(status='UNKNOWN', reason=str(exc))
    result['work'] = budget.work
    return result, candidate


def orbit_drift(task, budget, host):
    """N then S and W: a polynomial R with R(F(x))-R(x) constant decides the target's only index."""
    checker = host.local_module('apex_check'); invariant = host.local_module('invariant_check')
    engine = host.local_module('invariant'); algebra = host.local_module('algebra')
    b = checker.bind_orbit(task); clocked = invariant.bind(checker.clocked_task(b)); n = len(b['names'])
    basis = [powers + (0,) for powers in algebra.monomials(n, clocked['degree'])[1:]] + [(0,) * n + (1,)]
    columns = engine.build_operator(clocked, basis, budget, invariant, algebra)
    trace = [dict(direction='S', operation='form_clocked_drift_operator', columns=len(columns))]
    gaps = [algebra.evaluate({powers[:n]: 1}, b['initial'], budget, invariant)
            - algebra.evaluate({powers[:n]: 1}, b['target'], budget, invariant) for powers in basis[:-1]]

    def decides(vector):
        budget.use(2 * len(vector))
        if not vector[-1]: return False
        steps = sum(q * g for q, g in zip(vector[:-1], gaps) if q and g) / vector[-1]
        return steps.denominator != 1 or steps < 0 or steps <= b['max_steps']

    diagnostics = {}
    poly = engine.search_operator(clocked, basis, columns, budget, invariant, diagnostics, select=decides)
    if poly is None:
        return dict(status='UNKNOWN', trace=trace, invariant_search=diagnostics,
                    reason='no drift function within the degree bound decides the target')
    trace.append(dict(direction='N', operation='propose_clocked_drift_function', terms=len(poly)))
    kappa = poly[(0,) * n + (1,)]; drift = {e[:n]: q for e, q in poly.items() if not e[n]}
    steps = (algebra.evaluate(drift, b['initial'], budget, invariant)
             - algebra.evaluate(drift, b['target'], budget, invariant)) / kappa
    law = dict(kind='polynomial_invariant', task_id=clocked['identity'], polynomial=algebra.encoded(poly),
               initial_value=encoded(algebra.evaluate(poly, clocked['initial'], budget, invariant)))
    certificate = dict(kind='drift_separation', task_id=b['identity'], clocked=law)
    if steps.denominator == 1 and steps >= 0: certificate['index'] = int(steps)
    checked = checker.check_orbit(task, certificate, budget)
    if checked['outcome'] == 'EXCLUDED':
        trace.append(dict(direction='W', operation='refute_reachability_by_drift_value', accepted=True))
    else: trace.append(dict(direction='S', operation='witness_reachability_at_drift_index', index=checked['index']))
    return dict(status=checker.orbit_status(checked), certificate=certificate, check=checked, trace=trace,
                invariant_search=diagnostics)


def word_count_direct(task, budget, host):
    """S: iterate the checker's own prefix automaton to the original length."""
    checker = host.local_module('apex_check'); counted = checker.bind_word_count(task)
    answer = checker.count_words(task, budget)
    return dict(status='EXACT_DIRECT', answer=answer, task_id=counted['identity'],
                trace=[dict(direction='S', operation='iterate_original_word_automaton', length=counted['length'])])


def recurrence_certificate(derived, budget, host):
    found = host.local_module('recurrence').run(derived, budget, host.local_module('recurrence_check'))
    return found, list(found.get('trace', []))


def word_count_law(task, budget, host):
    """N then S: discover the all-length word recurrence and evaluate it at the original length."""
    checker = host.local_module('apex_check'); counted = checker.bind_word_count(task)
    found, trace = recurrence_certificate(counted['derived'], budget, host)
    if found['status'] != 'CHECKED_RECURRENCE':
        return dict(status='UNKNOWN', reason=found.get('reason', 'no checked word recurrence'), trace=trace)
    certificate = dict(kind='word_count_law', task_id=counted['identity'], recurrence=found['certificate'])
    checked = checker.check_word_count(task, certificate, budget)
    trace.append(dict(direction='S', operation='evaluate_word_law_at_original_length', length=counted['length']))
    return dict(status='CHECKED_EXACT', answer=checked['answer'], certificate=certificate, check=checked, trace=trace)


def generating_function(task, budget, host):
    """N then S: a checked recurrence with its initial terms as a rational generating function."""
    checker = host.local_module('apex_check'); carried = checker.carrier(task, 'discover_generating_function')
    found, trace = recurrence_certificate(carried['derived'], budget, host)
    if found['status'] != 'CHECKED_RECURRENCE':
        return dict(status='UNKNOWN', reason=found.get('reason', 'no checked recurrence'), trace=trace)
    numerator, denominator = checker.generating_function(found['certificate'])
    trace.append(dict(direction='N', operation='form_rational_generating_function', order=found['certificate']['order']))
    certificate = dict(kind='rational_generating_function', task_id=carried['identity'], recurrence=found['certificate'],
                       numerator=numerator, denominator=denominator)
    checked = checker.check_generating_function(task, certificate, budget)
    trace.append(dict(direction='S', operation='check_generating_function_on_original', accepted=True))
    return dict(status='CHECKED_GENERATING_FUNCTION', certificate=certificate, check=checked, trace=trace,
                numerator=numerator, denominator=denominator)


def recurrence_minimality(task, budget, host):
    """N, W then S: discover a recurrence, then refute every lower order with a Hankel determinant."""
    checker = host.local_module('apex_check'); carried = checker.carrier(task, 'certify_minimal_recurrence')
    found, trace = recurrence_certificate(carried['derived'], budget, host)
    if found['status'] != 'CHECKED_RECURRENCE':
        return dict(status='UNKNOWN', reason=found.get('reason', 'no checked recurrence'), trace=trace)
    certificate = dict(kind='minimal_recurrence', task_id=carried['identity'], recurrence=found['certificate'])
    trace.append(dict(direction='W', operation='refute_lower_orders_by_hankel_determinant',
                      order=found['certificate']['order']))
    checked = checker.check_minimal_recurrence(task, certificate, budget)
    trace.append(dict(direction='S', operation='check_minimal_order_on_original', accepted=True))
    return dict(status='CHECKED_MINIMAL_RECURRENCE', certificate=certificate, check=checked, trace=trace)


def recursive_refutations(task, state):
    """At most eight remembered refutations over the receiving definitions; proposals only."""
    rows = []
    for row in reversed(state['observations']):
        if (row.get('kind') == 'prove_recursive_identity' and row.get('status') == 'CHECKED_RECURSIVE_COUNTEREXAMPLE'
                and type(row.get('task')) is dict and type(row.get('certificate')) is dict
                and row['task'].get('domain') == task.get('domain')
                and row['task'].get('definitions') == task.get('definitions') and row['task'] != task):
            rows.append(row)
    return rows[:8]


def recursive_lift(task, state, budget, host):
    """E then S and W: a remembered refutation of an instance refutes the general equation."""
    engine = host.local_module('recursive'); checker = host.local_module('recursive_check')
    receiving = checker.bind(task, budget); theory = engine.Theory(task, budget)
    goal = engine.read_goal(task['goal']); scope = engine.goal_vars(goal); cache = {}
    rows = recursive_refutations(task, state)
    trace = [dict(direction='E', operation='collect_remembered_recursive_refutations', records=len(rows))]
    for row in rows:
        source = row['task']
        try:
            instance = engine.read_goal(source['goal'])
            values = {name: engine.read(value) for name, value in row['certificate']['point'].items()}
        except (TypeError, KeyError, IndexError): continue
        for left, right in ((instance[0], instance[1]), (instance[1], instance[0])):
            env = engine.match(goal[0], left, set(scope), theory, budget, {})
            if env is not None: env = engine.match(goal[1], right, set(scope), theory, budget, env)
            if env is None or set(env) != set(scope): continue
            try:
                point = {name: engine.data(engine.evaluate(engine.subst(env[name], values, budget), theory, budget, cache))
                         for name in scope}
            except (ValueError, engine.SearchLimit): continue
            trace.append(dict(direction='N', operation='propose_lifted_counterexample_point'))
            certificate = dict(kind='recursive_counterexample', task_id=receiving['identity'], point=point)
            try: checked = checker.check(task, certificate, budget)
            except checker.Invalid:
                trace.append(dict(direction='W', operation='refuse_lifted_counterexample')); continue
            trace.append(dict(direction='S', operation='check_lifted_counterexample_on_original', accepted=True))
            return dict(status='CHECKED_RECURSIVE_COUNTEREXAMPLE', certificate=certificate, check=checked, trace=trace)
    return dict(status='UNKNOWN', reason='no remembered refutation is an instance of this equation', trace=trace)


def level_set_lemma(invariant_task, invariant_certificate, host, budget):
    """A checked law P(F(x))=P(x) as the polynomial lemma P(x)-level=0 implies P(F(x))-level=0."""
    invariant = host.local_module('invariant_check'); checker = host.local_module('algebra_check')
    binding = invariant.bind(invariant_task); terms = invariant.polynomial(invariant_certificate['polynomial'], binding)
    names = binding['names']; level = 'level'
    while level in names: level += '_'

    def text(substitute):
        parts = []
        for exponents, q in terms:
            factors = ['(' + str(q.numerator) + ('/' + str(q.denominator) if q.denominator != 1 else '') + ')']
            factors += ['(' + substitute[i] + ')' + ('**' + str(k) if k > 1 else '') for i, k in enumerate(exponents) if k]
            parts.append('*'.join(factors))
        return '+'.join(parts) + '-' + level

    lemma = dict(query='polynomial_consequence', domain='QQ', variables=list(names) + [level],
                 assumptions=[text(names)], nonzero=[], goal=text(invariant_task['transition']), multiplier_degree=0)
    certificate = dict(kind='polynomial_combination', task_id=checker.bind(lemma)['identity'],
                       multipliers=[[[[0] * (len(names) + 1), [1, 1]]]])
    checker.check(lemma, certificate, budget)
    return lemma, certificate


def remember_level_set(state, invariant_task, invariant_certificate, host):
    """Store the level-set lemma of an admitted law for polynomial transfer; oversized laws are skipped."""
    algebra_check = host.local_module('algebra_check'); invariant = host.local_module('invariant_check')
    try: lemma, certificate = level_set_lemma(invariant_task, invariant_certificate, host, host.Budget(200_000))
    except (algebra_check.Invalid, algebra_check.Limit, invariant.Invalid, invariant.Limit, host.Exhausted): return None
    host.remember_lemma(state, lemma, dict(status='CHECKED_IMPLICATION', certificate=certificate))
    return lemma


def run_synthesis(strategy, task, state, budget, host):
    if strategy == 'law_instance': return law_instance(task, budget, host)
    if strategy == 'orbit_prefix': return orbit_prefix(task, budget, host)
    if strategy == 'orbit_invariant': return orbit_invariant(task, budget, host)
    if strategy == 'orbit_transfer': return orbit_transfer(task, budget, host, host.invariant_candidates(state))
    if strategy == 'orbit_drift': return orbit_drift(task, budget, host)
    if strategy == 'word_count_direct': return word_count_direct(task, budget, host)
    if strategy == 'word_count_law': return word_count_law(task, budget, host)
    if strategy == 'generating_function': return generating_function(task, budget, host)
    if strategy == 'recurrence_minimality': return recurrence_minimality(task, budget, host)
    if strategy == 'recursive_lifted_counterexample': return recursive_lift(task, state, budget, host)
    raise host.Refused('unknown apex synthesis')


def attempt(strategy, task, state, limit, host):
    """One bounded synthesized attempt; refused candidates and limits stay UNKNOWN."""
    budget = host.Budget(limit)
    try: result = run_synthesis(strategy, task, state, budget, host)
    except _limits(host) as exc: result = dict(status='UNKNOWN', reason=str(exc))
    except _invalid(host) as exc: result = dict(status='UNKNOWN', reason='candidate refused: ' + str(exc))
    result['work'] = budget.work
    return result


# ------------------------------------------ apex-only questions in one call

def single_binding(task, host):
    """Identity and scheduling shape of one apex-only original question."""
    checker = host.local_module('apex_check'); query = task.get('query') if type(task) is dict else None
    if query == 'prove_orbit_exclusion':
        b = checker.bind_orbit(task)
        return b['identity'], dict(query=query, variables=len(b['names']), degree=b['degree'], steps=b['max_steps'])
    if query == 'count_word_avoiders':
        counted = checker.bind_word_count(task)
        return counted['identity'], dict(query=query, lengths=[len(w) for w in counted['binding']['words']],
                                         length_bits=counted['length'].bit_length())
    if query in ('discover_generating_function', 'certify_minimal_recurrence'):
        carried = checker.carrier(task, query)
        return carried['identity'], dict(query=query, words='words' in carried['binding'],
                                         dimension=carried['binding']['n'])
    raise host.Refused('no apex route for this original query')


def single_status(task, result, budget, host):
    """Replay a certificate result on the original; return the status it supports."""
    checker = host.local_module('apex_check'); query = task['query']
    if query == 'prove_orbit_exclusion':
        return checker.orbit_status(checker.check_orbit(task, result.get('certificate'), budget))
    if query == 'count_word_avoiders':
        if result['status'] == 'EXACT_DIRECT':
            if type(result.get('answer')) is not int or checker.count_words(task, budget) != result['answer']:
                raise host.Refused('direct word count differs from the original automaton')
            return 'EXACT_DIRECT'
        if checker.check_word_count(task, result.get('certificate'), budget)['answer'] != result.get('answer'):
            raise host.Refused('word count answer differs from the checked law')
        return 'CHECKED_EXACT'
    if query == 'discover_generating_function':
        checker.check_generating_function(task, result.get('certificate'), budget)
        return 'CHECKED_GENERATING_FUNCTION'
    checker.check_minimal_recurrence(task, result.get('certificate'), budget)
    return 'CHECKED_MINIMAL_RECURRENCE'


def single_routes(task, host):
    """Word counts beyond the automaton's squared size try the law first; a chosen cost policy."""
    routes = SINGLE_ROUTES[task['query']]
    if task['query'] == 'count_word_avoiders':
        counted = host.local_module('apex_check').bind_word_count(task)
        if counted['length'] <= 4 * counted['binding']['n'] ** 2: routes = routes[::-1]
    return routes


def solve_single(task, state_path, limit, host):
    """Ask the faces of one apex-only question in order until one is checked on the original."""
    started = time.perf_counter_ns(); budget = host.Budget(limit)
    checker = host.local_module('apex_check'); faces = []
    try:
        identity, _ = single_binding(task, host); state = host.read_state(state_path)
        previous = next((o for o in state['observations'] if o['task_id'] == identity), None)
        result = None
        if previous and type(previous.get('certificate')) is dict and type(previous.get('status')) is str:
            try:
                saved = dict(status=previous['status'], certificate=previous['certificate'], answer=previous.get('answer'))
                result = dict(saved, status=single_status(task, saved, budget, host), reused_after_fresh_check=True)
                if result.get('answer') is None: result.pop('answer')
            except (checker.Invalid, host.Refused): result = None
        if result is None:
            for strategy in single_routes(task, host):
                try: found = run_synthesis(strategy, task, state, budget, host)
                except (checker.Limit, host.local_module('invariant_check').Limit,
                        host.local_module('recurrence_check').Limit) as exc:
                    found = dict(status='UNKNOWN', reason=str(exc))
                except _invalid(host) as exc:
                    found = dict(status='UNKNOWN', reason='candidate refused: ' + str(exc))
                faces.append(dict(face=STRATEGY_FACES.get(strategy, 'S'), route=strategy, status=found['status'],
                                  reason=found.get('reason'),
                                  directions=[step['direction'] for step in found.get('trace', []) if 'direction' in step]))
                if found['status'] != 'UNKNOWN':
                    result = dict(found, face=faces[-1]['face'], route=strategy); break
        if result is None:
            result = dict(status='UNKNOWN', reason='no face settled the original question within its bounds')
        else:
            if task['query'] == 'prove_orbit_exclusion' and result['certificate']['kind'] == 'invariant_separation':
                derived = checker.bind_orbit(task)['derived']
                host.remember_invariant(state, derived, dict(status='CHECKED_INVARIANT',
                                                             certificate=result['certificate']['invariant']))
            row = dict(task_id=identity, kind=task['query'], status=result['status'], task=task)
            if 'certificate' in result: row['certificate'] = result['certificate']
            if 'answer' in result: row['answer'] = result['answer']
            if 'certificate' in row: host.retain(state, state_path, row)
        result.update(task_id=identity, faces_tried=faces, work=budget.work, elapsed_ns=time.perf_counter_ns() - started,
                      limits='Only certificates replayed on the original question are reported; UNKNOWN is no '
                             'claim either way.')
        return result
    except _limits(host) as exc:
        return dict(status='UNKNOWN', reason=str(exc), faces_tried=faces, work=budget.work,
                    elapsed_ns=time.perf_counter_ns() - started)


# ------------------------------------------- the layer over campaign routes

class Layer:
    """Hooks that let the durable campaign executor run the apex plan and schedule."""
    kind = 'apex_research'
    QUERIES = frozenset(('transition_count', 'test_overlap_shortcut', 'polynomial_consequence', 'discover_guards',
                         'word_avoidance_identity', 'discover_recurrence', 'discover_word_recurrence',
                         'discover_invariant', 'prove_recursive_identity') + tuple(SINGLE_ROUTES))

    def __init__(self, host):
        self.host = host
        self.errors = _invalid(host)
        self.limits = _limits(host)[1:]
        self.traced = []

    def generation(self):
        return generation()

    def binding(self, task, host, budget):
        allowed = {'query', 'problems', 'attempt_work', 'max_attempts', 'name'}
        if type(task) is not dict or set(task) - allowed or task.get('query') != 'apex_research':
            raise host.Refused('apex task fields')
        problems = task.get('problems'); per = task.get('attempt_work', 1_000_000); steps = task.get('max_attempts', 64)
        if type(problems) is not list or not 1 <= len(problems) <= 16: raise host.Refused('apex problem count 1..16')
        if type(per) is not int or not 1 <= per <= 10_000_000: raise host.Refused('apex attempt work bound')
        if type(steps) is not int or not 1 <= steps <= 64: raise host.Refused('apex per-call attempts 1..64')
        for problem in problems:
            if type(problem) is not dict or problem.get('query') not in self.QUERIES:
                raise host.Refused('supported original apex task required')
            if problem['query'] in SINGLE_ROUTES: single_binding(problem, host)
            else: host.local_module('campaign').validate(problem, host, budget)
        return problems, per, steps, 'apex', host.digest({'query': 'apex_research', 'problems': problems, 'attempt_work': per})

    def plan(self, problems, host):
        campaign = host.local_module('campaign'); pyramid = host.local_module('pyramid'); result = []
        for index, problem in enumerate(problems):
            if problem['query'] in SINGLE_ROUTES:
                shape = host.digest(single_binding(problem, host)[1])
                routes = [dict(id=host.digest({'original': problem, 'strategy': s, 'receiving': problem}),
                               problem=index, strategy=s, task=problem, role='original', options={}, context=shape)
                          for s in single_routes(problem, host)]
            else:
                routes = campaign.routes(problem, index, host, True, True, True, True)
                extra = {'transition_count': ('law_instance',),
                         'prove_recursive_identity': ('recursive_seeded', 'recursive_lifted_counterexample')}
                for strategy in extra.get(problem['query'], ()):
                    routes.append(dict(id=host.digest({'original': problem, 'strategy': strategy, 'receiving': problem}),
                                       problem=index, strategy=strategy, task=problem, role='original',
                                       options={}, context=campaign.context(problem, host)))
            for route in routes:
                route['face'] = face(route)
                route['node'] = pyramid.route_node(route['strategy'], route['role'], route['task']['query'])
                if route['strategy'] in SYNTHESES: route['synthesis'] = route['strategy']
            result.extend(routes)
        return result

    def admit(self, route, result, budget, host):
        if route.get('synthesis') not in CHECKED_BY_APEX:
            return host.local_module('campaign').admit(route['task'], result, budget, host)
        if type(result) is not dict or type(result.get('status')) is not str: raise host.Refused('apex result shape')
        if result['status'] == 'UNKNOWN': return False
        checker = host.local_module('apex_check')
        if route['synthesis'] == 'law_instance':
            if result['status'] != 'CHECKED_EXACT' or type(result.get('answer')) is not int:
                raise host.Refused('law instance evidence')
            if checker.check_law_instance(route['task'], result.get('certificate'), budget)['answer'] != result['answer']:
                raise host.Refused('law instance answer differs from the checked law')
            return True
        expected = 'EXACT_DIRECT' if route['synthesis'] == 'word_count_direct' else None
        if expected is not None and result['status'] != expected: raise host.Refused('direct word count evidence')
        if result['status'] != single_status(route['task'], result, budget, host):
            raise host.Refused('apex evidence/status mismatch')
        return True

    def proposal_context(self, route, state, host):
        if route.get('synthesis') == 'recursive_seeded':
            seeds = recursive_seeds(route['task'], state, host, _Uncharged())
            if not seeds: return host.digest(dict(kind='recursive_seeds', seeds=[]))
            return host.digest(dict(kind='recursive_seeds', seeds=[s['source_commit_id'] for s in seeds],
                progress=host.local_module('recursive').progress_context(route['task'], state, host, policy='residual',
                                                                         seed_records=seeds)))
        if route.get('synthesis') == 'orbit_transfer':
            return host.digest([dict(task=o['task'], certificate=o['certificate']) for o in host.invariant_candidates(state)])
        if route.get('synthesis') == 'recursive_lifted_counterexample':
            return host.digest([dict(task=o['task'], certificate=o['certificate'])
                                for o in recursive_refutations(route['task'], state)])
        if 'synthesis' in route: return None
        return host.local_module('campaign').proposal_context(route, state, host)

    def deferred(self, route):
        """Explicit cost policy: exact iteration beyond the allocation waits behind other faces.

        auto iterates exactly when every terminal class is a singleton; quotient
        refinement starts from terminal classes and only splits them, so it then
        keeps every state. The bound counts every edge at every step. A direct
        word count is bounded the same way over its prefix automaton."""
        if route['strategy'] == 'word_count_direct':
            # Each step multiplies a row by the automaton; at most two edges leave a state.
            n = len({w[:k] for w in route['task']['patterns'] for k in range(len(w))})
            return (route['task']['length'] + 1) * 6 * n > self.allocation
        if route['task']['query'] != 'transition_count' or route['strategy'] not in ('auto', 'direct', 'quotient'):
            return False
        M, h = route['task']['matrix'], route['task']['horizon']
        edges = sum(c != 0 for row in M for c in row)
        exact = route['strategy'] == 'direct' or len(set(route['task']['terminal'])) == len(M)
        return exact and len(M) * len(M) + 2 * h * edges + 2 * len(M) > self.allocation

    def order(self, available, record, byid, samples, gen, allocation, host):
        """Choose the face with fewest executed attempts on this obligation, then rank inside it.

        Superseded attempts count: a resumed episode reopens its route after each
        stage, and uncounted stages would starve the other faces. Ties go to the
        face holding the best measured route score, then to FACE_ORDER.
        """
        campaign = host.local_module('campaign'); self.allocation = allocation
        problem = available[0]['problem']; counts = face_counts(record, byid, problem)
        ready = [r for r in available if not self.deferred(r)] or available
        scores = {r['id']: campaign.score(samples, r, gen) for r in ready}
        faces = [f for f in FACE_ORDER if any(r['face'] == f for r in ready)]
        best = {f: max(scores[r['id']] for r in ready if r['face'] == f) for f in faces}
        chosen = min(faces, key=lambda f: (counts[f], -best[f], FACE_ORDER.index(f)))
        front = sorted((r for r in ready if r['face'] == chosen), key=lambda r: scores[r['id']], reverse=True)
        return front + [r for r in available if r not in front], dict(face=chosen, face_attempts=counts,
            deferred=[r['strategy'] for r in available if r not in ready])

    def execute(self, route, state, allocation, host):
        """Run one synthesized route; a seeded episode returns its provisional instance state."""
        if route['synthesis'] == 'recursive_seeded':
            result, candidate = recursive_seeded(route['task'], state, allocation, host)
        else:
            result, candidate = attempt(route['synthesis'], route['task'], state, allocation, host), None
        self.traced.append(dict(problem=route['problem'], face=route['face'], node=route['node'],
                                strategy=route['strategy'], status=result['status'],
                                directions=[step['direction'] for step in result.get('trace', []) if 'direction' in step]))
        return result, candidate

    def remember(self, state, route, kept, host):
        certificate = kept.get('certificate')
        if route['task']['query'] == 'prove_recursive_identity' and kept['status'] in (
                'CHECKED_RECURSIVE_IDENTITY', 'CHECKED_RECURSIVE_COUNTEREXAMPLE'):
            # Admitted proofs seed same-definition questions; admitted refutations lift to their generalizations.
            identity = host.local_module('recursive_check').bind(route['task'])['identity']
            row = dict(task_id=identity, kind='prove_recursive_identity', status=kept['status'],
                       task=json.loads(host.canonical(route['task'])), certificate=json.loads(host.canonical(certificate)))
            state['observations'] = ([o for o in state['observations'] if o['task_id'] != identity] + [row])[-128:]
        if route['task']['query'] == 'discover_invariant' and kept['status'] == 'CHECKED_INVARIANT':
            # A conserved law also enters the polynomial library as its checked level-set lemma.
            remember_level_set(state, route['task'], certificate, host)
        if route.get('synthesis') in ORBIT_ROUTES and certificate.get('kind') == 'invariant_separation':
            derived = host.local_module('apex_check').bind_orbit(route['task'])['derived']
            host.remember_invariant(state, derived, dict(status='CHECKED_INVARIANT', certificate=certificate['invariant']))
            remember_level_set(state, derived, certificate['invariant'], host)

    def report(self, plan, outcomes, record, byid, executed):
        pyramid = self.host.local_module('pyramid')
        coverage = {}
        for attempt in record['attempts'] + record['superseded_attempts']:
            route = byid.get(attempt['route_id'])
            if route is None: continue
            row = coverage.setdefault(route['node'], dict(attempts=0, settled=0))
            row['attempts'] += 1; row['settled'] += attempt['result'].get('status') != 'UNKNOWN'
        faces = [face_counts(record, byid, index) for index in sorted({r['problem'] for r in plan})]
        return dict(layer='apex', pyramid_nodes=list(pyramid.NODE_ORDER), pyramid_coverage=coverage,
                    face_attempts=faces, synthesis_trace=self.traced,
                    route_faces={r['strategy']: r['face'] for r in plan})


def run(task, state_path, limit, host):
    return host.local_module('campaign').run(task, state_path, limit, host, layer=Layer(host))
