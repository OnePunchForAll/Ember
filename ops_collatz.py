"""Operators on residue-class maps T(n) = (a_i*n + b_i)/d for n = i mod d, such as 3n+1.

On a class n = M*t + r with M a power of d, the first k branches are fixed, so
T^k(M t + r) = alpha*t + beta exactly. When alpha < M the class descends for all
large t: this is the classical stopping-time argument. Refining classes, lifting
descents to subclasses, assembling covers, finite descent checks and cycle
search are all admitted by lexicon_check.py; a cycle avoiding 1 refutes the
claim that every orbit reaches 1 for that map.
"""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_collatz_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


L = _load('lexicon')
OPS = []


def op(name, dirs, consumes, produces, summary):
    def wrap(fn):
        OPS.append(dict(name=name, dirs=dirs, consumes=tuple(consumes), produces=tuple(produces), summary=summary,
                        fn=fn, entry=fn.__name__))
        return fn
    return wrap


def step(cmap, n):
    i = n % cmap['d']
    return (cmap['a'][i] * n + cmap['b'][i]) // cmap['d']


def affine(cmap, M, r, budget):
    """(alpha, beta) of T^j on M t + r for j = 1.. while branches are determined."""
    d = cmap['d']; alpha, beta = Q(M), Q(r); out = []
    while alpha.denominator == 1 and int(alpha) % d == 0 and len(out) < 64:
        budget.use(); i = int(beta) % d
        alpha, beta = cmap['a'][i] * alpha / d, (cmap['a'][i] * beta + cmap['b'][i]) / d
        out.append((alpha, beta))
    return out


def descent_bound(M, r, alpha, beta):
    threshold = (beta - r) / (M - alpha)
    t0 = int(threshold) + 1 if threshold >= 0 else 0
    return max(1, M * t0 + r)


def lift_bound(bound, M, r):
    """The least member of the subclass M*t + r at or above a class bound; every such member descends."""
    return r if bound <= r else r + M * (-(-(bound - r) // M))


def descent_data(cmap, M, r, steps, bound):
    return dict(map=cmap, modulus=M, residue=r, steps=steps, bound=bound)


@op('collatz_affine_descent', 'NWS', ('cclass',), ('descent', 'residual'),
    'Iterate the class symbolically; the first contracting affine form gives a checked descent, else a residual.')
def collatz_affine_descent(rt, cls):
    d = cls['data']; cmap, M, r = d['map'], d['modulus'], d['residue']
    for j, (alpha, beta) in enumerate(affine(cmap, M, r, rt.budget), 1):
        if alpha < M:
            claim = rt.propose('descent', descent_data(cmap, M, r, j, descent_bound(M, r, alpha, beta)), (cls,))
            return [claim] if rt.check(claim) else []
    return [rt.residual(cls, ['no contracting iterate while branches are determined'], 'refine the class')]


@op('collatz_split', 'N', ('cclass',), ('cclass',), 'Refine a class modulo M into d subclasses modulo d*M.')
def collatz_split(rt, cls):
    d = cls['data']; D = d['map']['d']
    return [rt.propose('cclass', dict(d, modulus=d['modulus'] * D, residue=d['residue'] + d['modulus'] * i), (cls,))
            for i in range(D)]


@op('collatz_descent_subclass', 'SE', ('descent',), ('descent',),
    'A descent on a class is a descent on each of its d subclasses, with the same number of steps.')
def collatz_descent_subclass(rt, desc):
    if desc['status'] != 'checked': return []
    d = desc['data']; D = d['map']['d']; out = []
    for i in range(D):
        r = d['residue'] + d['modulus'] * i
        claim = rt.transfer('descent', dict(d, modulus=d['modulus'] * D, residue=r,
                                            bound=max(1, lift_bound(d['bound'], d['modulus'] * D, r))), desc)
        if rt.check(claim): out.append(claim)
    return out


@op('collatz_cover_assemble', 'NS', ('cproblem',), ('dcover',),
    'Lift every checked descent of the map to the finest modulus present and assemble one descent cover.')
def collatz_cover_assemble(rt, cm):
    cmap = cm['data']['map']
    descents = [o for o in rt.objects.values() if o['kind'] == 'descent' and o['status'] == 'checked'
                and o['data']['map'] == cmap]
    if not descents: return []
    M = max(o['data']['modulus'] for o in descents)
    # Rows stay at their own moduli and coverage is counted by a sieve along the powers of d: the claim grows with the
    # descents she found, not with the modulus.
    rows = {}
    for o in sorted(descents, key=lambda o: (o['data']['modulus'], o['data']['residue'])):
        d = o['data']
        if M % d['modulus'] == 0: rows.setdefault((d['modulus'], d['residue']), [d['modulus'], d['residue'], d['steps'], d['bound']])
    if len(rows) > 1 << 17: return []
    D = cmap['d']; chain = [D]
    while chain[-1] < M: chain.append(chain[-1] * D)
    if chain[-1] != M: return []
    claim = rt.propose('dcover', dict(map=cmap, modulus=M, rows=sorted(rows.values()), bound=max(r[3] for r in rows.values()),
                                      chain=chain), (cm,))
    return [claim] if rt.check(claim) else []


@op('collatz_finite', 'NS', ('cproblem',), ('cfinite',),
    'Check that every n in [2, N) falls below itself; with n = 1 this gives every n < N reaches 1 by induction.')
def collatz_finite(rt, cm):
    claim = rt.propose('cfinite', dict(map=cm['data']['map'], lo=2, hi=cm['data']['verify_to'], cap=10_000), (cm,))
    return [claim] if rt.check(claim) else []


@op('collatz_cycle_search', 'NWS', ('cproblem',), ('cycle', 'residual'),
    'Iterate starts below 2000; a periodic orbit avoiding 1 refutes reaching 1, otherwise name the searched range.')
def collatz_cycle_search(rt, cm):
    cmap = cm['data']['map']
    for start in range(2, 2000):
        seen = {}; n = start; k = 0
        while n not in seen and k < 500 and n < 10 ** 12:
            rt.budget.use(); seen[n] = k; n = step(cmap, n); k += 1
        if n in seen and n != 1 and 1 not in seen:
            length = k - seen[n]
            claim = rt.propose('cycle', dict(map=cmap, start=n, length=length), (cm,))
            if rt.check(claim): return [claim]
    return [rt.residual(cm, ['no cycle avoiding 1 from starts below 2000'], 'cycle search bound')]


@op('collatz_descent_refute', 'WS', ('descent',), ('refutation',),
    'Evaluate an unchecked descent claim along its class; the first member that does not descend refutes it.')
def collatz_descent_refute(rt, desc):
    if desc['status'] == 'checked': return []
    d = desc['data']
    for t in range(0, 400):
        if d['modulus'] * t + d['residue'] < d['bound']: continue
        refutation = rt.refute(desc, dict(t=t))
        if refutation is not None: return [refutation]
    return []


@op('collatz_residual', 'W', ('dcover',), ('residual',), 'Name the classes of the cover modulus without a descent.')
def collatz_residual(rt, cover):
    d = cover['data']; covered = {row[0] for row in d['rows']}
    left = [r for r in range(d['modulus']) if r not in covered]
    return [rt.residual(cover, left[:4096], str(len(left)) + ' of ' + str(d['modulus']) + ' classes without descent')]


@op('collatz_cycle_refute', 'WS', ('cycle',), ('refutation',),
    'Iterate a claimed cycle; failing to return or passing through 1 refutes it.')
def collatz_cycle_refute(rt, cycle):
    if cycle['status'] == 'checked': return []
    refutation = rt.refute(cycle, {})
    return [refutation] if refutation is not None else []


COLLATZ = dict(d=2, a=[1, 3], b=[0, 1])
FIVE = dict(d=2, a=[1, 5], b=[0, 1])


def _cls(rt, M, r, cmap=COLLATZ): return rt.given('cclass', dict(map=cmap, modulus=M, residue=r))


def _descent(rt, M, r, steps, bound, check=True):
    obj = rt.propose('descent', descent_data(COLLATZ, M, r, steps, bound))
    if check: rt.check(obj)
    return obj


def _problem(rt, cmap=COLLATZ, verify_to=2000):
    return rt.given('cproblem', dict(map=cmap, depth=2, verify_to=verify_to))


def _cover_inputs(rt):
    for r in (0, 1, 2, 3): collatz_affine_descent(rt, _cls(rt, 4, r))
    return [_problem(rt)]


FIXTURES = {
    'collatz_affine_descent': [lambda rt: [_cls(rt, 4, 1)], lambda rt: [_cls(rt, 4, 3)]],
    'collatz_split': [lambda rt: [_cls(rt, 4, 3)]],
    'collatz_descent_subclass': [lambda rt: [_descent(rt, 4, 1, 2, 5)]],
    'collatz_cover_assemble': [_cover_inputs],
    'collatz_finite': [lambda rt: [_problem(rt)]],
    'collatz_cycle_search': [lambda rt: [_problem(rt, FIVE)], lambda rt: [_problem(rt)]],
    'collatz_descent_refute': [lambda rt: [_descent(rt, 4, 3, 2, 3, check=False)]],
    'collatz_residual': [lambda rt: [collatz_cover_assemble(rt, _cover_inputs(rt)[0])[0]]],
    'collatz_cycle_refute': [lambda rt: [rt.propose('cycle', dict(map=COLLATZ, start=1, length=2))]],
}
