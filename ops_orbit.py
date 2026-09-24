"""Operators on polynomial maps, their invariants and orbit reachability questions.

An orbit question asks whether x(n+1) = F(x(n)) from a start ever equals a target.
Exclusion certificates (conserved values, semi-invariants, finite modular
quotients, closed subsystems, iterates, conjugacies and inverse maps) are checked
by lexicon_check.py from the stated map, start and target. Transfers move a
checked invariant, fixed point, reach index or exclusion to an iterate, a
conjugate, an inverse, a product system or an enclosing system.
"""
from fractions import Fraction as Q
from itertools import product
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_orbit_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


L = _load('lexicon')
OPS = []
PRIMES = (2, 3, 5, 7, 11, 13)


def op(name, dirs, consumes, produces, summary):
    def wrap(fn):
        OPS.append(dict(name=name, dirs=dirs, consumes=tuple(consumes), produces=tuple(produces), summary=summary,
                        fn=fn, entry=fn.__name__))
        return fn
    return wrap


def compose(outer, inner, names):
    """Components of outer o inner as expression trees."""
    mapping = {v: e for v, e in zip(names, inner)}
    return [L.substitute(e, mapping) for e in outer]


def shift_h(names):
    """h translates the first variable by 1; h^-1 translates it back."""
    h = [L.add(L.var(names[0]), L.num(1))] + [L.var(v) for v in names[1:]]
    g = [L.add(L.var(names[0]), L.num(-1))] + [L.var(v) for v in names[1:]]
    return h, g


def evaluate_map(components, names, point):
    return [L.poly_eval(L.expand(e, names), point) for e in components]


def affine_parts(components, names):
    """(A, b) when every component is affine, else None."""
    A, b = [], []
    for e in components:
        poly = L.expand(e, names)
        if any(sum(k) > 1 for k in poly): return None
        A.append([poly.get(tuple(int(i == j) for i in range(len(names))), Q(0)) for j in range(len(names))])
        b.append(poly.get((0,) * len(names), Q(0)))
    return A, b


def enc_point(point):
    return [L.enc(x) for x in point]


def dec_point(raw):
    return [L.dec(x) for x in raw]


def orbit_data(names, components, start, target):
    return dict(vars=list(names), map=list(components), start=list(start), target=list(target))


def claimed(rt, kind, data, parents=(), source=None):
    obj = rt.transfer(kind, data, source, parents) if source is not None else rt.propose(kind, data, parents)
    return [obj] if rt.check(obj) else []


# ------------------------------------------------------------- transfers of invariants, fixed points and reach indices

@op('orbit_invariant_iterate', 'SE', ('invariant',), ('invariant',),
    'An invariant of F is an invariant of F o F.')
def orbit_invariant_iterate(rt, inv):
    if inv['status'] != 'checked': return []
    d = inv['data']
    return claimed(rt, 'invariant', dict(d, map=compose(d['map'], d['map'], d['vars'])), source=inv)


@op('orbit_invariant_conjugate', 'SE', ('invariant',), ('invariant',),
    'If P(F) = P then P(h) is conserved by h^-1 o F o h; here h translates the first variable.')
def orbit_invariant_conjugate(rt, inv):
    if inv['status'] != 'checked': return []
    d = inv['data']; names = d['vars']; h, g = shift_h(names)
    G = compose(g, compose(d['map'], h, names), names)
    return claimed(rt, 'invariant', dict(vars=names, map=G, poly=compose([d['poly']], h, names)[0]), source=inv)


@op('orbit_invariant_product', 'SE', ('invariant',), ('invariant',),
    'An invariant of F is an invariant of the product system (F, t -> t + 1) with a fresh coordinate t.')
def orbit_invariant_product(rt, inv):
    if inv['status'] != 'checked' or len(inv['data']['vars']) >= 8: return []
    d = inv['data']; t = 't'
    while t in d['vars']: t += '_'
    return claimed(rt, 'invariant', dict(vars=d['vars'] + [t], map=d['map'] + [L.add(L.var(t), L.num(1))], poly=d['poly']),
                   source=inv)


@op('orbit_invariant_linearize', 'SE', ('invariant',), ('invariant',),
    'When F(0) = 0, the lowest homogeneous part of an invariant is conserved by the linear part DF(0).')
def orbit_invariant_linearize(rt, inv):
    if inv['status'] != 'checked': return []
    d = inv['data']; names = d['vars']; n = len(names)
    polys = [L.expand(e, names) for e in d['map']]
    if any(p.get((0,) * n) for p in polys): return []
    linear = [L.poly_expr({k: c for k, c in p.items() if sum(k) == 1}, names) for p in polys]
    P = L.expand(d['poly'], names); low = min(sum(k) for k in P)
    lowest = {k: c for k, c in P.items() if sum(k) == low}
    if low == 0: return []
    return claimed(rt, 'invariant', dict(vars=names, map=linear, poly=L.poly_expr(lowest, names)), source=inv)


@op('orbit_semi_iterate', 'SE', ('semi',), ('semi',),
    'P(F) = lambda P gives P(F o F) = lambda^2 P.')
def orbit_semi_iterate(rt, semi):
    if semi['status'] != 'checked': return []
    d = semi['data']; lam = L.dec(d['factor'])
    return claimed(rt, 'semi', dict(d, map=compose(d['map'], d['map'], d['vars']), factor=L.enc(lam * lam)), source=semi)


@op('orbit_fixed_conjugate', 'SE', ('fixed',), ('fixed',),
    'A fixed point p of F gives the fixed point h^-1(p) of h^-1 o F o h.')
def orbit_fixed_conjugate(rt, fixed):
    if fixed['status'] != 'checked': return []
    d = fixed['data']; names = d['vars']; h, g = shift_h(names)
    point = evaluate_map(g, names, dec_point(d['point']))
    return claimed(rt, 'fixed', dict(vars=names, map=compose(g, compose(d['map'], h, names), names),
                                     point=enc_point(point)), source=fixed)


@op('orbit_fixed_iterate', 'SE', ('fixed',), ('fixed',), 'A fixed point of F is a fixed point of F o F.')
def orbit_fixed_iterate(rt, fixed):
    if fixed['status'] != 'checked': return []
    d = fixed['data']
    return claimed(rt, 'fixed', dict(d, map=compose(d['map'], d['map'], d['vars'])), source=fixed)


@op('orbit_reach_iterate', 'SE', ('reach',), ('reach',),
    'Reaching the target at an even index 2i under F is reaching it at index i under F o F.')
def orbit_reach_iterate(rt, reach):
    d = reach['data']
    if reach['status'] != 'checked' or d['index'] % 2: return []
    o = d['orbit']
    return claimed(rt, 'reach', dict(orbit=dict(o, map=compose(o['map'], o['map'], o['vars'])), index=d['index'] // 2),
                   source=reach)


@op('orbit_reach_shift', 'SE', ('reach',), ('reach',),
    'Reaching the target at index i >= 1 from x is reaching it at index i-1 from F(x).')
def orbit_reach_shift(rt, reach):
    d = reach['data']
    if reach['status'] != 'checked' or d['index'] < 1: return []
    o = d['orbit']; start = evaluate_map(o['map'], o['vars'], dec_point(o['start']))
    return claimed(rt, 'reach', dict(orbit=dict(o, start=enc_point(start)), index=d['index'] - 1), source=reach)


@op('orbit_reach_conjugate', 'SE', ('reach',), ('reach',),
    'A reach index for F from s to t is one for h^-1 o F o h from h^-1(s) to h^-1(t).')
def orbit_reach_conjugate(rt, reach):
    if reach['status'] != 'checked': return []
    d = reach['data']; o = d['orbit']; names = o['vars']; h, g = shift_h(names)
    s = evaluate_map(g, names, dec_point(o['start'])); t = evaluate_map(g, names, dec_point(o['target']))
    G = compose(g, compose(o['map'], h, names), names)
    return claimed(rt, 'reach', dict(orbit=orbit_data(names, G, enc_point(s), enc_point(t)), index=d['index']), source=reach)


# ------------------------------------------------------------- transfers of refutations (exclusions)

@op('orbit_exclusion_iterate', 'WSE', ('exclusion',), ('exclusion',),
    'The orbit of F o F lies inside the orbit of F, so an exclusion for F excludes for F o F.')
def orbit_exclusion_iterate(rt, exc):
    if exc['status'] != 'checked': return []
    o = exc['data']['orbit']; G = compose(o['map'], o['map'], o['vars'])
    cert = dict(type='iterate', base=o['map'], k=2, inner=exc['data']['certificate'])
    return claimed(rt, 'exclusion', dict(orbit=dict(o, map=G), certificate=cert), source=exc)


@op('orbit_exclusion_conjugate', 'WSE', ('exclusion',), ('exclusion',),
    'An exclusion for F from s to t excludes for h^-1 o F o h from h^-1(s) to h^-1(t).')
def orbit_exclusion_conjugate(rt, exc):
    if exc['status'] != 'checked': return []
    o = exc['data']['orbit']; names = o['vars']; h, g = shift_h(names)
    s = evaluate_map(g, names, dec_point(o['start'])); t = evaluate_map(g, names, dec_point(o['target']))
    G = compose(g, compose(o['map'], h, names), names)
    cert = dict(type='conjugate', h=h, h_inverse=g, base=dict(map=o['map'], start=o['start'], target=o['target']),
                inner=exc['data']['certificate'])
    return claimed(rt, 'exclusion', dict(orbit=orbit_data(names, G, enc_point(s), enc_point(t)), certificate=cert),
                   source=exc)


@op('orbit_exclusion_reverse', 'WSE', ('exclusion', 'inverse'), ('exclusion',),
    'If t is never reached from s under F, then s is never reached from t under the inverse map.')
def orbit_exclusion_reverse(rt, exc, inv):
    o = exc['data']['orbit']; i = inv['data']
    if exc['status'] != 'checked' or inv['status'] != 'checked' or i['vars'] != o['vars'] or i['map'] != o['map']: return []
    cert = dict(type='reverse', inverse=o['map'], inner=exc['data']['certificate'])
    question = orbit_data(o['vars'], i['inverse'], o['target'], o['start'])
    return claimed(rt, 'exclusion', dict(orbit=question, certificate=cert), (inv,), exc)


@op('orbit_exclusion_embed', 'WSE', ('exclusion', 'orbit'), ('exclusion',),
    'An exclusion for a closed coordinate subsystem excludes the enclosing system with matching coordinates.')
def orbit_exclusion_embed(rt, exc, orbit):
    if exc['status'] != 'checked': return []
    sub, full = exc['data']['orbit'], orbit['data']
    idx = [full['vars'].index(v) for v in sub['vars'] if v in full['vars']]
    if len(idx) != len(sub['vars']) or len(idx) == len(full['vars']) or sorted(idx) != idx: return []
    if [full['map'][i] for i in idx] != sub['map'] or [full['start'][i] for i in idx] != sub['start'] \
            or [full['target'][i] for i in idx] != sub['target']: return []
    cert = dict(type='subsystem', indices=idx, inner=exc['data']['certificate'])
    return claimed(rt, 'exclusion', dict(orbit=full, certificate=cert), (orbit,), exc)


@op('orbit_invariant_to_exclusion', 'WSE', ('invariant', 'orbit'), ('exclusion', 'residual'),
    'A checked invariant of the orbit\'s map whose values at start and target differ excludes the target.')
def orbit_invariant_to_exclusion(rt, inv, orbit):
    d, o = inv['data'], orbit['data']
    if inv['status'] != 'checked' or d['vars'] != o['vars'] or d['map'] != o['map']: return []
    P = L.expand(d['poly'], d['vars'])
    if L.poly_eval(P, dec_point(o['start'])) == L.poly_eval(P, dec_point(o['target'])):
        return [rt.residual(orbit, ['invariant takes equal values at start and target'], 'no separation')]
    return claimed(rt, 'exclusion', dict(orbit=o, certificate=dict(type='invariant', poly=d['poly'])), (orbit,), inv)


@op('orbit_semi_to_exclusion', 'WSE', ('semi', 'orbit'), ('exclusion', 'residual'),
    'P(x(n)) = lambda^n P(x(0)) leaves at most one index for the target value; exclude or name the residual.')
def orbit_semi_to_exclusion(rt, semi, orbit):
    d, o = semi['data'], orbit['data']
    if semi['status'] != 'checked' or d['vars'] != o['vars'] or d['map'] != o['map']: return []
    lam = L.dec(d['factor']); P = L.expand(d['poly'], d['vars'])
    v0, vt = L.poly_eval(P, dec_point(o['start'])), L.poly_eval(P, dec_point(o['target']))
    cert = dict(type='semi', poly=d['poly'], factor=d['factor'])
    if v0 != 0 and abs(lam) not in (0, 1) and vt != 0:
        value, n = v0, 0
        while n <= 4096 and (abs(value) <= abs(vt) if abs(lam) > 1 else abs(value) >= abs(vt)):
            if value == vt: cert['index'] = n; break
            value *= lam; n += 1
    out = claimed(rt, 'exclusion', dict(orbit=o, certificate=cert), (orbit,), semi)
    return out or [rt.residual(orbit, ['semi-invariant does not exclude the target'], 'no separation')]


# ------------------------------------------------------------- proposals

def monomials(n, degree):
    return [k for k in product(range(degree + 1), repeat=n) if 0 < sum(k) <= degree]


@op('orbit_semi_search', 'NS', ('map',), ('semi',),
    'Solve P(F) = lambda P over polynomials of degree <= 2 for lambda in {-1, 2, -2, 3, 1/2} by exact nullspaces.')
def orbit_semi_search(rt, mp):
    d = mp['data']; names = d['vars']; basis = monomials(len(names), 2); out = []
    images = []
    for k in basis:
        term = L.mul(*[L.power(L.var(v), e) for v, e in zip(names, k) if e]) if any(k) else L.num(1)
        images.append((term, L.expand(compose([term], d['map'], names)[0], names)))
    for lam in (Q(-1), Q(2), Q(-2), Q(3), Q(1, 2)):
        rt.budget.use(len(basis) ** 2)
        keys = sorted(set().union(*[img for _, img in images], *[{k: 1} for k in basis]))
        rows = [[img.get(key, Q(0)) - lam * (Q(1) if key == k else Q(0)) for k, (_, img) in zip(basis, images)]
                for key in keys]
        for vector in L.nullspace(rows, len(basis))[:1]:
            poly = {k: c for k, c in zip(basis, vector) if c}
            out += claimed(rt, 'semi', dict(vars=names, map=d['map'], poly=L.poly_expr(poly, names), factor=L.enc(lam)), (mp,))
    return out


@op('orbit_fixed_point', 'NS', ('map',), ('fixed',), 'Solve (A - I)x = -b for an affine map x -> Ax + b.')
def orbit_fixed_point(rt, mp):
    d = mp['data']; parts = affine_parts(d['map'], d['vars'])
    if parts is None: return []
    A, b = parts; n = len(A)
    sol = L.solve_linear([[A[i][j] - (1 if i == j else 0) for j in range(n)] for i in range(n)], [-x for x in b])
    if sol is None: return []
    return claimed(rt, 'fixed', dict(vars=d['vars'], map=d['map'], point=enc_point(sol)), (mp,))


@op('orbit_two_cycle', 'NS', ('map',), ('fixed',),
    'Fixed points of F o F that are not fixed by F, for an affine map.')
def orbit_two_cycle(rt, mp):
    d = mp['data']; names = d['vars']; FF = compose(d['map'], d['map'], names)
    parts = affine_parts(FF, names)
    if parts is None: return []
    A, b = parts; n = len(A)
    sol = L.solve_linear([[A[i][j] - (1 if i == j else 0) for j in range(n)] for i in range(n)], [-x for x in b])
    if sol is None or evaluate_map(d['map'], names, sol) == sol: return []
    return claimed(rt, 'fixed', dict(vars=names, map=FF, point=enc_point(sol)), (mp,))


@op('orbit_inverse_map', 'NS', ('map',), ('inverse',),
    'Invert an affine map with an invertible linear part: x -> A^-1 (x - b).')
def orbit_inverse_map(rt, mp):
    d = mp['data']; names = d['vars']; parts = affine_parts(d['map'], names)
    if parts is None: return []
    A, b = parts; n = len(A); columns = []
    for j in range(n):
        col = L.solve_linear(A, [Q(int(i == j)) for i in range(n)])
        if col is None: return []
        columns.append(col)
    inv = [[columns[j][i] for j in range(n)] for i in range(n)]
    shift = [sum(inv[i][j] * b[j] for j in range(n)) for i in range(n)]
    comps = [L.add(*[L.mul(L.num(inv[i][j]), L.var(names[j])) for j in range(n) if inv[i][j]], L.num(-shift[i]))
             for i in range(n)]
    return claimed(rt, 'inverse', dict(vars=names, map=d['map'], inverse=comps), (mp,))


@op('orbit_invariant_combine', 'NS', ('invariant', 'invariant'), ('invariant',),
    'Sums and products of invariants of one map are invariants.')
def orbit_invariant_combine(rt, first, second):
    a, b = first['data'], second['data']
    if first['id'] == second['id'] or a['vars'] != b['vars'] or a['map'] != b['map']: return []
    if first['status'] != 'checked' or second['status'] != 'checked': return []
    return (claimed(rt, 'invariant', dict(a, poly=L.add(a['poly'], b['poly'])), (first, second))
            + claimed(rt, 'invariant', dict(a, poly=L.mul(a['poly'], b['poly'])), (first, second)))


@op('orbit_linear_sequence', 'NS', ('orbit',), ('law',),
    'For a linear integer map, the first coordinate of the orbit is u*A**n*e1; Cayley-Hamilton gives its law.')
def orbit_linear_sequence(rt, orbit):
    o = orbit['data']; parts = affine_parts(o['map'], o['vars'])
    if parts is None or any(parts[1]): return []
    A = parts[0]; start = dec_point(o['start'])
    if not all(x.denominator == 1 for row in A for x in row) or not all(x.denominator == 1 for x in start): return []
    n = len(A)
    # Row vector state s(k) = x(k)^T satisfies s(k+1) = s(k) A^T.
    M = [[int(A[j][i]) for j in range(n)] for i in range(n)]
    sd = dict(type='matrix', matrix=M, initial=[int(x) for x in start], terminal=[1] + [0] * (n - 1))
    P = L.charpoly(A); P = L.pscale(P, 1 / P[-1]); r = len(P) - 1
    law = dict({'def': sd}, coefficients=[L.enc(-P[j]) for j in range(r)], initial=[L.enc(x) for x in L.terms(sd, r)])
    return claimed(rt, 'law', law, (orbit,))


@op('orbit_modular_exclusion', 'NWS', ('orbit',), ('exclusion',),
    'Reduce the orbit modulo a small prime; if its finite eventually periodic orbit avoids the target residue, exclude.')
def orbit_modular_exclusion(rt, orbit):
    o = orbit['data']; names = o['vars']
    polys = [L.expand(e, names) for e in o['map']]
    start, target = dec_point(o['start']), dec_point(o['target'])
    for p in PRIMES:
        if any(c.denominator % p == 0 for poly in polys for c in poly.values()): continue
        if any(x.denominator % p == 0 for x in start + target): continue
        red = lambda x: x.numerator * pow(x.denominator, -1, p) % p
        s = tuple(red(x) for x in start); t = tuple(red(x) for x in target); seen = set(); hit = False
        while s not in seen and len(seen) <= p ** len(names):
            rt.budget.use(len(s))
            if s == t: hit = True; break
            seen.add(s)
            s = tuple(red(L.poly_eval(poly, list(s))) for poly in polys)
        if hit: continue
        return claimed(rt, 'exclusion', dict(orbit=o, certificate=dict(type='modular', modulus=p)), (orbit,))
    return []


# ------------------------------------------------------------- refutations and residuals

@op('orbit_invariant_refute', 'WS', ('invariant',), ('refutation',),
    'Evaluate P(F(p)) - P(p) at exact points; a nonzero value refutes an unchecked invariant.')
def orbit_invariant_refute(rt, inv):
    if inv['status'] == 'checked': return []
    n = len(inv['data']['vars'])
    for i in range(8):
        point = [Q(i + j + 1, 1 + (j % 2)) for j in range(n)]
        refutation = rt.refute(inv, dict(point=enc_point(point)))
        if refutation is not None: return [refutation]
    return []


@op('orbit_invariant_residual', 'W', ('invariant',), ('residual',),
    'Name P(F(x)) - P(x) of an unchecked invariant as the open part.')
def orbit_invariant_residual(rt, inv):
    if inv['status'] == 'checked': return []
    d = inv['data']; names = d['vars']
    diff = L.poly_add(L.expand(compose([d['poly']], d['map'], names)[0], names), L.poly_scale(L.expand(d['poly'], names), -1))
    if not diff: return []
    return [rt.residual(inv, [L.canonical(L.poly_expr(diff, names))[:4000]], 'P(F(x)) - P(x) is not zero')]


@op('orbit_reach_refute', 'WS', ('reach',), ('refutation',),
    'Iterate to a claimed reach index; a different point refutes the claim.')
def orbit_reach_refute(rt, reach):
    if reach['status'] == 'checked': return []
    refutation = rt.refute(reach, {})
    return [refutation] if refutation is not None else []


@op('orbit_fixed_refute', 'WS', ('fixed',), ('refutation',), 'Evaluate F at a claimed fixed point; F(p) != p refutes it.')
def orbit_fixed_refute(rt, fixed):
    if fixed['status'] == 'checked': return []
    refutation = rt.refute(fixed, {})
    return [refutation] if refutation is not None else []


# ------------------------------------------------------------- fixtures

X, Y = L.var('x'), L.var('y')
ROTATION = (['x', 'y'], [Y, L.mul(L.num(-1), X)])
NONLINEAR = (['x', 'y'], [L.add(Y, L.power(X, 2)), L.sub(L.mul(L.num(-1), X), L.power(L.add(Y, L.power(X, 2)), 2))])
NONLINEAR_INV = L.add(L.power(X, 2), L.power(L.add(Y, L.power(X, 2)), 2))
STEP2 = (['x'], [L.add(X, L.num(2))])


def _inv(rt, names, comps, poly):
    obj = rt.propose('invariant', dict(vars=names, map=comps, poly=poly)); rt.check(obj); return obj


def _checked(rt, kind, data):
    obj = rt.propose(kind, data); rt.check(obj); return obj


def _orbit(rt, names, comps, start, target):
    return rt.given('orbit', orbit_data(names, comps, [[x, 1] for x in start], [[x, 1] for x in target]))


def _step2_exclusion(rt):
    return _checked(rt, 'exclusion', dict(orbit=orbit_data(['x'], STEP2[1], [[0, 1]], [[1, 1]]),
                                          certificate=dict(type='modular', modulus=2)))


def _affine(rt):
    return rt.given('map', dict(vars=['x', 'y'], map=[L.add(L.mul(L.num(2), X), Y, L.num(1)), L.add(X, Y)]))


FIXTURES = {
    'orbit_invariant_iterate': [lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2)))]],
    'orbit_invariant_conjugate': [lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2)))]],
    'orbit_invariant_product': [lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2)))]],
    'orbit_invariant_linearize': [lambda rt: [_inv(rt, *NONLINEAR, NONLINEAR_INV)]],
    'orbit_semi_iterate': [lambda rt: [_checked(rt, 'semi', dict(vars=['x'], map=[L.mul(L.num(2), X)], poly=X,
                                                                  factor=[2, 1]))]],
    'orbit_fixed_conjugate': [lambda rt: [_checked(rt, 'fixed', dict(vars=['x', 'y'], map=ROTATION[1], point=[[0, 1], [0, 1]]))]],
    'orbit_fixed_iterate': [lambda rt: [_checked(rt, 'fixed', dict(vars=['x', 'y'], map=ROTATION[1], point=[[0, 1], [0, 1]]))]],
    'orbit_reach_iterate': [lambda rt: [_checked(rt, 'reach', dict(orbit=orbit_data(['x'], STEP2[1], [[0, 1]], [[8, 1]]),
                                                                    index=4))]],
    'orbit_reach_shift': [lambda rt: [_checked(rt, 'reach', dict(orbit=orbit_data(['x'], STEP2[1], [[0, 1]], [[8, 1]]),
                                                                  index=4))]],
    'orbit_reach_conjugate': [lambda rt: [_checked(rt, 'reach', dict(orbit=orbit_data(['x'], STEP2[1], [[0, 1]], [[8, 1]]),
                                                                      index=4))]],
    'orbit_exclusion_iterate': [lambda rt: [_step2_exclusion(rt)]],
    'orbit_exclusion_conjugate': [lambda rt: [_step2_exclusion(rt)]],
    'orbit_exclusion_reverse': [lambda rt: [_step2_exclusion(rt),
                                            _checked(rt, 'inverse', dict(vars=['x'], map=STEP2[1],
                                                                         inverse=[L.add(X, L.num(-2))]))]],
    'orbit_exclusion_embed': [lambda rt: [_step2_exclusion(rt),
                                          _orbit(rt, ['x', 'y'], [L.add(X, L.num(2)), L.add(Y, X)], [0, 5], [1, 7])]],
    'orbit_invariant_to_exclusion': [lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2))),
                                                 _orbit(rt, *ROTATION, [1, 0], [2, 0])],
                                     lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2))),
                                                 _orbit(rt, *ROTATION, [3, 4], [5, 0])]],
    'orbit_semi_to_exclusion': [lambda rt: [_checked(rt, 'semi', dict(vars=['x'], map=[L.mul(L.num(2), X)], poly=X,
                                                                       factor=[2, 1])),
                                            _orbit(rt, ['x'], [L.mul(L.num(2), X)], [1], [3])],
                                lambda rt: [_checked(rt, 'semi', dict(vars=['x'], map=[L.mul(L.num(2), X)], poly=X,
                                                                       factor=[2, 1])),
                                            _orbit(rt, ['x'], [L.mul(L.num(2), X)], [1], [8])]],
    'orbit_semi_search': [lambda rt: [rt.given('map', dict(vars=['x', 'y'], map=[L.mul(L.num(2), X), L.add(Y, X)]))]],
    'orbit_fixed_point': [lambda rt: [_affine(rt)]],
    'orbit_two_cycle': [lambda rt: [rt.given('map', dict(vars=['x'], map=[L.add(L.mul(L.num(-1), X), L.num(3))]))]],
    'orbit_inverse_map': [lambda rt: [_affine(rt)]],
    'orbit_invariant_combine': [lambda rt: [_inv(rt, *ROTATION, L.add(L.power(X, 2), L.power(Y, 2))),
                                            _inv(rt, *ROTATION, L.power(L.add(L.power(X, 2), L.power(Y, 2)), 2))]],
    'orbit_linear_sequence': [lambda rt: [_orbit(rt, ['x', 'y'], [L.add(X, Y), X], [1, 0], [5, 3])]],
    'orbit_modular_exclusion': [lambda rt: [_orbit(rt, ['x', 'y'], [L.add(X, L.num(2)), L.add(Y, X)], [0, 5], [1, 7])]],
    'orbit_invariant_refute': [lambda rt: [rt.propose('invariant', dict(vars=['x', 'y'], map=ROTATION[1],
                                                                         poly=L.add(X, Y)))]],
    'orbit_invariant_residual': [lambda rt: [rt.propose('invariant', dict(vars=['x', 'y'], map=ROTATION[1],
                                                                           poly=L.add(X, Y)))]],
    'orbit_reach_refute': [lambda rt: [rt.propose('reach', dict(orbit=orbit_data(['x'], STEP2[1], [[0, 1]], [[8, 1]]),
                                                                  index=3))]],
    'orbit_fixed_refute': [lambda rt: [rt.propose('fixed', dict(vars=['x', 'y'], map=ROTATION[1], point=[[1, 1], [0, 1]]))]],
}
