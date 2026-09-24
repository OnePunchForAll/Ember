"""Exact bounded invariant proposals; only the original-transition checker admits.

For each nonconstant basis monomial m, form m(F(x))-m(x). A rational nullspace
vector proposes P. Optional coefficient-incidence components only split this
same operator; they never replace the original transition or the final check.
"""
from fractions import Fraction as Q

MAX_COLUMNS = 128
MAX_ROWS = 4096


def validate_basis(binding, basis, budget, checker):
    n = len(binding['names']); d = binding['degree']
    checker.need(type(basis) in (list, tuple) and 0 < len(basis) <= MAX_COLUMNS,
                 'invariant proposal column bound')
    seen = set(); result = []
    for powers in basis:
        budget.use(n + 1)
        checker.need(type(powers) in (list, tuple) and len(powers) == n and
                     all(type(k) is int and 0 <= k <= d for k in powers) and
                     1 <= sum(powers) <= d, 'invariant proposal monomial bound')
        powers = tuple(powers)
        checker.need(powers not in seen, 'duplicate invariant proposal monomial')
        seen.add(powers); result.append(powers)
    return result


def build_operator(binding, basis, budget, checker, algebra):
    """Return exact residual columns once, shared by full and mapped policies."""
    basis = validate_basis(binding, basis, budget, checker)
    names = binding['names']; zero = (0,) * len(names)
    transitions = [algebra.expand(node, names, budget, checker) for node in binding['transitions']]
    powers = {(i, 0): {zero: Q(1)} for i in range(len(names))}

    def power(i, exponent):
        for k in range(1, exponent + 1):
            if (i, k) not in powers:
                powers[i, k] = algebra.multiply(powers[i, k - 1], transitions[i], budget, checker)
        return powers[i, exponent]

    columns = []; rows = set()
    for exponents in basis:
        composed = {zero: Q(1)}
        for i, k in enumerate(exponents):
            budget.use()
            if k:
                composed = algebra.multiply(composed, power(i, k), budget, checker)
        residual = algebra.add(composed, {exponents: Q(-1)}, budget, checker)
        budget.use(len(residual)); rows.update(residual)
        if len(rows) > MAX_ROWS:
            raise checker.Limit('invariant operator row limit')
        columns.append(residual)
    return columns


def search_operator(binding, basis, columns, budget, checker, diagnostics=None, select=None):
    """Propose the first focus-relevant nullspace basis vector by exact elimination.

    If any vector in this kernel involves focus, at least one vector of a full
    nullspace basis does. Failure here remains an unadmitted search result.
    An explicit linear selector replaces the focus test; a linear functional
    that vanishes on every basis vector vanishes on the whole kernel.
    """
    basis = validate_basis(binding, basis, budget, checker)
    width = len(basis)
    checker.need(type(columns) in (list, tuple) and len(columns) == width,
                 'invariant operator column correspondence')
    rows = set()
    for column in columns:
        budget.use(len(column)); rows.update(column)
        if len(rows) > MAX_ROWS:
            raise checker.Limit('invariant operator row limit')
    pivots = {}
    for monomial in sorted(rows):
        budget.use(width)
        row = [column.get(monomial, Q(0)) for column in columns]
        for lead, prior in sorted(pivots.items()):
            budget.use(); scale = row[lead]
            if scale:
                for j in range(lead, width):
                    budget.use(2); row[j] = checker.bounded(row[j] - scale * prior[j])
        budget.use(width)
        lead = next((j for j, coefficient in enumerate(row) if coefficient), None)
        if lead is None:
            continue
        scale = row[lead]
        for j in range(lead, width):
            budget.use(); row[j] = checker.bounded(row[j] / scale)
        pivots[lead] = row
    free = [j for j in range(width) if j not in pivots]
    if diagnostics is not None:
        diagnostics.update(columns=width, rows=len(rows), rank=len(pivots),
                           nullity=len(free), candidate_vectors=0)
    for free_column in free:
        vector = [Q(0)] * width; vector[free_column] = Q(1)
        for lead, row in sorted(pivots.items(), reverse=True):
            total = Q(0)
            for j in range(lead + 1, width):
                budget.use(2); total = checker.bounded(total + row[j] * vector[j])
            vector[lead] = -total
        if diagnostics is not None:
            diagnostics['candidate_vectors'] += 1
        if select is not None:
            if not select(vector):
                continue
        else:
            budget.use(width * len(binding['focus']))
            if not any(q and any(basis[j][i] for i in binding['focus']) for j, q in enumerate(vector)):
                continue
        poly = {powers: q for powers, q in zip(basis, vector) if q}
        scale = poly[min(poly)]
        for powers in poly:
            budget.use(); poly[powers] = checker.bounded(poly[powers] / scale)
        return poly
    return None


def search_basis(binding, basis, budget, checker, algebra, diagnostics=None):
    """Explicit restricted-basis proposal helper; caller owns its shared budget."""
    columns = build_operator(binding, basis, budget, checker, algebra)
    return search_operator(binding, basis, columns, budget, checker, diagnostics)


def validated_components(groups, columns, budget, checker):
    """Check partition and actual row separation, not just graph metadata."""
    checker.need(type(groups) is list and 0 < len(groups) <= len(columns),
                 'invariant map component bound')
    seen = set(); row_owner = {}; normalized = []
    for group_index, group in enumerate(groups):
        checker.need(type(group) is list and group, 'nonempty invariant map component')
        current = []
        for index in group:
            budget.use()
            checker.need(type(index) is int and 0 <= index < len(columns) and index not in seen,
                         'invariant map must partition columns exactly once')
            seen.add(index); current.append(index)
            for powers, coefficient in columns[index].items():
                budget.use()
                if not coefficient:
                    continue
                checker.need(powers not in row_owner or row_owner[powers] == group_index,
                             'invariant map split a shared nonzero residual row')
                row_owner[powers] = group_index
        normalized.append(sorted(current))
    checker.need(len(seen) == len(columns), 'invariant map omitted columns')
    return sorted(normalized, key=lambda group: group[0])


def run(task, budget, checker, algebra, policy='full', supports=None, mapper=None):
    """Generate one invariant or UNKNOWN; host handles total work exhaustion.

    Full is the unchanged strong baseline. Mapped builds the same full operator
    once and solves validated independent components using the same elimination.
    A map bound or malformed partition falls back to the already-built operator.
    Explicit supports belong to search_basis rather than an unmeasured schedule.
    """
    binding = checker.bind(task)
    checker.need(policy in ('full', 'mapped'), 'invariant producer policy')
    checker.need(supports is None, 'use search_basis for explicit invariant supports')
    checker.need(policy != 'mapped' or mapper is not None, 'mapped invariant policy requires mapper')
    basis = algebra.monomials(len(binding['names']), binding['degree'])[1:]
    started = budget.work
    trace = []; diagnostics = dict(policy=policy, full_columns=len(basis),
        operator_work=0, mapping_work=0, search_work=0, checking_work=0,
        initial_value_work=0, rejected_maps=0, skipped_components=0,
        fallback=False, searches=[])
    result = dict(status='UNKNOWN', trace=trace, invariant_search=diagnostics,
        limits='Bounded polynomial grammar and arithmetic; UNKNOWN does not certify absence of an invariant.')
    try:
        before = budget.work
        try:
            columns = build_operator(binding, basis, budget, checker, algebra)
        finally:
            diagnostics['operator_work'] = budget.work - before
        trace.append(dict(direction='S', operation='form_original_transition_residual_operator', columns=len(columns)))
        groups = None
        if policy == 'mapped':
            before = budget.work
            try:
                graph = mapper.build(binding, basis, columns, budget)
                checker.need(type(graph) is dict, 'invariant map object')
                groups = validated_components(graph.get('components'), columns, budget, checker)
                result['dependency_map'] = graph
                trace.append(dict(direction='N', operation='partition_exact_residual_incidence', components=len(groups)))
            except (checker.Invalid, checker.Limit, mapper.MapLimit, TypeError, KeyError, ValueError) as exc:
                diagnostics.update(fallback=True, rejected_maps=1, map_failure=str(exc))
                trace.append(dict(direction='W', operation='reject_map_and_use_full_operator', reason=str(exc)))
            finally:
                diagnostics['mapping_work'] = budget.work - before
        if groups is None:
            groups = [list(range(len(basis)))]
        candidate = None
        before = budget.work
        try:
            for group in groups:
                budget.use(len(group) * len(binding['focus']))
                if not any(any(basis[j][i] for i in binding['focus']) for j in group):
                    diagnostics['skipped_components'] += 1
                    diagnostics['searches'].append(dict(columns=len(group), skipped='no focus monomial'))
                    continue
                search = dict(original_column_indices=group)
                diagnostics['searches'].append(search)
                candidate = search_operator(binding, [basis[j] for j in group], [columns[j] for j in group],
                                            budget, checker, search)
                if candidate is not None:
                    break
        finally:
            diagnostics['search_work'] = budget.work - before
        if candidate is None:
            result['reason'] = 'no focus-relevant candidate in the bounded polynomial kernel search'
            return result
        certificate = dict(kind='polynomial_invariant', task_id=binding['identity'], polynomial=algebra.encoded(candidate))
        if binding['initial'] is not None:
            before = budget.work
            try:
                initial = algebra.evaluate(candidate, binding['initial'], budget, checker)
            finally:
                diagnostics['initial_value_work'] = budget.work - before
            certificate['initial_value'] = [initial.numerator, initial.denominator]
        trace.append(dict(direction='N', operation='propose_nullspace_polynomial', terms=len(candidate)))
        before = budget.work
        try:
            checked = checker.check(task, certificate, budget)
        except checker.Invalid as exc:
            result['reason'] = 'candidate rejected on original transition: ' + str(exc)
            trace.append(dict(direction='W', operation='reject_invariant_candidate', reason=str(exc)))
            return result
        finally:
            diagnostics['checking_work'] = budget.work - before
        checker.need(checked.get('ok') is True, 'invariant checker did not admit candidate')
        trace.append(dict(direction='S', operation='check_original_transition_identity', accepted=True))
        result.update(status='CHECKED_INVARIANT', certificate=certificate, check=checked, scope=checked['scope'])
        return result
    except checker.Limit as exc:
        result['reason'] = str(exc)
        return result
    finally:
        diagnostics['total_work'] = budget.work - started


# Checked cross-system invariant candidate reuse; full and mapped code above is unchanged.
import itertools

REUSE_RECORD_CAP = 8
REUSE_BINDING_CAP = 16
REUSE_WORK_CAP = 100_000


class ReuseBudgetEnded(RuntimeError):
    pass


class ReuseBudget:
    """Charge a bounded prepass to its parent without consuming reserved fallback."""
    def __init__(self, parent, limit):
        self.parent = parent; self.limit = limit; self.work = 0

    def use(self, amount=1):
        if self.work + amount > self.limit:
            raise ReuseBudgetEnded('reserved invariant reuse budget exhausted')
        self.parent.use(amount); self.work += amount


def reuse_bindings(active, source_names, receiving_names, budget):
    """At most sixteen injective maps; preserve every matching active name first."""
    if len(active) > len(receiving_names):
        return []
    budget.use(len(active) * len(receiving_names) + 1)
    preferred = [receiving_names.index(source_names[i]) if source_names[i] in receiving_names else None
                 for i in active]
    used = {i for i in preferred if i is not None}
    unused = iter(i for i in range(len(receiving_names)) if i not in used)
    preferred = tuple(next(unused) if i is None else i for i in preferred)
    output = [preferred]; seen = {preferred}
    for proposal in itertools.permutations(range(len(receiving_names)), len(active)):
        budget.use(len(active) + 1)
        if proposal in seen:
            continue
        seen.add(proposal); output.append(proposal)
        if len(output) >= REUSE_BINDING_CAP:
            break
    return output


def renamed_invariant(terms, active, mapping, width, budget, checker):
    """Injective transport changes coordinates, never the receiving equations."""
    poly = {}
    for source_exponents, coefficient in terms:
        budget.use(width + len(active) + 1)
        exponents = [0] * width
        for source_index, receiving_index in zip(active, mapping):
            exponents[receiving_index] = source_exponents[source_index]
        poly[tuple(exponents)] = coefficient
    scale = poly[min(poly)]
    for exponents in poly:
        budget.use(); poly[exponents] = checker.bounded(poly[exponents] / scale)
    return poly


def run_reuse(task, budget, checker, algebra, records):
    """Recheck stored laws only as candidates; reserve full original search fallback."""
    receiving = checker.bind(task)
    allowance = min(REUSE_WORK_CAP, max(0, (budget.limit - budget.work) // 4))
    portion = ReuseBudget(budget, allowance)
    diagnostics = dict(used=False, record_cap=REUSE_RECORD_CAP, binding_cap=REUSE_BINDING_CAP,
        slice_limit=allowance, work=0, source_check_work=0, binding_work=0,
        target_check_work=0, fallback_work=0, fallback=False, cap_exhausted=False,
        records_considered=0, sources_checked=0, source_failures=0, same_task_skipped=0,
        bindings_considered=0, candidate_duplicates=0, candidates_considered=0,
        candidates_filtered=0, target_checks=0, target_failures=0, failures=[])
    seen_polynomials = set(); answer = None

    def phase(name, operation):
        before = portion.work
        try:
            return operation()
        finally:
            diagnostics[name] += portion.work - before

    def source(record):
        portion.use()
        checker.need(type(record) is dict and type(record.get('task')) is dict,
                     'invariant source record needs its original task')
        binding = checker.bind(record['task'])
        if binding['identity'] == receiving['identity']:
            return binding, None
        certificate = record.get('certificate')
        checked = checker.check(record['task'], certificate, portion)
        checker.need(checked.get('ok') is True, 'source invariant check did not admit')
        return binding, certificate

    def prepare(source_binding, certificate):
        terms = checker.polynomial(certificate['polynomial'], source_binding)
        portion.use(len(terms) * (len(source_binding['names']) + 1))
        active = [i for i in range(len(source_binding['names'])) if any(exponents[i] for exponents, _ in terms)]
        return terms, active, reuse_bindings(active, source_binding['names'], receiving['names'], portion)

    def target_candidate(terms, active, mapping):
        poly = renamed_invariant(terms, active, mapping, len(receiving['names']), portion, checker)
        key = tuple((powers, q.numerator, q.denominator) for powers, q in sorted(poly.items()))
        portion.use(len(key))
        if key in seen_polynomials:
            diagnostics['candidate_duplicates'] += 1
            return None
        seen_polynomials.add(key); diagnostics['candidates_considered'] += 1
        if (any(sum(powers) > receiving['degree'] for powers in poly) or
                not any(powers[i] for powers in poly for i in receiving['focus'])):
            diagnostics['candidates_filtered'] += 1
            return None
        candidate = dict(kind='polynomial_invariant', task_id=receiving['identity'],
                         polynomial=algebra.encoded(poly))
        if receiving['initial'] is not None:
            value = algebra.evaluate(poly, receiving['initial'], portion, checker)
            candidate['initial_value'] = [value.numerator, value.denominator]
        return candidate

    try:
        try:
            if type(records) not in (list, tuple):
                diagnostics['failures'].append(dict(stage='records', reason='source records must be a list or tuple'))
                candidates = ()
            else:
                candidates = records[:REUSE_RECORD_CAP]
            for index, record in enumerate(candidates):
                diagnostics['records_considered'] += 1
                try:
                    source_binding, source_certificate = phase('source_check_work', lambda: source(record))
                    if source_certificate is None:
                        diagnostics['same_task_skipped'] += 1
                        continue
                    diagnostics['sources_checked'] += 1
                    terms, active, mappings = phase('binding_work', lambda: prepare(source_binding, source_certificate))
                except (checker.Invalid, checker.Limit, TypeError, KeyError, ValueError) as exc:
                    diagnostics['source_failures'] += 1
                    diagnostics['failures'].append(dict(stage='source', record_index=index, reason=str(exc)))
                    continue
                for mapping in mappings:
                    diagnostics['bindings_considered'] += 1
                    try:
                        candidate = phase('binding_work', lambda: target_candidate(terms, active, mapping))
                        if candidate is None:
                            continue
                        diagnostics['target_checks'] += 1
                        checked = phase('target_check_work', lambda: checker.check(task, candidate, portion))
                        checker.need(checked.get('ok') is True, 'receiving invariant check did not admit')
                    except (checker.Invalid, checker.Limit, TypeError, KeyError, ValueError) as exc:
                        diagnostics['target_failures'] += 1
                        diagnostics['failures'].append(dict(stage='candidate', record_index=index,
                            binding=list(mapping), reason=str(exc)))
                        continue
                    names = {source_binding['names'][i]: receiving['names'][j] for i, j in zip(active, mapping)}
                    diagnostics.update(used=True, accepted_source_task_id=source_binding['identity'], accepted_binding=names)
                    answer = dict(status='CHECKED_INVARIANT', certificate=candidate, check=checked,
                        proof_method='rechecked_invariant_candidate', scope=checked['scope'], trace=[
                            dict(direction='S', operation='freshly_check_source_invariant', source_task_id=source_binding['identity']),
                            dict(direction='N', operation='rename_active_polynomial_candidate', binding=names,
                                 standing='CANDIDATE_FOR_DIFFERENT_ORIGINAL_SYSTEM'),
                            dict(direction='S', operation='check_original_receiving_transition', task_id=receiving['identity'], accepted=True)])
                    break
                if answer is not None:
                    break
        except ReuseBudgetEnded as exc:
            diagnostics.update(cap_exhausted=True, reason=str(exc))
        finally:
            diagnostics['work'] = portion.work
        if answer is None:
            diagnostics['fallback'] = True
            before = budget.work
            try:
                answer = run(task, budget, checker, algebra)
            finally:
                diagnostics['fallback_work'] = budget.work - before
            answer['trace'] = [dict(direction='W', operation='reuse_unresolved_try_original_full_search',
                                    reuse_work=portion.work, cap_exhausted=diagnostics['cap_exhausted'])] + answer.get('trace', [])
        answer['law_reuse'] = diagnostics
        return answer
    except Exception as exc:
        # The host owns its Exhausted type. Preserve diagnostics without treating
        # that exception (or a programming error) as a successful local fallback.
        exc.law_reuse = diagnostics
        raise
