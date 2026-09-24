"""Separate checker for apex syntheses; composes original checkers, imports no producer.

A law instance evaluates an all-index recurrence that the recurrence checker
admits on the original transition system, or on a quotient whose equations are
checked here against that original. Orbit certificates are a finite witness, a
repeated state, or a checked polynomial invariant separating the initial point
from the target. Every certificate is bound to the exact original task.
"""
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path


class Invalid(ValueError): pass
class Limit(RuntimeError): pass


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_apex_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


_recurrence = _load('recurrence_check')
_invariant = _load('invariant_check')
_algebra = _invariant._algebra
_INVALID = (_recurrence.Invalid, _invariant.Invalid)
_LIMIT = (_recurrence.Limit, _invariant.Limit)
MAX_ORBIT_STEPS = 1024
WORD_LENGTH_LIMIT = 20000


def need(condition, reason):
    if not condition: raise Invalid(reason)


def _guard(call):
    """Translate component checker failures into this checker's own classes."""
    try: return call()
    except _INVALID as exc: raise Invalid(str(exc)) from exc
    except _LIMIT as exc: raise Limit(str(exc)) from exc


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def bind_transition(task):
    """The transition_count binding and identity used by ember.bind, rebuilt here."""
    need(type(task) is dict and task.get('query') == 'transition_count', 'original transition-count query')
    need(not set(task) - {'query', 'matrix', 'initial', 'terminal', 'horizon', 'name', 'family'}, 'unsupported matrix fields')
    M, u, v, h = task.get('matrix'), task.get('initial'), task.get('terminal'), task.get('horizon')
    need(type(M) is list and 1 <= len(M) <= 256, 'matrix dimension')
    n = len(M)
    need(all(type(r) is list and len(r) == n for r in M), 'matrix shape')
    need(type(u) is list and type(v) is list and len(u) == n and len(v) == n, 'vector shape')
    need(type(h) is int and 0 <= h <= 4096, 'horizon')
    need(all(type(x) is int and abs(x) <= 1_000_000 for r in M for x in r), 'matrix entry')
    need(all(type(x) is int and abs(x) <= 1_000_000 for x in u + v), 'vector entry')
    return M, u, v, h, digest({'matrix': M, 'initial': u, 'terminal': v, 'horizon': h, 'query': 'transition_count'})


def check_quotient(M, u, v, identity, certificate, budget):
    """Check MP=PQ and v=Pw on the original; return the quotient system (Q, uP, w)."""
    need(type(certificate) is dict and set(certificate) == {'task_id', 'blocks', 'quotient', 'terminal', 'rule'},
         'quotient certificate fields')
    need(certificate['task_id'] == identity and certificate['rule'] == 'MP=PQ;v=Pw', 'quotient task binding')
    blocks, Q, w = certificate['blocks'], certificate['quotient'], certificate['terminal']
    need(type(blocks) is list and blocks and all(type(b) is list and b for b in blocks), 'partition shape')
    flat = [i for b in blocks for i in b]
    need(all(type(i) is int for i in flat) and sorted(flat) == list(range(len(M))), 'partition coverage')
    k = len(blocks)
    need(type(Q) is list and len(Q) == k and all(type(r) is list and len(r) == k for r in Q), 'quotient shape')
    need(type(w) is list and len(w) == k, 'quotient terminal shape')
    need(all(type(x) is int for r in Q for x in r) and all(type(x) is int for x in w), 'inexact quotient')
    for a, block in enumerate(blocks):
        for i in block:
            budget.use()
            need(v[i] == w[a], 'v != P w')
            for b, target in enumerate(blocks):
                total = 0
                for j in target: budget.use(); total += M[i][j]
                need(total == Q[a][b], 'M P != P Q')
    projected = []
    for block in blocks:
        budget.use(len(block)); projected.append(sum(u[i] for i in block))
    return Q, projected, w


def recurrence_task(M, u, v):
    """The derived all-index question; its order bound is the carrier dimension."""
    return dict(query='discover_recurrence', domain='QQ', matrix=M, initial=u, terminal=v, max_order=len(M))


def evaluate(certificate, index, budget):
    """a(index) from checked initial terms by exact integer stepping."""
    c = [_guard(lambda x=x: _recurrence.rational(x)) for x in certificate['coefficients']]
    a = [_guard(lambda x=x: _recurrence.rational(x)) for x in certificate['initial_terms']]
    need(all(x.denominator == 1 for x in a), 'integer sequence initial terms')
    r = len(c)
    if r == 0: return 0
    if index < r: return int(a[index])
    scale = 1
    for q in c: scale = scale * q.denominator // math.gcd(scale, q.denominator)
    weights = [int(q * scale) for q in c]; window = [int(x) for x in a]
    for _ in range(index - r + 1):
        budget.use(2 * r)
        total = sum(x * y for x, y in zip(weights, window))
        need(total % scale == 0, 'checked recurrence produced a nonintegral term')
        window = window[1:] + [total // scale]
    return window[-1]


def check_law_instance(task, certificate, budget):
    M, u, v, h, identity = bind_transition(task)
    need(type(certificate) is dict and certificate.get('kind') == 'law_instance', 'law instance kind')
    need(set(certificate) in ({'kind', 'task_id', 'recurrence'}, {'kind', 'task_id', 'quotient', 'recurrence'}),
         'law instance fields')
    need(certificate['task_id'] == identity, 'original transition task binding')
    compressed = 'quotient' in certificate
    carrier = check_quotient(M, u, v, identity, certificate['quotient'], budget) if compressed else (M, u, v)
    derived = recurrence_task(*carrier)
    checked = _guard(lambda: _recurrence.check(derived, certificate['recurrence'], budget))
    answer = evaluate(certificate['recurrence'], h, budget)
    scope = 'The exact original count u*M**h*v at the original horizon.'
    proof = ('A recurrence admitted for every index on the original system, evaluated from its checked initial terms.'
             if not compressed else 'Original quotient equations MP=PQ and v=Pw give u*M**h*v=(uP)*Q**h*w; '
             'a recurrence admitted for every index on that quotient is evaluated from its checked initial terms.')
    return dict(ok=True, kind='law_instance', answer=answer, order=checked['order'], carrier_states=len(carrier[0]),
                original_states=len(M), compressed=compressed, scope=scope, proof=proof,
                formal_status='NOT_FORMALLY_VERIFIED')


def bind_orbit(task):
    """An orbit question; its derived invariant task shares the original transition."""
    need(type(task) is dict, 'orbit task object')
    allowed = {'query', 'domain', 'variables', 'transition', 'initial', 'target', 'max_degree', 'max_steps', 'name', 'family'}
    need(not set(task) - allowed, 'unsupported orbit task fields')
    need(task.get('query') == 'prove_orbit_exclusion' and task.get('domain') == 'QQ', 'original rational orbit query')
    need('initial' in task and 'target' in task, 'orbit initial and target points are required')
    derived = dict(query='discover_invariant', domain='QQ', variables=task.get('variables'),
                   transition=task.get('transition'), max_degree=task.get('max_degree', 2), initial=task['initial'])
    binding = _guard(lambda: _invariant.bind(derived))
    raw = task['target']
    need(type(raw) is list and len(raw) == len(binding['names']), 'target rational point dimension')
    target = [_guard(lambda q=q: _algebra.exact(q)) for q in raw]
    steps = task.get('max_steps', 64)
    need(type(steps) is int and 0 <= steps <= MAX_ORBIT_STEPS, 'orbit step bound 0..1024')
    original = dict(query='prove_orbit_exclusion', domain='QQ', variables=binding['names'], transition=task['transition'],
                    initial=task['initial'], target=raw, max_degree=binding['degree'], max_steps=steps)
    return dict(binding, target=target, max_steps=steps, derived=derived, identity=digest(original),
                invariant_identity=binding['identity'])


def orbit_step(b, point, budget):
    return [_guard(lambda node=node: _algebra.value(node, b['names'], point, budget)) for node in b['transitions']]


def orbit_prefix(b, count, budget):
    states = [list(b['initial'])]
    for _ in range(count):
        states.append(orbit_step(b, states[-1], budget))
    return states


def check_orbit(task, certificate, budget):
    b = bind_orbit(task)
    need(type(certificate) is dict and certificate.get('task_id') == b['identity'], 'original orbit task binding')
    kind = certificate.get('kind')
    if kind == 'orbit_witness':
        need(set(certificate) == {'kind', 'task_id', 'index'}, 'orbit witness fields')
        index = certificate['index']
        need(type(index) is int and 0 <= index <= b['max_steps'], 'orbit witness index bound')
        states = orbit_prefix(b, index, budget)
        need(states[index] == b['target'], 'orbit witness does not reach the original target')
        return dict(ok=True, kind=kind, outcome='REACHES', index=index,
                    scope='The original orbit x(n+1)=F(x(n)) from the initial point equals the target at this index.',
                    proof='Exact rational iteration of the original transition expressions.',
                    formal_status='NOT_FORMALLY_VERIFIED')
    if kind == 'periodic_orbit':
        need(set(certificate) == {'kind', 'task_id', 'start', 'period'}, 'periodic orbit fields')
        start, period = certificate['start'], certificate['period']
        need(type(start) is int and type(period) is int and start >= 0 and period >= 1
             and start + period <= b['max_steps'], 'periodic orbit index bound')
        states = orbit_prefix(b, start + period, budget)
        need(states[start] == states[start + period], 'orbit does not repeat at the certified indices')
        for state in states[:start + period]:
            budget.use(len(state))
            need(state != b['target'], 'target occurs in the certified finite orbit')
        return dict(ok=True, kind=kind, outcome='EXCLUDED', states=start + period,
                    scope='No nonnegative iterate of the original orbit equals the target.',
                    proof='A deterministic orbit that repeats a state visits only its first start+period states.',
                    formal_status='NOT_FORMALLY_VERIFIED')
    if kind == 'invariant_separation':
        need(set(certificate) == {'kind', 'task_id', 'invariant', 'target_value'}, 'invariant separation fields')
        invariant = certificate['invariant']
        checked = _guard(lambda: _invariant.check(b['derived'], invariant, budget))
        terms = _guard(lambda: _invariant.polynomial(invariant['polynomial'], b))
        initial = _guard(lambda: _algebra.exact(invariant['initial_value']))
        target = _guard(lambda: _algebra.monomial_value(terms, b['target'], budget))
        need(_guard(lambda: _algebra.exact(certificate['target_value'])) == target, 'target invariant value differs')
        need(target != initial, 'invariant does not separate the target from the initial point')
        return dict(ok=True, kind=kind, outcome='EXCLUDED', grid_points=checked['grid_points'],
                    scope='No nonnegative iterate of the original orbit equals the target.',
                    proof='P(F(x))=P(x) on the complete original degree grid gives P(x(n))=P(x(0)) for every n; '
                          'P(target) differs from P(x(0)).',
                    formal_status='NOT_FORMALLY_VERIFIED')
    if kind == 'drift_separation':
        need(set(certificate) in ({'kind', 'task_id', 'clocked'}, {'kind', 'task_id', 'clocked', 'index'}),
             'drift separation fields')
        task_c = clocked_task(b)
        checked = _guard(lambda: _invariant.check(task_c, certificate['clocked'], budget))
        clocked = _guard(lambda: _invariant.bind(task_c))
        terms = _guard(lambda: _invariant.polynomial(certificate['clocked']['polynomial'], clocked))
        tick = len(b['names'])
        need(all(e[tick] == 0 or (e[tick] == 1 and sum(e) == 1) for e, _ in terms), 'clock must enter alone and linearly')
        kappa = next((q for e, q in terms if e[tick] == 1), 0)
        need(kappa != 0, 'drift certificate needs a clock term')
        drift = [(e[:tick], q) for e, q in terms if e[tick] == 0]
        start = _guard(lambda: _algebra.monomial_value(drift, b['initial'], budget))
        end = _guard(lambda: _algebra.monomial_value(drift, b['target'], budget))
        steps = (start - end) / kappa
        proof = ('K(x,clock)=R(x)+kappa*clock is conserved by the clocked transition on the complete original grid, '
                 'so R(x(n))=R(x(0))-kappa*n; only n=(R(x(0))-R(target))/kappa can meet the target.')
        if steps.denominator != 1 or steps < 0:
            need('index' not in certificate, 'no orbit index meets the target drift value')
            return dict(ok=True, kind=kind, outcome='EXCLUDED', grid_points=checked['grid_points'],
                        scope='No nonnegative iterate of the original orbit equals the target.', proof=proof,
                        formal_status='NOT_FORMALLY_VERIFIED')
        index = int(steps)
        need(certificate.get('index') == index and index <= b['max_steps'], 'drift index outside the checked prefix')
        states = orbit_prefix(b, index, budget)
        reaches = states[index] == b['target']
        return dict(ok=True, kind=kind, outcome='REACHES' if reaches else 'EXCLUDED', index=index,
                    grid_points=checked['grid_points'], proof=proof, formal_status='NOT_FORMALLY_VERIFIED',
                    scope=('The original orbit equals the target at this index.' if reaches else
                           'No nonnegative iterate of the original orbit equals the target.'))
    raise Invalid('unsupported orbit certificate kind')


def clocked_task(b):
    """The orbit with a clock variable; R(F(x))-R(x)=c becomes an invariant R(x)-c*clock."""
    clock = 'clock'
    while clock in b['names']: clock += '_'
    derived = b['derived']
    return dict(query='discover_invariant', domain='QQ', variables=list(b['names']) + [clock],
                transition=list(derived['transition']) + [clock + '+1'], max_degree=b['degree'],
                initial=list(derived['initial']) + [[0, 1]])


def orbit_status(checked):
    return 'CHECKED_ORBIT_REACHES' if checked['outcome'] == 'REACHES' else 'CHECKED_ORBIT_EXCLUSION'


def carrier(task, query):
    """A matrix or forbidden-word carrier and its derived all-index recurrence question."""
    need(type(task) is dict and task.get('query') == query, 'original ' + query + ' query')
    if 'patterns' in task:
        need(not set(task) - {'query', 'patterns', 'name', 'family'}, 'unsupported word carrier fields')
        derived = dict(query='discover_word_recurrence', patterns=task.get('patterns'))
    else:
        need(not set(task) - {'query', 'domain', 'matrix', 'initial', 'terminal', 'name', 'family'},
             'unsupported matrix carrier fields')
        derived = dict(query='discover_recurrence', domain=task.get('domain'), matrix=task.get('matrix'),
                       initial=task.get('initial'), terminal=task.get('terminal'))
    binding = _guard(lambda: _recurrence.bind(derived))
    derived['max_order'] = binding['n']
    binding = _guard(lambda: _recurrence.bind(derived))
    identity = digest(dict({k: v for k, v in derived.items() if k != 'query'}, query=query))
    return dict(derived=derived, binding=binding, identity=identity)


def carrier_system(binding, budget):
    if 'words' in binding: return _guard(lambda: _recurrence.original_word_system(binding['words'], budget))
    return binding['matrix'], binding['initial'], binding['terminal']


def carrier_terms(binding, count, budget):
    """The first terms u*M**h*v of the original carrier, computed here in exact integers."""
    M, u, v = carrier_system(binding, budget); row = list(u); out = []
    for _ in range(count):
        budget.use(2 * len(row)); out.append(sum(x * y for x, y in zip(row, v)))
        following = [0] * len(row)
        for i, x in enumerate(row):
            if x:
                for j, w in enumerate(M[i]):
                    if w: budget.use(2); following[j] += x * w
        row = following
    return out


def generating_function(recurrence_certificate):
    """Q(x)=1-sum c_j x^(r-j) and P=(Q*sum_{h<r} a_h x^h) mod x^r, both trimmed."""
    c = [_guard(lambda x=x: _recurrence.rational(x)) for x in recurrence_certificate['coefficients']]
    a = [_guard(lambda x=x: _recurrence.rational(x)) for x in recurrence_certificate['initial_terms']]
    r = len(c)
    Q = [Fraction(1)] + [-c[r - k] for k in range(1, r + 1)]
    P = [sum(Q[i] * a[k - i] for i in range(k + 1)) for k in range(r)]
    while P and P[-1] == 0: P.pop()
    while len(Q) > 1 and Q[-1] == 0: Q.pop()
    return [[q.numerator, q.denominator] for q in P], [[q.numerator, q.denominator] for q in Q]


def check_generating_function(task, certificate, budget):
    carried = carrier(task, 'discover_generating_function')
    need(type(certificate) is dict and set(certificate) == {'kind', 'task_id', 'recurrence', 'numerator', 'denominator'}
         and certificate['kind'] == 'rational_generating_function' and certificate['task_id'] == carried['identity'],
         'generating function certificate binding')
    checked = _guard(lambda: _recurrence.check(carried['derived'], certificate['recurrence'], budget))
    numerator, denominator = generating_function(certificate['recurrence'])
    need(certificate['numerator'] == numerator and certificate['denominator'] == denominator,
         'generating function differs from the checked recurrence and initial terms')
    return dict(ok=True, kind='rational_generating_function', order=checked['order'],
                scope='sum_{h>=0} a(h) x^h = P(x)/Q(x) as formal power series for the original carrier; not necessarily reduced.',
                proof='Q(x)*A(x) has zero coefficients from x^r on by the checked recurrence; the lower ones are P.',
                formal_status='NOT_FORMALLY_VERIFIED')


def hankel_determinant(terms, order, budget):
    """Exact determinant of [a(i+j)] for i,j<order by fraction-free elimination."""
    matrix = [[terms[i + j] for j in range(order)] for i in range(order)]
    previous, sign = 1, 1
    for k in range(order):
        pivot = next((i for i in range(k, order) if matrix[i][k]), None)
        if pivot is None: return 0
        if pivot != k: matrix[k], matrix[pivot] = matrix[pivot], matrix[k]; sign = -sign
        for i in range(k + 1, order):
            for j in range(k + 1, order):
                budget.use(3)
                matrix[i][j] = (matrix[i][j] * matrix[k][k] - matrix[i][k] * matrix[k][j]) // previous
        previous = matrix[k][k]
    return sign * (matrix[order - 1][order - 1] if order else 1)


def check_minimal_recurrence(task, certificate, budget):
    carried = carrier(task, 'certify_minimal_recurrence')
    need(type(certificate) is dict and set(certificate) == {'kind', 'task_id', 'recurrence'}
         and certificate['kind'] == 'minimal_recurrence' and certificate['task_id'] == carried['identity'],
         'minimal recurrence certificate binding')
    checked = _guard(lambda: _recurrence.check(carried['derived'], certificate['recurrence'], budget))
    order = checked['order']
    det = hankel_determinant(carrier_terms(carried['binding'], max(0, 2 * order - 1), budget), order, budget)
    need(det != 0, 'Hankel determinant vanishes: a lower order is not excluded')
    return dict(ok=True, kind='minimal_recurrence', order=order, hankel_determinant_bits=abs(det).bit_length(),
                scope='The checked recurrence holds for every index and no linear recurrence of lower order does.',
                proof='A recurrence of order s<r would make the columns of the r-by-r Hankel matrix dependent; '
                      'its determinant, recomputed from the original carrier, is nonzero.',
                formal_status='NOT_FORMALLY_VERIFIED')


def bind_word_count(task):
    need(type(task) is dict and task.get('query') == 'count_word_avoiders', 'original word-count query')
    need(not set(task) - {'query', 'patterns', 'length', 'name', 'family'}, 'unsupported word-count fields')
    carried = carrier(dict(query='count_word_avoiders', patterns=task.get('patterns')), 'count_word_avoiders')
    length = task.get('length')
    need(type(length) is int and 0 <= length <= WORD_LENGTH_LIMIT, 'word length bound 0..20000')
    return dict(carried, length=length,
                identity=digest(dict(query='count_word_avoiders', patterns=carried['binding']['words'], length=length)))


def count_words(task, budget):
    """Exact count by iterating the checker's own prefix automaton."""
    counted = bind_word_count(task)
    return carrier_terms(counted['binding'], counted['length'] + 1, budget)[-1]


def check_word_count(task, certificate, budget):
    counted = bind_word_count(task)
    need(type(certificate) is dict and set(certificate) == {'kind', 'task_id', 'recurrence'}
         and certificate['kind'] == 'word_count_law' and certificate['task_id'] == counted['identity'],
         'word count certificate binding')
    checked = _guard(lambda: _recurrence.check(counted['derived'], certificate['recurrence'], budget))
    return dict(ok=True, kind='word_count_law', answer=evaluate(certificate['recurrence'], counted['length'], budget),
                order=checked['order'], scope='The number of binary words of the original length avoiding both patterns.',
                proof='A recurrence admitted for every length on the original automaton, evaluated from its checked terms.',
                formal_status='NOT_FORMALLY_VERIFIED')


def check(task, certificate, budget):
    need(type(task) is dict, 'apex task object')
    if task.get('query') == 'transition_count': return check_law_instance(task, certificate, budget)
    if task.get('query') == 'prove_orbit_exclusion': return check_orbit(task, certificate, budget)
    if task.get('query') == 'count_word_avoiders': return check_word_count(task, certificate, budget)
    if task.get('query') == 'discover_generating_function': return check_generating_function(task, certificate, budget)
    if task.get('query') == 'certify_minimal_recurrence': return check_minimal_recurrence(task, certificate, budget)
    raise Invalid('no apex synthesis checker for this original query')
