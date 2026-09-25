"""Checks for Ember's windows: finite, exact views onto problems her other claims cannot state.

A window question names a tool (its question kind), a family and parameters. Three claim kinds answer it:

- value {q, family, params, value}: admitted when this module computes family(params) exactly and obtains value;
- witness {q, family, params, witness}: admitted when the witness proves the family's stated property;
- proof {q, family, params, proof}: admitted when the proof object checks, for example a RUP refutation.

Each family states what it decides, and every family is bounded: a window is a finite fragment of its problem and
never settles the open problem it looks at. This module imports no producer or operator code; the real-number and
discrete families live in window_real.py and window_discrete.py and register here.
"""
import hashlib
import importlib.util
import json
from math import gcd, isqrt
from pathlib import Path


class Invalid(ValueError): pass


def need(condition, reason):
    if not condition: raise Invalid(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def integer(x, low=None, high=None, what='integer field'):
    need(type(x) is int and (low is None or x >= low) and (high is None or x <= high), what)
    return x


# One question kind per tool: the types route her operators, so each tool's moves see only its own windows.
TOOLS = ('census_q', 'primes_q', 'arith_q', 'dioph_q', 'approx_q', 'field_q', 'zeta_q', 'const_q', 'digits_q',
         'interval_q', 'kakeya_q', 'spectrum_q', 'variety_q', 'algebra_q', 'group_q', 'knot_q', 'config_q', 'graph_q',
         'setsys_q', 'additive_q', 'sat_q', 'bigint_q', 'orbit_q', 'dynamics_q', 'circuit_q', 'operator_q', 'design_q',
         'lattice_q', 'covering_q')
CLAIMS = ('value', 'witness', 'proof')
FAMILIES = {}
MEMO = {}
MEMO_SIZE = 64


def family(tool, name, kind, scope):
    """Register a family: value families compute, witness and proof families verify."""
    assert tool in TOOLS and kind in CLAIMS
    def wrap(fn):
        FAMILIES[(tool, name)] = dict(kind=kind, fn=fn, scope=scope)
        return fn
    return wrap


def spec_of(data, kind):
    need(type(data) is dict and data.get('q') in TOOLS and type(data.get('family')) is str
         and type(data.get('params')) is dict, 'window fields')
    spec = FAMILIES.get((data['q'], data['family']))
    need(spec is not None, 'no family ' + str(data.get('family')) + ' for ' + str(data.get('q')))
    need(spec['kind'] == kind, 'family ' + data['family'] + ' answers with ' + spec['kind'])
    return spec


def compute(tool, name, params, budget):
    """The value of a value family, memoised by its canonical parameters (a deterministic computation)."""
    spec = spec_of(dict(q=tool, family=name, params=params), 'value')
    key = digest([tool, name, params])
    if key in MEMO:
        MEMO[key] = MEMO.pop(key); return json.loads(MEMO[key])
    value = json.loads(canonical(spec['fn'](params, budget)))
    while len(MEMO) >= MEMO_SIZE: del MEMO[next(iter(MEMO))]
    MEMO[key] = canonical(value)
    return value


def check(kind, data, budget):
    need(kind in CLAIMS, 'not a window claim')
    field = dict(value='value', witness='witness', proof='proof')[kind]
    need(type(data) is dict and set(data) == {'q', 'family', 'params', field}, 'window claim fields')
    spec = spec_of(data, kind)
    if kind == 'value':
        value = compute(data['q'], data['family'], data['params'], budget)
        need(canonical(value) == canonical(data['value']), 'the stated value differs from the computed value')
        return dict(ok=True, kind='value', scope=spec['scope'], proof='Exact recomputation of the family.')
    summary = spec['fn'](data['params'], data[field], budget)
    return dict(ok=True, kind=kind, scope=spec['scope'], summary=summary,
                proof='The ' + kind + ' checked against the family\'s stated property.')


def refute(kind, data, witness, budget):
    """A value claim is refuted by recomputation; a witness or proof claim by its failing check."""
    need(kind in CLAIMS and witness == {}, 'window refutation takes an empty witness')
    try:
        check(kind, data, budget)
    except Invalid as exc:
        return dict(ok=True, kind='refutation', scope='The ' + kind + ' claim is false as stated: ' + str(exc)[:160],
                    proof='Its own check fails on recomputation.')
    raise Invalid('the claim checks, so it is not refuted')


def question(kind, data):
    need(type(data) is dict, 'object data')
    if kind in TOOLS:
        need(set(data) == {'family', 'params'}, 'window question fields')
        return digest(dict(q='window', tool=kind, family=data['family'], params=data['params']))
    if kind in CLAIMS:
        return digest(dict(q='window', tool=data.get('q'), family=data.get('family'), params=data.get('params')))
    raise Invalid('not a window object')


# ------------------------------------------------------------- integers: primality, sieves, factorization

SMALL_PRIMES = [p for p in range(2, 1000) if all(p % d for d in range(2, isqrt(p) + 1))]
# Deterministic Miller-Rabin: the first k primes as bases decide every n below each bound (Jaeschke; Sorenson and
# Webster, 2015, for the last bound).
MR_TABLE = ((2047, 1), (1373653, 2), (25326001, 3), (3215031751, 4), (2152302898747, 5), (3474749660383, 6),
            (341550071728321, 7), (3825123056546413051, 9), (318665857834031151167461, 12),
            (3317044064679887385961981, 13))
MR_LIMIT = MR_TABLE[-1][0]
SIEVE_LIMIT = 20_000_000
_SIEVE = [bytearray(b'\x00\x00\x01\x01')]


def sieve(n, budget):
    """A primality table below n (cached, extended on demand, at most SIEVE_LIMIT)."""
    need(n <= SIEVE_LIMIT, 'sieve bound')
    table = _SIEVE[0]
    if len(table) >= n: return table
    size = max(n, 2 * len(table)) if 2 * len(table) <= SIEVE_LIMIT else n
    budget.use(size)
    table = bytearray([1]) * size; table[0] = table[1] = 0
    for p in range(2, isqrt(size - 1) + 1):
        if table[p]: table[p * p::p] = bytes(len(range(p * p, size, p)))
    _SIEVE[0] = table
    return table


def is_prime(n, budget):
    """Exact primality: a table below the sieve bound, trial division, then deterministic Miller-Rabin."""
    if n < 2: return False
    if n < len(_SIEVE[0]): return bool(_SIEVE[0][n])
    for p in SMALL_PRIMES:
        if n % p == 0: return n == p
    need(n < MR_LIMIT, 'primality beyond the certified Miller-Rabin range')
    k = next(k for bound, k in MR_TABLE if n < bound)
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    budget.use(k * n.bit_length())
    for a in SMALL_PRIMES[:k]:
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True


def next_prime(n, budget):
    n = max(n + 1, 2)
    while not is_prime(n, budget): n += 1; budget.use()
    return n


def prev_prime(n, budget):
    n -= 1
    while n >= 2 and not is_prime(n, budget): n -= 1; budget.use()
    return n if n >= 2 else None


def _rho(n, budget):
    """A nontrivial factor of composite n by Pollard-Brent rho."""
    if n % 2 == 0: return 2
    for c in range(1, 200):
        y, r, q, g, x, ys = 2, 1, 1, 1, 2, 2
        while g == 1:
            x = y
            for _ in range(r): y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(128, r - k)):
                    y = (y * y + c) % n; q = q * abs(x - y) % n
                budget.use(128)
                g = gcd(q, n); k += 128
            r *= 2
            need(r < 1 << 26, 'factorization bound')
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n; g = gcd(abs(x - ys), n)
        if g != n: return g
    raise Invalid('factorization bound')


def factor(n, budget):
    """Prime factorization {p: e} of n >= 1, every factor certified prime."""
    need(type(n) is int and n >= 1, 'factorization of a positive integer')
    out = {}
    for p in SMALL_PRIMES:
        if p * p > n: break
        while n % p == 0: out[p] = out.get(p, 0) + 1; n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if is_prime(m, budget): out[m] = out.get(m, 0) + 1; continue
        d = _rho(m, budget); stack += [d, m // d]
    return dict(sorted(out.items()))


def sigma(n, budget):
    out = 1
    for p, e in factor(n, budget).items(): out *= (p ** (e + 1) - 1) // (p - 1)
    return out


def phi(n, budget):
    out = n
    for p in factor(n, budget): out = out // p * (p - 1)
    return out


def iroot(n, k):
    """floor(n ** (1/k)) for n >= 0."""
    if n < 2: return n
    x = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x: break
        x = y
    while x ** k > n: x -= 1
    while (x + 1) ** k <= n: x += 1
    return x


def icbrt_floor(v):
    """floor of the real cube root of an integer."""
    if v >= 0: return iroot(v, 3)
    r = iroot(-v, 3)
    return -r if r ** 3 == -v else -r - 1


def fib_pair(n):
    """(F(n), F(n+1)) by fast doubling."""
    if n == 0: return 0, 1
    a, b = fib_pair(n >> 1)
    c = a * (2 * b - a); d = a * a + b * b
    return (d, c + d) if n & 1 else (c, d)


def fib_mod(n, m):
    def go(k):
        if k == 0: return 0, 1
        a, b = go(k >> 1)
        c = a * (2 * b - a) % m; d = (a * a + b * b) % m
        return (d, (c + d) % m) if k & 1 else (c, d)
    return go(n)[0]


def jacobi(a, n):
    need(n > 0 and n % 2 == 1, 'Jacobi symbol modulus')
    a %= n; result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5): result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3: result = -result
        a %= n
    return result if n == 1 else 0


def lucas_lehmer(p, budget):
    """Whether 2^p - 1 is prime, for prime p (exact)."""
    if p == 2: return True
    M = (1 << p) - 1; s = 4
    budget.use(p * (p // 64 + 1))
    for _ in range(p - 2):
        s = s * s - 2
        s = (s & M) + (s >> p)
        if s >= M: s -= M
    return s == 0


def pepin(n, budget):
    """Whether the Fermat number 2^(2^n) + 1 is prime (Pepin's test; n = 0 gives 3)."""
    need(0 <= n <= 15, 'Fermat index bound')
    F = (1 << (1 << n)) + 1
    if n == 0: return True
    budget.use((1 << n) * ((1 << n) // 64 + 1))
    return pow(3, (F - 1) // 2, F) == F - 1


def bernoulli_mod(p, budget):
    """B_0 .. B_(p-3) modulo p (their denominators are prime to p there)."""
    need(p >= 5, 'prime at least 5')
    inv = [0, 1] + [0] * (p - 2)
    for i in range(2, p): inv[i] = (p - (p // i) * inv[p % i] % p) % p
    B = [1]; row = [1, 1]  # row holds binomial(m + 1, k) mod p
    for m in range(1, p - 2):
        row = [1] + [(row[k - 1] + row[k]) % p for k in range(1, len(row))] + [1]
        budget.use(m)
        # sum over k <= m of binomial(m + 1, k) B_k = 0, and binomial(m + 1, m) = m + 1 is prime to p here
        B.append(-sum(row[k] * B[k] for k in range(m)) * inv[row[m]] % p)
    return B


def regular(p, budget):
    need(p >= 3, 'odd prime')
    if p in (3, 5): return True
    B = bernoulli_mod(p, budget)
    return all(B[k] % p for k in range(2, p - 2, 2))


def class_number_imaginary(D, budget):
    """h(D) for a negative discriminant D: the number of reduced primitive forms."""
    need(D < 0 and D % 4 in (0, 1), 'negative discriminant')
    h = 0; a = 1
    while 3 * a * a <= -D:
        for b in range(-a + 1, a + 1):
            if (b * b - D) % (4 * a): continue
            c = (b * b - D) // (4 * a)
            if c < a or (c == a and b < 0) or gcd(gcd(a, abs(b)), c) != 1: continue
            h += 1
        budget.use(2 * a); a += 1
    return h


def class_number_real(d, budget):
    """The class number of Q(sqrt d), d > 1 squarefree: reduced indefinite forms counted by cycles (the narrow class
    number), halved when the principal cycle does not contain -1 times the principal form (norm of the unit +1)."""
    need(d > 1, 'real quadratic field')
    for p, e in factor(d, budget).items(): need(e == 1, 'squarefree d')
    D = d if d % 4 == 1 else 4 * d; r = isqrt(D)
    def reduced(a, b):
        # |sqrt(D) - 2|a|| < b < sqrt(D), decided with integers (D is not a square)
        A = abs(a)
        return 0 < b and b * b < D and D < (2 * A + b) ** 2 and (2 * A - b <= 0 or (2 * A - b) ** 2 < D)
    forms = []
    for b in range(1, r + 1):
        if (b * b - D) % 4: continue
        N = (D - b * b) // 4
        for a in range(1, r + 1):  # a reduced form has |a| < sqrt(D)
            budget.use()
            if N % a: continue
            for s in (1, -1):
                A, C = s * a, -s * (N // a)
                if reduced(A, b) and gcd(gcd(a, b), abs(C)) == 1: forms.append((A, b, C))
    forms = set(forms)
    def rho(f):
        a, b, c = f; C = abs(c)
        # b' = -b mod 2|c| in (r - 2|c|, r], the unique reduced successor
        bp = -b % (2 * C)
        while bp <= r - 2 * C or bp > r:
            bp += 2 * C if bp <= r - 2 * C else -2 * C
        return (c, bp, (bp * bp - D) // (4 * c))
    seen = {}; cycles = 0
    for f in sorted(forms):
        if f in seen: continue
        cycles += 1; g = f
        while g not in seen:
            budget.use(); seen[g] = cycles; g = rho(g)
            need(g in forms, 'reduction left the reduced forms')
    b0 = next(b for b in range(r, 0, -1) if (b * b - D) % 4 == 0 and reduced(1, b))
    principal = (1, b0, (b0 * b0 - D) // 4)
    minus = any(f[0] == -1 for f in seen if seen[f] == seen[principal])
    return cycles if minus else cycles // 2


# ------------------------------------------------------------- the predicate language of tallies

MAX_TALLY = 10_000_000


def _ev(e, env, budget, depth=0):
    """Evaluate an integer expression or predicate. Integers are literals, strings are bound variables."""
    need(depth < 40, 'expression depth')
    budget.use()
    if type(e) is int: return e
    if type(e) is str:
        need(e in env, 'unbound variable ' + e); return env[e]
    need(type(e) is list and e and type(e[0]) is str, 'expression node')
    head, args = e[0], e[1:]
    if head in ('and', 'or'):
        for a in args:
            v = _ev(a, env, budget, depth + 1)
            if head == 'and' and not v: return False
            if head == 'or' and v: return True
        return head == 'and'
    if head in ('exists', 'forall'):
        var, lo, hi, body = args
        need(type(var) is str and var != 'n', 'quantified variable')
        lo, hi = _ev(lo, env, budget, depth + 1), _ev(hi, env, budget, depth + 1)
        need(hi - lo <= 100_000, 'quantifier range')
        for v in range(lo, hi):
            value = _ev(body, dict(env, **{var: v}), budget, depth + 1)
            if head == 'exists' and value: return True
            if head == 'forall' and not value: return False
        return head == 'forall'
    vals = [_ev(a, env, budget, depth + 1) for a in args]
    fn = FUNCTIONS.get(head)
    need(fn is not None, 'unknown function ' + head)
    arity, run = fn
    need(arity is None or len(vals) == arity, 'arity of ' + head)
    return run(vals, budget)


def _nonneg(x, what): need(type(x) is int and x >= 0, what); return x


def _pow(v, budget):
    b, k = v; need(type(k) is int and 0 <= k <= 4096 and abs(b).bit_length() * k <= 1 << 20, 'power bound')
    budget.use(abs(b).bit_length() * k // 64 + 1); return b ** k


def _fact(v, budget):
    n = _nonneg(v[0], 'factorial argument'); need(n <= 3000, 'factorial bound')
    out = 1
    for i in range(2, n + 1): out *= i
    budget.use(n); return out


def _rev(v, budget):
    n = _nonneg(v[0], 'reversal argument'); budget.use(len(str(n)) // 32 + 1); return int(str(n)[::-1])


def _small(n, what, bound=10 ** 30):
    need(type(n) is int and 1 <= n <= bound, what); return n


def _primroot(v, budget):
    a, p = v
    if p < 3 or not is_prime(p, budget) or a % p == 0: return False
    return all(pow(a, (p - 1) // q, p) != 1 for q in factor(p - 1, budget))


def _goldbach(v, budget):
    n = v[0]
    if n < 4 or n % 2: return False
    for p in range(2, n // 2 + 1):
        if is_prime(p, budget) and is_prime(n - p, budget): return True
    return False


def _field_ok(d, budget):
    _small(d, 'field bound', 10 ** 6)
    return d > 1 and all(e == 1 for e in factor(d, budget).values())


def _fib(v, budget):
    n = _nonneg(v[0], 'Fibonacci index'); need(n <= 100_000, 'Fibonacci bound'); budget.use(n // 64 + 1)
    return fib_pair(n)[0]


FUNCTIONS = {
    # arithmetic
    'add': (2, lambda v, b: v[0] + v[1]), 'sub': (2, lambda v, b: v[0] - v[1]), 'mul': (2, lambda v, b: v[0] * v[1]),
    'neg': (1, lambda v, b: -v[0]), 'pow': (2, _pow), 'mod': (2, lambda v, b: v[0] % v[1] if v[1] else None),
    'fdiv': (2, lambda v, b: v[0] // v[1] if v[1] else None), 'abs': (1, lambda v, b: abs(v[0])),
    'pow2': (1, lambda v, b: _pow([2, _nonneg(v[0], 'exponent')], b)), 'gcd': (2, lambda v, b: gcd(v[0], v[1])),
    'isqrt': (1, lambda v, b: isqrt(_nonneg(v[0], 'square root argument'))),
    'digitsum': (1, lambda v, b: sum(map(int, str(abs(v[0]))))),
    'fact': (1, _fact), 'rev': (1, _rev),
    'fib': (1, lambda v, b: _fib(v, b)),
    # comparisons and logic
    'eq': (2, lambda v, b: v[0] == v[1]), 'ne': (2, lambda v, b: v[0] != v[1]), 'lt': (2, lambda v, b: v[0] < v[1]),
    'le': (2, lambda v, b: v[0] <= v[1]), 'gt': (2, lambda v, b: v[0] > v[1]), 'ge': (2, lambda v, b: v[0] >= v[1]),
    'not': (1, lambda v, b: not v[0]), 'divides': (2, lambda v, b: v[0] != 0 and v[1] % v[0] == 0),
    'even': (1, lambda v, b: v[0] % 2 == 0), 'odd': (1, lambda v, b: v[0] % 2 == 1),
    'square': (1, lambda v, b: v[0] >= 0 and isqrt(v[0]) ** 2 == v[0]),
    'cube': (1, lambda v, b: (lambda r: r ** 3 == abs(v[0]))(iroot(abs(v[0]), 3))),
    'palindrome': (1, lambda v, b: str(abs(v[0])) == str(abs(v[0]))[::-1]),
    # primes (tools: infinitude, prime distribution)
    'prime': (1, lambda v, b: is_prime(v[0], b)),
    'nextprime': (1, lambda v, b: next_prime(v[0], b)), 'prevprime': (1, lambda v, b: prev_prime(v[0], b)),
    'goldbach': (1, _goldbach),
    # arithmetic functions
    'sigma': (1, lambda v, b: sigma(_small(v[0], 'sigma argument'), b)),
    'phi': (1, lambda v, b: phi(_small(v[0], 'phi argument'), b)),
    'tau': (1, lambda v, b: (lambda f: __import__('math').prod(e + 1 for e in f.values()))(factor(_small(v[0], 'tau argument'), b))),
    'aliquot': (1, lambda v, b: sigma(_small(v[0], 'aliquot argument'), b) - v[0]),
    'rad': (1, lambda v, b: __import__('math').prod(factor(_small(v[0], 'rad argument'), b))),
    'omega': (1, lambda v, b: len(factor(_small(v[0], 'omega argument'), b))),
    'squarefree': (1, lambda v, b: all(e == 1 for e in factor(_small(v[0], 'squarefree argument'), b).values())),
    # big integers
    'mersenne': (1, lambda v, b: is_prime(v[0], b) and lucas_lehmer(_small(v[0], 'Mersenne exponent', 20_000), b)),
    'fermat': (1, lambda v, b: pepin(v[0], b)),
    'wieferich': (1, lambda v, b: v[0] > 2 and pow(2, v[0] - 1, v[0] * v[0]) == 1),
    'primroot': (2, _primroot),
    # number fields
    'regular': (1, lambda v, b: is_prime(v[0], b) and v[0] > 2 and regular(_small(v[0], 'regular prime bound', 2000), b)),
    # (0 stands for "not a field of this kind": d not squarefree, or -D not a discriminant)
    'classno_real': (1, lambda v, b: class_number_real(v[0], b) if _field_ok(v[0], b) else 0),
    'classno_imag': (1, lambda v, b: class_number_imaginary(-_small(v[0], 'discriminant bound', 10 ** 7), b)
                     if v[0] % 4 in (0, 3) else 0),
}


def tally(pred, lo, bounds, budget):
    """How many n in [lo, bound) satisfy pred, for each bound (increasing)."""
    integer(lo, -10 ** 12, 10 ** 12, 'tally start')
    need(type(bounds) is list and 1 <= len(bounds) <= 12 and all(type(b) is int for b in bounds)
         and all(x < y for x, y in zip([lo] + bounds, bounds)), 'increasing bounds above the start')
    need(bounds[-1] - lo <= MAX_TALLY, 'tally range')
    if bounds[-1] <= SIEVE_LIMIT and bounds[-1] > 0: sieve(min(SIEVE_LIMIT, 2 * bounds[-1] + 64), budget)
    counts = []; count = 0; n = lo
    for bound in bounds:
        while n < bound:
            if _ev(pred, dict(n=n), budget): count += 1
            n += 1
        counts.append(count)
    return counts


@family('census_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_tally(params, budget):
    need(set(params) == {'pred', 'lo', 'bounds'}, 'tally fields')
    return tally(params['pred'], params['lo'], params['bounds'], budget)


@family('primes_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_prime_tally(params, budget): return fam_tally(params, budget)


@family('arith_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_arith_tally(params, budget): return fam_tally(params, budget)


@family('dioph_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_dioph_tally(params, budget): return fam_tally(params, budget)


@family('bigint_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_bigint_tally(params, budget): return fam_tally(params, budget)


@family('field_q', 'tally', 'value',
        'For each listed bound, the number of integers n with start <= n < bound satisfying the predicate.')
def fam_field_tally(params, budget): return fam_tally(params, budget)


@family('census_q', 'members', 'value',
        'Every integer n with start <= n < end satisfying the predicate, in increasing order (at most 4096).')
def fam_members(params, budget):
    need(set(params) == {'pred', 'lo', 'hi'}, 'member list fields')
    lo, hi = integer(params['lo'], -10 ** 12, 10 ** 12), integer(params['hi'])
    need(lo < hi and hi - lo <= MAX_TALLY, 'member range')
    if 0 < hi <= SIEVE_LIMIT: sieve(min(SIEVE_LIMIT, 2 * hi + 64), budget)
    out = []
    for n in range(lo, hi):
        if _ev(params['pred'], dict(n=n), budget):
            out.append(n); need(len(out) <= 4096, 'member list bound')
    return out


# ------------------------------------------------------------- prime distribution

@family('primes_q', 'gap_records', 'value',
        'The record gaps between consecutive primes p < q with lo <= p < hi: each listed [p, q - p] exceeds every '
        'earlier gap in the range.')
def fam_gap_records(params, budget):
    need(set(params) == {'lo', 'hi'}, 'gap fields')
    lo, hi = integer(params['lo'], 2), integer(params['hi'])
    need(lo < hi <= SIEVE_LIMIT // 2 and hi - lo <= MAX_TALLY, 'gap range')
    table = sieve(min(SIEVE_LIMIT, 2 * hi + 1000), budget)
    p = lo if table[lo] else next_prime(lo, budget); best = 0; out = []
    while p < hi:
        q = p + 1
        while not table[q]: q += 1
        budget.use(q - p)
        if q - p > best: best = q - p; out.append([p, best])
        p = q
    return out


@family('primes_q', 'goldbach', 'value',
        'Whether every even n with lo <= n < hi is a sum of two primes; with it, the even n whose least such prime p '
        'is largest, and that p.')
def fam_goldbach(params, budget):
    need(set(params) == {'lo', 'hi'}, 'Goldbach fields')
    lo, hi = integer(params['lo'], 4), integer(params['hi'])
    need(lo < hi <= 4_000_000, 'Goldbach range')
    table = sieve(hi + 1, budget); worst = [lo + lo % 2, 0]; failures = []
    for n in range(lo + lo % 2, hi, 2):
        p = 2
        while p <= n // 2 and not (table[p] and table[n - p]): p += 1
        budget.use(p)
        if p > n // 2: failures.append(n); need(len(failures) <= 64, 'failure list bound'); continue
        if p > worst[1]: worst = [n, p]
    return dict(all=not failures, failures=failures, worst=worst)


@family('primes_q', 'gilbreath', 'value',
        'For the first k primes, the leading entries of the rows of iterated absolute differences: the first row index '
        'whose leading entry is not 1, or 0 if every row checked starts with 1.')
def fam_gilbreath(params, budget):
    need(set(params) == {'k'}, 'Gilbreath fields'); k = integer(params['k'], 2, 20_000)
    table = sieve(max(1000, int(k * 12 + 100)), budget)
    row = [p for p in range(len(table)) if table[p]][:k]
    need(len(row) == k, 'prime table too short')
    for i in range(1, k):
        row = [abs(b - a) for a, b in zip(row, row[1:])]
        budget.use(len(row))
        if row[0] != 1: return i
    return 0


# ------------------------------------------------------------- arithmetic functions

@family('arith_q', 'totient_singletons', 'value',
        'The integers m with lo <= m < hi having exactly one solution x of phi(x) = m (Carmichael conjectured there '
        'are none).')
def fam_totient_singletons(params, budget):
    need(set(params) == {'lo', 'hi'}, 'totient fields')
    lo, hi = integer(params['lo'], 1), integer(params['hi'])
    need(lo < hi <= 1000, 'totient range')
    top = max(7, hi * hi)  # phi(x) >= sqrt(x) for x > 6, so phi(x) < hi forces x < hi^2
    budget.use(top)
    ph = list(range(top + 1))
    for p in range(2, top + 1):
        if ph[p] == p:
            for m in range(p, top + 1, p): ph[m] -= ph[m] // p
    count = {}
    for x in range(1, top + 1):
        if lo <= ph[x] < hi: count[ph[x]] = count.get(ph[x], 0) + 1
    return sorted(m for m, c in count.items() if c == 1)


@family('arith_q', 'odd_weird', 'witness',
        'Every odd abundant n below the bound is semiperfect: the witness names, for each, distinct proper divisors '
        'summing to n. So no odd weird number lies below the bound.')
def fam_odd_weird(params, witness, budget):
    need(set(params) == {'hi'}, 'odd weird fields'); hi = integer(params['hi'], 3, 2_000_000)
    need(type(witness) is dict, 'witness table')
    budget.use(hi * 2)
    s = [0] * hi
    for d in range(1, hi // 2 + 1):
        for m in range(2 * d, hi, d): s[m] += d
    abundant = [n for n in range(1, hi, 2) if s[n] > n]
    need(set(witness) == {str(n) for n in abundant}, 'witnesses for exactly the odd abundant numbers')
    for n in abundant:
        parts = witness[str(n)]
        need(type(parts) is list and len(set(parts)) == len(parts) and all(type(d) is int and 0 < d < n and n % d == 0
                                                                           for d in parts), 'distinct proper divisors')
        need(sum(parts) == n, 'the divisors of ' + str(n) + ' do not sum to it')
        budget.use(len(parts))
    return dict(odd_abundant=len(abundant))


# ------------------------------------------------------------- Diophantine boxes

@family('dioph_q', 'erdos_moser', 'value',
        'Every solution of 1^k + 2^k + ... + (m-1)^k = m^k with 2 <= m <= m_max and 1 <= k <= k_max.')
def fam_erdos_moser(params, budget):
    need(set(params) == {'m_max', 'k_max'}, 'Erdos-Moser fields')
    M, K = integer(params['m_max'], 2, 2000), integer(params['k_max'], 1, 200)
    out = []
    for k in range(1, K + 1):
        s = 0
        for m in range(2, M + 1):
            s += (m - 1) ** k; budget.use(k // 16 + 1)
            if s == m ** k: out.append([m, k])
    return out


@family('dioph_q', 'euler_bricks', 'value',
        'Every Euler brick a < b < c <= max_edge (a^2+b^2, a^2+c^2, b^2+c^2 all squares) with gcd(a, b, c) = 1, each '
        'marked perfect when a^2 + b^2 + c^2 is also a square.')
def fam_euler_bricks(params, budget):
    need(set(params) == {'max_edge'}, 'brick fields'); N = integer(params['max_edge'], 1, 20_000)
    partner = {}
    for a in range(1, N + 1):
        for b in range(a + 1, N + 1):
            budget.use()
            s = a * a + b * b; r = isqrt(s)
            if r * r == s: partner.setdefault(a, []).append(b)
    out = []
    for a, bs in sorted(partner.items()):
        for i, b in enumerate(bs):
            for c in bs[i + 1:]:
                budget.use()
                t = b * b + c * c
                if isqrt(t) ** 2 == t and gcd(gcd(a, b), c) == 1:
                    u = a * a + b * b + c * c
                    out.append([a, b, c, isqrt(u) ** 2 == u])
    return out


def _perfect_power(n):
    """(c, z) with c^z = n and z >= 2 maximal, or None."""
    if n < 4: return None
    for z in range(n.bit_length(), 1, -1):
        c = iroot(n, z)
        if c ** z == n and c > 1: return c, z
    return None


@family('dioph_q', 'power_sums', 'value',
        'Every solution of a^x + b^y = c^z with coprime positive a <= b... bases at most base_max (a, b), exponents x, '
        'y, z in [exp_min, exp_max], and 1/x + 1/y + 1/z < 1 when the mode is fermat_catalan; mode beal lists the '
        'coprime solutions with every exponent at least 3.')
def fam_power_sums(params, budget):
    need(set(params) == {'base_max', 'exp_min', 'exp_max', 'mode'} and params['mode'] in ('beal', 'fermat_catalan'),
         'power sum fields')
    A, e0, e1 = integer(params['base_max'], 1, 400), integer(params['exp_min'], 2, 30), integer(params['exp_max'], 2, 30)
    need(e0 <= e1, 'exponent range')
    out = set()
    for a in range(1, A + 1):
        for b in range(1, A + 1):
            if gcd(a, b) != 1: continue
            for x in range(e0, e1 + 1):
                for y in range(e0, e1 + 1):
                    budget.use(4)
                    s = a ** x + b ** y
                    for z in range(e0, min(e1, s.bit_length()) + 1):
                        c = iroot(s, z)
                        if c ** z != s: continue
                        if params['mode'] == 'fermat_catalan' and not (x * y + y * z + z * x < x * y * z): continue
                        if params['mode'] == 'beal' and min(x, y, z) < 3: continue
                        key = tuple(sorted([(a, x), (b, y)])) + ((c, z),)
                        out.add(key)
    return [[list(u), list(v), list(w)] for u, v, w in sorted(out)]


@family('dioph_q', 'power_differences', 'value',
        'For each d with 1 <= d <= d_max, the number of pairs of perfect powers u < v <= x_max (exponent >= 2) with '
        'v - u = d, listed when at least min_count.')
def fam_power_differences(params, budget):
    need(set(params) == {'x_max', 'd_max', 'min_count'}, 'power difference fields')
    X, D, K = integer(params['x_max'], 4, 10 ** 12), integer(params['d_max'], 1, 10 ** 6), integer(params['min_count'], 1)
    powers = set()
    for k in range(2, X.bit_length() + 1):
        for c in range(2, iroot(X, k) + 1): powers.add(c ** k); budget.use()
    powers.add(1); ps = sorted(powers); count = {}
    for i, u in enumerate(ps):
        for v in ps[i + 1:]:
            if v - u > D: break
            budget.use(); count[v - u] = count.get(v - u, 0) + 1
    return {str(d): c for d, c in sorted(count.items()) if c >= K}


@family('dioph_q', 'abc_hits', 'value',
        'Every coprime triple a + b = c with a <= b and c < c_max whose quality log c / log rad(abc) is at least q '
        '(checked as c^den >= rad(abc)^num).')
def fam_abc_hits(params, budget):
    need(set(params) == {'c_max', 'q'}, 'abc fields'); C = integer(params['c_max'], 3, 20_000)
    q = params['q']; need(type(q) is list and len(q) == 2 and all(type(x) is int and x > 0 for x in q), 'quality')
    num, den = q
    rad = [1] * C
    for p in range(2, C):
        if rad[p] == 1:
            for m in range(p, C, p): rad[m] *= p
    budget.use(C * 4)
    out = []
    for c in range(3, C):
        for a in range(1, c // 2 + 1):
            budget.use()
            b = c - a
            if gcd(a, b) != 1: continue
            r = rad[a] * rad[b] * rad[c]
            if c ** den >= r ** num: out.append([a, b, c])
    return out


@family('dioph_q', 'pascal', 'value',
        'Every value v <= n_max (v > 1) occurring at least min_count times among the binomial coefficients C(n, k), '
        'with its multiplicity.')
def fam_pascal(params, budget):
    need(set(params) == {'n_max', 'min_count'}, 'Pascal fields')
    N, K = integer(params['n_max'], 2, 10 ** 10), integer(params['min_count'], 2)
    count = {}
    k = 2
    while True:
        # C(n, k) with n >= 2k; C(2k, k) grows past N quickly
        n = 2 * k; c = 1
        for i in range(k): c = c * (n - i) // (i + 1)
        if c > N: break
        while c <= N:
            budget.use()
            count[c] = count.get(c, 0) + (1 if n == 2 * k else 2)
            n += 1; c = c * n // (n - k)
        k += 1
    out = {}
    for v, c in count.items():
        total = c + (2 if v > 2 else 1)  # C(v, 1) and C(v, v - 1)
        if total >= K: out[str(v)] = total
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))


@family('dioph_q', 'three_cubes', 'value',
        'For 1 <= n < n_max with n not 4 or 5 mod 9: how many are x^3 + y^3 + z^3 with |x|, |y|, |z| <= bound, and '
        'which are not.')
def fam_three_cubes(params, budget):
    need(set(params) == {'n_max', 'bound'}, 'three cubes fields')
    N, B = integer(params['n_max'], 2, 1001), integer(params['bound'], 1, 3000)
    targets = {n for n in range(1, N) if n % 9 not in (4, 5)}; found = set()
    for x in range(-B, B + 1):
        x3 = x ** 3
        for y in range(-B, x + 1):
            s = x3 + y ** 3; budget.use()
            # z^3 = n - s with 1 <= n < N: z runs over a short interval
            lo, hi = icbrt_floor(-s), icbrt_floor(N - 1 - s)
            for z in range(max(lo, -B), min(hi, B) + 1):
                n = s + z ** 3
                if n in targets: found.add(n)
    missing = sorted(targets - found)
    return dict(represented=len(found), missing=missing)


@family('dioph_q', 'congruent', 'value',
        'For squarefree n <= n_max: the n Tunnell\'s counts exclude (not congruent, unconditionally), the n with a '
        'rational right triangle of area n found from Pythagorean triples with legs from m, k <= search, and the rest '
        '(Tunnell equality holds, so congruent if the Birch and Swinnerton-Dyer conjecture holds).')
def fam_congruent(params, budget):
    need(set(params) == {'n_max', 'search'}, 'congruent fields')
    N, S = integer(params['n_max'], 1, 2000), integer(params['search'], 1, 1000)
    def count(target, a, b, c):
        t = 0; X = isqrt(target // a) if a else 0
        for x in range(-X, X + 1):
            r1 = target - a * x * x
            Y = isqrt(r1 // b)
            for y in range(-Y, Y + 1):
                r2 = r1 - b * y * y
                if r2 % c: continue
                z2 = r2 // c; z = isqrt(z2)
                if z * z == z2: t += 1 if z == 0 else 2
            budget.use(2 * Y + 1)
        return t
    squarefree = [n for n in range(1, N + 1) if all(n % (p * p) for p in range(2, isqrt(n) + 1))]
    spf = list(range(2 * S + 2))
    for q in range(2, isqrt(2 * S + 1) + 1):
        if spf[q] == q:
            for j in range(q * q, 2 * S + 2, q):
                if spf[j] == j: spf[j] = q
    def odd_primes(x, acc):
        while x > 1:
            q = spf[x]; x //= q; acc[q] = acc.get(q, 0) ^ 1
    area = {}
    for m in range(2, S + 1):
        for k in range(1, m):
            if (m - k) % 2 == 0 or gcd(m, k) != 1: continue
            budget.use(8); acc = {}
            for part in (m, k, m - k, m + k): odd_primes(part, acc)
            core = 1
            for q, odd in acc.items():
                if odd: core *= q
            if core <= N and core not in area: area[core] = [m, k]
    out = dict(not_congruent=[], triangle={}, tunnell_equal_only=[])
    for n in squarefree:
        if n % 2: A, B = count(n, 2, 1, 8), count(n, 2, 1, 32)
        else: A, B = count(n // 2, 4, 1, 8), count(n // 2, 4, 1, 32)
        if A != 2 * B: out['not_congruent'].append(n)
        elif n in area: out['triangle'][str(n)] = area[n]
        else: out['tunnell_equal_only'].append(n)
    return out


# ------------------------------------------------------------- number fields

@family('field_q', 'irregular_pairs', 'value',
        'Every irregular pair (p, 2k): p <= p_max prime, 2 <= 2k <= p - 3 and p divides the numerator of B_2k.')
def fam_irregular_pairs(params, budget):
    need(set(params) == {'p_max'}, 'irregular pair fields'); P = integer(params['p_max'], 5, 1200)
    out = []
    for p in range(5, P + 1):
        if not is_prime(p, budget): continue
        B = bernoulli_mod(p, budget)
        out += [[p, k] for k in range(2, p - 2, 2) if B[k] % p == 0]
    return out


@family('field_q', 'class_numbers', 'value',
        'For squarefree d with 2 <= d <= d_max: the number of real quadratic fields Q(sqrt d) of each class number.')
def fam_class_numbers(params, budget):
    need(set(params) == {'d_max'}, 'class number fields'); N = integer(params['d_max'], 2, 20_000)
    hist = {}
    for d in range(2, N + 1):
        if any(d % (p * p) == 0 for p in range(2, isqrt(d) + 1)): continue
        h = class_number_real(d, budget); hist[str(h)] = hist.get(str(h), 0) + 1
    return dict(sorted(hist.items(), key=lambda kv: int(kv[0])))


@family('field_q', 'mahler_small', 'value',
        'Among the integer polynomials of the given degree with leading coefficient 1, coefficients in {-1, 0, 1}, '
        'nonzero constant term, reciprocal when asked, and not a product of cyclotomic polynomials: those whose Mahler '
        'measure is certified below the bound by Graeffe iteration, and those the iteration count leaves undecided.')
def fam_mahler_small(params, budget):
    need(set(params) == {'degree', 'bound', 'reciprocal', 'iterations'}, 'Mahler fields')
    d, it = integer(params['degree'], 2, 14), integer(params['iterations'], 4, 16)
    bound = params['bound']
    need(type(bound) is list and len(bound) == 2 and all(type(x) is int for x in bound) and bound[0] > bound[1] > 0,
         'bound above 1')
    bnum, bden = bound; recip = params['reciprocal'] is True
    from itertools import product
    free = d // 2 if recip else d - 1  # coefficients 1..d-1 (reciprocal: 1..d//2), c_0 = c_d or chosen
    below, undecided = [], []
    for tail in product((-1, 0, 1), repeat=free):
        for c0 in ((1,) if recip else (-1, 1)):
            if recip:
                half = [c0] + list(tail); coeffs = half + half[:d + 1 - len(half)][::-1]
            else:
                coeffs = [c0] + list(tail) + [1]
            if len(coeffs) != d + 1 or coeffs[-1] != 1: continue
            g = _strip_cyclotomic(coeffs, budget)
            if len(g) == 1: continue
            lo2, hi2 = _mahler_powers(g, it, budget)  # M^(2^(it+1)) lies in [lo2, hi2]
            e = 1 << (it + 1)
            if hi2 * bden ** e < bnum ** e: below.append(coeffs)
            elif lo2 * bden ** e < bnum ** e: undecided.append(coeffs)
    return dict(below=below, undecided=undecided)


def _pdivmod(a, b):
    """Division of integer polynomials (lowest degree first) by a monic divisor: (quotient, remainder)."""
    a = list(a); db = len(b) - 1
    if len(a) - 1 < db: return [0], a
    q = [0] * (len(a) - db)
    for i in range(len(a) - 1, db - 1, -1):
        c = a[i]
        if c:
            q[i - db] = c
            for j in range(db + 1): a[i - db + j] -= c * b[j]
    r = a[:db] or [0]
    while len(r) > 1 and r[-1] == 0: r.pop()
    return q, r


_CYCLOTOMIC = {}


def _cyclotomic(n):
    """Phi_n with integer coefficients, lowest degree first."""
    if n not in _CYCLOTOMIC:
        p = [-1] + [0] * (n - 1) + [1]  # x^n - 1
        for d in range(1, n):
            if n % d == 0: p, _ = _pdivmod(p, _cyclotomic(d))
        _CYCLOTOMIC[n] = p
    return _CYCLOTOMIC[n]


def _strip_cyclotomic(coeffs, budget):
    """Divide out every factor x and every cyclotomic factor of an integer polynomial."""
    g = list(coeffs)
    while len(g) > 1 and g[0] == 0: g = g[1:]
    n = 1
    while n <= 240:
        c = _cyclotomic(n)
        if len(c) > len(g): n += 1; continue
        q, r = _pdivmod(g, c); budget.use(len(g) * len(c))
        if all(x == 0 for x in r): g = q
        else: n += 1
    return g


def _graeffe(h):
    """The Graeffe transform: roots squared. h(x) = e(x^2) + x o(x^2) gives (-1)^d (e(y)^2 - y o(y)^2)."""
    d = len(h) - 1; e2 = _psq(h[0::2]); o2 = _psq(h[1::2]); g = [0] * (d + 1)
    for i, c in enumerate(e2): g[i] += c
    for i, c in enumerate(o2): g[i + 1] -= c
    return [-c for c in g] if d % 2 else g


def _mahler_powers(g, it, budget):
    """Bounds on M(g)^(2^(it+1)) after it Graeffe steps h: M(h) <= ||h||_2 (Landau) and ||h||_2^2 <= C(2d, d) M(h)^2
    (from |h_j| <= C(d, j) M(h))."""
    from math import comb
    from fractions import Fraction
    h = list(g); d = len(g) - 1
    for _ in range(it):
        h = _graeffe(h); budget.use(d * d)
    norm2 = sum(c * c for c in h)
    return Fraction(norm2, comb(2 * d, d)), Fraction(norm2)


def _psq(a):
    out = [0] * (2 * len(a) - 1) if a else []
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(a): out[i + j] += x * y
    return out


# ------------------------------------------------------------- big integers

@family('bigint_q', 'mersenne', 'value',
        'Every prime p <= p_max for which 2^p - 1 is prime (Lucas-Lehmer).')
def fam_mersenne(params, budget):
    need(set(params) == {'p_max'}, 'Mersenne fields'); P = integer(params['p_max'], 2, 6000)
    return [p for p in range(2, P + 1) if is_prime(p, budget) and lucas_lehmer(p, budget)]


@family('bigint_q', 'fermat', 'value', 'Every n <= n_max for which 2^(2^n) + 1 is prime (Pepin).')
def fam_fermat(params, budget):
    need(set(params) == {'n_max'}, 'Fermat fields'); N = integer(params['n_max'], 0, 15)
    return [n for n in range(N + 1) if pepin(n, budget)]


@family('bigint_q', 'wall_sun_sun', 'value',
        'Every prime 5 < p < p_max with p^2 dividing F(p - (p/5)), where (p/5) is the Legendre symbol.')
def fam_wall_sun_sun(params, budget):
    need(set(params) == {'p_max'}, 'Wall-Sun-Sun fields'); P = integer(params['p_max'], 7, 5_000_000)
    table = sieve(P + 1, budget); out = []
    for p in range(7, P):
        if not table[p]: continue
        budget.use(4 * p.bit_length())
        e = 1 if p % 5 in (1, 4) else -1
        if fib_mod(p - e, p * p) == 0: out.append(p)
    return out


def proth_prime(k, n, a, budget):
    """Proth: N = k 2^n + 1 with k < 2^n is prime if a^((N-1)/2) = -1 mod N."""
    N = k * (1 << n) + 1
    need(k % 2 == 1 and k < (1 << n), 'Proth form')
    budget.use(n * (n // 64 + 1))
    return pow(a, (N - 1) // 2, N) == N - 1


def _lucas_uv(P, Q, k, N):
    """(U_k, V_k) mod N of the Lucas sequences with parameters P, Q."""
    U, V, Qk = 0, 2, 1  # U_0, V_0, Q^0
    Uk, Vk = 1, P % N
    # binary ladder from the top bit
    U, V, Qm = 0, 2, 1
    for bit in bin(k)[2:]:
        # double: U_2m = U_m V_m, V_2m = V_m^2 - 2 Q^m
        U, V, Qm = U * V % N, (V * V - 2 * Qm) % N, Qm * Qm % N
        if bit == '1':
            # add one: U_(m+1) = (P U_m + V_m)/2, V_(m+1) = (D U_m + P V_m)/2
            D = P * P - 4 * Q
            U, V = (P * U + V), (D * U + P * V)
            U = U * pow(2, -1, N) % N; V = V * pow(2, -1, N) % N; Qm = Qm * Q % N
    return U, V


def riesel_prime(k, n, P, budget):
    """An N+1 test for N = k 2^n - 1 (k odd, k < 2^n) with Q = 1 and D = P^2 - 4: N is prime when Jacobi(D, N) = -1,
    V_((N+1)/2) = -2 (mod N) and gcd(U_((N+1)/q), N) = 1 for every odd prime q dividing k. Proof: for a prime p | N,
    D is a unit mod p, so alpha = (P + sqrt D)/2 lives in a reduced ring; alpha^((N+1)/2) = -1 and the gcd conditions
    give alpha order exactly N + 1. Alpha has norm 1, so its order divides p + 1 (or p - 1 when D is a square mod p),
    hence N + 1 <= p + 1 and N = p."""
    N = k * (1 << n) - 1
    need(k % 2 == 1 and k < (1 << n) and N > 3, 'Riesel form')
    D = P * P - 4
    need(jacobi(D % N, N) == -1, 'Jacobi symbol must be -1')
    budget.use(4 * n * (n // 64 + 1))
    _, V = _lucas_uv(P, 1, (N + 1) // 2, N)
    if V != N - 2: return False
    for q in factor(k, budget):
        Uq, _ = _lucas_uv(P, 1, (N + 1) // q, N)
        if gcd(Uq, N) != 1: return False
    return True


@family('bigint_q', 'proth_primes', 'witness',
        'For every odd k in the listed range, the witness gives n <= n_max and a base a proving k 2^n + 1 prime (by '
        'Proth\'s theorem when k < 2^n, else by deterministic Miller-Rabin); the k without a witness are listed as '
        'unresolved and nothing is claimed for them.')
def fam_proth_primes(params, witness, budget):
    need(set(params) == {'k_lo', 'k_hi', 'n_max'}, 'Proth fields')
    lo, hi, nmax = integer(params['k_lo'], 1), integer(params['k_hi']), integer(params['n_max'], 1, 5000)
    need(lo < hi and hi - lo <= 20_000, 'k range')
    need(type(witness) is dict and set(witness) == {'primes', 'unresolved'}, 'witness fields')
    ks = {k for k in range(lo, hi) if k % 2}
    primes, unresolved = witness['primes'], witness['unresolved']
    need(type(primes) is dict and set(primes) | set(map(str, unresolved)) == set(map(str, ks))
         and not set(primes) & set(map(str, unresolved)), 'every odd k either witnessed or listed unresolved')
    for key, (n, a) in primes.items():
        k = int(key); integer(n, 1, nmax); N = k * (1 << n) + 1
        if k < (1 << n): need(proth_prime(k, n, a, budget), 'Proth test fails for k = ' + key)
        else: need(is_prime(N, budget), 'k 2^n + 1 is not prime for k = ' + key)
    return dict(resolved=len(primes), unresolved=len(unresolved))


@family('bigint_q', 'riesel_primes', 'witness',
        'For every odd k in the listed range, the witness gives n <= n_max and a Lucas parameter P proving k 2^n - 1 '
        'prime (deterministic Miller-Rabin below 3.3 10^24, above it an N+1 test with Lucas sequences, which needs '
        'k < 2^n); the k without a witness are listed as unresolved and nothing is claimed for them.')
def fam_riesel_primes(params, witness, budget):
    need(set(params) == {'k_lo', 'k_hi', 'n_max'}, 'Riesel fields')
    lo, hi, nmax = integer(params['k_lo'], 1), integer(params['k_hi']), integer(params['n_max'], 1, 3000)
    need(lo < hi and hi - lo <= 20_000, 'k range')
    need(type(witness) is dict and set(witness) == {'primes', 'unresolved'}, 'witness fields')
    ks = {k for k in range(lo, hi) if k % 2}
    primes, unresolved = witness['primes'], witness['unresolved']
    need(type(primes) is dict and set(primes) | set(map(str, unresolved)) == set(map(str, ks))
         and not set(primes) & set(map(str, unresolved)), 'every odd k either witnessed or listed unresolved')
    for key, (n, P) in primes.items():
        k = int(key); integer(n, 1, nmax); N = k * (1 << n) - 1
        if N < MR_LIMIT: need(is_prime(N, budget), 'k 2^n - 1 is not prime for k = ' + key)
        else: need(type(P) is int and riesel_prime(k, n, P, budget), 'the N+1 test fails for k = ' + key)
    return dict(resolved=len(primes), unresolved=len(unresolved))


@family('bigint_q', 'pratt', 'proof',
        'n is prime: a Pratt certificate, a base of order n - 1 with a certified factorization of n - 1.')
def fam_pratt(params, proof, budget):
    need(set(params) == {'n'}, 'Pratt fields'); n = integer(params['n'], 2)
    need(n.bit_length() <= 4096, 'Pratt bound')
    def verify(m, cert, depth):
        need(depth < 64, 'certificate depth')
        if m < 1000: need(m in SMALL_PRIMES, str(m) + ' is not prime'); return
        need(type(cert) is dict and set(cert) == {'a', 'factors'} and type(cert['factors']) is dict, 'certificate shape')
        a = cert['a']; fs = cert['factors']; prod = 1
        for key, (e, sub) in fs.items():
            q = int(key); need(q >= 2 and type(e) is int and e >= 1, 'factor entry'); prod *= q ** e
            verify(q, sub, depth + 1)
        need(prod == m - 1, 'the factors do not multiply to ' + str(m) + ' - 1')
        budget.use(len(fs) * m.bit_length())
        need(pow(a, m - 1, m) == 1 and all(pow(a, (m - 1) // int(q), m) != 1 for q in fs), 'the base has smaller order')
    verify(n, proof, 0)
    return dict(bits=n.bit_length())


# ------------------------------------------------------------- orbits

@family('orbit_q', 'reverse_add', 'value',
        'Iterating n -> n + reverse(n) from the start for at most the given steps: the first step producing a '
        'palindrome (or null) and the number of digits reached.')
def fam_reverse_add(params, budget):
    need(set(params) == {'start', 'steps'}, 'reverse-and-add fields')
    n, S = integer(params['start'], 1, 10 ** 18), integer(params['steps'], 1, 50_000)
    for i in range(1, S + 1):
        s = str(n); n = n + int(s[::-1]); t = str(n); budget.use(len(t) // 16 + 1)
        if t == t[::-1]: return dict(palindrome_at=i, digits=len(t))
    return dict(palindrome_at=None, digits=len(str(n)))


@family('orbit_q', 'affine_orbit', 'value',
        'The orbit of the start under the residue-class map T(n) = (a_i n + b_i)/d (n = i mod d) for the given '
        'steps: the step where it first repeats a value (or null), its largest value\'s bit length, and the '
        'bit length at the last step.')
def fam_affine_orbit(params, budget):
    need(set(params) == {'map', 'start', 'steps'}, 'orbit fields')
    m = params['map']; need(type(m) is dict and set(m) == {'d', 'a', 'b'}, 'map fields')
    d, A, B = integer(m['d'], 2, 16), m['a'], m['b']
    need(type(A) is list and type(B) is list and len(A) == len(B) == d and all(type(x) is int for x in A + B)
         and all((A[i] * i + B[i]) % d == 0 for i in range(d)), 'integer map')
    n, S = integer(params['start'], 1), integer(params['steps'], 1, 200_000)
    seen = {n: 0}; top = n.bit_length()
    for i in range(1, S + 1):
        r = n % d; n = (A[r] * n + B[r]) // d; budget.use(n.bit_length() // 64 + 1)
        need(n.bit_length() <= 200_000, 'orbit bit bound')
        top = max(top, n.bit_length())
        if n in seen: return dict(repeat_at=i, max_bits=top, last_bits=n.bit_length())
        if len(seen) < 100_000: seen[n] = i
    return dict(repeat_at=None, max_bits=top, last_bits=n.bit_length())


@family('orbit_q', 'amusical', 'value',
        'Conway\'s permutation g(2n) = 3n, g(4n+1) = 3n+1, g(4n-1) = 3n-1 and its inverse, from the start for the '
        'given steps each way: whether and when the start recurs, and the largest bit length each way.')
def fam_amusical(params, budget):
    need(set(params) == {'start', 'steps'}, 'amusical fields')
    s0, S = integer(params['start'], 1), integer(params['steps'], 1, 200_000)
    def g(n): return 3 * n // 2 if n % 2 == 0 else (3 * n + 1) // 4 if n % 4 == 1 else (3 * n - 1) // 4
    def ginv(m): return 2 * m // 3 if m % 3 == 0 else (4 * m - 1) // 3 if m % 3 == 1 else (4 * m + 1) // 3
    out = {}
    for name, f in (('forward', g), ('backward', ginv)):
        n, top, back = s0, s0.bit_length(), None
        for i in range(1, S + 1):
            n = f(n); budget.use(n.bit_length() // 64 + 1); top = max(top, n.bit_length())
            need(top <= 200_000, 'orbit bit bound')
            if n == s0: back = i; break
        out[name] = dict(returns_at=back, max_bits=top)
    return out


@family('orbit_q', 'aliquot', 'value',
        'The aliquot sequence n -> sigma(n) - n from the start for at most the given steps while terms stay below '
        '10^digits_max: where it ends (0), cycles, or stops being followed, with its largest term\'s digit count.')
def fam_aliquot(params, budget):
    need(set(params) == {'start', 'steps', 'digits_max'}, 'aliquot fields')
    n, S, Dm = integer(params['start'], 1), integer(params['steps'], 1, 2000), integer(params['digits_max'], 2, 24)
    seen = {n: 0}; top = len(str(n))
    for i in range(1, S + 1):
        if n == 1: return dict(ends_at=i, cycle=None, stopped=None, max_digits=top)
        n = sigma(n, budget) - n; top = max(top, len(str(n)))
        if n == 0: return dict(ends_at=i, cycle=None, stopped=None, max_digits=top)
        if n in seen: return dict(ends_at=None, cycle=[seen[n], i], stopped=None, max_digits=top)
        if len(str(n)) > Dm: return dict(ends_at=None, cycle=None, stopped=i, max_digits=top)
        seen[n] = i
    return dict(ends_at=None, cycle=None, stopped=S, max_digits=top)


# ------------------------------------------------------------- covering systems

def _lcm(a, b): return a // gcd(a, b) * b


@family('covering_q', 'covering', 'witness',
        'The witness classes r mod m (m > 1) cover every integer; with distinct moduli, and all moduli odd when the '
        'parameters ask.')
def fam_covering(params, witness, budget):
    need(set(params) == {'distinct', 'odd', 'lcm_max'}, 'covering fields')
    need(type(witness) is list and 1 <= len(witness) <= 2000, 'covering classes')
    L = 1
    for r, m in witness:
        integer(m, 2); integer(r, 0, m - 1); L = _lcm(L, m); need(L <= params['lcm_max'] <= 10 ** 7, 'lcm bound')
    mods = [m for _, m in witness]
    if params['distinct']: need(len(set(mods)) == len(mods), 'moduli repeat')
    if params['odd']: need(all(m % 2 for m in mods), 'an even modulus')
    budget.use(L * len(witness) // 8 + L)
    hit = bytearray(L)
    for r, m in witness: hit[r::m] = b'\x01' * len(range(r, L, m))
    need(all(hit), 'some residue mod ' + str(L) + ' is not covered')
    return dict(classes=len(witness), lcm=L)


@family('covering_q', 'sierpinski_covering', 'witness',
        'k 2^n + sign is divisible by one of the listed primes for every n >= 1, and exceeds that prime: so it is '
        'composite for every n (k is a Sierpinski number for sign +1, a Riesel number for sign -1).')
def fam_sierpinski_covering(params, witness, budget):
    need(set(params) == {'k', 'sign'} and params['sign'] in (1, -1), 'covering fields')
    k = integer(params['k'], 1, 10 ** 12); sign = params['sign']
    need(type(witness) is dict and set(witness) == {'primes', 'period'}, 'witness fields')
    ps, T = witness['primes'], integer(witness['period'], 1, 10 ** 5)
    need(type(ps) is list and 1 <= len(ps) <= 64 and all(type(p) is int and is_prime(p, budget) for p in ps), 'primes')
    for p in ps: need(pow(2, T, p) == 1, 'the period is not a multiple of the order of 2 mod ' + str(p))
    need(k > max(ps) or all(k * (1 << n) + sign > max(ps) for n in range(1, 64)), 'values above the primes')
    budget.use(T * len(ps))
    for n in range(T):
        e = n if n else T  # n >= 1: use the representative in [1, T]
        need(any((k * pow(2, e, p) + sign) % p == 0 for p in ps), 'no listed prime divides at n = ' + str(e) + ' mod T')
    return dict(period=T, primes=len(ps))


@family('covering_q', 'distinct_cover_search', 'value',
        'Whether some choice of one residue class for each listed modulus covers every integer (exhaustive search '
        'with the listed moduli, each used once).')
def fam_distinct_cover_search(params, budget):
    need(set(params) == {'moduli'}, 'search fields'); mods = params['moduli']
    need(type(mods) is list and 1 <= len(mods) <= 24 and all(type(m) is int and m >= 2 for m in mods), 'moduli')
    L = 1
    for m in mods: L = _lcm(L, m); need(L <= 200_000, 'lcm bound')
    order = sorted(mods)
    density = sum(__import__('fractions').Fraction(1, m) for m in mods)
    if density < 1: return dict(exists=False, reason='density below 1')
    full = (1 << L) - 1
    def mask(r, m):
        x, width = 1 << r, m
        while width < L: x |= x << width; width *= 2
        return x & full
    masks = {m: [mask(r, m) for r in range(m)] for m in set(mods)}
    budget.use(L)
    def go(i, covered):
        budget.use()
        if covered == full: return True
        if i == len(order): return False
        rest = sum(__import__('fractions').Fraction(1, m) for m in order[i:])
        missing = L - bin(covered).count('1')
        if rest * L < missing: return False
        return any(go(i + 1, covered | mk) for mk in masks[order[i]])
    return dict(exists=go(0, 0), reason='exhaustive search')


def _register_modules():
    """Load the real-number and discrete families; each receives this module's namespace as CORE and registers."""
    from types import SimpleNamespace
    core = SimpleNamespace(**{k: v for k, v in globals().items() if not k.startswith('__')})
    for name in ('window_real', 'window_discrete'):
        spec = importlib.util.spec_from_file_location('ember_window_' + name, Path(__file__).with_name(name + '.py'))
        module = importlib.util.module_from_spec(spec); module.CORE = core
        spec.loader.exec_module(module)


_register_modules()
