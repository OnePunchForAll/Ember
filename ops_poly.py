"""Operators on polynomial identities and polynomials over QQ.

An identity claim states lhs = rhs as expression trees in listed variables; the
checker expands both sides independently. Transfers rewrite a checked identity's
trees (substitution, specialization, differentiation, renaming, sums and
products of identities) into a new claim, which the checker expands again.
Proposals produce factorizations, gcds, Bezout relations, partial fractions,
symmetric reductions, Taylor shifts and square roots, each stated as an identity.
"""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_poly_' + name, Path(__file__).with_name(name + '.py'))
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


def identity(vars_, lhs, rhs):
    return dict(vars=list(vars_), lhs=lhs, rhs=rhs)


def claimed(rt, kind, data, parents, source=None):
    obj = rt.transfer(kind, data, source, parents) if source is not None else rt.propose(kind, data, parents)
    return [obj] if rt.check(obj) else []


def univariate_of(p):
    d = p['data']
    if len(d['vars']) != 1: return None, None
    return d['vars'][0], L.univariate(d['expr'], d['vars'][0], None)


def expr_of(coefficients, name):
    return L.univariate_expr(coefficients, name)


# ------------------------------------------------------------- transfers of checked identities

@op('poly_substitute_identity', 'SE', ('identity',), ('identity',),
    'Replace a variable by a polynomial in the variables on both sides of a checked identity.')
def poly_substitute_identity(rt, ident):
    if ident['status'] != 'checked': return []
    d = ident['data']; v = d['vars'][0]
    image = L.add(L.mul(L.num(2), L.var(v)), L.num(-1)) if len(d['vars']) == 1 else L.add(L.var(v), L.var(d['vars'][1]))
    mapping = {v: image}
    return claimed(rt, 'identity', identity(d['vars'], L.substitute(d['lhs'], mapping), L.substitute(d['rhs'], mapping)),
                   (), ident)


@op('poly_specialize_identity', 'SE', ('identity',), ('identity',),
    'Instantiate one variable of a checked identity at a rational point.')
def poly_specialize_identity(rt, ident):
    if ident['status'] != 'checked': return []
    d = ident['data']; v = d['vars'][-1]; mapping = {v: L.num(Q(3, 2))}
    return claimed(rt, 'identity', identity(d['vars'], L.substitute(d['lhs'], mapping), L.substitute(d['rhs'], mapping)),
                   (), ident)


@op('poly_differentiate_identity', 'SE', ('identity',), ('identity',),
    'Differentiate both sides of a checked identity with respect to one variable.')
def poly_differentiate_identity(rt, ident):
    if ident['status'] != 'checked': return []
    d = ident['data']; v = d['vars'][0]
    return claimed(rt, 'identity', identity(d['vars'], L.derivative(d['lhs'], v), L.derivative(d['rhs'], v)), (), ident)


@op('poly_swap_identity', 'SE', ('identity',), ('identity',),
    'Exchange two variables throughout a checked identity.')
def poly_swap_identity(rt, ident):
    if ident['status'] != 'checked' or len(ident['data']['vars']) < 2: return []
    d = ident['data']; x, y = d['vars'][0], d['vars'][1]; mapping = {x: L.var(y), y: L.var(x)}
    return claimed(rt, 'identity', identity(d['vars'], L.substitute(d['lhs'], mapping), L.substitute(d['rhs'], mapping)),
                   (), ident)


@op('poly_sum_identities', 'SE', ('identity', 'identity'), ('identity',),
    'Add two checked identities over the union of their variables.')
def poly_sum_identities(rt, first, second):
    if first['status'] != 'checked' or second['status'] != 'checked' or first['id'] == second['id']: return []
    a, b = first['data'], second['data']; names = list(dict.fromkeys(a['vars'] + b['vars']))
    if len(names) > 8: return []
    return claimed(rt, 'identity', identity(names, L.add(a['lhs'], b['lhs']), L.add(a['rhs'], b['rhs'])), (second,), first)


@op('poly_product_identities', 'SE', ('identity', 'identity'), ('identity',),
    'Multiply two checked identities side by side.')
def poly_product_identities(rt, first, second):
    if first['status'] != 'checked' or second['status'] != 'checked' or first['id'] == second['id']: return []
    a, b = first['data'], second['data']; names = list(dict.fromkeys(a['vars'] + b['vars']))
    if len(names) > 8: return []
    return claimed(rt, 'identity', identity(names, L.mul(a['lhs'], b['lhs']), L.mul(a['rhs'], b['rhs'])), (second,), first)


@op('poly_telescoping_sum', 'SE', ('identity',), ('closed',),
    'A checked identity P(n+1) - P(n) = q(n) gives the closed form sum_{k<=n} q(k) = P(n+1) - P(0).')
def poly_telescoping_sum(rt, ident):
    d = ident['data']
    if ident['status'] != 'checked' or d['vars'] != ['n'] or d['lhs'][0] != 'sub': return []
    upper, lower = d['lhs'][1], d['lhs'][2]
    shifted = L.substitute(lower, {'n': L.add(L.var('n'), L.num(1))})
    if L.expand(shifted, ['n']) != L.expand(upper, ['n']): return []
    P = L.univariate(lower, 'n'); q = L.univariate(d['rhs'], 'n')
    closed = L.padd(L.pshift(P, 1), [-L.peval(P, 0)])
    sd = dict(type='transform', op='partial_sum', args=[dict(type='poly', coefficients=[L.enc(x) for x in q] or [[0, 1]])])
    return claimed(rt, 'closed', {'def': sd, 'form': dict(type='poly', coefficients=[L.enc(x) for x in closed] or [[0, 1]])},
                   (), ident)


# ------------------------------------------------------------- proposals stated as identities

@op('poly_factor_linear', 'NS', ('poly',), ('identity',),
    'Split off every rational linear factor of a univariate polynomial by the rational root test.')
def poly_factor_linear(rt, p):
    v, c = univariate_of(p)
    if v is None or len(c) < 2: return []
    roots, rest = [], c
    for root in L.rational_roots(c):
        while True:
            q = L.pexact(rest, [-root, Q(1)])
            if q is None: break
            roots.append(root); rest = q
    if not roots: return []
    factors = [L.add(L.var(v), L.num(-root)) for root in roots]
    return claimed(rt, 'identity', identity([v], p['data']['expr'], L.mul(expr_of(rest, v), *factors)), (p,))


@op('poly_gcd', 'NS', ('poly', 'poly'), ('identity',),
    'Euclid gives g = gcd(p, q); state p = g*(p/g) and q = g*(q/g).')
def poly_gcd(rt, first, second):
    v1, a = univariate_of(first); v2, b = univariate_of(second)
    if v1 is None or v1 != v2 or first['id'] == second['id']: return []
    g = L.pgcd(a, b)
    if len(g) < 2: return []
    out = []
    for obj, c in ((first, a), (second, b)):
        out += claimed(rt, 'identity', identity([v1], obj['data']['expr'], L.mul(expr_of(g, v1), expr_of(L.pexact(c, g), v1))),
                       (first, second))
    return out


@op('poly_squarefree', 'NS', ('poly',), ('identity',),
    'Write p = gcd(p, p\') * (p / gcd(p, p\')), separating repeated factors.')
def poly_squarefree(rt, p):
    v, c = univariate_of(p)
    if v is None: return []
    g = L.pgcd(c, L.pderiv(c))
    if len(g) < 2: return []
    return claimed(rt, 'identity', identity([v], p['data']['expr'], L.mul(expr_of(g, v), expr_of(L.pexact(c, g), v))), (p,))


@op('poly_bezout', 'NS', ('poly', 'poly'), ('identity',),
    'Solve the Sylvester system for u*p + v*q = R, with R the resultant of coprime p and q.')
def poly_bezout(rt, first, second):
    v1, a = univariate_of(first); v2, b = univariate_of(second)
    if v1 is None or v1 != v2 or first['id'] == second['id'] or len(a) < 2 or len(b) < 2: return []
    m, n = len(a) - 1, len(b) - 1
    # u has degree < n and v degree < m; coefficients of u*a + v*b must vanish above degree 0.
    rows = []
    for k in range(m + n):
        rows.append([a[k - i] if 0 <= k - i < len(a) else Q(0) for i in range(n)] +
                    [b[k - j] if 0 <= k - j < len(b) else Q(0) for j in range(m)])
    sol = L.solve_linear(rows, [Q(1)] + [Q(0)] * (m + n - 1))
    if sol is None: return []
    u, w = L.ptrim(sol[:n]), L.ptrim(sol[n:])
    lhs = L.add(L.mul(expr_of(u, v1), first['data']['expr']), L.mul(expr_of(w, v1), second['data']['expr']))
    return claimed(rt, 'identity', identity([v1], lhs, L.num(1)), (first, second))


@op('poly_linear_relation', 'NS', ('poly', 'poly', 'poly'), ('identity',),
    'Find rational c with c1*p1 + c2*p2 + c3*p3 = 0 from the exact coefficient nullspace.')
def poly_linear_relation(rt, p1, p2, p3):
    objs = [p1, p2, p3]
    if len({o['id'] for o in objs}) < 3 or len({tuple(o['data']['vars']) for o in objs}) != 1: return []
    names = p1['data']['vars']; polys = [L.expand(o['data']['expr'], names) for o in objs]
    keys = sorted(set().union(*polys))
    basis = L.nullspace([[p.get(k, Q(0)) for p in polys] for k in keys], 3)
    if not basis: return []
    c = basis[0]
    lhs = L.add(*[L.mul(L.num(ci), o['data']['expr']) for ci, o in zip(c, objs) if ci])
    return claimed(rt, 'identity', identity(names, lhs, L.num(0)), tuple(objs))


@op('poly_partial_fractions', 'NS', ('poly', 'poly', 'poly'), ('identity',),
    'For coprime q1, q2 write p = a*q2 + b*q1 with deg a < deg q1, the numerators of p/(q1 q2).')
def poly_partial_fractions(rt, p, q1, q2):
    vs = {univariate_of(o)[0] for o in (p, q1, q2)}
    if len(vs) != 1 or None in vs or len({p['id'], q1['id'], q2['id']}) < 3: return []
    v = vs.pop(); P, A, B = (univariate_of(o)[1] for o in (p, q1, q2))
    if len(L.pgcd(A, B)) != 1 or len(P) >= len(A) + len(B) - 1: return []
    m, n = len(A) - 1, len(B) - 1
    rows = [[B[k - i] if 0 <= k - i < len(B) else Q(0) for i in range(m)] +
            [A[k - j] if 0 <= k - j < len(A) else Q(0) for j in range(n)] for k in range(m + n)]
    sol = L.solve_linear(rows, [P[k] if k < len(P) else Q(0) for k in range(m + n)])
    if sol is None: return []
    lhs = L.add(L.mul(expr_of(L.ptrim(sol[:m]), v), q2['data']['expr']), L.mul(expr_of(L.ptrim(sol[m:]), v), q1['data']['expr']))
    return claimed(rt, 'identity', identity([v], p['data']['expr'], lhs), (p, q1, q2))


@op('poly_symmetric_reduction', 'NS', ('poly',), ('identity',),
    'Rewrite a symmetric polynomial in x, y through e1 = x + y and e2 = x*y by leading-term elimination.')
def poly_symmetric_reduction(rt, p):
    names = p['data']['vars']
    if len(names) != 2: return []
    poly = L.expand(p['data']['expr'], names)
    if any(poly.get((j, i), 0) != c for (i, j), c in poly.items()): return []
    rest = dict(poly); terms = []
    e1 = {(1, 0): Q(1), (0, 1): Q(1)}; e2 = {(1, 1): Q(1)}
    while rest:
        rt.budget.use()
        (i, j), c = max(rest.items())
        if i < j: return []
        term = {(0, 0): Q(c)}
        for _ in range(i - j): term = L.poly_mul(term, e1)
        for _ in range(j): term = L.poly_mul(term, e2)
        rest = L.poly_add(rest, L.poly_scale(term, -1)); terms.append((c, i - j, j))
    x, y = (L.var(n) for n in names)
    rhs = L.add(*[L.mul(L.num(c), L.power(L.add(x, y), a), L.power(L.mul(x, y), b)) for c, a, b in terms])
    return claimed(rt, 'identity', identity(names, p['data']['expr'], rhs), (p,))


@op('poly_taylor_shift', 'NS', ('poly',), ('identity',),
    'Expand a univariate polynomial in powers of (x - 1).')
def poly_taylor_shift(rt, p):
    v, c = univariate_of(p)
    if v is None or len(c) < 2: return []
    shifted = L.pshift(c, 1)
    rhs = L.add(*[L.mul(L.num(a), L.power(L.add(L.var(v), L.num(-1)), i)) for i, a in enumerate(shifted) if a])
    return claimed(rt, 'identity', identity([v], p['data']['expr'], rhs), (p,))


@op('poly_square_root', 'NS', ('poly',), ('identity',),
    'Recognise a perfect square p = q^2 by the coefficient recursion for q.')
def poly_square_root(rt, p):
    v, c = univariate_of(p)
    if v is None or len(c) < 3 or (len(c) - 1) % 2: return []
    lead = c[-1]
    root_lead = next((Q(a, b) for a in range(1, 64) for b in range(1, 64) if Q(a, b) ** 2 == lead), None)
    if root_lead is None: return []
    d = (len(c) - 1) // 2; q = [Q(0)] * (d + 1); q[d] = root_lead
    for k in range(d - 1, -1, -1):
        known = sum(q[i] * q[d + k - i] for i in range(k + 1, d))
        q[k] = (c[d + k] - known) / (2 * root_lead)
    if L.pmul(q, q) != L.ptrim(c): return []
    return claimed(rt, 'identity', identity([v], p['data']['expr'], L.mul(expr_of(q, v), expr_of(q, v))), (p,))


# ------------------------------------------------------------- refutations and residuals

def sample_points(n):
    base = [Q(2), Q(-1), Q(3), Q(1, 2), Q(5), Q(-3, 2), Q(7), Q(11)]
    return [[base[(i + j) % len(base)] + i for j in range(n)] for i in range(6)]


@op('poly_identity_refute', 'WS', ('identity',), ('refutation',),
    'Evaluate an unchecked identity at exact rational points; the first difference refutes it.')
def poly_identity_refute(rt, ident):
    if ident['status'] == 'checked': return []
    for point in sample_points(len(ident['data']['vars'])):
        refutation = rt.refute(ident, dict(point=[L.enc(x) for x in point]))
        if refutation is not None: return [refutation]
    return []


@op('poly_identity_mod_refute', 'WS', ('identity',), ('refutation',),
    'Search small integer points modulo 10007 for a nonzero difference, then refute exactly there.')
def poly_identity_mod_refute(rt, ident):
    if ident['status'] == 'checked': return []
    d = ident['data']; names = d['vars']
    try: diff = L.poly_add(L.expand(d['lhs'], names), L.poly_scale(L.expand(d['rhs'], names), -1))
    except (KeyError, ValueError): return []
    m = 10007
    for i in range(40):
        point = [(i * (j + 3) + j) % 17 - 8 for j in range(len(names))]
        value = L.poly_eval(diff, point); rt.budget.use(len(diff))
        if value.numerator % m and value.denominator % m:
            refutation = rt.refute(ident, dict(point=[[x, 1] for x in point]))
            if refutation is not None: return [refutation]
    return []


@op('poly_residual', 'W', ('identity',), ('residual',),
    'Name the nonzero remainder lhs - rhs of an unchecked identity as the open part.')
def poly_residual(rt, ident):
    if ident['status'] == 'checked': return []
    d = ident['data']; names = d['vars']
    diff = L.poly_add(L.expand(d['lhs'], names), L.poly_scale(L.expand(d['rhs'], names), -1))
    if not diff: return []
    return [rt.residual(ident, [L.canonical(L.poly_expr(diff, names))[:4000]], 'lhs - rhs is not zero')]


# ------------------------------------------------------------- fixtures

def _poly(rt, names, expr): return rt.given('poly', dict(vars=names, expr=expr))


def _ident(rt, names, lhs, rhs, check=True):
    obj = rt.propose('identity', identity(names, lhs, rhs))
    if check: rt.check(obj)
    return obj


X, Y = L.var('x'), L.var('y')
SQUARE = (['x', 'y'], L.power(L.add(X, Y), 2), L.add(L.power(X, 2), L.mul(L.num(2), X, Y), L.power(Y, 2)))
CUBE_DIFF = (['x'], L.add(L.power(X, 3), L.num(-1)), L.mul(L.add(X, L.num(-1)), L.add(L.power(X, 2), X, L.num(1))))
CUBIC = L.add(L.power(X, 3), L.mul(L.num(-6), L.power(X, 2)), L.mul(L.num(11), X), L.num(-6))

FIXTURES = {
    'poly_substitute_identity': [lambda rt: [_ident(rt, *SQUARE)]],
    'poly_specialize_identity': [lambda rt: [_ident(rt, *SQUARE)]],
    'poly_differentiate_identity': [lambda rt: [_ident(rt, *SQUARE)]],
    'poly_swap_identity': [lambda rt: [_ident(rt, ['x', 'y'], L.mul(X, L.add(X, Y)), L.add(L.power(X, 2), L.mul(X, Y)))]],
    'poly_sum_identities': [lambda rt: [_ident(rt, *SQUARE), _ident(rt, *CUBE_DIFF)]],
    'poly_product_identities': [lambda rt: [_ident(rt, *SQUARE), _ident(rt, *CUBE_DIFF)]],
    'poly_telescoping_sum': [lambda rt: [_ident(rt, ['n'], L.sub(L.power(L.add(L.var('n'), L.num(1)), 2),
                                                                 L.power(L.var('n'), 2)),
                                                L.add(L.mul(L.num(2), L.var('n')), L.num(1)))]],
    'poly_factor_linear': [lambda rt: [_poly(rt, ['x'], CUBIC)]],
    'poly_gcd': [lambda rt: [_poly(rt, ['x'], CUBIC), _poly(rt, ['x'], L.add(L.power(X, 2), L.num(-1)))]],
    'poly_squarefree': [lambda rt: [_poly(rt, ['x'], L.mul(L.power(L.add(X, L.num(-1)), 2), L.add(X, L.num(2))))]],
    'poly_bezout': [lambda rt: [_poly(rt, ['x'], L.add(L.power(X, 2), L.num(1))), _poly(rt, ['x'], L.add(X, L.num(2)))]],
    'poly_linear_relation': [lambda rt: [_poly(rt, ['x', 'y'], L.power(L.add(X, Y), 2)),
                                         _poly(rt, ['x', 'y'], L.power(L.add(X, L.mul(L.num(-1), Y)), 2)),
                                         _poly(rt, ['x', 'y'], L.mul(X, Y))]],
    'poly_partial_fractions': [lambda rt: [_poly(rt, ['x'], L.add(X, L.num(3))), _poly(rt, ['x'], L.add(X, L.num(-1))),
                                           _poly(rt, ['x'], L.add(X, L.num(2)))]],
    'poly_symmetric_reduction': [lambda rt: [_poly(rt, ['x', 'y'], L.add(L.power(X, 3), L.power(Y, 3)))]],
    'poly_taylor_shift': [lambda rt: [_poly(rt, ['x'], CUBIC)]],
    'poly_square_root': [lambda rt: [_poly(rt, ['x'], L.add(L.mul(L.num(4), L.power(X, 4)), L.mul(L.num(4), L.power(X, 2)),
                                                           L.num(1)))]],
    'poly_identity_refute': [lambda rt: [_ident(rt, ['x', 'y'], L.power(L.add(X, Y), 2),
                                                L.add(L.power(X, 2), L.power(Y, 2)), check=False)]],
    'poly_identity_mod_refute': [lambda rt: [_ident(rt, ['x'], L.power(L.add(X, L.num(1)), 3),
                                                    L.add(L.power(X, 3), L.num(1)), check=False)]],
    'poly_residual': [lambda rt: [_ident(rt, ['x'], L.power(L.add(X, L.num(1)), 2), L.add(L.power(X, 2), L.num(1)),
                                         check=False)]],
}
