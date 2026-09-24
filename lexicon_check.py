"""Separate checker for Ember's typed language; it imports no producer or operator code.

Every claim is checked against the question stated in its own data, with exact
rational arithmetic and charged work. Sequence laws use an agreement bound: a
definition whose terms satisfy a known recurrence of order at most D and a
claimed recurrence of order R that agree on D+R consecutive terms agree for
every index, because their difference satisfies the product recurrence of order
D+R. Polynomial identities are expanded exactly. Unit-fraction families are
polynomial identities in the class parameter k with integer values at deg+1
consecutive points and nonnegative shifted coefficients. Orbit exclusions use
invariants, semi-invariants, finite modular quotients, closed subsystems,
iterates, conjugacies or inverse maps, each rechecked here.
"""
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path


class Invalid(ValueError): pass
class Limit(RuntimeError): pass


MAX_TERMS = 8192
MAX_BITS = 60000
MAX_STEPS = 4096
MAX_MODULAR_STATES = 1 << 20
MAX_RANGE = 2_000_000
QUESTION_KINDS = ('seq', 'words', 'orbit', 'map', 'poly', 'esq', 'eclass', 'en', 'count', 'diophantine', 'modq',
                  'cmap', 'cclass', 'cproblem', 'template', 'residual', 'matrixq')


def need(condition, reason):
    if not condition: raise Invalid(reason)


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_lexicon_check_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


_recurrence = _load('recurrence_check')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def rat(x):
    if type(x) is int: return Q(x)
    need(type(x) is list and len(x) == 2 and all(type(v) is int for v in x) and x[1] != 0, 'rational pair')
    q = Q(x[0], x[1])
    need(max(abs(q.numerator), q.denominator).bit_length() <= MAX_BITS, 'rational bit bound')
    return q


def small(q):
    if max(abs(q.numerator), q.denominator).bit_length() > MAX_BITS: raise Limit('exact value exceeds bit bound')
    return q


def integer(x, low=None, high=None):
    need(type(x) is int and (low is None or x >= low) and (high is None or x <= high), 'integer field')
    return x


# ------------------------------------------------------------- expressions

def names_of(vars_):
    need(type(vars_) is list and 1 <= len(vars_) <= 8 and len(set(vars_)) == len(vars_)
         and all(type(v) is str and v.isidentifier() for v in vars_), 'variable list')
    return vars_


def poly(e, names, budget, depth=0):
    """Exact expansion {exponents: Q}; an independent copy of the producer's expansion."""
    budget.use()
    need(type(e) is list and e and type(e[0]) is str and depth <= 256, 'expression node')
    n = len(names); head = e[0]
    if head == 'num':
        need(len(e) == 3, 'number node'); value = rat([e[1], e[2]])
        return {(0,) * n: value} if value else {}
    if head == 'var':
        need(len(e) == 2 and e[1] in names, 'unknown variable')
        exponents = [0] * n; exponents[names.index(e[1])] = 1
        return {tuple(exponents): Q(1)}
    if head in ('add', 'mul'):
        out = {} if head == 'add' else {(0,) * n: Q(1)}
        for item in e[1:]:
            part = poly(item, names, budget, depth + 1)
            out = _padd(out, part, budget) if head == 'add' else _pmul(out, part, budget)
        return out
    if head == 'sub':
        need(len(e) == 3, 'subtraction node')
        return _padd(poly(e[1], names, budget, depth + 1), {k: -v for k, v in poly(e[2], names, budget, depth + 1).items()},
                     budget)
    if head == 'neg':
        need(len(e) == 2, 'negation node')
        return {k: -v for k, v in poly(e[1], names, budget, depth + 1).items()}
    if head == 'pow':
        need(len(e) == 3 and type(e[2]) is int and 0 <= e[2] <= 16, 'power node')
        base = poly(e[1], names, budget, depth + 1); out = {(0,) * n: Q(1)}
        for _ in range(e[2]): out = _pmul(out, base, budget)
        return out
    raise Invalid('expression head')


def _padd(a, b, budget):
    out = dict(a)
    for key, value in b.items():
        budget.use(); total = out.get(key, 0) + value
        if total: out[key] = total
        else: out.pop(key, None)
    return out


def _pmul(a, b, budget):
    out = {}
    if len(a) * len(b) > 400_000: raise Limit('polynomial product size')
    for ka, va in a.items():
        for kb, vb in b.items():
            budget.use(); key = tuple(x + y for x, y in zip(ka, kb))
            if sum(key) > 64: raise Limit('polynomial degree bound')
            total = out.get(key, 0) + va * vb
            if total: out[key] = small(total)
            else: out.pop(key, None)
    return out


def evaluate(e, names, point, budget):
    total = Q(0)
    for exponents, c in poly(e, names, budget).items():
        term = c
        for x, k in zip(point, exponents):
            if k: budget.use(k); term *= x ** k
        total += term
    return small(total)


def substituted(e, mapping):
    """Replace variables by expressions; checker copy."""
    if e[0] == 'var': return mapping.get(e[1], e)
    if e[0] == 'num': return e
    if e[0] == 'pow': return ['pow', substituted(e[1], mapping), e[2]]
    return [e[0], *(substituted(x, mapping) for x in e[1:])]


def map_of(data):
    names = names_of(data.get('vars'))
    components = data.get('map')
    need(type(components) is list and len(components) == len(names), 'map components')
    return names, components


def point_of(raw, names):
    need(type(raw) is list and len(raw) == len(names), 'point dimension')
    return [rat(x) for x in raw]


# ------------------------------------------------------------- univariate helpers (checker copies)

def u_trim(a):
    a = list(a)
    while a and a[-1] == 0: a.pop()
    return a


def u_eval(a, x):
    value = Q(0)
    for c in reversed(a): value = value * x + c
    return value


def u_poly(e, name, budget):
    p = poly(e, [name], budget)
    if not p: return []
    out = [Q(0)] * (max(k[0] for k in p) + 1)
    for (k,), c in p.items(): out[k] = c
    return u_trim(out)


def u_shift(a, c):
    """a(x+c) by repeated synthetic expansion."""
    out = []
    for coefficient in reversed(a):
        out = [Q(0)] + out  # multiply by x
        for i in range(len(out) - 1): out[i] += c * out[i + 1]
        out[0] += coefficient
    return u_trim(out)


def binomial(n, k):
    if k < 0 or k > n: return 0
    out = 1
    for i in range(1, k + 1): out = out * (n - k + i) // i
    return out


# ------------------------------------------------------------- sequence definitions

def seq_def(sd, depth=0):
    need(type(sd) is dict and type(sd.get('type')) is str and depth <= 8, 'sequence definition')
    return sd


def annihilator(sd, budget, depth=0):
    """Order bound D: the definition satisfies a monic linear recurrence of order <= D for every index."""
    seq_def(sd, depth); kind = sd['type']; budget.use()
    if kind == 'lrs':
        need(set(sd) == {'type', 'coefficients', 'initial'} and type(sd['coefficients']) is list
             and len(sd['coefficients']) <= 64 and type(sd['initial']) is list
             and len(sd['initial']) == len(sd['coefficients']), 'linear recurrence definition')
        return len(sd['coefficients'])
    if kind == 'matrix':
        need(set(sd) == {'type', 'matrix', 'initial', 'terminal'}, 'matrix definition fields')
        M, u, v = sd['matrix'], sd['initial'], sd['terminal']
        need(type(M) is list and 1 <= len(M) <= 64 and all(type(r) is list and len(r) == len(M) for r in M)
             and type(u) is list and type(v) is list and len(u) == len(v) == len(M)
             and all(type(x) is int and abs(x) <= 10 ** 6 for r in M for x in r)
             and all(type(x) is int and abs(x) <= 10 ** 6 for x in u + v), 'matrix definition')
        return len(M)
    if kind == 'words':
        need(set(sd) == {'type', 'patterns'} and type(sd['patterns']) is list and 1 <= len(sd['patterns']) <= 3
             and all(type(w) is str and 1 <= len(w) <= 7 and not set(w) - set('01') for w in sd['patterns']),
             'binary word definition')
        return len(word_system(sd['patterns'], budget)[0])
    if kind == 'poly':
        need(set(sd) == {'type', 'coefficients'} and type(sd['coefficients']) is list and len(sd['coefficients']) <= 32,
             'polynomial definition')
        return len(sd['coefficients'])
    if kind == 'expsum':
        need(set(sd) == {'type', 'terms'} and type(sd['terms']) is list and 1 <= len(sd['terms']) <= 16
             and all(type(t) is list and len(t) == 2 for t in sd['terms']), 'exponential sum definition')
        return len(sd['terms'])
    if kind == 'terms':
        raise Invalid('a finite list of terms has no all-index law; only finite claims apply')
    need(kind == 'transform' and set(sd) <= {'type', 'op', 'args', 'params'} and type(sd.get('args')) is list,
         'sequence transform definition')
    op, args, params = sd['op'], sd['args'], sd.get('params', {})
    need(type(params) is dict, 'transform parameters')
    arity = {'sum': 2, 'product': 2, 'interleave': 2, 'convolution': 2}.get(op, 1)
    need(len(args) == arity, 'transform arity')
    D = [annihilator(a, budget, depth + 1) for a in args]
    if op in ('shift', 'scale', 'difference', 'binomial', 'inverse_binomial', 'twist'):
        need(set(params) == {'shift': {'s'}, 'scale': {'c'}, 'twist': {'c'}}.get(op, set()), 'transform parameters')
        if op == 'shift': integer(params['s'], 0, 4096)
        if op in ('scale', 'twist'): rat(params['c'])
        return D[0]
    if op in ('sum', 'convolution'): return D[0] + D[1]
    if op == 'product': return D[0] * D[1]
    if op == 'partial_sum': return D[0] + 1
    if op == 'decimate':
        need(set(params) == {'t', 'j'}, 'decimation parameters')
        integer(params['t'], 1, 16); integer(params['j'], 0, params['t'] - 1)
        return D[0]
    if op == 'interleave': return 2 * (D[0] + D[1])
    if op == 'polymul':
        need(set(params) == {'p'} and type(params['p']) is list and 1 <= len(params['p']) <= 8, 'polynomial multiplier')
        return D[0] * len(params['p'])
    if op == 'reciprocal': return D[0] + 1
    if op == 'aerate':
        need(set(params) == {'t'}, 'aeration parameter'); integer(params['t'], 1, 16)
        return D[0] * params['t']
    raise Invalid('unknown sequence transform')


def word_system(patterns, budget):
    return _recurrence.original_word_system(patterns, budget) if len(patterns) == 2 and \
        patterns[0] not in patterns[1] and patterns[1] not in patterns[0] else _word_system(patterns, budget)


def _word_system(patterns, budget):
    prefixes = {''}
    for w in patterns:
        for k in range(1, len(w)): budget.use(k); prefixes.add(w[:k])
    states = sorted(prefixes, key=lambda t: (len(t), t)); M = [[0] * len(states) for _ in states]
    for i, state in enumerate(states):
        for letter in '01':
            extended = state + letter; budget.use(len(extended) * len(patterns))
            if any(w in extended for w in patterns): continue
            best = ''
            for p in states:
                budget.use(max(1, len(p)))
                if len(p) > len(best) and extended.endswith(p): best = p
            M[i][states.index(best)] += 1
    return M, [1] + [0] * (len(states) - 1), [1] * len(states)


def seq_terms(sd, count, budget, depth=0):
    """Exact terms of a definition; independent of the producer's evaluation."""
    need(0 <= count <= MAX_TERMS, 'term count bound')
    kind = sd['type']
    if kind == 'lrs':
        c = [rat(x) for x in sd['coefficients']]; out = [rat(x) for x in sd['initial']][:count]; r = len(c)
        while len(out) < count:
            budget.use(2 * r + 1)
            out.append(small(sum(cj * out[len(out) - r + j] for j, cj in enumerate(c))) if r else Q(0))
        return out
    if kind in ('matrix', 'words'):
        M, u, v = (sd['matrix'], sd['initial'], sd['terminal']) if kind == 'matrix' else word_system(sd['patterns'], budget)
        row = [Q(x) for x in u]; out = []
        for _ in range(count):
            budget.use(2 * len(row)); out.append(sum(x * y for x, y in zip(row, v)))
            following = [Q(0)] * len(row)
            for i, x in enumerate(row):
                if x:
                    for j, w in enumerate(M[i]):
                        if w: budget.use(); following[j] += x * w
            row = [small(x) for x in following]
        return out
    if kind == 'poly':
        c = [rat(x) for x in sd['coefficients']]
        return [u_eval(c, Q(n)) for n in range(count)]
    if kind == 'terms':
        need(set(sd) == {'type', 'values'} and type(sd['values']) is list and len(sd['values']) <= MAX_TERMS,
             'finite term list'); need(count <= len(sd['values']), 'finite term list is too short')
        return [rat(x) for x in sd['values'][:count]]
    if kind == 'expsum':
        pairs = [(rat(a), rat(b)) for a, b in sd['terms']]; out = []
        for n in range(count):
            budget.use(len(pairs)); out.append(small(sum(a * b ** n for a, b in pairs)))
        return out
    op, args, params = sd['op'], sd['args'], sd.get('params', {})
    sub = lambda i, k: seq_terms(args[i], k, budget, depth + 1)
    budget.use(count)
    if op == 'shift': return sub(0, count + params['s'])[params['s']:]
    if op == 'scale': return [rat(params['c']) * x for x in sub(0, count)]
    if op == 'sum': return [x + y for x, y in zip(sub(0, count), sub(1, count))]
    if op == 'product': return [small(x * y) for x, y in zip(sub(0, count), sub(1, count))]
    if op == 'partial_sum':
        out, total = [], Q(0)
        for x in sub(0, count): total += x; out.append(total)
        return out
    if op == 'difference':
        a = sub(0, count + 1); return [a[i + 1] - a[i] for i in range(count)]
    if op == 'decimate':
        t, j = params['t'], params['j']; need(t * count + j <= MAX_TERMS, 'decimation term bound')
        a = sub(0, t * max(0, count - 1) + j + 1); return [a[t * n + j] for n in range(count)]
    if op in ('binomial', 'inverse_binomial'):
        a = sub(0, count); out = []
        for n in range(count):
            budget.use(n + 1)
            out.append(small(sum(binomial(n, k) * (-1 if op == 'inverse_binomial' and (n - k) % 2 else 1) * a[k]
                                 for k in range(n + 1))))
        return out
    if op == 'interleave':
        a = sub(0, (count + 1) // 2 + 1); b = sub(1, count // 2 + 1)
        return [a[n // 2] if n % 2 == 0 else b[n // 2] for n in range(count)]
    if op == 'twist':
        c = rat(params['c']); return [small(c ** n * x) for n, x in enumerate(sub(0, count))]
    if op == 'polymul':
        p = [rat(x) for x in params['p']]; return [small(u_eval(p, Q(n)) * x) for n, x in enumerate(sub(0, count))]
    if op == 'convolution':
        a, b = sub(0, count), sub(1, count); out = []
        for n in range(count):
            budget.use(n + 1); out.append(small(sum(a[k] * b[n - k] for k in range(n + 1))))
        return out
    if op == 'reciprocal':
        a = sub(0, count); need(count == 0 or a[0] != 0, 'reciprocal series needs a nonzero first term'); out = []
        for n in range(count):
            budget.use(n + 1)
            out.append(small(((1 if n == 0 else 0) - sum(a[k] * out[n - k] for k in range(1, n + 1))) / a[0]))
        return out
    if op == 'aerate':
        t = params['t']; a = sub(0, count // t + 1)
        return [a[n // t] if n % t == 0 else Q(0) for n in range(count)]
    raise Invalid('unknown sequence transform')


def rational_series(numerator, denominator, count, budget):
    P = [rat(x) for x in numerator]; Qd = [rat(x) for x in denominator]
    need(Qd and Qd[0] != 0, 'series denominator needs a nonzero constant term')
    out = []
    for n in range(count):
        budget.use(len(Qd))
        value = (P[n] if n < len(P) else 0) - sum(Qd[j] * out[n - j] for j in range(1, min(n, len(Qd) - 1) + 1))
        out.append(small(value / Qd[0]))
    return out


def form_terms(form, count, budget):
    need(type(form) is dict, 'closed form')
    if form.get('type') == 'lincomb':
        need(set(form) == {'type', 'defs', 'coefficients'} and type(form['defs']) is list
             and len(form['defs']) == len(form['coefficients']) and 1 <= len(form['defs']) <= 4, 'linear combination form')
        parts = [seq_terms(d, count, budget) for d in form['defs']]; c = [rat(x) for x in form['coefficients']]
        return ([sum(ci * part[n] for ci, part in zip(c, parts)) for n in range(count)],
                sum(annihilator(d, budget) for d in form['defs']))
    if form.get('type') == 'poly':
        c = [rat(x) for x in form['coefficients']]; need(len(c) <= 32, 'closed polynomial degree')
        return [u_eval(c, Q(n)) for n in range(count)], len(c)
    need(form.get('type') == 'expsum' and type(form.get('terms')) is list and 1 <= len(form['terms']) <= 16,
         'closed exponential sum')
    pairs = [(rat(a), rat(b)) for a, b in form['terms']]; out = []
    for n in range(count):
        budget.use(len(pairs)); out.append(small(sum(a * b ** n for a, b in pairs)))
    return out, len(pairs)


def check_law(data, budget):
    need(set(data) == {'def', 'coefficients', 'initial'}, 'law fields')
    c = [rat(x) for x in data['coefficients']]; a0 = [rat(x) for x in data['initial']]
    need(len(c) == len(a0) and len(c) <= 128, 'law order')
    D = annihilator(data['def'], budget); R = len(c)
    a = seq_terms(data['def'], D + R, budget)
    need(a[:R] == a0, 'law initial terms differ from the definition')
    for n in range(D):
        budget.use(R + 1)
        need(a[n + R] == sum(cj * a[n + j] for j, cj in enumerate(c)), 'law fails at index ' + str(n + R))
    return dict(ok=True, kind='law', order=R, agreement_terms=D + R,
                scope='The defined sequence satisfies the recurrence for every index n >= 0.',
                proof='Both sides satisfy monic recurrences of orders D and R; agreement on D+R terms forces equality.')


def check_gf(data, budget):
    need(set(data) == {'def', 'numerator', 'denominator'}, 'generating function fields')
    P, Qd = data['numerator'], data['denominator']
    need(type(P) is list and type(Qd) is list and len(P) <= 128 and 1 <= len(Qd) <= 128, 'generating function size')
    D = annihilator(data['def'], budget); order = max(len(Qd) - 1, len(P))
    count = D + order
    need(seq_terms(data['def'], count, budget) == rational_series(P, Qd, count, budget),
         'series expansion differs from the definition')
    return dict(ok=True, kind='gf', agreement_terms=count,
                scope='sum a(n) x^n equals P(x)/Q(x) as formal power series.',
                proof='The series of P/Q satisfies an all-index recurrence of order max(deg Q, deg P+1); '
                      'agreement on D plus that order terms forces equality.')


def check_closed(data, budget):
    need(set(data) == {'def', 'form'}, 'closed form fields')
    D = annihilator(data['def'], budget)
    probe, order = form_terms(data['form'], 0, budget)
    count = D + order
    values, _ = form_terms(data['form'], count, budget)
    need(seq_terms(data['def'], count, budget) == values, 'closed form differs from the definition')
    return dict(ok=True, kind='closed', agreement_terms=count, scope='a(n) equals the closed form for every n >= 0.',
                proof='Polynomial and exponential-sum forms satisfy recurrences of known order; agreement bound.')


class Machine:
    """A deterministic integer state machine mod m whose output is the sequence mod m."""

    def __init__(self, state, step, out):
        self.state, self.step, self.out = state, step, out

    def advance(self, k):
        for _ in range(k): self.state = self.step(self.state)
        return self


def machine(sd, m, budget, depth=0):
    """State machines for integer recurrences, matrices, words and closed transforms of them."""
    need(depth <= 6, 'machine depth')
    kind = sd['type']
    if kind == 'lrs':
        c = [rat(x) for x in sd['coefficients']]; a = [rat(x) for x in sd['initial']]
        need(all(x.denominator == 1 for x in c + a), 'periodicity needs integer recurrence data')
        c = [int(x) for x in c]

        def step(s):
            budget.use(len(s) + 1)
            return s[1:] + (sum(cj * x for cj, x in zip(c, s)) % m,) if c else s
        return Machine(tuple(int(x) % m for x in a), step, (lambda s: s[0] if s else 0))
    if kind in ('matrix', 'words'):
        annihilator(sd, budget)
        M, u, v = (sd['matrix'], sd['initial'], sd['terminal']) if kind == 'matrix' else word_system(sd['patterns'], budget)

        def step(s):
            budget.use(len(s) * len(s))
            return tuple(sum(s[i] * M[i][j] for i in range(len(s))) % m for j in range(len(s)))
        return Machine(tuple(x % m for x in u), step, lambda s: sum(x * y for x, y in zip(s, v)) % m)
    need(kind == 'transform', 'periodicity is checked for integer recurrences, matrices, words and their transforms')
    op, args, params = sd['op'], sd['args'], sd.get('params', {})
    if op in ('sum', 'product'):
        A, B = machine(args[0], m, budget, depth + 1), machine(args[1], m, budget, depth + 1)
        combine = (lambda x, y: (x + y) % m) if op == 'sum' else (lambda x, y: x * y % m)
        return Machine((A.state, B.state), lambda s: (A.step(s[0]), B.step(s[1])),
                       lambda s: combine(A.out(s[0]), B.out(s[1])))
    A = machine(args[0], m, budget, depth + 1)
    if op == 'shift': integer(params['s'], 0, MAX_STEPS); return A.advance(params['s'])
    if op == 'scale':
        c = rat(params['c']); need(c.denominator == 1, 'integer scale for periodicity')
        return Machine(A.state, A.step, lambda s: int(c) * A.out(s) % m)
    if op == 'decimate':
        t, j = integer(params['t'], 1, 16), integer(params['j'], 0, 15); A.advance(j)

        def step(s):
            for _ in range(t): s = A.step(s)
            return s
        return Machine(A.state, step, A.out)
    raise Invalid('no periodic machine for this transform')


def check_period(data, budget):
    need(set(data) == {'def', 'modulus', 'start', 'period'}, 'period fields')
    m = integer(data['modulus'], 2, 10 ** 9); start = integer(data['start'], 0, MAX_STEPS)
    P = integer(data['period'], 1, MAX_STEPS * 16)
    mc = machine(data['def'], m, budget).advance(start)
    first = mc.state; mc.advance(P)
    need(mc.state == first, 'state does not repeat after the claimed period')
    return dict(ok=True, kind='period', scope='a(n+P) = a(n) mod m for every n >= start.',
                proof='A deterministic integer state determines all later terms mod m; it repeats after P steps from start.')


def check_hyper(data, budget):
    need(set(data) == {'def', 'p', 'q', 'upto'}, 'hypergeometric fields')
    upto = integer(data['upto'], 1, 2048)
    p = [rat(x) for x in data['p']]; q = [rat(x) for x in data['q']]
    a = seq_terms(data['def'], upto + 1, budget)
    for n in range(upto):
        budget.use(4)
        need(a[n + 1] * u_eval(q, Q(n)) == a[n] * u_eval(p, Q(n)), 'term ratio fails at index ' + str(n))
    return dict(ok=True, kind='hyper', scope='a(n+1)q(n) = a(n)p(n) for 0 <= n < upto only; a finite claim.',
                proof='Direct evaluation of the first upto+1 terms.')


# ------------------------------------------------------------- polynomial identities and maps

def check_identity(data, budget):
    need(set(data) == {'vars', 'lhs', 'rhs'}, 'identity fields')
    names = names_of(data['vars'])
    difference = _padd(poly(data['lhs'], names, budget), {k: -v for k, v in poly(data['rhs'], names, budget).items()},
                       budget)
    need(not difference, 'identity sides differ after exact expansion')
    return dict(ok=True, kind='identity', scope='lhs = rhs as polynomials over QQ.', proof='Exact expansion.')


def composed(e, names, components):
    return substituted(e, {name: c for name, c in zip(names, components)})


def check_invariant(data, budget, factor=None):
    need(set(data) == ({'vars', 'map', 'poly'} if factor is None else {'vars', 'map', 'poly', 'factor'}), 'invariant fields')
    names, components = map_of(data)
    image = poly(composed(data['poly'], names, components), names, budget)
    base = poly(data['poly'], names, budget)
    need(base and any(sum(k) for k in base), 'invariant must be a nonconstant polynomial')
    lam = Q(1) if factor is None else rat(factor)
    need(not _padd(image, {k: -lam * v for k, v in base.items()}, budget),
         'P(F(x)) differs from ' + ('P(x)' if factor is None else 'lambda*P(x)'))
    return lam


def check_fixed(data, budget):
    need(set(data) == {'vars', 'map', 'point'}, 'fixed point fields')
    names, components = map_of(data); p = point_of(data['point'], names)
    need([evaluate(c, names, p, budget) for c in components] == p, 'F(p) differs from p')
    return dict(ok=True, kind='fixed', scope='F(p) = p.', proof='Exact evaluation.')


def check_inverse(data, budget):
    need(set(data) == {'vars', 'map', 'inverse'}, 'inverse fields')
    names, components = map_of(data)
    inverse = data['inverse']; need(type(inverse) is list and len(inverse) == len(names), 'inverse components')
    for outer, inner in ((inverse, components), (components, inverse)):
        for i, e in enumerate(outer):
            need(poly(composed(e, names, inner), names, budget) == poly(['var', names[i]], names, budget),
                 'maps are not mutually inverse')
    return dict(ok=True, kind='inverse', scope='G(F(x)) = x and F(G(x)) = x as polynomial maps.', proof='Exact expansion.')


def orbit_of(data):
    need(type(data) is dict and set(data) == {'vars', 'map', 'start', 'target'}, 'orbit question fields')
    names, components = map_of(data)
    return names, components, point_of(data['start'], names), point_of(data['target'], names)


def orbit_point(names, components, point, count, budget):
    for _ in range(count):
        point = [evaluate(c, names, point, budget) for c in components]
    return point


def exclusion(orbit, certificate, budget, depth=0):
    """True when the certificate proves no nonnegative iterate equals the target."""
    need(depth <= 4 and type(certificate) is dict, 'exclusion certificate')
    names, components, start, target = orbit_of(orbit)
    kind = certificate.get('type')
    if kind == 'invariant':
        need(set(certificate) == {'type', 'poly'}, 'invariant certificate fields')
        check_invariant(dict(vars=names, map=components, poly=certificate['poly']), budget)
        need(evaluate(certificate['poly'], names, start, budget) != evaluate(certificate['poly'], names, target, budget),
             'invariant takes the same value at start and target')
        return 'conserved value differs'
    if kind == 'semi':
        need(set(certificate) <= {'type', 'poly', 'factor', 'index'}, 'semi-invariant certificate fields')
        lam = check_invariant(dict(vars=names, map=components, poly=certificate['poly'], factor=certificate['factor']),
                              budget, certificate['factor'])
        v0 = evaluate(certificate['poly'], names, start, budget); vt = evaluate(certificate['poly'], names, target, budget)
        # P(x(n)) = lam**n * P(x(0)); collect every n >= 0 at which that value equals P(target).
        if v0 == 0:
            need(vt != 0, 'semi-invariant vanishes at start and target')
            need('index' not in certificate, 'no candidate index exists')
            return 'semi-invariant stays zero and is nonzero at the target'
        rho = vt / v0
        need(not ((lam == 0 and rho == 0) or (lam == 1 and rho == 1) or (lam == -1 and rho in (1, -1))),
             'the target value recurs along the orbit')
        candidates = []
        if lam == 0: candidates = [0] if rho == 1 else []
        elif abs(lam) != 1 and rho != 0:
            value, n = Q(1), 0
            while abs(value) <= abs(rho) if abs(lam) > 1 else abs(value) >= abs(rho):
                budget.use(); need(n <= MAX_STEPS, 'semi-invariant index search bound')
                if value == rho: candidates.append(n)
                value = small(value * lam); n += 1
        if not candidates:
            need('index' not in certificate, 'no candidate index exists')
            return 'semi-invariant value excludes'
        need(len(candidates) == 1 and certificate.get('index') == candidates[0], 'certificate must name the candidate index')
        need(orbit_point(names, components, start, candidates[0], budget) != target,
             'orbit meets the target at the candidate index')
        return 'semi-invariant leaves one index, where the orbit differs from the target'
    if kind == 'modular':
        need(set(certificate) == {'type', 'modulus'}, 'modular certificate fields')
        m = integer(certificate['modulus'], 2, 10 ** 6)
        reduced = [_mod_poly(poly(c, names, budget), m) for c in components]
        s = tuple(_mod_value(x, m) for x in start); t = tuple(_mod_value(x, m) for x in target)
        seen = set()
        while s not in seen:
            need(len(seen) < MAX_MODULAR_STATES, 'modular orbit state bound'); budget.use(len(s) + 1)
            need(s != t, 'target residue occurs in the modular orbit')
            seen.add(s)
            s = tuple(_mod_eval(p, s, m, budget) for p in reduced)
        return 'target residue absent from the eventually periodic modular orbit'
    if kind == 'subsystem':
        need(set(certificate) == {'type', 'indices', 'inner'}, 'subsystem certificate fields')
        idx = certificate['indices']
        need(type(idx) is list and idx and sorted(set(idx)) == idx and all(type(i) is int and 0 <= i < len(names) for i in idx),
             'subsystem indices')
        inside = {names[i] for i in idx}
        for i in idx:
            need(set(_vars(components[i])) <= inside, 'subsystem is not closed under the map')
        sub = dict(vars=[names[i] for i in idx], map=[components[i] for i in idx],
                   start=[orbit['start'][i] for i in idx], target=[orbit['target'][i] for i in idx])
        exclusion(sub, certificate['inner'], budget, depth + 1)
        return 'closed coordinate subsystem excludes'
    if kind == 'iterate':
        need(set(certificate) == {'type', 'base', 'k', 'inner'}, 'iterate certificate fields')
        k = integer(certificate['k'], 1, 8); base = certificate['base']
        need(type(base) is list and len(base) == len(names), 'base map components')
        power = [['var', v] for v in names]
        for _ in range(k): power = [composed(e, names, base) for e in power]
        for mine, theirs in zip(components, power):
            need(poly(mine, names, budget) == poly(theirs, names, budget), 'map is not the k-th iterate of the base map')
        exclusion(dict(orbit, map=base), certificate['inner'], budget, depth + 1)
        return 'orbit of the iterate lies in the excluded base orbit'
    if kind == 'conjugate':
        need(set(certificate) == {'type', 'h', 'h_inverse', 'base', 'inner'}, 'conjugacy certificate fields')
        h, g = certificate['h'], certificate['h_inverse']; base = certificate['base']
        check_inverse(dict(vars=names, map=h, inverse=g), budget)
        need(type(base) is dict and set(base) == {'map', 'start', 'target'}, 'conjugate base question')
        conj = [composed(composed(e, names, base['map']), names, h) for e in g]
        for mine, theirs in zip(components, conj):
            need(poly(mine, names, budget) == poly(theirs, names, budget), 'map is not h^-1 F h')
        bs, bt = point_of(base['start'], names), point_of(base['target'], names)
        need([evaluate(e, names, bs, budget) for e in g] == start and [evaluate(e, names, bt, budget) for e in g] == target,
             'start or target is not the conjugated point')
        exclusion(dict(vars=names, map=base['map'], start=base['start'], target=base['target']),
                  certificate['inner'], budget, depth + 1)
        return 'conjugate orbit excluded'
    if kind == 'reverse':
        need(set(certificate) == {'type', 'inverse', 'inner'}, 'reverse certificate fields')
        check_inverse(dict(vars=names, map=components, inverse=certificate['inverse']), budget)
        exclusion(dict(vars=names, map=certificate['inverse'], start=orbit['target'], target=orbit['start']),
                  certificate['inner'], budget, depth + 1)
        return 'start is not in the backward orbit of the target'
    raise Invalid('unknown exclusion certificate')


def _vars(e):
    out = set()

    def walk(t):
        if t[0] == 'var': out.add(t[1])
        elif t[0] in ('add', 'mul', 'sub', 'neg'):
            for x in t[1:]: walk(x)
        elif t[0] == 'pow': walk(t[1])
    walk(e)
    return out


def _mod_value(x, m):
    need(gcd(x.denominator, m) == 1, 'value is not integral at the modulus')
    return x.numerator * pow(x.denominator, -1, m) % m


def _mod_poly(p, m):
    return [(k, _mod_value(c, m)) for k, c in p.items()]


def _mod_eval(p, point, m, budget):
    total = 0
    for exponents, c in p:
        budget.use(len(exponents)); term = c
        for x, k in zip(point, exponents):
            if k: term = term * pow(x, k, m) % m
        total += term
    return total % m


def check_exclusion(data, budget):
    need(set(data) == {'orbit', 'certificate'}, 'exclusion fields')
    how = exclusion(data['orbit'], data['certificate'], budget)
    return dict(ok=True, kind='exclusion', method=how, scope='No nonnegative iterate of the orbit equals the target.',
                proof='The certificate is rechecked from the original map, start and target.')


def check_reach(data, budget):
    need(set(data) == {'orbit', 'index'}, 'reach fields')
    names, components, start, target = orbit_of(data['orbit']); n = integer(data['index'], 0, MAX_STEPS)
    need(orbit_point(names, components, start, n, budget) == target, 'orbit does not meet the target at the index')
    return dict(ok=True, kind='reach', scope='The orbit equals the target at the index.', proof='Exact iteration.')


# ------------------------------------------------------------- unit fractions

def class_of(data):
    a = integer(data.get('a'), 1, 64); m = integer(data.get('m'), 1, 10 ** 9); r = integer(data.get('r'), 0, m - 1)
    return a, m, r


def check_ufrac(data, budget):
    need(set(data) == {'a', 'n', 'x'}, 'unit fraction fields')
    a = integer(data['a'], 1, 64); n = integer(data['n'], 1, 10 ** 30)
    xs = data['x']; need(type(xs) is list and 1 <= len(xs) <= 8 and all(type(x) is int and x >= 1 for x in xs),
                         'positive integer denominators')
    budget.use(len(xs))
    need(sum(Q(1, x) for x in xs) == Q(a, n), 'unit fractions do not sum to a/n')
    return dict(ok=True, kind='ufrac', scope='a/n equals the sum of the listed unit fractions.', proof='Exact arithmetic.')


def family_polys(data, budget):
    need(set(data) == {'a', 'm', 'r', 'k0', 'x'}, 'family fields')
    a, m, r = class_of(data); k0 = integer(data['k0'], 0, 10 ** 6)
    xs = data['x']; need(type(xs) is list and 1 <= len(xs) <= 6, 'family term count')
    return a, m, r, k0, [u_poly(e, 'k', budget) for e in xs]


def check_ufam(data, budget):
    a, m, r, k0, xs = family_polys(data, budget)
    n = [Q(r), Q(m)]
    need(m * k0 + r >= 1, 'class values must be positive')
    product = [Q(1)]
    for x in xs: product = _umul(product, x, budget)
    left = [a * c for c in product]
    right = []
    for i in range(len(xs)):
        others = [Q(1)]
        for j, x in enumerate(xs):
            if j != i: others = _umul(others, x, budget)
        right = _uadd(right, others)
    right = _umul(n, right, budget)
    need(u_trim(_uadd(left, [-c for c in right])) == [], 'family identity a*prod(x) = n*sum(prod others) fails')
    for x in xs:
        need(all(u_eval(x, Q(k)).denominator == 1 for k in range(max(1, len(x)))), 'denominator is not integer valued')
        shifted = u_shift(x, Q(k0))
        need(shifted and shifted[0] > 0 and all(c >= 0 for c in shifted), 'denominator not positive for every k >= k0')
    return dict(ok=True, kind='ufam', terms=len(xs), bound=m * k0 + r,
                scope='For every integer k >= k0 and n = m*k + r, a/n is the sum of the unit fractions 1/x_i(k).',
                proof='Polynomial identity in k; integer values at deg+1 consecutive points give integer values on Z; '
                      'nonnegative coefficients of x_i(k0+t) with positive constant give positivity.')


def _umul(a, b, budget):
    if not a or not b: return []
    out = [Q(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b): budget.use(); out[i + j] += x * y
    return u_trim(out)


def _uadd(a, b):
    n = max(len(a), len(b))
    return u_trim([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(n)])


def check_cover(data, budget, families_checked=None):
    need(set(data) == {'a', 'terms', 'modulus', 'entries', 'bound'}, 'cover fields')
    a = integer(data['a'], 1, 64); terms = integer(data['terms'], 2, 6); M = integer(data['modulus'], 1, 10 ** 7)
    bound = integer(data['bound'], 1); entries = data['entries']
    need(type(entries) is list and 1 <= len(entries) <= 4096, 'cover entries')
    for entry in entries:
        need(type(entry) is dict and set(entry) == {'family'}, 'cover entry fields')
        family = entry['family']
        need(family['a'] == a and len(family['x']) == terms, 'family belongs to another question')
        checked = check_ufam(family, budget)
        need(M % family['m'] == 0, 'family modulus must divide the cover modulus')
        need(bound >= checked['bound'], 'cover bound below a family threshold')
    budget.use(M)
    covered = cover_residues(data)
    return dict(ok=True, kind='cover', covered=len(covered), modulus=M, bound=bound,
                scope='Every n >= bound whose residue mod the modulus lies in a listed family class has an a/n '
                      'representation.',
                proof='Each covered residue lies in the class m*k + r of a checked family, m dividing the modulus, '
                      'whose threshold m*k0 + r is at most bound.')


def cover_residues(data):
    out = set(); M = data['modulus']
    for entry in data['entries']:
        f = entry['family']; out.update(range(f['r'], M, f['m']))
    return out


def check_finite(data, budget):
    need(set(data) == {'a', 'terms', 'lo', 'hi', 'witnesses', 'divisors', 'cover'}, 'finite range fields')
    a = integer(data['a'], 1, 64); terms = integer(data['terms'], 2, 6)
    lo = integer(data['lo'], 1); hi = integer(data['hi'], lo); need(hi - lo <= MAX_RANGE, 'finite range bound')
    witnesses, divisors, cover = data['witnesses'], data['divisors'], data['cover']
    need(type(witnesses) is dict and type(divisors) is dict, 'witness tables')
    thresholds = {}
    if cover is not None:
        check_cover(cover, budget)
        need(cover['a'] == a and cover['terms'] == terms, 'cover belongs to another question')
        for entry in cover['entries']:
            f = entry['family']; row = thresholds.setdefault(f['m'], {})
            row[f['r']] = min(row.get(f['r'], f['m'] * f['k0'] + f['r']), f['m'] * f['k0'] + f['r'])
    done = set(); via_cover = via_witness = via_divisor = 0
    for n in range(lo, hi):
        budget.use(1 + len(thresholds))
        if any(n >= row.get(n % m, n + 1) for m, row in thresholds.items()):
            via_cover += 1; done.add(n); continue
        key = str(n)
        if key in witnesses:
            xs = witnesses[key]
            need(type(xs) is list and len(xs) == terms - 1 and all(type(x) is int and x >= 1 for x in xs), 'witness shape')
            rest = Q(a, n) - sum(Q(1, x) for x in xs); budget.use(terms)
            need(rest > 0 and rest.numerator == 1, 'witness does not leave a unit fraction')
            via_witness += 1; done.add(n); continue
        d = divisors.get(key)
        need(type(d) is int and 1 < d < n and n % d == 0 and d in done, 'no checked representation for ' + key)
        via_divisor += 1; done.add(n)
    return dict(ok=True, kind='finite', count=hi - lo, via_cover=via_cover, via_witness=via_witness,
                via_divisor=via_divisor,
                scope='Every integer n with lo <= n < hi has a representation of a/n with the stated number of terms.',
                proof='A checked family whose class contains n at or above its own threshold, an exact witness with a '
                      'unit remainder, or a checked divisor d of n scaled by n/d.')


def check_reduction(data, budget):
    need(data == dict(a=data.get('a'), terms=data.get('terms'), rule='multiples'), 'reduction fields')
    integer(data['a'], 1, 64); integer(data['terms'], 2, 6)
    return dict(ok=True, kind='reduction', scope='A representation of a/n gives one of a/(t*n) for every t >= 1.',
                proof='a/(t n) = sum 1/(t x_i) whenever a/n = sum 1/x_i.')


def check_pattern(data, budget):
    need(set(data) == {'cover', 'rule'} and data['rule'] == 'uncovered_coprime_are_squares', 'pattern fields')
    check_cover(data['cover'], budget)
    M = data['cover']['modulus']; covered = cover_residues(data['cover'])
    budget.use(2 * M)
    squares = {x * x % M for x in range(M) if gcd(x, M) == 1}
    for x in range(M):
        if gcd(x, M) == 1: need((x in squares) != (x in covered), 'residue ' + str(x) + ' breaks the pattern')
    return dict(ok=True, kind='pattern', squares=len(squares),
                scope='For this cover only: a coprime residue is uncovered exactly when it is a square mod the modulus.',
                proof='Exhaustive comparison over the residues; a statement about the cover, not about every n.')


def check_density(data, budget):
    need(set(data) == {'cover', 'fraction'}, 'density fields')
    check_cover(data['cover'], budget)
    fraction = rat(data['fraction'])
    need(fraction == Q(len(cover_residues(data['cover'])), data['cover']['modulus']), 'covered fraction differs')
    return dict(ok=True, kind='density', scope='The listed residues form exactly this fraction of all residues.',
                proof='Counting.')


# ------------------------------------------------------------- matrices, divisibility and roots

def check_countval(data, budget):
    need(set(data) == {'matrix', 'initial', 'terminal', 'horizon', 'value'}, 'count fields')
    sd = dict(type='matrix', matrix=data['matrix'], initial=data['initial'], terminal=data['terminal'])
    annihilator(sd, budget); h = integer(data['horizon'], 0, MAX_STEPS)
    need(seq_terms(sd, h + 1, budget)[h] == rat(data['value']), 'count differs')
    return dict(ok=True, kind='countval', scope='u*M**h*v equals the value.', proof='Exact iteration.')


def check_divis(data, budget):
    need(set(data) == {'expr', 'modulus'}, 'divisibility fields')
    m = integer(data['modulus'], 2, 10 ** 12); f = u_poly(data['expr'], 'n', budget)
    values = [u_eval(f, Q(n)) for n in range(max(1, len(f)))]
    need(all(v.denominator == 1 for v in values), 'polynomial is not integer valued')
    diffs = [int(v) for v in values]
    for _ in range(len(diffs)):
        need(diffs[0] % m == 0, 'a forward difference is not divisible by the modulus')
        diffs = [y - x for x, y in zip(diffs, diffs[1:])]
        budget.use(len(diffs) + 1)
    return dict(ok=True, kind='divis', scope='m divides f(n) for every integer n.',
                proof='f = sum b_i C(n,i) with b_i the forward differences at 0; m divides every b_i.')


def root_poly(data):
    p = data.get('poly'); need(type(p) is list and 1 <= len(p) <= 16 and all(type(c) is int for c in p), 'integer polynomial')
    return p


def check_rootmod(data, budget):
    need(set(data) == {'poly', 'modulus', 'root'}, 'modular root fields')
    p = root_poly(data); m = integer(data['modulus'], 2, 10 ** 18); x = integer(data['root'], 0, m - 1)
    budget.use(len(p))
    need(sum(c * pow(x, i, m) for i, c in enumerate(p)) % m == 0, 'not a root modulo m')
    return dict(ok=True, kind='rootmod', scope='f(root) = 0 mod m.', proof='Exact evaluation.')


def check_nosolmod(data, budget):
    need(set(data) == {'poly', 'modulus'}, 'modular nonexistence fields')
    p = root_poly(data); m = integer(data['modulus'], 2, 10 ** 6)
    for x in range(m):
        budget.use(len(p))
        need(sum(c * pow(x, i, m) for i, c in enumerate(p)) % m != 0, 'f has a root modulo m')
    return dict(ok=True, kind='nosolmod', scope='f has no root modulo m.', proof='Exhaustive evaluation over Z/m.')


def check_introot(data, budget):
    need(set(data) == {'poly', 'root'}, 'integer root fields')
    p = root_poly(data); x = integer(data['root']); budget.use(len(p))
    need(sum(c * x ** i for i, c in enumerate(p)) == 0, 'not an integer root')
    return dict(ok=True, kind='introot', scope='f(root) = 0 over the integers.', proof='Exact evaluation.')


def check_eigen(data, budget):
    need(set(data) == {'matrix', 'value', 'vector'}, 'eigenvector fields')
    M = data['matrix']; n = len(M) if type(M) is list else 0
    need(1 <= n <= 32 and all(type(r) is list and len(r) == n for r in M), 'square matrix')
    A = [[rat(x) for x in r] for r in M]; lam = rat(data['value'])
    need(type(data['vector']) is list, 'vector'); v = [rat(x) for x in data['vector']]
    need(len(v) == n and any(v), 'nonzero vector of matching size'); budget.use(n * n)
    need([sum(A[i][j] * v[j] for j in range(n)) for i in range(n)] == [lam * x for x in v], 'M v differs from lambda v')
    return dict(ok=True, kind='eigen', scope='M v = lambda v with v nonzero.', proof='Exact arithmetic.')


def check_cycle(data, budget):
    need(set(data) == {'map', 'start', 'length'}, 'cycle fields')
    d, A, B = cmap_of(data['map']); x = integer(data['start'], 1); length = integer(data['length'], 1, 10_000)
    seen = []
    for _ in range(length):
        budget.use(); seen.append(x); i = x % d; x = (A[i] * x + B[i]) // d
    need(x == data['start'], 'the orbit does not return to its start')
    need(1 not in seen, 'the cycle contains 1')
    return dict(ok=True, kind='cycle', smallest=min(seen),
                scope='A periodic orbit avoiding 1: this map has an orbit that never reaches 1.', proof='Exact iteration.')


def check_nosol(data, budget):
    need(set(data) == {'poly', 'modulus'}, 'integer nonexistence fields')
    check_nosolmod(data, budget)
    return dict(ok=True, kind='nosol', scope='f has no integer root.',
                proof='An integer root would reduce to a root modulo m.')


# ------------------------------------------------------------- residue-class maps (Collatz type)

def cmap_of(data):
    need(type(data) is dict and set(data) == {'d', 'a', 'b'}, 'class map fields')
    d = integer(data['d'], 2, 16); A, B = data['a'], data['b']
    need(type(A) is list and type(B) is list and len(A) == len(B) == d
         and all(type(x) is int and 1 <= x <= 10 ** 6 for x in A) and all(type(x) is int and abs(x) <= 10 ** 6 for x in B),
         'class map coefficients')
    for i in range(d): need((A[i] * i + B[i]) % d == 0, 'branch does not map its class to integers')
    return d, A, B


def affine_iterate(cmap, M, r, steps, budget):
    """T^steps(M t + r) = alpha t + beta when every branch is determined by the class."""
    d, A, B = cmap_of(cmap); alpha, beta = Q(M), Q(r)
    for _ in range(steps):
        budget.use()
        need(alpha.denominator == 1 and int(alpha) % d == 0 and beta.denominator == 1, 'branch not determined by the class')
        i = int(beta) % d
        alpha, beta = A[i] * alpha / d, (A[i] * beta + B[i]) / d
    return alpha, beta


def check_descent(data, budget):
    need(set(data) == {'map', 'modulus', 'residue', 'steps', 'bound'}, 'descent fields')
    M = integer(data['modulus'], 2, 1 << 40); r = integer(data['residue'], 0, M - 1)
    steps = integer(data['steps'], 1, 64); bound = integer(data['bound'], 1)
    alpha, beta = affine_iterate(data['map'], M, r, steps, budget)
    need(alpha < M, 'iterate does not contract the class')
    # alpha t + beta < M t + r  <=>  t > (beta - r) / (M - alpha)
    threshold = (beta - r) / (M - alpha)
    t0 = int(threshold) + 1 if threshold >= 0 else 0
    need(bound >= M * t0 + r, 'descent bound below threshold')
    return dict(ok=True, kind='descent', alpha=[alpha.numerator, alpha.denominator],
                scope='For every n >= bound with n = residue mod modulus, T^steps(n) < n.',
                proof='The class fixes every branch, so T^steps(Mt+r) = alpha t + beta with alpha < M.')


def check_dcover(data, budget):
    need(set(data) == {'map', 'modulus', 'rows', 'bound'}, 'descent cover fields')
    M = integer(data['modulus'], 2, 1 << 40); bound = integer(data['bound'], 1)
    rows = data['rows']; need(type(rows) is list and rows and len(rows) <= 1 << 17, 'descent cover rows')
    residues = set()
    for row in rows:
        need(type(row) is list and len(row) == 3, 'descent row [residue, steps, bound]')
        r, steps, row_bound = row
        check_descent(dict(map=data['map'], modulus=M, residue=r, steps=steps, bound=row_bound), budget)
        need(bound >= row_bound and r not in residues, 'cover bound below a row bound, or a repeated residue')
        residues.add(r)
    return dict(ok=True, kind='dcover', covered=len(residues), modulus=M,
                scope='Every n >= bound in a listed class has T^j(n) < n for its certified j.', proof='Each row checked.')


def check_cfinite(data, budget):
    need(set(data) == {'map', 'lo', 'hi', 'cap'}, 'finite descent fields')
    d, A, B = cmap_of(data['map'])
    lo = integer(data['lo'], 2); hi = integer(data['hi'], lo); need(hi - lo <= MAX_RANGE, 'finite descent range')
    cap = integer(data['cap'], 1, 100_000)
    for n in range(lo, hi):
        x, k = n, 0
        while x >= n:
            budget.use(); i = x % d; x = (A[i] * x + B[i]) // d; k += 1
            need(k <= cap, 'no descent within the step cap for ' + str(n))
    return dict(ok=True, kind='cfinite', scope='Every n with lo <= n < hi reaches a value below n.',
                proof='Exact iteration with a step cap.')


# ------------------------------------------------------------- refutations

def check_refutation(data, budget):
    need(set(data) == {'claim', 'witness'} and type(data['claim']) is dict and type(data['witness']) is dict,
         'refutation fields')
    claim, w = data['claim'], data['witness']; kind, cd = claim.get('kind'), claim.get('data')
    need(type(cd) is dict, 'refuted claim data')
    if kind in ('law', 'gf', 'closed'):
        i = integer(w.get('index'), 0, MAX_TERMS - 1)
        actual = seq_terms(cd['def'], i + 1, budget)[i]
        if kind == 'law':
            predicted = _law_value(cd, i, budget)
        elif kind == 'gf':
            predicted = rational_series(cd['numerator'], cd['denominator'], i + 1, budget)[i]
        else:
            predicted = form_terms(cd['form'], i + 1, budget)[0][i]
        need(actual != predicted, 'claim agrees with the definition at the index')
        return dict(ok=True, kind='refutation', refutes=kind, index=i)
    if kind in ('identity',):
        names = names_of(cd['vars']); p = point_of(w.get('point'), names)
        need(evaluate(cd['lhs'], names, p, budget) != evaluate(cd['rhs'], names, p, budget), 'sides agree at the point')
        return dict(ok=True, kind='refutation', refutes=kind)
    if kind in ('invariant', 'semi'):
        names, components = map_of(cd); p = point_of(w.get('point'), names)
        image = [evaluate(c, names, p, budget) for c in components]
        lam = rat(cd['factor']) if kind == 'semi' else Q(1)
        need(evaluate(cd['poly'], names, image, budget) != lam * evaluate(cd['poly'], names, p, budget),
             'invariance holds at the point')
        return dict(ok=True, kind='refutation', refutes=kind)
    if kind == 'ufam':
        a, m, r, k0, xs = family_polys(cd, budget); k = integer(w.get('k'), k0, 10 ** 9)
        values = [u_eval(x, Q(k)) for x in xs]
        bad = any(v.denominator != 1 or v <= 0 for v in values) or sum(1 / v for v in values if v) != Q(a, m * k + r) \
            or any(v == 0 for v in values)
        need(bad, 'family is valid at this k')
        return dict(ok=True, kind='refutation', refutes=kind, k=k)
    if kind == 'ufrac':
        try: check_ufrac(cd, budget)
        except Invalid: return dict(ok=True, kind='refutation', refutes=kind)
        raise Invalid('unit fraction claim holds')
    if kind == 'divis':
        f = u_poly(cd['expr'], 'n', budget); n = integer(w.get('n'))
        value = u_eval(f, Q(n)); need(value.denominator != 1 or int(value) % cd['modulus'] != 0, 'divisible at n')
        return dict(ok=True, kind='refutation', refutes=kind, n=n)
    if kind == 'exclusion':
        names, components, start, target = orbit_of(cd['orbit']); i = integer(w.get('index'), 0, MAX_STEPS)
        need(orbit_point(names, components, start, i, budget) == target, 'orbit does not meet the target at the index')
        return dict(ok=True, kind='refutation', refutes=kind, index=i)
    if kind == 'descent':
        d, A, B = cmap_of(cd['map']); t = integer(w.get('t'), 0)
        n = cd['modulus'] * t + cd['residue']; need(n >= cd['bound'], 'witness below the claimed bound')
        x = n
        for _ in range(cd['steps']): budget.use(); i = x % d; x = (A[i] * x + B[i]) // d
        need(x >= n, 'descends at the witness')
        return dict(ok=True, kind='refutation', refutes=kind, n=n)
    if kind == 'period':
        i = integer(w.get('index'), cd['start'], MAX_TERMS // 2)
        a = seq_terms(cd['def'], i + cd['period'] + 1, budget)
        need(a[i].denominator == 1 and a[i + cd['period']].denominator == 1, 'terms must be integers')
        need((int(a[i + cd['period']]) - int(a[i])) % cd['modulus'] != 0, 'period holds at the index')
        return dict(ok=True, kind='refutation', refutes=kind, index=i)
    if kind == 'countval':
        try: check_countval(cd, budget)
        except Invalid: return dict(ok=True, kind='refutation', refutes=kind)
        raise Invalid('count claim holds')
    if kind in ('rootmod', 'introot', 'eigen', 'cycle', 'reach', 'fixed'):
        # Finite claims: the claim's own exact evaluation fails.
        try: CHECKS[kind](cd, budget)
        except Invalid: return dict(ok=True, kind='refutation', refutes=kind)
        raise Invalid('claim holds')
    if kind == 'nosolmod':
        m = cd['modulus']; x = integer(w.get('root'), 0, m - 1); budget.use(len(cd['poly']))
        need(sum(c * pow(x, i, m) for i, c in enumerate(cd['poly'])) % m == 0, 'witness is not a root')
        return dict(ok=True, kind='refutation', refutes=kind, root=x)
    if kind == 'hyper':
        i = integer(w.get('index'), 0, cd['upto'] - 1); a = seq_terms(cd['def'], i + 2, budget)
        need(a[i + 1] * u_eval([rat(x) for x in cd['q']], Q(i)) != a[i] * u_eval([rat(x) for x in cd['p']], Q(i)),
             'term ratio holds at the index')
        return dict(ok=True, kind='refutation', refutes=kind, index=i)
    if kind == 'pattern':
        check_cover(cd['cover'], budget); M = cd['cover']['modulus']; x = integer(w.get('residue'), 0, M - 1)
        need(gcd(x, M) == 1, 'witness residue must be coprime')
        square = any(y * y % M == x for y in range(M) if gcd(y, M) == 1); budget.use(M)
        need(square == (x in cover_residues(cd['cover'])), 'residue agrees with the pattern')
        return dict(ok=True, kind='refutation', refutes=kind, residue=x)
    raise Invalid('no refutation rule for this claim kind')


def _law_value(cd, i, budget):
    c = [rat(x) for x in cd['coefficients']]; a = [rat(x) for x in cd['initial']]
    while len(a) <= i:
        budget.use(len(c) + 1); a.append(sum(cj * a[len(a) - len(c) + j] for j, cj in enumerate(c)) if c else Q(0))
    return a[i]


# ------------------------------------------------------------- questions and dispatch

def question(kind, data):
    """The question an object is about; transfers must change it, claims must bind it."""
    need(type(data) is dict, 'object data')
    if kind in ('law', 'gf', 'closed', 'period', 'hyper'): return digest(dict(q='seq', def_=data.get('def')))
    if kind == 'seq': return digest(dict(q='seq', def_=data.get('def')))
    if kind in ('invariant', 'semi', 'fixed', 'inverse', 'map'): return digest(dict(q='map', vars=data.get('vars'), map=data.get('map')))
    if kind in ('exclusion', 'reach'): return digest(dict(q='orbit', orbit=data.get('orbit')))
    if kind == 'orbit': return digest(dict(q='orbit', orbit=data))
    if kind in ('ufam', 'eclass'):
        return digest(dict(q='eclass', a=data.get('a'), m=data.get('m'), r=data.get('r'),
                           terms=len(data['x']) if 'x' in data else data.get('terms')))
    if kind == 'ufrac': return digest(dict(q='en', a=data.get('a'), n=data.get('n'), terms=len(data.get('x', []))))
    if kind == 'en': return digest(dict(q='en', a=data.get('a'), n=data.get('n'), terms=data.get('terms')))
    if kind == 'pattern': return digest(dict(q='esq', a=data['cover'].get('a'), terms=data['cover'].get('terms')))
    if kind in ('cover', 'density', 'esq', 'finite', 'reduction'):
        body = data.get('cover', data) if kind == 'density' else data
        return digest(dict(q='esq', a=body.get('a'), terms=body.get('terms')))
    if kind in ('countval', 'count'):
        return digest(dict(q='count', m=data.get('matrix'), u=data.get('initial'), v=data.get('terminal'), h=data.get('horizon')))
    if kind in ('divis',): return digest(dict(q='divis', expr=data.get('expr')))
    if kind in ('rootmod', 'nosolmod', 'modq'): return digest(dict(q='modroot', poly=data.get('poly'), m=data.get('modulus')))
    if kind in ('nosol', 'diophantine', 'introot'): return digest(dict(q='introot', poly=data.get('poly')))
    if kind == 'eigen': return digest(dict(q='eigen', matrix=data.get('matrix')))
    if kind == 'cycle': return digest(dict(q='cmap', map=data.get('map')))
    if kind in ('descent', 'cclass'):
        return digest(dict(q='cclass', map=data.get('map'), m=data.get('modulus'), r=data.get('residue')))
    if kind in ('dcover', 'cfinite', 'cmap', 'cproblem'):
        return digest(dict(q='cmap', map=data.get('map') if kind != 'cmap' else data))
    if kind in ('identity', 'poly', 'words', 'template'): return digest(dict(q=kind, data=data))
    if kind == 'refutation': return question(data['claim']['kind'], data['claim']['data'])
    if kind == 'residual': return data.get('question', digest(data))
    raise Invalid('unknown object kind ' + str(kind))


CHECKS = dict(law=check_law, gf=check_gf, closed=check_closed, period=check_period, hyper=check_hyper,
              identity=check_identity, fixed=check_fixed, inverse=check_inverse, exclusion=check_exclusion,
              reach=check_reach, ufrac=check_ufrac, ufam=check_ufam, cover=check_cover, finite=check_finite,
              reduction=check_reduction, density=check_density, pattern=check_pattern, countval=check_countval, divis=check_divis,
              rootmod=check_rootmod, nosolmod=check_nosolmod, nosol=check_nosol, descent=check_descent,
              introot=check_introot, eigen=check_eigen, cycle=check_cycle,
              dcover=check_dcover, cfinite=check_cfinite, refutation=check_refutation)


def check(kind, data, budget):
    """Admit a claim of the given kind, or raise Invalid; question kinds are not claims."""
    need(type(data) is dict, 'object data')
    if kind == 'invariant':
        check_invariant(data, budget)
        return dict(ok=True, kind='invariant', scope='P(F(x)) = P(x) as polynomials.', proof='Exact expansion.')
    if kind == 'semi':
        check_invariant(data, budget, data.get('factor'))
        return dict(ok=True, kind='semi', scope='P(F(x)) = lambda*P(x) as polynomials.', proof='Exact expansion.')
    need(kind in CHECKS, 'no checker for kind ' + str(kind))
    try: return CHECKS[kind](data, budget)
    except (KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        raise Invalid('malformed ' + kind + ': ' + type(exc).__name__) from exc
