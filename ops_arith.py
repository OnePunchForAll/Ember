"""Operators on integer polynomials: roots modulo m, integer roots, non-existence and divisibility.

Roots move between moduli by Hensel lifting and the Chinese remainder theorem;
non-existence modulo m transfers to every multiple of m and to the integers;
divisibility m | f(n) for all n transfers to compositions f(g(n)) and lcms.
The checker decides each claim by evaluation over Z/m or forward differences.
"""
from fractions import Fraction as Q
import importlib.util
from math import gcd
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_arith_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


L = _load('lexicon')
OPS = []
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23)


def op(name, dirs, consumes, produces, summary):
    def wrap(fn):
        OPS.append(dict(name=name, dirs=dirs, consumes=tuple(consumes), produces=tuple(produces), summary=summary,
                        fn=fn, entry=fn.__name__))
        return fn
    return wrap


def claimed(rt, kind, data, parents=(), source=None):
    obj = rt.transfer(kind, data, source, parents) if source is not None else rt.propose(kind, data, parents)
    return [obj] if rt.check(obj) else []


def value(p, x, m=None):
    total = sum(c * x ** i for i, c in enumerate(p)) if m is None else sum(c * pow(x, i, m) for i, c in enumerate(p))
    return total if m is None else total % m


def derivative(p):
    return [i * c for i, c in enumerate(p)][1:]


def expr_of(p):
    return L.univariate_expr([Q(c) for c in p], 'n')


# ------------------------------------------------------------- transfers

@op('arith_hensel_lift', 'SE', ('rootmod',), ('rootmod',),
    'A simple root r mod p (f\'(r) invertible) lifts to r - f(r)/f\'(r) mod p^2.')
def arith_hensel_lift(rt, root):
    if root['status'] != 'checked': return []
    d = root['data']; p, r, f = d['modulus'], d['root'], d['poly']
    if not L.is_prime(p) or value(derivative(f), r, p) == 0 or p * p > 10 ** 18: return []
    lifted = (r - value(f, r, p * p) * pow(value(derivative(f), r, p), -1, p)) % (p * p)
    return claimed(rt, 'rootmod', dict(poly=f, modulus=p * p, root=lifted), source=root)


@op('arith_crt_roots', 'SE', ('rootmod', 'rootmod'), ('rootmod',),
    'Roots modulo coprime m1 and m2 combine to a root modulo m1*m2.')
def arith_crt_roots(rt, first, second):
    a, b = first['data'], second['data']
    if first['status'] != 'checked' or second['status'] != 'checked' or a['poly'] != b['poly']: return []
    if gcd(a['modulus'], b['modulus']) != 1: return []
    r, m = L.crt(a['root'], a['modulus'], b['root'], b['modulus'])
    return claimed(rt, 'rootmod', dict(poly=a['poly'], modulus=m, root=r), (second,), first)


@op('arith_rootmod_reduce', 'SE', ('rootmod',), ('rootmod',), 'A root modulo m is a root modulo every divisor of m.')
def arith_rootmod_reduce(rt, root):
    if root['status'] != 'checked': return []
    d = root['data']; out = []
    for q in L.divisors(d['modulus'])[1:-1][:3]:
        out += claimed(rt, 'rootmod', dict(poly=d['poly'], modulus=q, root=d['root'] % q), source=root)
    return out


@op('arith_rootmod_to_divisibility', 'SE', ('rootmod',), ('divis',),
    'f(r) = 0 mod m gives m | f(r + m*n) for every integer n.')
def arith_rootmod_to_divisibility(rt, root):
    if root['status'] != 'checked': return []
    d = root['data']; m, r = d['modulus'], d['root']
    shifted = L.substitute(expr_of(d['poly']), {'n': L.add(L.mul(L.num(m), L.var('n')), L.num(r))})
    return claimed(rt, 'divis', dict(expr=shifted, modulus=m), source=root)


@op('arith_divisibility_to_rootmod', 'SE', ('divis',), ('rootmod',),
    'If m | f(n) for every n and f has integer coefficients, then 0 is a root of f modulo m.')
def arith_divisibility_to_rootmod(rt, div):
    if div['status'] != 'checked': return []
    d = div['data']; p = L.univariate(d['expr'], 'n')
    if not all(c.denominator == 1 for c in p): return []
    return claimed(rt, 'rootmod', dict(poly=[int(c) for c in p] or [0], modulus=d['modulus'], root=0), source=div)


@op('arith_divisibility_compose', 'SE', ('divis',), ('divis',),
    'm | f(n) for every n gives m | f(g(n)) for integer-valued g; here g(n) = n^2 + 1.')
def arith_divisibility_compose(rt, div):
    if div['status'] != 'checked': return []
    d = div['data']; g = L.add(L.power(L.var('n'), 2), L.num(1))
    return claimed(rt, 'divis', dict(expr=L.substitute(d['expr'], {'n': g}), modulus=d['modulus']), source=div)


@op('arith_divisibility_lcm', 'NS', ('divis', 'divis'), ('divis',),
    'm1 | f and m2 | f for every n give the stronger answer lcm(m1, m2) | f to the same question.')
def arith_divisibility_lcm(rt, first, second):
    a, b = first['data'], second['data']
    if first['status'] != 'checked' or second['status'] != 'checked' or a['expr'] != b['expr']: return []
    m = L.lcm(a['modulus'], b['modulus'])
    if m in (a['modulus'], b['modulus']): return []
    return claimed(rt, 'divis', dict(expr=a['expr'], modulus=m), (first, second))


@op('arith_nosol_to_integers', 'WSE', ('nosolmod',), ('nosol',),
    'No root modulo m means no integer root, since an integer root reduces to one modulo m.')
def arith_nosol_to_integers(rt, none):
    if none['status'] != 'checked': return []
    return claimed(rt, 'nosol', dict(poly=none['data']['poly'], modulus=none['data']['modulus']), source=none)


@op('arith_nosol_lift_modulus', 'WSE', ('nosolmod',), ('nosolmod',),
    'No root modulo m means no root modulo any multiple of m.')
def arith_nosol_lift_modulus(rt, none):
    if none['status'] != 'checked': return []
    d = none['data']
    if d['modulus'] * 3 > 10 ** 6: return []
    return claimed(rt, 'nosolmod', dict(poly=d['poly'], modulus=d['modulus'] * 3), source=none)


# ------------------------------------------------------------- proposals and searches

@op('arith_root_search', 'NS', ('diophantine',), ('rootmod',), 'Exhaust residues modulo small primes for roots.')
def arith_root_search(rt, question):
    f = question['data']['poly']; out = []
    for p in PRIMES:
        rt.budget.use(p * len(f))
        r = next((x for x in range(p) if value(f, x, p) == 0), None)
        if r is not None: out += claimed(rt, 'rootmod', dict(poly=f, modulus=p, root=r), (question,))
        if len(out) >= 3: break
    return out


@op('arith_nosol_search', 'NWS', ('diophantine',), ('nosolmod',),
    'Find a modulus up to 64 where f has no root by exhaustive evaluation.')
def arith_nosol_search(rt, question):
    f = question['data']['poly']
    for m in range(2, 65):
        rt.budget.use(m * len(f))
        if all(value(f, x, m) for x in range(m)):
            return claimed(rt, 'nosolmod', dict(poly=f, modulus=m), (question,))
    return []


@op('arith_legendre_nosol', 'NWS', ('diophantine',), ('nosolmod',),
    'For x^2 - a, Euler\'s criterion finds a prime where a is a nonresidue.')
def arith_legendre_nosol(rt, question):
    f = question['data']['poly']
    if len(f) != 3 or f[1] != 0 or f[2] != 1: return []
    a = -f[0]
    for p in PRIMES[1:]:
        rt.budget.use(p.bit_length())
        if a % p and L.legendre(a, p) == -1:
            return claimed(rt, 'nosolmod', dict(poly=f, modulus=p), (question,))
    return []


@op('arith_integer_root_search', 'NS', ('diophantine',), ('introot',),
    'Test the divisors of the constant term (rational root theorem) as integer roots.')
def arith_integer_root_search(rt, question):
    f = question['data']['poly']; out = []
    if f[0] == 0: return claimed(rt, 'introot', dict(poly=f, root=0), (question,))
    for dvs in L.divisors(abs(f[0]))[:64]:
        for x in (dvs, -dvs):
            rt.budget.use(len(f))
            if value(f, x) == 0: out += claimed(rt, 'introot', dict(poly=f, root=x), (question,))
    return out


@op('arith_fixed_divisor', 'NS', ('poly',), ('divis',),
    'The gcd of the forward differences at 0 is the largest m with m | f(n) for every n.')
def arith_fixed_divisor(rt, poly):
    if poly['data']['vars'] != ['n']: return []
    p = L.univariate(poly['data']['expr'], 'n'); values = [L.peval(p, n) for n in range(max(1, len(p)))]
    if not all(v.denominator == 1 for v in values): return []
    diffs = [int(v) for v in values]; g = 0
    while diffs:
        g = gcd(g, diffs[0]); diffs = [y - x for x, y in zip(diffs, diffs[1:])]
    if g < 2: return []
    return claimed(rt, 'divis', dict(expr=poly['data']['expr'], modulus=g), (poly,))


# ------------------------------------------------------------- refutations

@op('arith_divisibility_refute', 'WS', ('divis',), ('refutation',), 'Find n with m not dividing f(n).')
def arith_divisibility_refute(rt, div):
    if div['status'] == 'checked': return []
    for n in range(0, 200):
        refutation = rt.refute(div, dict(n=n))
        if refutation is not None: return [refutation]
    return []


@op('arith_root_refute', 'WS', ('rootmod',), ('refutation',), 'Evaluate a claimed root; a nonzero residue refutes it.')
def arith_root_refute(rt, root):
    if root['status'] == 'checked': return []
    refutation = rt.refute(root, {})
    return [refutation] if refutation is not None else []


@op('arith_integer_root_refute', 'WS', ('introot',), ('refutation',), 'Evaluate a claimed integer root exactly.')
def arith_integer_root_refute(rt, root):
    if root['status'] == 'checked': return []
    refutation = rt.refute(root, {})
    return [refutation] if refutation is not None else []


@op('arith_nosol_refute', 'WS', ('nosolmod',), ('refutation',),
    'Exhaust residues for a root; one root refutes a claimed modular non-existence.')
def arith_nosol_refute(rt, none):
    if none['status'] == 'checked': return []
    d = none['data']
    for x in range(min(d['modulus'], 100000)):
        rt.budget.use(len(d['poly']))
        if value(d['poly'], x, d['modulus']) == 0:
            refutation = rt.refute(none, dict(root=x))
            return [refutation] if refutation is not None else []
    return []


# ------------------------------------------------------------- fixtures

def _checked(rt, kind, data):
    obj = rt.propose(kind, data); rt.check(obj); return obj


N = L.var('n')
FIXTURES = {
    'arith_hensel_lift': [lambda rt: [_checked(rt, 'rootmod', dict(poly=[-2, 0, 1], modulus=7, root=3))]],
    'arith_crt_roots': [lambda rt: [_checked(rt, 'rootmod', dict(poly=[-2, 0, 1], modulus=7, root=3)),
                                    _checked(rt, 'rootmod', dict(poly=[-2, 0, 1], modulus=17, root=6))]],
    'arith_rootmod_reduce': [lambda rt: [_checked(rt, 'rootmod', dict(poly=[-2, 0, 1], modulus=119, root=45))]],
    'arith_rootmod_to_divisibility': [lambda rt: [_checked(rt, 'rootmod', dict(poly=[-2, 0, 1], modulus=7, root=3))]],
    'arith_divisibility_to_rootmod': [lambda rt: [_checked(rt, 'divis', dict(expr=L.mul(N, L.add(N, L.num(1))), modulus=2))]],
    'arith_divisibility_compose': [lambda rt: [_checked(rt, 'divis', dict(expr=L.mul(N, L.add(N, L.num(1))), modulus=2))]],
    'arith_divisibility_lcm': [lambda rt: [_checked(rt, 'divis', dict(expr=L.sub(L.power(N, 3), N), modulus=2)),
                                           _checked(rt, 'divis', dict(expr=L.sub(L.power(N, 3), N), modulus=3))]],
    'arith_nosol_to_integers': [lambda rt: [_checked(rt, 'nosolmod', dict(poly=[-3, 0, 1], modulus=5))]],
    'arith_nosol_lift_modulus': [lambda rt: [_checked(rt, 'nosolmod', dict(poly=[-3, 0, 1], modulus=5))]],
    'arith_root_search': [lambda rt: [rt.given('diophantine', dict(poly=[-2, 0, 1]))]],
    'arith_nosol_search': [lambda rt: [rt.given('diophantine', dict(poly=[-3, 0, 1]))]],
    'arith_legendre_nosol': [lambda rt: [rt.given('diophantine', dict(poly=[-3, 0, 1]))]],
    'arith_integer_root_search': [lambda rt: [rt.given('diophantine', dict(poly=[-6, 11, -6, 1]))]],
    'arith_fixed_divisor': [lambda rt: [rt.given('poly', dict(vars=['n'], expr=L.sub(L.power(N, 3), N)))]],
    'arith_divisibility_refute': [lambda rt: [rt.propose('divis', dict(expr=L.power(N, 2), modulus=2))]],
    'arith_root_refute': [lambda rt: [rt.propose('rootmod', dict(poly=[-2, 0, 1], modulus=7, root=2))]],
    'arith_integer_root_refute': [lambda rt: [rt.propose('introot', dict(poly=[-2, 0, 1], root=1))]],
    'arith_nosol_refute': [lambda rt: [rt.propose('nosolmod', dict(poly=[-2, 0, 1], modulus=7))]],
}
