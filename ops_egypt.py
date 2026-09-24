"""Operators on unit-fraction questions: a/n = 1/x_1 + ... + 1/x_t.

Families are polynomial in the class parameter k with n = m*k + r. The divisor
ansatz takes x = (s*n + c)/a, so a/n - 1/x = e/N after reduction, and writes
1/y + 1/z = e/N with y = (N + d)/e and z = (N + N^2/d)/e for a divisor d of N^2
built from the primitive factors of N. Every family, witness, cover and finite
range is admitted only by lexicon_check.py; an operator's search can miss.
"""
from fractions import Fraction as Q
import importlib.util
from itertools import product
from math import gcd
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_egypt_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


L = _load('lexicon')
OPS = []
BASE_S = range(1, 13)
BASE_C = range(0, 40)
EXTENDED_S = range(1, 25)
EXTENDED_C = range(0, 240)
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)


def op(name, dirs, consumes, produces, summary):
    def wrap(fn):
        OPS.append(dict(name=name, dirs=dirs, consumes=tuple(consumes), produces=tuple(produces), summary=summary,
                        fn=fn, entry=fn.__name__))
        return fn
    return wrap


# ------------------------------------------------------------- shared producer helpers

def family_data(a, m, r, k0, polys):
    return dict(a=a, m=m, r=r, k0=k0, x=[L.univariate_expr(p, 'k') for p in polys])


def family_polys(data):
    return [L.univariate(e, 'k') for e in data['x']]


def least_start(polys, limit=64):
    """Smallest k0 with every polynomial positive from k0 on, by the checker's shifted-coefficient test."""
    for k0 in range(limit):
        if all(L.nonnegative_from(p, k0) for p in polys): return k0
    return None


def integral(polys):
    return all(L.integer_valued(p) for p in polys)


def ansatz(a, m, r, pairs, budget, limit=1):
    """Families of the divisor ansatz on the class n = m*k + r, in the order of the (s, c) pairs.

    Integer values at k = 0..4 prefilter every divisor shape; survivors are built
    as exact polynomials. Degrees are at most four, so five points decide integrality.
    """
    ks = range(5); nk = [m * k + r for k in ks]; found = []
    cont_n = gcd(m, r); n_p = [Q(r, cont_n), Q(m, cont_n)]
    for s, c in pairs:
        budget.use()
        if (s * r + c) % a or (s * m) % a: continue
        X0, X1 = (s * r + c) // a, (s * m) // a
        if X0 <= 0: continue
        cont_x = gcd(X0, X1); x = [Q(X0), Q(X1)]; x_p = [Q(X0, cont_x), Q(X1, cont_x)]
        if c == 0:
            if s == 1: continue
            e = s - 1; prims = [x_p]; const = cont_x
        elif s == 1: e = c; prims = [n_p, x_p]; const = cont_n * cont_x
        else: e = None; prims = [n_p, x_p]; const = cont_n * cont_x
        if e is not None:
            g = gcd(e, const); e //= g; const //= g
        pk = [[int(L.peval(f, k)) for k in ks] for f in prims]
        Nk = [const * pk[0][i] * (pk[1][i] if len(prims) > 1 else 1) for i in ks]
        Ek = [e] * 5 if e is not None else [(s - 1) * n + c for n in nk]
        for cdiv in L.divisors(const * const):
            for exps in product(*[range(3) for _ in prims]):
                budget.use(2); ok = True
                for i in ks:
                    dk = cdiv
                    for f, j in zip(pk, exps): dk *= f[i] ** j
                    if dk <= 0 or (Nk[i] * Nk[i]) % dk or (Nk[i] + dk) % Ek[i] or (Nk[i] + Nk[i] * Nk[i] // dk) % Ek[i]:
                        ok = False; break
                if not ok: continue
                N = L.pscale(prims[0], const) if len(prims) == 1 else L.pscale(L.pmul(prims[0], prims[1]), const)
                d = [Q(cdiv)]
                for f, j in zip(prims, exps): d = L.pmul(d, L.ppow(f, j))
                other = L.pexact(L.pmul(N, N), d)
                if other is None: continue
                if e is not None:
                    y = L.pscale(L.padd(N, d), Q(1, e)); z = L.pscale(L.padd(N, other), Q(1, e))
                else:
                    E = [Q((s - 1) * r + c), Q((s - 1) * m)]
                    y = L.pexact(L.padd(N, d), E); z = L.pexact(L.padd(N, other), E)
                    if y is None or z is None: continue
                if not integral([x, y, z]): continue
                k0 = least_start([x, y, z, [Q(r), Q(m)]])
                if k0 is None: continue
                found.append((family_data(a, m, r, k0, [x, y, z]),
                              dict(a=a, s=s, c=c, cdiv=cdiv, exps=list(exps), form='const' if e is not None else 'poly')))
                if len(found) >= limit: return found
    return found


def witness(a, n, budget, max_excess=None):
    """Smallest-x representation a/n = 1/x + 1/y + 1/z by the divisor method, or None."""
    fn = L.factor(n)
    for x in range(n // a + 1, 3 * n // a + 2):
        budget.use()
        e = a * x - n
        if e <= 0: continue
        if max_excess is not None and e > max_excess: return None
        N = n * x; g = gcd(e, N); e //= g; N //= g
        exponents = dict(fn)
        for p, k in L.factor(x).items(): exponents[p] = exponents.get(p, 0) + k
        for p, k in L.factor(g).items(): exponents[p] -= k
        primes = [p for p, k in exponents.items() if k > 0]
        best = None
        for powers in product(*[range(2 * exponents[p] + 1) for p in primes]):
            budget.use()
            d = 1
            for p, k in zip(primes, powers): d *= p ** k
            if d > N or (N + d) % e or (N + N * N // d) % e: continue
            y = (N + d) // e
            if best is None or y < best[0]: best = (y, (N + N * N // d) // e)
        if best is not None: return [x, best[0], best[1]]
    return None


def two_term(a, n, budget):
    """a/n = 1/y + 1/z via (a*y - n)(a*z - n) = n^2, smallest y."""
    best = None
    for d in L.square_divisors(n):
        budget.use()
        if d > n: break
        if (n + d) % a or (n + n * n // d) % a: continue
        y, z = (n + d) // a, (n + n * n // d) // a
        if best is None or y < best[0]: best = (y, z)
    return list(best) if best else None


def question_class(obj):
    d = obj['data']
    return d['a'], d['terms'], d['m'], d['r']


def refute_family(rt, fam, ks):
    """W: the first k at which a candidate family fails, admitted by the checker."""
    for k in ks:
        refutation = rt.refute(fam, dict(k=k))
        if refutation is not None: return refutation
    return None


def checked_families(rt, a, terms):
    return [o for o in rt.objects.values() if o['kind'] == 'ufam' and o['status'] == 'checked'
            and o['data']['a'] == a and len(o['data']['x']) == terms]


def cover_set(data):
    out = set(); M = data['modulus']
    for entry in data['entries']:
        f = entry['family']; out.update(range(f['r'], M, f['m']))
    return out


def best_cover(rt, a, terms, modulus=None):
    covers = [o for o in rt.objects.values() if o['kind'] == 'cover' and o['status'] == 'checked'
              and o['data']['a'] == a and o['data']['terms'] == terms
              and (modulus is None or o['data']['modulus'] == modulus)]
    return max(covers, key=lambda o: (Q(len(cover_set(o['data'])), o['data']['modulus']), -o['data']['bound']), default=None)


def assemble(families, a, terms, M):
    """One entry per family whose modulus divides M and whose class no coarser included family contains."""
    entries = []; bound = 1; kept = []
    for f in sorted(families, key=lambda o: (o['data']['m'], o['data']['r'], o['data']['k0'])):
        d = f['data']
        if M % d['m'] or any(d['m'] % m == 0 and d['r'] % m == r for m, r in kept): continue
        kept.append((d['m'], d['r'])); entries.append(dict(family=d))
        bound = max(bound, d['m'] * d['k0'] + d['r'])
    return dict(a=a, terms=terms, modulus=M, entries=entries, bound=bound) if entries else None


def lagrange(points):
    out = []
    for i, (xi, yi) in enumerate(points):
        basis = [Q(1)]; denom = Q(1)
        for j, (xj, _) in enumerate(points):
            if j != i: basis = L.pmul(basis, [-xj, Q(1)]); denom *= xi - xj
        out = L.padd(out, L.pscale(basis, yi / denom))
    return out


def template_of(fam):
    """Recover (s, c) of a checked family whose first denominator is linear."""
    d = fam['data']; a, m, r = d['a'], d['m'], d['r']; polys = family_polys(d)
    if len(polys) != 3 or len(polys[0]) != 2: return None
    x = polys[0]; s = x[1] * a / m; c = x[0] * a - s * r
    if s.denominator != 1 or c.denominator != 1 or s < 1 or c < 0: return None
    return int(s), int(c)


# ------------------------------------------------------------- witnesses

@op('egypt_witness_search', 'NWS', ('en',), ('ufrac', 'residual'),
    'Search x from just above n/a with the divisor method for the last two terms; a miss leaves a residual.')
def egypt_witness_search(rt, en):
    a, n, terms = en['data']['a'], en['data']['n'], en['data']['terms']
    xs = witness(a, n, rt.budget, max_excess=4 * a * 64) if terms == 3 else two_term(a, n, rt.budget) if terms == 2 else None
    if xs is None: return [rt.residual(en, ['no witness within the search bound'], 'witness search miss')]
    claim = rt.propose('ufrac', dict(a=a, n=n, x=xs), (en,))
    return [claim] if rt.check(claim) else []


@op('egypt_greedy', 'NS', ('en',), ('ufrac',),
    'Take a near-greedy first term, then solve the remaining fraction exactly with the two-term divisor rule.')
def egypt_greedy(rt, en):
    a, n, terms = en['data']['a'], en['data']['n'], en['data']['terms']
    if terms != 3: return []
    for x in range(n // a + 1, n // a + 4):
        rest = Q(a, n) - Q(1, x)
        if rest <= 0: continue
        pair = two_term(rest.numerator, rest.denominator, rt.budget)
        if pair is None: continue
        claim = rt.propose('ufrac', dict(a=a, n=n, x=[x] + pair), (en,))
        if rt.check(claim): return [claim]
    return []


# ------------------------------------------------------------- transfers between questions

@op('egypt_zero_class', 'SE', ('ufrac',), ('ufam',),
    'A checked representation of a/p gives the family x_i*k for the class 0 mod p.')
def egypt_zero_class(rt, rep):
    d = rep['data']
    claim = rt.transfer('ufam', family_data(d['a'], d['n'], 0, 1, [[Q(0), Q(x)] for x in d['x']]), rep)
    return [claim] if rt.check(claim) else []


@op('egypt_specialize', 'SE', ('ufam',), ('ufrac',),
    'Evaluate a checked family at its first class members to get instance representations.')
def egypt_specialize(rt, fam):
    d = fam['data']; out = []
    for k in (d['k0'], d['k0'] + 1):
        xs = [int(L.peval(p, k)) for p in family_polys(d)]
        claim = rt.transfer('ufrac', dict(a=d['a'], n=d['m'] * k + d['r'], x=xs), fam)
        if rt.check(claim): out.append(claim)
    return out


@op('egypt_subclass', 'SE', ('ufam',), ('ufam',),
    'Restrict a family on n = m*k + r to the subclasses mod t*m by substituting k = t*k + j.')
def egypt_subclass(rt, fam):
    d = fam['data']; out = []
    for t in (2, 3):
        for j in range(t):
            polys = [L.pcompose(p, [Q(j), Q(t)]) for p in family_polys(d)]
            k0 = max(0, -(-(d['k0'] - j) // t))
            claim = rt.transfer('ufam', family_data(d['a'], d['m'] * t, d['r'] + d['m'] * j, k0, polys), fam)
            if rt.check(claim): out.append(claim)
    return out


@op('egypt_scale_class', 'SE', ('ufam',), ('ufam',),
    'a/(t*n) = sum 1/(t*x_i): a family on m*k + r gives one on t*m*k + t*r.')
def egypt_scale_class(rt, fam):
    d = fam['data']; out = []
    for t in (2, 3):
        claim = rt.transfer('ufam', family_data(d['a'], d['m'] * t, d['r'] * t, d['k0'],
                                               [L.pscale(p, t) for p in family_polys(d)]), fam)
        if rt.check(claim): out.append(claim)
    return out


@op('egypt_more_terms', 'SE', ('ufam',), ('ufam',),
    'Split the largest denominator by 1/x = 1/(x+1) + 1/(x(x+1)) to pass to one more term.')
def egypt_more_terms(rt, fam):
    d = fam['data']; polys = family_polys(d)
    if len(polys) >= 6: return []
    i = max(range(len(polys)), key=lambda j: (len(polys[j]), polys[j][-1]))
    x = polys[i]; x1 = L.padd(x, [Q(1)])
    claim = rt.transfer('ufam', family_data(d['a'], d['m'], d['r'], d['k0'], polys[:i] + [x1, L.pmul(x, x1)] + polys[i + 1:]),
                        fam)
    return [claim] if rt.check(claim) else []


@op('egypt_numerator_add', 'SE', ('ufam', 'ufam'), ('ufam',),
    'Families for a1/n and a2/n on one class give (a1+a2)/n with the terms of both.')
def egypt_numerator_add(rt, first, second):
    d1, d2 = first['data'], second['data']
    if (d1['m'], d1['r']) != (d2['m'], d2['r']) or len(d1['x']) + len(d2['x']) > 6 or first['id'] == second['id']:
        return []
    claim = rt.transfer('ufam', dict(a=d1['a'] + d2['a'], m=d1['m'], r=d1['r'], k0=max(d1['k0'], d2['k0']),
                                     x=d1['x'] + d2['x']), first, (second,))
    return [claim] if rt.check(claim) else []


@op('egypt_divide_numerator', 'SE', ('ufam',), ('ufam',),
    'If g divides a, m and r then a/n = (a/g)/(n/g): the same denominators serve the class (m/g)k + r/g.')
def egypt_divide_numerator(rt, fam):
    d = fam['data']; out = []
    for g in L.divisors(gcd(gcd(d['a'], d['m']), d['r'])):
        if g == 1: continue
        claim = rt.transfer('ufam', dict(a=d['a'] // g, m=d['m'] // g, r=d['r'] // g, k0=d['k0'], x=d['x']), fam)
        if rt.check(claim): out.append(claim)
    return out


@op('egypt_family_identity', 'SE', ('ufam',), ('identity',),
    'Transfer a checked family to the polynomial identity a*prod(x_i) = n*sum_i prod_{j!=i} x_j in k.')
def egypt_family_identity(rt, fam):
    d = fam['data']; xs = d['x']
    n = L.add(L.mul(L.num(d['m']), L.var('k')), L.num(d['r']))
    rhs = L.mul(n, L.add(*[L.mul(L.num(1), *[x for j, x in enumerate(xs) if j != i]) for i in range(len(xs))]))
    claim = rt.transfer('identity', dict(vars=['k'], lhs=L.mul(L.num(d['a']), *xs), rhs=rhs), fam)
    return [claim] if rt.check(claim) else []


# ------------------------------------------------------------- family discovery

@op('egypt_divisor_ansatz', 'NWS', ('eclass',), ('ufam', 'residual'),
    'Base grammar: x = (s*n+c)/a with s < 13 and c < 40, and every divisor shape of N^2; a miss is a residual.')
def egypt_divisor_ansatz(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    found = ansatz(a, m, r, [(s, c) for s in BASE_S for c in BASE_C], rt.budget)
    if not found: return [rt.residual(cls, ['base divisor grammar exhausted'], 'ansatz miss')]
    fam = rt.propose('ufam', found[0][0], (cls,))
    return [fam] if rt.check(fam) else []


@op('egypt_ansatz_extend', 'NWS', ('eclass',), ('ufam', 'template', 'residual'),
    'Invent a template outside the base grammar (s < 25, c < 240, polynomial excess); it becomes a reusable move.')
def egypt_ansatz_extend(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    pairs = [(s, c) for s in EXTENDED_S for c in EXTENDED_C if not (s in BASE_S and c in BASE_C)]
    found = ansatz(a, m, r, pairs, rt.budget)
    if not found: return [rt.residual(cls, ['extended divisor grammar exhausted'], 'extended ansatz miss')]
    fam = rt.propose('ufam', found[0][0], (cls,))
    if not rt.check(fam): return []
    return [fam, rt.propose('template', found[0][1], (fam,))]


@op('egypt_template_transfer', 'NWSE', ('ufam', 'eclass'), ('ufam', 'refutation'),
    'Apply the (s, c) template of a checked family to another class; refute the naive candidate if it breaks.')
def egypt_template_transfer(rt, fam, cls):
    a, terms, m, r = question_class(cls)
    shape = template_of(fam)
    if shape is None or terms != 3 or fam['data']['a'] != a or fam['status'] != 'checked': return []
    s, c = shape
    found = ansatz(a, m, r, [(s, c)], rt.budget)
    if found:
        candidate = rt.propose('ufam', found[0][0], (cls,), source=fam)
        return [candidate] if rt.check(candidate) else []
    n = [Q(r), Q(m)]; x = [Q(s * r + c, a), Q(s * m, a)]
    candidate = rt.propose('ufam', family_data(a, m, r, 0, [x, L.pmul(n, x), L.pmul(n, x)]), (cls,), source=fam)
    refutation = refute_family(rt, candidate, range(0, 6))
    return [candidate, refutation] if refutation is not None else [candidate]


@op('egypt_family_fit', 'NWS', ('eclass',), ('ufam', 'refutation'),
    'For each small excess e, take the least valid divisor at five class members and interpolate x, y, z in k.')
def egypt_family_fit(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    ks = [k for k in range(0, 12) if m * k + r >= 2][:5]
    last = None
    for e0 in range(1, 4 * a + 1):
        rows = []
        for k in ks:
            n = m * k + r
            if (n + e0) % a: break
            x = (n + e0) // a; N = n * x; g = gcd(e0, N); e, Nr = e0 // g, N // g
            d = next((d for d in L.square_divisors(Nr) if d <= Nr and (Nr + d) % e == 0 and (Nr + Nr * Nr // d) % e == 0), None)
            if d is None: break
            rows.append([x, (Nr + d) // e, (Nr + Nr * Nr // d) // e])
        if len(rows) < len(ks): continue
        polys = [lagrange([(Q(k), Q(row[i])) for k, row in zip(ks, rows)]) for i in range(3)]
        k0 = max(ks[0], least_start(polys) or 0)
        candidate = rt.propose('ufam', family_data(a, m, r, k0, polys), (cls,))
        if rt.check(candidate): return [candidate]
        last = candidate
    if last is None: return []
    refutation = refute_family(rt, last, range(last['data']['k0'], last['data']['k0'] + 60))
    return [last, refutation] if refutation is not None else [last]


@op('egypt_generalize_witness', 'NWSE', ('ufrac',), ('ufam', 'refutation'),
    'Read the (s, c) excess pattern of a checked instance and propose it for the instance class mod a*e.')
def egypt_generalize_witness(rt, rep):
    d = rep['data']; a, n = d['a'], d['n']
    if len(d['x']) != 3 or rep['status'] != 'checked': return []
    x = min(d['x'])
    for s in (1, 2, 3, 4):
        c = a * x - s * n
        if c < 0: continue
        e = max(1, (s - 1) * n + c) if s == 1 else max(1, c)
        for m in (a * e, 2 * a * e, 3 * a * e):
            found = ansatz(a, m, n % m, [(s, c)], rt.budget)
            if found:
                candidate = rt.propose('ufam', found[0][0], (rep,), source=rep)
                if rt.check(candidate): return [candidate]
        m = a * e; r = n % m
        candidate = rt.propose('ufam', family_data(a, m, r, 0, [[Q(s * r + c, a), Q(s * m, a)], [Q(n)], [Q(n)]]),
                               (rep,), source=rep)
        refutation = refute_family(rt, candidate, range(0, 6))
        if refutation is not None: return [candidate, refutation]
    return []


@op('egypt_class_split', 'N', ('eclass',), ('eclass',),
    'Refine a class mod m into t subclasses mod t*m, for the least prime t not dividing m.')
def egypt_class_split(rt, cls):
    a, terms, m, r = question_class(cls)
    t = next(p for p in PRIMES if m % p)
    return [rt.propose('eclass', dict(a=a, terms=terms, m=m * t, r=r + m * j), (cls,)) for j in range(t)]


@op('egypt_class_refine', 'N', ('eclass', 'esq'), ('eclass',),
    'Refine a class mod m toward the question modulus M by the least prime p of M/m, raising a prime power if p | m.')
def egypt_class_refine(rt, cls, esq):
    a, terms, m, r = question_class(cls); M = esq['data']['modulus']
    if M % m or M == m or esq['data']['a'] != a: return []
    t = min(L.factor(M // m))
    return [rt.propose('eclass', dict(a=a, terms=terms, m=m * t, r=r + m * j), (cls,)) for j in range(t)]


@op('egypt_family_refute', 'WS', ('ufam',), ('refutation',),
    'Evaluate an unchecked family at k0..k0+40 and let the checker admit the first failure.')
def egypt_family_refute(rt, fam):
    if fam['status'] == 'checked': return []
    refutation = refute_family(rt, fam, range(fam['data']['k0'], fam['data']['k0'] + 40))
    return [refutation] if refutation is not None else []


# ------------------------------------------------------------- covers, residuals and finite ranges

@op('egypt_cover_assemble', 'NS', ('esq',), ('cover',),
    'Assemble every checked family whose modulus divides the question modulus into one cover claim.')
def egypt_cover_assemble(rt, esq):
    d = esq['data']
    data = assemble(checked_families(rt, d['a'], d['terms']), d['a'], d['terms'], d['modulus'])
    if data is None: return []
    cover = rt.propose('cover', data, (esq,))
    return [cover] if rt.check(cover) else []


@op('egypt_cover_lift', 'NS', ('cover',), ('cover',),
    'Restate a cover modulo t*M for the least prime t not dividing M; each residue lifts to t residues.')
def egypt_cover_lift(rt, cover):
    d = cover['data']; M = d['modulus']
    t = next(p for p in PRIMES if M % p)
    if M * t > 10 ** 6: return []
    lifted = rt.propose('cover', dict(d, modulus=M * t), (cover,))
    return [lifted] if rt.check(lifted) else []


@op('egypt_cover_merge', 'NS', ('cover', 'cover'), ('cover',),
    'Merge two covers of one question modulo the lcm of their moduli.')
def egypt_cover_merge(rt, first, second):
    d1, d2 = first['data'], second['data']
    if (d1['a'], d1['terms']) != (d2['a'], d2['terms']) or first['id'] == second['id']: return []
    M = L.lcm(d1['modulus'], d2['modulus'])
    if M > 10 ** 6: return []
    families = {L.digest(e['family']): dict(data=e['family']) for e in d1['entries'] + d2['entries']}
    data = assemble(list(families.values()), d1['a'], d1['terms'], M)
    if data is None: return []
    merged = rt.propose('cover', data, (first, second))
    return [merged] if rt.check(merged) else []


@op('egypt_residual', 'W', ('cover',), ('residual',),
    'Name the residues modulo the cover modulus that no checked family covers.')
def egypt_residual(rt, cover):
    d = cover['data']; covered = cover_set(d)
    left = [x for x in range(d['modulus']) if x not in covered]
    return [rt.residual(cover, left[:4096], str(len(left)) + ' residues mod ' + str(d['modulus']) + ' uncovered')]


@op('egypt_square_pattern', 'NWS', ('cover',), ('pattern', 'refutation'),
    'Conjecture that the uncovered coprime residues are exactly the coprime squares; check it or refute it.')
def egypt_square_pattern(rt, cover):
    d = cover['data']
    claim = rt.propose('pattern', dict(cover=d, rule='uncovered_coprime_are_squares'), (cover,))
    if rt.check(claim): return [claim]
    covered = cover_set(d); M = d['modulus']
    squares = {x * x % M for x in range(M) if gcd(x, M) == 1}
    for x in range(M):
        if gcd(x, M) == 1 and (x in squares) == (x in covered):
            refutation = rt.refute(claim, dict(residue=x))
            if refutation is not None: return [claim, refutation]
    return [claim]


@op('egypt_density', 'NS', ('cover',), ('density',),
    'State the exact fraction of residues a cover covers.')
def egypt_density(rt, cover):
    d = cover['data']
    claim = rt.propose('density', dict(cover=d, fraction=L.enc(Q(len(cover_set(d)), d['modulus']))), (cover,))
    return [claim] if rt.check(claim) else []


@op('egypt_finite_verify', 'NWS', ('esq',), ('finite', 'residual'),
    'Verify every n in [min, verify_to): cover classes, a checked prime divisor scaled up, or a new witness.')
def egypt_finite_verify(rt, esq):
    d = esq['data']; a, terms, lo, hi = d['a'], d['terms'], d['min'], d['verify_to']
    cover = best_cover(rt, a, terms)
    thresholds = {}
    for entry in (cover['data']['entries'] if cover else []):
        f = entry['family']; row = thresholds.setdefault(f['m'], {})
        row[f['r']] = min(row.get(f['r'], f['m'] * f['k0'] + f['r']), f['m'] * f['k0'] + f['r'])
    witnesses, divisors, done, missing = {}, {}, set(), []
    for n in range(lo, hi):
        rt.budget.use(1 + len(thresholds))
        if any(n >= row.get(n % m, n + 1) for m, row in thresholds.items()): done.add(n); continue
        p = next((q for q in sorted(L.factor(n)) if q < n and q in done), None)
        if p is not None: divisors[str(n)] = p; done.add(n); continue
        xs = witness(a, n, rt.budget, max_excess=4 * a * 256) if terms == 3 else None
        if xs is None: missing.append(n); continue
        witnesses[str(n)] = sorted(xs)[:-1]; done.add(n)
    if missing: return [rt.residual(esq, missing[:4096], 'no witness found within the search bound')]
    claim = rt.propose('finite', dict(a=a, terms=terms, lo=lo, hi=hi, witnesses=witnesses, divisors=divisors,
                                      cover=cover['data'] if cover else None), (esq,) + ((cover,) if cover else ()))
    return [claim] if rt.check(claim) else []


# ------------------------------------------------------------- fixtures for the move bench

def _en(rt, n, a=4, terms=3): return rt.given('en', dict(a=a, n=n, terms=terms))


def _cls(rt, m, r, a=4, terms=3): return rt.given('eclass', dict(a=a, terms=terms, m=m, r=r))


def _esq(rt, M, a=4, terms=3, verify_to=200):
    return rt.given('esq', dict(a=a, terms=terms, min=2, modulus=M, verify_to=verify_to))


def _checked(rt, kind, data):
    obj = rt.propose(kind, data); rt.check(obj); return obj


def _fam(rt, m, r):
    return _checked(rt, 'ufam', ansatz(4, m, r, [(s, c) for s in BASE_S for c in BASE_C], rt.budget)[0][0])


def _rep(rt, n, xs=None):
    return _checked(rt, 'ufrac', dict(a=4, n=n, x=xs or witness(4, n, rt.budget)))


def _one_over_n(rt, m, r):
    return _checked(rt, 'ufam', dict(a=1, m=m, r=r, k0=0, x=[L.univariate_expr([Q(r), Q(m)], 'k')]))


def _even_family(rt):
    return _checked(rt, 'ufam', family_data(4, 2, 0, 1, [[Q(0), Q(1)], [Q(0), Q(2)], [Q(0), Q(2)]]))


def _cover(rt):
    fams = [_fam(rt, 840, r) for r in (11, 13, 17)] + [_even_family(rt)]
    return _checked(rt, 'cover', assemble(fams, 4, 3, 840))


def _small_cover(rt):
    return _checked(rt, 'cover', assemble([_fam(rt, 24, r) for r in (5, 7, 11, 13, 17, 19, 23)], 4, 3, 24))


def _two_covers(rt):
    return [_checked(rt, 'cover', assemble([_fam(rt, 24, 11)], 4, 3, 24)),
            _checked(rt, 'cover', assemble([_fam(rt, 40, 3)], 4, 3, 40))]


def _assembly(rt):
    _fam(rt, 24, 11); _fam(rt, 24, 23)
    return [_esq(rt, 24)]


FIXTURES = {
    'egypt_witness_search': [lambda rt: [_en(rt, 1009)], lambda rt: [_en(rt, 7, a=5, terms=4)],
                             lambda rt: [_en(rt, 3, terms=2)]],
    'egypt_greedy': [lambda rt: [_en(rt, 23)]],
    'egypt_zero_class': [lambda rt: [_rep(rt, 7, [2, 21, 42])]],
    'egypt_specialize': [lambda rt: [_fam(rt, 24, 11)]],
    'egypt_subclass': [lambda rt: [_fam(rt, 24, 11)]],
    'egypt_scale_class': [lambda rt: [_fam(rt, 24, 11)]],
    'egypt_more_terms': [lambda rt: [_fam(rt, 24, 11)]],
    'egypt_numerator_add': [lambda rt: [_fam(rt, 24, 11), _one_over_n(rt, 24, 11)]],
    'egypt_divide_numerator': [lambda rt: [_even_family(rt)]],
    'egypt_family_identity': [lambda rt: [_fam(rt, 24, 11)]],
    'egypt_divisor_ansatz': [lambda rt: [_cls(rt, 840, 11)], lambda rt: [_cls(rt, 840, 1)]],
    'egypt_ansatz_extend': [lambda rt: [_cls(rt, 9240, 6001)], lambda rt: [_cls(rt, 840, 1)]],
    'egypt_template_transfer': [lambda rt: [_fam(rt, 840, 11), _cls(rt, 840, 19)],
                                lambda rt: [_fam(rt, 840, 11), _cls(rt, 840, 13)]],
    'egypt_family_fit': [lambda rt: [_cls(rt, 4, 3)], lambda rt: [_cls(rt, 4, 1)]],
    'egypt_generalize_witness': [lambda rt: [_rep(rt, 11, [3, 34, 1122])], lambda rt: [_rep(rt, 1009)]],
    'egypt_class_split': [lambda rt: [_cls(rt, 840, 1)]],
    'egypt_class_refine': [lambda rt: [_cls(rt, 9240, 2521), _esq(rt, 27720)], lambda rt: [_cls(rt, 9240, 2521), _esq(rt, 83160)]],
    'egypt_family_refute': [lambda rt: [rt.propose('ufam', family_data(4, 840, 1, 0, [[Q(1), Q(210)], [Q(1)], [Q(1)]]))]],
    'egypt_cover_assemble': [_assembly],
    'egypt_cover_lift': [lambda rt: [_cover(rt)]],
    'egypt_cover_merge': [_two_covers],
    'egypt_residual': [lambda rt: [_cover(rt)]],
    'egypt_square_pattern': [lambda rt: [_cover(rt)], lambda rt: [_small_cover(rt)]],
    'egypt_density': [lambda rt: [_cover(rt)]],
    'egypt_finite_verify': [lambda rt: [_esq(rt, 24, verify_to=400)], lambda rt: [_esq(rt, 24, terms=4, verify_to=5)]],
}
