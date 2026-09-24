"""Ember's typed mathematical language: objects, operator registry and runtime.

An object is a kind plus exact JSON data. Question objects state what is being
asked; claim objects state an answer that the separate checker in
lexicon_check.py must admit. Operators in the ops_*.py modules consume and
produce objects. Each output is created through one runtime event, and every
event carries a checkable precondition:

- propose (N): a new candidate claim or object that did not exist before;
- refute (W): a refutation, an orbit exclusion, a modular non-existence proof or
  a cycle, each counted only once the checker admits it, or a residual that names
  the open part of a question;
- check (S): the checker admits a claim against the question stated in its data;
- transfer (E): a claim about another question derived from a checked claim.

The move bench runs every operator and requires the directions it declares to
equal the events it actually produced. Directions and scores schedule work; only
the checker establishes a claim, and a checked claim holds only in the scope the
checker states.
"""
from fractions import Fraction
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path

Q = Fraction
OP_MODULES = ('ops_seq', 'ops_poly', 'ops_orbit', 'ops_egypt', 'ops_arith', 'ops_word', 'ops_matrix', 'ops_collatz')
DIRECTIONS = ('N', 'W', 'S', 'E')
# Checked objects of these kinds refute an existence or reachability claim.
EVIDENCE_KINDS = ('refutation', 'exclusion', 'nosolmod', 'nosol', 'cycle', 'nofamily')
RESIDUAL_KINDS = ('residual',)
MAX_OBJECT_BYTES = 262_144


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def enc(q):
    q = Q(q)
    return [q.numerator, q.denominator]


def dec(pair):
    if type(pair) is int: return Q(pair)
    if type(pair) is not list or len(pair) != 2 or type(pair[0]) is not int or type(pair[1]) is not int or pair[1] == 0:
        raise ValueError('rational pair')
    return Q(pair[0], pair[1])


# ------------------------------------------------------------- univariate polynomials (low degree first)

def ptrim(a):
    a = [Q(x) for x in a]
    while a and a[-1] == 0: a.pop()
    return a


def padd(a, b):
    n = max(len(a), len(b))
    return ptrim([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(n)])


def psub(a, b):
    return padd(a, [-x for x in b])


def pscale(a, c):
    return ptrim([x * c for x in a])


def pmul(a, b):
    if not a or not b: return []
    out = [Q(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b): out[i + j] += x * y
    return ptrim(out)


def ppow(a, k):
    out = [Q(1)]
    for _ in range(k): out = pmul(out, a)
    return out


def peval(a, x):
    value = Q(0)
    for c in reversed(a): value = value * x + c
    return value


def pdivmod(a, b):
    a = ptrim(a); b = ptrim(b)
    if not b: raise ZeroDivisionError('polynomial division by zero')
    quotient = [Q(0)] * max(1, len(a) - len(b) + 1)
    while len(a) >= len(b) and a:
        c = a[-1] / b[-1]; shift = len(a) - len(b); quotient[shift] = c
        for i, y in enumerate(b): a[i + shift] -= c * y
        a = ptrim(a)
    return ptrim(quotient), a


def pexact(a, b):
    q, r = pdivmod(a, b)
    return q if not r else None


def pgcd(a, b):
    a, b = ptrim(a), ptrim(b)
    while b: a, b = b, pdivmod(a, b)[1]
    return pscale(a, 1 / a[-1]) if a else []


def pderiv(a):
    return ptrim([i * a[i] for i in range(1, len(a))])


def pcompose(a, b):
    out = []
    for c in reversed(a): out = padd(pmul(out, b), [c])
    return out


def pshift(a, c):
    return pcompose(a, [Q(c), Q(1)])


def integer_valued(a):
    """A polynomial is integer valued on Z iff it is so at deg+1 consecutive integers."""
    return all(peval(a, k).denominator == 1 for k in range(max(1, len(a))))


def nonnegative_from(a, start):
    """All coefficients of a(start+t) nonnegative with positive constant: a(k)>0 for k>=start."""
    b = pshift(a, start)
    return bool(b) and b[0] > 0 and all(c >= 0 for c in b)


def rational_roots(a):
    """Rational roots of a polynomial with rational coefficients."""
    a = ptrim(a)
    if not a: return []
    scale = 1
    for c in a: scale = scale * c.denominator // gcd(scale, c.denominator)
    ints = [int(c * scale) for c in a]
    roots = set()
    while ints and ints[0] == 0: roots.add(Q(0)); ints = ints[1:]
    if len(ints) <= 1: return sorted(roots)
    for p in divisors(abs(ints[0])):
        for q in divisors(abs(ints[-1])):
            for sign in (1, -1):
                r = Q(sign * p, q)
                if peval([Q(c) for c in ints], r) == 0: roots.add(r)
    return sorted(roots)


# ------------------------------------------------------------- expression trees and multivariate polynomials

def num(q):
    q = Q(q)
    return ['num', q.numerator, q.denominator]


def var(name):
    return ['var', name]


def add(*items):
    return ['add', *items]


def mul(*items):
    return ['mul', *items]


def sub(a, b):
    return ['sub', a, b]


def power(a, k):
    return ['pow', a, k]


def vars_of(e):
    out = set()

    def walk(t):
        if t[0] == 'var': out.add(t[1])
        elif t[0] in ('add', 'mul', 'sub', 'neg'):
            for x in t[1:]: walk(x)
        elif t[0] == 'pow': walk(t[1])
    walk(e)
    return out


def substitute(e, mapping):
    """Replace variables by expressions."""
    if e[0] == 'var': return mapping.get(e[1], e)
    if e[0] == 'num': return e
    if e[0] == 'pow': return ['pow', substitute(e[1], mapping), e[2]]
    return [e[0], *(substitute(x, mapping) for x in e[1:])]


def derivative(e, name):
    """Symbolic derivative of an expression tree."""
    head = e[0]
    if head == 'num': return num(0)
    if head == 'var': return num(1 if e[1] == name else 0)
    if head == 'add': return ['add', *(derivative(x, name) for x in e[1:])]
    if head == 'sub': return ['sub', derivative(e[1], name), derivative(e[2], name)]
    if head == 'neg': return ['neg', derivative(e[1], name)]
    if head == 'pow':
        k = e[2]
        if k == 0: return num(0)
        return ['mul', num(k), ['pow', e[1], k - 1], derivative(e[1], name)]
    if head == 'mul':
        items = e[1:]
        return ['add', *(['mul', *(derivative(x, name) if j == i else x for j, x in enumerate(items))]
                         for i in range(len(items)))]
    raise ValueError('expression head')


def expand(e, names, budget=None):
    """Exact sparse polynomial {exponents: Fraction} of an expression tree."""
    n = len(names); index = {name: i for i, name in enumerate(names)}

    def charge(k=1):
        if budget is not None: budget.use(k)

    def walk(t):
        charge()
        head = t[0]
        if head == 'num': return {(0,) * n: Q(t[1], t[2])} if t[1] else {}
        if head == 'var':
            exponents = [0] * n; exponents[index[t[1]]] = 1
            return {tuple(exponents): Q(1)}
        if head == 'add':
            out = {}
            for x in t[1:]: out = poly_add(out, walk(x), charge)
            return out
        if head == 'sub': return poly_add(walk(t[1]), poly_scale(walk(t[2]), -1), charge)
        if head == 'neg': return poly_scale(walk(t[1]), -1)
        if head == 'mul':
            out = {(0,) * n: Q(1)}
            for x in t[1:]: out = poly_mul(out, walk(x), charge)
            return out
        if head == 'pow':
            base = walk(t[1]); out = {(0,) * n: Q(1)}
            for _ in range(t[2]): out = poly_mul(out, base, charge)
            return out
        raise ValueError('expression head')
    return walk(e)


def poly_add(a, b, charge=lambda k=1: None):
    out = dict(a)
    for key, value in b.items():
        charge(); total = out.get(key, 0) + value
        if total: out[key] = total
        else: out.pop(key, None)
    return out


def poly_scale(a, c):
    return {key: value * c for key, value in a.items()} if c else {}


def poly_mul(a, b, charge=lambda k=1: None):
    out = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            charge(); key = tuple(x + y for x, y in zip(ka, kb)); total = out.get(key, 0) + va * vb
            if total: out[key] = total
            else: out.pop(key, None)
    return out


def poly_expr(poly, names):
    """Expression tree of a sparse polynomial."""
    terms = []
    for exponents, c in sorted(poly.items()):
        factors = [num(c)] + [['pow', var(name), k] for name, k in zip(names, exponents) if k]
        terms.append(['mul', *factors])
    return ['add', *terms] if terms else num(0)


def poly_eval(poly, point):
    total = Q(0)
    for exponents, c in poly.items():
        term = Q(c)
        for x, k in zip(point, exponents):
            if k: term *= Q(x) ** k
        total += term
    return total


def univariate(e, name, budget=None):
    """Coefficient list of an expression in one variable."""
    poly = expand(e, [name], budget)
    if not poly: return []
    out = [Q(0)] * (max(k[0] for k in poly) + 1)
    for (k,), c in poly.items(): out[k] = c
    return ptrim(out)


def univariate_expr(coefficients, name):
    return poly_expr({(i,): Q(c) for i, c in enumerate(coefficients) if c}, [name])


# ------------------------------------------------------------- integers

def divisors(v):
    v = abs(v)
    if v == 0: return [1]
    small, large = [], []
    i = 1
    while i * i <= v:
        if v % i == 0:
            small.append(i)
            if i * i != v: large.append(v // i)
        i += 1
    return small + large[::-1]


def square_divisors(v):
    """Sorted divisors of v*v, generated from the factorization of v."""
    out = [1]
    for p, k in factor(v).items():
        out = [d * p ** e for d in out for e in range(2 * k + 1)]
    return sorted(out)


def factor(v):
    """Prime factorization by trial division, as {prime: exponent}."""
    v = abs(v); out = {}; p = 2
    while p * p <= v:
        while v % p == 0: out[p] = out.get(p, 0) + 1; v //= p
        p += 1 if p == 2 else 2
    if v > 1: out[v] = out.get(v, 0) + 1
    return out


def is_prime(v):
    return v >= 2 and factor(v) == {v: 1}


def legendre(a, p):
    a %= p
    if a == 0: return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def lcm(a, b):
    return a // gcd(a, b) * b


def crt(r1, m1, r2, m2):
    """Common residue of r1 mod m1 and r2 mod m2, or None."""
    g = gcd(m1, m2)
    if (r2 - r1) % g: return None
    m = lcm(m1, m2); t = ((r2 - r1) // g) * pow(m1 // g, -1, m2 // g) % (m2 // g)
    return (r1 + m1 * t) % m, m


# ------------------------------------------------------------- exact linear algebra

def solve_linear(rows, rhs):
    """One exact solution of rows*x = rhs (free variables zero), or None."""
    m = [list(map(Q, row)) + [Q(b)] for row, b in zip(rows, rhs)]
    width = len(rows[0]) if rows else 0; pivots = []; r = 0
    for c in range(width):
        p = next((i for i in range(r, len(m)) if m[i][c]), None)
        if p is None: continue
        m[r], m[p] = m[p], m[r]; inv = 1 / m[r][c]; m[r] = [x * inv for x in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c]:
                f = m[i][c]; m[i] = [x - f * y for x, y in zip(m[i], m[r])]
        pivots.append(c); r += 1
    if any(all(x == 0 for x in row[:-1]) and row[-1] for row in m): return None
    solution = [Q(0)] * width
    for i, c in enumerate(pivots): solution[c] = m[i][-1]
    return solution


def nullspace(rows, width):
    """A basis of {x: rows*x=0}."""
    m = [list(map(Q, row)) for row in rows]; pivots = []; r = 0
    for c in range(width):
        p = next((i for i in range(r, len(m)) if m[i][c]), None)
        if p is None: continue
        m[r], m[p] = m[p], m[r]; inv = 1 / m[r][c]; m[r] = [x * inv for x in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c]:
                f = m[i][c]; m[i] = [x - f * y for x, y in zip(m[i], m[r])]
        pivots.append(c); r += 1
    basis = []
    for free in (c for c in range(width) if c not in pivots):
        v = [Q(0)] * width; v[free] = Q(1)
        for i, c in enumerate(pivots): v[c] = -m[i][free]
        basis.append(v)
    return basis


def charpoly(M):
    """Characteristic polynomial det(xI-M), low degree first (Faddeev-LeVerrier)."""
    n = len(M); A = [[Q(x) for x in row] for row in M]
    coefficients = [Q(1)]; current = [[Q(0)] * n for _ in range(n)]
    for k in range(1, n + 1):
        for i in range(n): current[i][i] += coefficients[-1]
        current = [[sum(A[i][t] * current[t][j] for t in range(n)) for j in range(n)] for i in range(n)]
        c = -sum(current[i][i] for i in range(n)) / k
        coefficients.append(c)
    return list(reversed(coefficients))  # coefficients[k] multiplies x**(n-k); reversed gives low first


def berlekamp_massey(terms):
    """Shortest linear recurrence a(n+r)=sum c_j a(n+j) generating the terms, as c (low first)."""
    s = [Q(x) for x in terms]
    C = [Q(1)]; B = [Q(1)]; L = 0; m = 1; b = Q(1)
    for n in range(len(s)):
        C = C + [Q(0)] * max(0, L + 1 - len(C))
        d = s[n] + sum(C[i] * s[n - i] for i in range(1, L + 1))
        if d == 0: m += 1; continue
        T = list(C); coef = d / b
        C = C + [Q(0)] * max(0, len(B) + m - len(C))
        for i, x in enumerate(B): C[i + m] -= coef * x
        if 2 * L <= n: L = n + 1 - L; B = T; b = d; m = 1
        else: m += 1
    C = C + [Q(0)] * max(0, L + 1 - len(C))
    return [-C[L - j] for j in range(L)]


# ------------------------------------------------------------- producer-side sequence evaluation

def lrs_terms(coefficients, initial, count):
    c = [Q(x) for x in coefficients]; out = [Q(x) for x in initial[:count]]; r = len(c)
    while len(out) < count:
        out.append(sum(cj * out[len(out) - r + j] for j, cj in enumerate(c)) if r else Q(0))
    return out[:count]


def word_matrix(patterns):
    """Prefix automaton of binary words avoiding every pattern."""
    prefixes = {''}
    for w in patterns:
        for k in range(1, len(w)): prefixes.add(w[:k])
    states = sorted(prefixes, key=lambda t: (len(t), t)); M = [[0] * len(states) for _ in states]
    for i, state in enumerate(states):
        for letter in '01':
            extended = state + letter
            if any(w in extended for w in patterns): continue
            best = max((p for p in states if extended.endswith(p)), key=len)
            M[i][states.index(best)] += 1
    return M, [1] + [0] * (len(states) - 1), [1] * len(states)


def terms(sd, count):
    """First terms of a sequence definition (producer copy; the checker has its own)."""
    kind = sd['type']
    if kind == 'lrs': return lrs_terms([dec(x) for x in sd['coefficients']], [dec(x) for x in sd['initial']], count)
    if kind in ('matrix', 'words'):
        M, u, v = ((sd['matrix'], sd['initial'], sd['terminal']) if kind == 'matrix' else word_matrix(sd['patterns']))
        row = [Q(x) for x in u]; out = []
        for _ in range(count):
            out.append(sum(x * Q(y) for x, y in zip(row, v)))
            row = [sum(row[i] * M[i][j] for i in range(len(row))) for j in range(len(row))]
        return out
    if kind == 'poly': return [peval([dec(x) for x in sd['coefficients']], n) for n in range(count)]
    if kind == 'terms': return [dec(x) for x in sd['values'][:count]]
    if kind == 'expsum': return [sum(dec(c) * dec(q) ** n for c, q in sd['terms']) for n in range(count)]
    if kind == 'transform': return transform_terms(sd, count)
    raise ValueError('sequence definition')


def transform_terms(sd, count):
    op, args, params = sd['op'], sd['args'], sd.get('params', {})
    if op == 'shift': return terms(args[0], count + params['s'])[params['s']:]
    if op == 'scale': return [dec(params['c']) * x for x in terms(args[0], count)]
    if op == 'sum': return [x + y for x, y in zip(terms(args[0], count), terms(args[1], count))]
    if op == 'product': return [x * y for x, y in zip(terms(args[0], count), terms(args[1], count))]
    if op == 'partial_sum':
        out, total = [], Q(0)
        for x in terms(args[0], count): total += x; out.append(total)
        return out
    if op == 'difference':
        a = terms(args[0], count + 1)
        return [a[i + 1] - a[i] for i in range(count)]
    if op == 'decimate':
        t, j = params['t'], params['j']; a = terms(args[0], t * (count - 1) + j + 1)
        return [a[t * n + j] for n in range(count)]
    if op in ('binomial', 'inverse_binomial'):
        a = terms(args[0], count); sign = -1 if op == 'inverse_binomial' else 1
        return [sum(Q(binomial(n, k)) * (sign ** (n - k)) * a[k] for k in range(n + 1)) for n in range(count)]
    if op == 'interleave':
        a = terms(args[0], (count + 1) // 2 + 1); b = terms(args[1], count // 2 + 1)
        return [a[n // 2] if n % 2 == 0 else b[n // 2] for n in range(count)]
    if op == 'twist':
        c = dec(params['c']); return [c ** n * x for n, x in enumerate(terms(args[0], count))]
    if op == 'polymul':
        p = [dec(x) for x in params['p']]; return [peval(p, n) * x for n, x in enumerate(terms(args[0], count))]
    if op == 'convolution':
        a, b = terms(args[0], count), terms(args[1], count)
        return [sum(a[k] * b[n - k] for k in range(n + 1)) for n in range(count)]
    if op == 'reciprocal':
        a = terms(args[0], count); out = []
        for n in range(count):
            out.append(((1 if n == 0 else 0) - sum(a[k] * out[n - k] for k in range(1, n + 1))) / a[0])
        return out
    if op == 'aerate':
        t = params['t']; a = terms(args[0], count // t + 1)
        return [a[n // t] if n % t == 0 else Q(0) for n in range(count)]
    raise ValueError('sequence transform')


def binomial(n, k):
    if k < 0 or k > n: return 0
    out = 1
    for i in range(1, k + 1): out = out * (n - k + i) // i
    return out


# ------------------------------------------------------------- runtime

class Runtime:
    """Creates objects through checkable events and keeps the per-call event log."""

    def __init__(self, checker, budget, workspace=None):
        self.checker = checker; self.budget = budget
        self.objects = workspace if workspace is not None else {}
        self.events = []

    def _make(self, kind, data, parents, status):
        data = json.loads(canonical(data))
        if len(canonical(data)) > MAX_OBJECT_BYTES: raise ValueError('object exceeds 256 KiB')
        question = self.checker.question(kind, data)
        identity = digest(dict(kind=kind, data=data))
        existing = self.objects.get(identity)
        if existing is not None: return existing, False
        obj = dict(id=identity, kind=kind, data=data, question=question, status=status,
                   parents=[p['id'] for p in parents])
        self.objects[identity] = obj
        return obj, True

    def given(self, kind, data, status='given'):
        """A root question or an imported object; status 'checked' only through check()."""
        obj, _ = self._make(kind, data, (), status if status == 'given' else 'given')
        return obj

    def propose(self, kind, data, parents=(), source=None):
        """N: a new candidate. With a checked source about another question it is also a transfer."""
        obj, fresh = self._make(kind, data, parents, 'candidate')
        if fresh:
            self.events.append(('N', obj['id']))
            if source is not None and source.get('status') == 'checked' and source['question'] != obj['question']:
                self.events.append(('E', obj['id']))
        return obj

    def transfer(self, kind, data, source, parents=()):
        """E: a claim about another question derived from a checked claim by a stated rule."""
        if source.get('status') != 'checked': raise ValueError('transfer source must be checked')
        obj, fresh = self._make(kind, data, (source,) + tuple(parents), 'candidate')
        if fresh and obj['question'] != source['question']: self.events.append(('E', obj['id']))
        return obj

    def check(self, obj):
        """S: admit a claim through the separate checker; returns True only on admission."""
        if obj['status'] == 'checked': return True
        try: result = self.checker.check(obj['kind'], obj['data'], self.budget)
        except self.checker.Invalid as exc:
            obj.setdefault('rejections', []).append(str(exc)[:200]); return False
        obj['status'] = 'checked'; obj['evidence'] = result
        self.events.append(('S', obj['id']))
        if obj['kind'] in EVIDENCE_KINDS: self.events.append(('W', obj['id']))
        return True

    def refute(self, claim, witness, kind='refutation'):
        """W: a refutation exists only if the checker admits it against the claim's own data."""
        data = dict(claim=dict(kind=claim['kind'], data=claim['data']), witness=witness)
        obj, fresh = self._make(kind, data, (claim,), 'candidate')
        if not fresh and obj['status'] == 'checked': return obj
        try: result = self.checker.check(kind, data, self.budget)
        except self.checker.Invalid:
            self.objects.pop(obj['id'], None); return None
        obj['status'] = 'checked'; obj['evidence'] = result; claim['status'] = 'refuted'
        self.events.append(('W', obj['id'])); self.events.append(('S', obj['id']))
        return obj

    def residual(self, of, items, note):
        """W: name the open part of a question; a residual is bookkeeping, never a claim."""
        obj, fresh = self._make('residual', dict(of=of['id'], question=of['question'], items=items, note=note),
                                (of,), 'open')
        if fresh: self.events.append(('W', obj['id']))
        return obj


def load_ops():
    """Collect every operator from the ops modules, in module order."""
    root = Path(__file__).resolve().parent; registry = {}; fixtures = {}
    for name in OP_MODULES:
        spec = importlib.util.spec_from_file_location('ember_lexicon_' + name, root / (name + '.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for spec_row in module.OPS:
            if spec_row['name'] in registry: raise ValueError('duplicate operator ' + spec_row['name'])
            registry[spec_row['name']] = dict(spec_row, module=name + '.py')
        fixtures.update(getattr(module, 'FIXTURES', {}))
        for key, value in getattr(module, 'GOALS', {}).items(): registry.setdefault('_goals', {})[key] = value
    return registry, fixtures


def registry_table():
    """Operators without callables, for reports."""
    registry, _ = load_ops()
    return [dict(name=k, dirs=v['dirs'], consumes=list(v['consumes']), produces=list(v['produces']),
                 module=v['module'], summary=v['summary']) for k, v in registry.items() if not k.startswith('_')]
