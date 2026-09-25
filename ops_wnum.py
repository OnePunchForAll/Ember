"""Operators on Ember's windows: compute a window's value, widen a checked window, refute a wrong value, and search
for number-theoretic and analytic witnesses.

A window question (kinds such as census_q, zeta_q, const_q) names a family and its parameters. A compute operator
asks the checker's window function for the family's value and proposes it as a value claim; the checker admits it
(for value windows her proposal and her checker share that computation, and the independent verdict is the second
implementation). Search operators find witnesses with their own code (Proth bases, subset sums, speed-set times,
covering sets, invariant subspaces), and the checker verifies them. A widen operator restates a checked window with
larger bounds: a new question derived from a checked answer.
"""
from fractions import Fraction as Q
import importlib.util
from math import gcd, isqrt
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_wnum_' + name, Path(__file__).with_name(name + '.py'))
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


def compute(rt, root):
    """Propose the root window's value (as the checker computes it) and have it checked; [] when the family is not a
    value family or is out of bounds."""
    d = root['data']
    try: value = rt.checker.window_compute(root['kind'], d['family'], d['params'], rt.budget)
    except rt.checker.Invalid: return []
    claim = rt.propose('value', dict(q=root['kind'], family=d['family'], params=d['params'], value=value), (root,))
    return [claim] if rt.check(claim) else []


# One compute operator per tool, so each tool's windows route to its own move.
@op('census_compute', 'NS', ('census_q',), ('value',),
    'Count integers satisfying a typed predicate over ranges (a growth ladder), exactly.')
def census_compute(rt, root): return compute(rt, root)


@op('primes_compute', 'NS', ('primes_q',), ('value',),
    'Compute prime gap records, Goldbach tables, Gilbreath rows or prime tallies, exactly.')
def primes_compute(rt, root): return compute(rt, root)


@op('arith_compute', 'NS', ('arith_q',), ('value',),
    'Compute divisor-function tallies and totient fibres, exactly.')
def arith_compute(rt, root): return compute(rt, root)


@op('dioph_compute', 'NS', ('dioph_q',), ('value',),
    'Enumerate the solutions of a Diophantine equation in a box, exactly.')
def dioph_compute(rt, root): return compute(rt, root)


@op('field_compute', 'NS', ('field_q',), ('value',),
    'Compute class numbers, irregular pairs and small Mahler measures, exactly.')
def field_compute(rt, root): return compute(rt, root)


@op('bigint_compute', 'NS', ('bigint_q',), ('value',),
    'Run Lucas-Lehmer, Pepin and Fibonacci tests over a range, exactly.')
def bigint_compute(rt, root): return compute(rt, root)


@op('orbit_compute', 'NS', ('orbit_q',), ('value',),
    'Follow an orbit (reverse-and-add, residue maps, aliquot, Conway) for a bounded number of steps.')
def orbit_compute(rt, root): return compute(rt, root)


@op('covering_compute', 'NS', ('covering_q',), ('value',),
    'Search exhaustively for a covering system with the listed moduli.')
def covering_compute(rt, root): return compute(rt, root)


@op('zeta_compute', 'NS', ('zeta_q',), ('value',),
    'Evaluate zeta or L-functions with interval arithmetic: signs on the critical line, zero counts, errors.')
def zeta_compute(rt, root): return compute(rt, root)


@op('const_compute', 'NS', ('const_q',), ('value',),
    'Enclose a constant with interval arithmetic: digits, continued fraction, excluded rationals and '
    'relations.')
def const_compute(rt, root): return compute(rt, root)


@op('digits_compute', 'NS', ('digits_q',), ('value',),
    'Count the digits of a constant certified by interval arithmetic.')
def digits_compute(rt, root): return compute(rt, root)


@op('interval_compute', 'NS', ('interval_q',), ('value',),
    "Compute an exact set of reals (Mahler's Z-number condition) as rational intervals.")
def interval_compute(rt, root): return compute(rt, root)


@op('approx_compute', 'NS', ('approx_q',), ('value',),
    'Bound the Littlewood product n ||n x|| ||n y|| over a range, with interval arithmetic.')
def approx_compute(rt, root): return compute(rt, root)


@op('dynamics_compute', 'NS', ('dynamics_q',), ('value',),
    'Certify Mandelbrot points, x2 x3 orbits or averaged Lienard zeros, exactly.')
def dynamics_compute(rt, root): return compute(rt, root)


@op('spectrum_compute', 'NS', ('spectrum_q',), ('value',),
    'Count eigenvalues of a discrete Laplacian below thresholds by exact inertia.')
def spectrum_compute(rt, root): return compute(rt, root)


@op('lattice_compute', 'NS', ('lattice_q',), ('value',),
    'Compute lattice model partition functions and Galerkin conservation identities, exactly.')
def lattice_compute(rt, root): return compute(rt, root)


@op('knot_compute', 'NS', ('knot_q',), ('value',),
    'Compute a knot invariant: the Jones polynomial or the Kashaev invariant with interval bounds.')
def knot_compute(rt, root): return compute(rt, root)


@op('graph_compute', 'NS', ('graph_q',), ('value',),
    'Compute a graph invariant or an exhaustive census over small graphs.')
def graph_compute(rt, root): return compute(rt, root)


@op('setsys_compute', 'NS', ('setsys_q',), ('value',),
    'Run an exhaustive census over small set systems or partial orders.')
def setsys_compute(rt, root): return compute(rt, root)


@op('additive_compute', 'NS', ('additive_q',), ('value',),
    'Compute sums, products, Sidon maxima and cube-sum exceptions, exactly.')
def additive_compute(rt, root): return compute(rt, root)


@op('design_compute', 'NS', ('design_q',), ('value',),
    'Classify orders for Hadamard matrices and projective planes by construction rules.')
def design_compute(rt, root): return compute(rt, root)


@op('circuit_compute', 'NS', ('circuit_q',), ('value',),
    'Compute exact circuit sizes, graph isomorphism or small unique-game values.')
def circuit_compute(rt, root): return compute(rt, root)


@op('algebra_compute', 'NS', ('algebra_q',), ('value',),
    'Compute Galois groups and Casas-Alvero searches, exactly.')
def algebra_compute(rt, root): return compute(rt, root)


@op('group_compute', 'NS', ('group_q',), ('value',),
    'Enumerate cosets to compute the order of a finitely presented group.')
def group_compute(rt, root): return compute(rt, root)


@op('variety_compute', 'NS', ('variety_q',), ('value',),
    'Count points of curves and surfaces over finite fields.')
def variety_compute(rt, root): return compute(rt, root)


@op('config_compute', 'NS', ('config_q',), ('value',),
    'Compute exact geometric quantities: polar volume products and lattice minima.')
def config_compute(rt, root): return compute(rt, root)


# The widening rule of each family, kept within the family's own bounds (window_check, window_real, window_discrete):
# a proposal the checker would refuse on sight is no proposal.
WIDEN_CAPS = dict(tally=10_000_000, members=10_000_000, gap_records=10_000_000, goldbach=4_000_000, gilbreath=20_000,
                  mersenne=6000, wall_sun_sun=5_000_000, irregular_pairs=1200, zeta_signs=4000, l4_signs=2000,
                  digit_counts=100_000, circle_errors=20_000, reverse_add=50_000, affine_orbit=200_000, amusical=200_000,
                  mahler_z=200, littlewood=200_000, class_numbers=20_000, four_cubes=1_000_000)


def _widened(tool, family, params):
    """Larger bounds for a checked window, or None when the family has no widening rule or its bound is reached."""
    p = dict(params); cap = WIDEN_CAPS.get(family)
    if cap is None: return None
    if family == 'tally':
        last = p['bounds'][-1]; nxt = last * 10 if last < 1_000_000 else last * 2
        if nxt - p['lo'] > cap: return None
        p['bounds'] = p['bounds'] + [nxt]
    elif family == 'members':
        p['hi'] = p['lo'] + 2 * (p['hi'] - p['lo'])
        if p['hi'] - p['lo'] > cap: return None
    elif family in ('gap_records', 'goldbach'):
        p['hi'] = 2 * p['hi']
        if p['hi'] > cap: return None
    elif family == 'gilbreath': p['k'] = 2 * p['k']
    elif family in ('mersenne', 'wall_sun_sun', 'irregular_pairs'): p['p_max'] = 2 * p['p_max']
    elif family in ('zeta_signs', 'l4_signs'):
        p['count'] = 2 * p['count']
        if _rat_value(p['t0']) + _rat_value(p['h']) * p['count'] > (2000 if family == 'zeta_signs' else 500): return None
    elif family == 'digit_counts': p['n'] = 2 * p['n']
    elif family == 'circle_errors': p['r_max'] = 2 * p['r_max']
    elif family in ('reverse_add', 'affine_orbit', 'amusical'): p['steps'] = 2 * p['steps']
    elif family == 'mahler_z': p['steps'] = p['steps'] + 20
    elif family == 'littlewood': p['n_max'] = 2 * p['n_max']
    elif family == 'class_numbers': p['d_max'] = 2 * p['d_max']
    elif family == 'four_cubes': p['N'] = 2 * p['N']
    key = dict(gilbreath='k', mersenne='p_max', wall_sun_sun='p_max', irregular_pairs='p_max', zeta_signs='count',
               l4_signs='count', digit_counts='n', circle_errors='r_max', reverse_add='steps', affine_orbit='steps',
               amusical='steps', mahler_z='steps', littlewood='n_max', class_numbers='d_max', four_cubes='N').get(family)
    if key is not None and p[key] > cap: return None
    return p


def _rat_value(x):
    """A window's rational parameter as a Fraction (an integer, or a [numerator, denominator] pair)."""
    from fractions import Fraction
    return Fraction(x) if type(x) is int else Fraction(x[0], x[1])


WIDEN = _widened  # her scan reads this rule to propose a settled window's widening as her own next problem


@op('window_widen', 'NSE', ('value',), ('value',),
    'Restate a checked window with larger bounds and compute it: a new question derived from a checked answer.')
def window_widen(rt, claim):
    if claim['status'] != 'checked': return []
    d = claim['data']; p = _widened(d['q'], d['family'], d['params'])
    if p is None: return []
    try: value = rt.checker.window_compute(d['q'], d['family'], p, rt.budget)
    except rt.checker.Invalid: return []
    root = rt.given(d['q'], dict(family=d['family'], params=p))
    new = rt.propose('value', dict(q=d['q'], family=d['family'], params=p, value=value), (root,), source=claim)
    return [new] if rt.check(new) else []


@op('window_refute', 'WS', ('value',), ('refutation',),
    'Recompute a window value that is not yet admitted; a different result refutes the claim.')
def window_refute(rt, claim):
    if claim['status'] == 'checked': return []
    r = rt.refute(claim, {})
    return [r] if r is not None else []


# ------------------------------------------------------------- number-theoretic witnesses

def _mr(n):
    """Deterministic Miller-Rabin below 3.3e24 (her own copy for searching)."""
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41):
        if n % p == 0: return n == p
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41):
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True


def _jacobi(a, n):
    a %= n; r = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5): r = -r
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3: r = -r
        a %= n
    return r if n == 1 else 0


def proth_search(params, rt):
    lo, hi, nmax = params['k_lo'], params['k_hi'], params['n_max']; primes = {}; unresolved = []
    for k in range(lo, hi):
        if k % 2 == 0: continue
        hit = None
        for n in range(1, nmax + 1):
            rt.budget.use(n // 32 + 1); N = k * (1 << n) + 1
            if k < (1 << n):
                a = next((a for a in range(3, 200) if _jacobi(a, N) == -1), None)
                if a is not None and pow(a, (N - 1) // 2, N) == N - 1: hit = [n, a]; break
            elif N < 3 * 10 ** 24 and _mr(N): hit = [n, 0]; break
        if hit: primes[str(k)] = hit
        else: unresolved.append(k)
    return dict(primes=primes, unresolved=unresolved)


def _lucas(P, k, N):
    """(U_k, V_k) mod N for Q = 1, by the doubling ladder V_2m = V_m^2 - 2, V_2m+1 = V_m V_m+1 - P (her own copy)."""
    v0, v1 = 2, P % N  # V_m, V_m+1
    for bit in bin(k)[2:]:
        if bit == '1': v0, v1 = (v0 * v1 - P) % N, (v1 * v1 - 2) % N
        else: v0, v1 = (v0 * v0 - 2) % N, (v0 * v1 - P) % N
    D = P * P - 4
    # U_k = (2 V_k+1 - P V_k) / D
    return (2 * v1 - P * v0) * pow(D, -1, N) % N, v0


def riesel_search(params, rt):
    lo, hi, nmax = params['k_lo'], params['k_hi'], params['n_max']; primes = {}; unresolved = []
    for k in range(lo, hi):
        if k % 2 == 0: continue
        hit = None
        for n in range(1, nmax + 1):
            rt.budget.use(n // 16 + 1); N = k * (1 << n) - 1
            if N < 4: continue
            if N < 3 * 10 ** 24:
                if _mr(N): hit = [n, 0]; break
                continue
            if k >= (1 << n) or pow(3, N - 1, N) != 1: continue  # a cheap composite filter first
            fs = [q for q in range(3, k + 1, 2) if k % q == 0 and all(q % r for r in range(3, int(q ** 0.5) + 1, 2))]
            for P in range(3, 400):
                if _jacobi(P * P - 4, N) != -1: continue
                rt.budget.use(4 * n)
                if _lucas(P, (N + 1) // 2, N)[1] != N - 2: continue
                if all(gcd(_lucas(P, (N + 1) // q, N)[0], N) == 1 for q in fs): hit = [n, P]; break
            if hit: break
        if hit: primes[str(k)] = hit
        else: unresolved.append(k)
    return dict(primes=primes, unresolved=unresolved)


def pratt_certificate(n, rt, depth=0):
    """A Pratt certificate for a prime n: a generator and certified prime factors of n - 1."""
    if n < 1000: return {}
    f = _factor(n - 1, rt)
    for a in range(2, 1000):
        rt.budget.use(len(f))
        if pow(a, n - 1, n) == 1 and all(pow(a, (n - 1) // q, n) != 1 for q in f):
            return dict(a=a, factors={str(q): [e, pratt_certificate(q, rt, depth + 1)] for q, e in f.items()})
    return None


def _factor(n, rt):
    out = {}
    for p in range(2, 1000):
        while n % p == 0: out[p] = out.get(p, 0) + 1; n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if _mr(m): out[m] = out.get(m, 0) + 1; continue
        c = 1
        while True:
            x = y = 2; d = 1
            while d == 1:
                rt.budget.use()
                x = (x * x + c) % m; y = (y * y + c) % m; y = (y * y + c) % m; d = gcd(abs(x - y), m)
            if d != m: break
            c += 1
        stack += [d, m // d]
    return out


def odd_weird_search(params, rt):
    hi = params['hi']; s = [0] * hi
    for d in range(1, hi // 2 + 1):
        for m in range(2 * d, hi, d): s[m] += d
    rt.budget.use(hi * 2); out = {}
    for n in range(1, hi, 2):
        if s[n] <= n: continue
        divs = sorted((d for d in range(1, n) if n % d == 0), reverse=True)
        pick = _subset_sum(divs, n, rt)
        if pick is None: return None
        out[str(n)] = pick
    return out


def _subset_sum(items, target, rt):
    """Distinct items (descending) summing to target, by depth-first search with a suffix-sum bound."""
    suffix = [0] * (len(items) + 1)
    for i in range(len(items) - 1, -1, -1): suffix[i] = suffix[i + 1] + items[i]
    out = []
    def go(i, left):
        rt.budget.use()
        if left == 0: return True
        if i == len(items) or suffix[i] < left: return False
        if items[i] <= left:
            out.append(items[i])
            if go(i + 1, left - items[i]): return True
            out.pop()
        return go(i + 1, left)
    return out if go(0, target) else None


def sierpinski_covering_search(params, rt):
    """A covering set for k 2^n + sign: primes p whose order of 2 divides a period T, chosen greedily until every n mod
    T is covered."""
    k, sign = params['k'], params['sign']
    for T in (2, 4, 6, 8, 10, 12, 18, 24, 36, 48, 60, 72, 120, 144, 180, 360):
        cands = []
        for p in range(3, 20000):
            if not _mr(p) or pow(2, T, p) != 1: continue
            rt.budget.use(T)
            hits = {n for n in range(1, T + 1) if (k * pow(2, n, p) + sign) % p == 0}
            if hits: cands.append((p, hits))
        need = set(range(1, T + 1)); chosen = []
        while need:
            best = max(cands, key=lambda c: len(c[1] & need), default=None)
            if best is None or not best[1] & need: break
            chosen.append(best[0]); need -= best[1]
        if not need and (k > max(chosen)): return dict(primes=sorted(chosen), period=T)
    return None


def covering_search(params, rt):
    """A covering system with distinct moduli (odd if asked) from the divisors of candidate lcms, by greedy choice of
    the residue covering most uncovered points and backtracking on the last moduli."""
    odd = params['odd']
    for L in ((12, 24, 48, 120, 360) if not odd else (315, 945, 3465, 10395, 45045)):
        if L > params['lcm_max']: continue
        mods = [m for m in range(2, L + 1) if L % m == 0 and (not odd or m % 2)]
        uncovered = set(range(L)); chosen = []
        for m in sorted(mods):
            if not uncovered: break
            best = max(range(m), key=lambda r: sum(1 for x in range(r, L, m) if x in uncovered))
            rt.budget.use(L)
            gain = {x for x in range(best, L, m) if x in uncovered}
            if gain: chosen.append([best, m]); uncovered -= gain
        if not uncovered: return chosen
    return None


# ------------------------------------------------------------- analytic witnesses

def lonely_runner_search(params, rt):
    from itertools import combinations
    k, S = params['k'], params['s_max']; bound = Q(1, k + 1); out = {}
    for vs in combinations(range(1, S + 1), k):
        found = None
        for den in range(k + 1, 4 * (k + 1) * max(vs) + 1):
            for num in range(1, den):
                if gcd(num, den) != 1: continue
                rt.budget.use(k)
                t = Q(num, den)
                if all(min((t * v) % 1, 1 - (t * v) % 1) >= bound for v in vs): found = [num, den]; break
            if found: break
        if found is None: return None
        out[','.join(map(str, vs))] = found
    return out


def invariant_subspace_search(params, rt):
    """A proper invariant subspace of a rational matrix: a Krylov space span{v, Av, A^2 v, ...} of dimension below n,
    trying the standard basis vectors and their pairwise sums."""
    A = [[Q(x) if type(x) is int else Q(x[0], x[1]) for x in r] for r in params['matrix']]; n = len(A)
    def rank_basis(vs):
        basis = []; rows = []
        for v in vs:
            w = list(v)
            for b, piv in rows:
                if w[piv]: f = w[piv] / b[piv]; w = [x - f * y for x, y in zip(w, b)]
            piv = next((i for i in range(n) if w[i]), None)
            if piv is not None: rows.append((w, piv)); basis.append(v)
        return basis
    cands = [[Q(int(i == j)) for j in range(n)] for i in range(n)]
    cands += [[Q(int(i == j or k == j)) for j in range(n)] for i in range(n) for k in range(i + 1, n)]
    for v in cands:
        vs = [v]
        for _ in range(n):
            w = [sum(A[i][j] * vs[-1][j] for j in range(n)) for i in range(n)]; rt.budget.use(n * n)
            if len(rank_basis(vs + [w])) == len(vs): break
            vs.append(w)
        if len(vs) < n: return [[[x.numerator, x.denominator] for x in u] for u in vs]
    return None


SEARCHES = {
    ('bigint_q', 'proth_primes'): proth_search, ('bigint_q', 'riesel_primes'): riesel_search,
    ('arith_q', 'odd_weird'): odd_weird_search, ('covering_q', 'sierpinski_covering'): sierpinski_covering_search,
    ('covering_q', 'covering'): covering_search, ('approx_q', 'lonely_runner'): lonely_runner_search,
    ('operator_q', 'invariant_subspace'): invariant_subspace_search,
}


def search(rt, root, kind='witness'):
    d = root['data']; fn = SEARCHES.get((root['kind'], d['family']))
    if fn is None: return []
    try: found = fn(d['params'], rt)
    except (KeyError, TypeError, ValueError, ZeroDivisionError): return []
    if found is None: return []
    claim = rt.propose(kind, {'q': root['kind'], 'family': d['family'], 'params': d['params'], kind: found}, (root,))
    return [claim] if rt.check(claim) else []


@op('arith_search', 'NS', ('arith_q',), ('witness',),
    'Find, for every odd abundant number below a bound, proper divisors summing to it (no odd weird number there).')
def arith_search(rt, root): return search(rt, root)


@op('bigint_search', 'NS', ('bigint_q',), ('witness',),
    'Find primes k 2^n + 1 (Proth bases) or k 2^n - 1 (Lucas parameters) for every odd k in a range.')
def bigint_search(rt, root): return search(rt, root)


@op('bigint_prove', 'NS', ('bigint_q',), ('proof',),
    'Build a Pratt primality certificate: a generator modulo n and certified prime factors of n - 1.')
def bigint_prove(rt, root):
    d = root['data']
    if d['family'] != 'pratt': return []
    n = d['params'].get('n')
    if type(n) is not int or n < 2 or (n < 3 * 10 ** 24 and not _mr(n)): return []
    cert = pratt_certificate(n, rt)
    if cert is None: return []
    claim = rt.propose('proof', dict(q='bigint_q', family='pratt', params=d['params'], proof=cert), (root,))
    return [claim] if rt.check(claim) else []


@op('covering_search', 'NS', ('covering_q',), ('witness',),
    'Find a covering system with distinct moduli, or a covering set of primes proving k 2^n +- 1 always composite.')
def covering_search_op(rt, root): return search(rt, root)


@op('approx_search', 'NS', ('approx_q',), ('witness',),
    'Find, for every set of runner speeds, a rational time leaving every runner at least 1/(k+1) from the start.')
def approx_search(rt, root): return search(rt, root)


@op('operator_search', 'NS', ('operator_q',), ('witness',),
    'Find a proper invariant subspace of a rational matrix as a Krylov space.')
def operator_search(rt, root): return search(rt, root)


def _w(rt, tool, family, params): return rt.given(tool, dict(family=family, params=params))


def _wrong(rt):
    return [rt.propose('value', dict(q='census_q', family='tally', params=dict(pred=['prime', 'n'], lo=2, bounds=[30]),
                                     value=[9]))]


FIXTURES = {
    'census_compute': [lambda rt: [_w(rt, 'census_q', 'tally', dict(pred=['prime', 'n'], lo=2, bounds=[100, 1000]))]],
    'primes_compute': [lambda rt: [_w(rt, 'primes_q', 'gap_records', dict(lo=2, hi=1000))]],
    'arith_compute': [lambda rt: [_w(rt, 'arith_q', 'totient_singletons', dict(lo=1, hi=50))]],
    'dioph_compute': [lambda rt: [_w(rt, 'dioph_q', 'euler_bricks', dict(max_edge=250))]],
    'field_compute': [lambda rt: [_w(rt, 'field_q', 'irregular_pairs', dict(p_max=80))]],
    'bigint_compute': [lambda rt: [_w(rt, 'bigint_q', 'mersenne', dict(p_max=130))]],
    'orbit_compute': [lambda rt: [_w(rt, 'orbit_q', 'reverse_add', dict(start=89, steps=50))]],
    'covering_compute': [lambda rt: [_w(rt, 'covering_q', 'distinct_cover_search', dict(moduli=[2, 3, 4, 6, 12]))]],
    'zeta_compute': [lambda rt: [_w(rt, 'zeta_q', 'zeta_signs', dict(t0=13, h=[1, 2], count=4))]],
    'const_compute': [lambda rt: [_w(rt, 'const_q', 'cf_prefix', dict(expr='pi', terms=8))]],
    'digits_compute': [lambda rt: [_w(rt, 'digits_q', 'digit_counts', dict(expr='pi', n=100))]],
    'interval_compute': [lambda rt: [_w(rt, 'interval_q', 'mahler_z', dict(lo=1, hi=3, steps=8))]],
    'approx_compute': [lambda rt: [_w(rt, 'approx_q', 'littlewood', dict(a=2, b=3, n_max=100))]],
    'dynamics_compute': [lambda rt: [_w(rt, 'dynamics_q', 'x2x3_orbits', dict(q=35))]],
    'spectrum_compute': [lambda rt: [_w(rt, 'spectrum_q', 'eigen_counts', dict(cells=[[0, 0], [0, 1], [1, 0]],
                                                                                thresholds=[[1, 2], 2]))]],
    'lattice_compute': [lambda rt: [_w(rt, 'lattice_q', 'ising', dict(L=2, M=2))]],
    'knot_compute': [lambda rt: [_w(rt, 'knot_q', 'jones', dict(pd=[[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]))]],
    'graph_compute': [lambda rt: [_w(rt, 'graph_q', 'chromatic', dict(graph=dict(named='petersen')))]],
    'setsys_compute': [lambda rt: [_w(rt, 'setsys_q', 'frankl_small', dict(m=2))]],
    'additive_compute': [lambda rt: [_w(rt, 'additive_q', 'sidon_max', dict(n=12))]],
    'design_compute': [lambda rt: [_w(rt, 'design_q', 'plane_orders', dict(n_max=12))]],
    'circuit_compute': [lambda rt: [_w(rt, 'circuit_q', 'circuit_sizes', dict(n=2, max_size=2))]],
    'algebra_compute': [lambda rt: [_w(rt, 'algebra_q', 'galois_group', dict(poly=[-1, -1, 0, 1], p_max=50))]],
    'group_compute': [lambda rt: [_w(rt, 'group_q', 'coset_order', dict(ngens=2, relators=[[1, 1], [2, 2, 2], [1, 2, 1, 2]],
                                                                         limit=100))]],
    'variety_compute': [lambda rt: [_w(rt, 'variety_q', 'elliptic_ap', dict(a=-1, b=0, p_max=30))]],
    'config_compute': [lambda rt: [_w(rt, 'config_q', 'mahler_polygon', dict(vertices=[[1, 0], [0, 1], [-1, 0], [0, -1]]))]],
    'window_widen': [lambda rt: [compute(rt, _w(rt, 'census_q', 'tally', dict(pred=['prime', 'n'], lo=2, bounds=[100])))[0]]],
    'window_refute': [_wrong],
    'arith_search': [lambda rt: [_w(rt, 'arith_q', 'odd_weird', dict(hi=3000))]],
    'bigint_search': [lambda rt: [_w(rt, 'bigint_q', 'proth_primes', dict(k_lo=1, k_hi=30, n_max=40))]],
    'bigint_prove': [lambda rt: [_w(rt, 'bigint_q', 'pratt', dict(n=1000000007))]],
    'covering_search': [lambda rt: [_w(rt, 'covering_q', 'covering', dict(distinct=True, odd=False, lcm_max=1000))]],
    'approx_search': [lambda rt: [_w(rt, 'approx_q', 'lonely_runner', dict(k=3, s_max=6))]],
    'operator_search': [lambda rt: [_w(rt, 'operator_q', 'invariant_subspace',
                                        dict(matrix=[[0, 0, 0], [1, 0, 0], [0, 1, 0]]))]],
}
