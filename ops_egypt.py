"""Operators on unit-fraction questions: a/n = 1/x_1 + ... + 1/x_t.

Families are polynomial in the class parameter k with n = m*k + r. The divisor
ansatz takes x = (s*n + c)/a, so a/n - 1/x = e/N after reduction, and writes
1/y + 1/z = e/N with y = (N + d)/e and z = (N + N^2/d)/e for a divisor d of N^2
built from the primitive factors of N. Every family, witness, cover and finite
range is admitted only by lexicon_check.py; an operator's search can miss.

The classical operators use the two fixed-parameter solution types: Type II
x = u*v*d, y = u*w*d*n, z = v*w*d*n with a*u*v*d = n + e and e*w = u + v, and
Type I x = u*v*d*n, y = u*w*d, z = v*w*d with (u+v)*n + w = a*u*v*w*d. A class
none of them reaches can be certified as such (a 'nofamily' claim), and the
refinement prime for such classes can be chosen by measured yield.
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
CLASSICAL_BOUND = 0  # 0: every classical parameter set (Type I is finite at a fixed modulus); n > 0 bounds u, v, w by n
LIFT_CAP = 10 ** 7
LIFT_CLASSES = 60_000
WALL_CAP = 10 ** 12
SWEEP_CLASSES = 4000
RANGE_FRONTIER = 30  # she extends a checked range in chunks of its own size, up to this multiple of verify_to
# Work units on the prover's side are priced at about a microsecond of this machine (the witness search's price):
# the cover loop one unit a number plus one per ten moduli, a factor check half the bit length, a family step half
# the bit length of its linear form; measured 2026-09-25 (CAMPAIGNS.md, consolidation), the checker's charges unchanged.
BREATH = 64  # an anytime move breathes after this many n


def op(name, dirs, consumes, produces, summary):
    def wrap(fn):
        OPS.append(dict(name=name, dirs=dirs, consumes=tuple(consumes), produces=tuple(produces), summary=summary,
                        fn=fn, entry=fn.__name__))
        return fn
    return wrap


# ------------------------------------------------------------- shared producer helpers

def family_data(a, m, r, k0, polys):
    return dict(a=a, m=m, r=r, k0=k0, x=[[[c.numerator, c.denominator] for c in L.ptrim([Q(c) for c in p])] for p in polys])


def family_polys(data):
    """Denominators as coefficient lists; saved families may still use expression trees or name their parameters."""
    xs = data['x'] if 'x' in data else L.classical_x(data['a'], data['m'], data['r'], data['p'])
    return [L.univariate(e, 'k') if e and type(e[0]) is str else [Q(n, d) for n, d in e] for e in xs]


def compact_family(data):
    """The shortest certificate for the same family: its parameters when it is classical, else every denominator
    as a coefficient list."""
    if 'p' in data: return {k: v for k, v in data.items() if k != 'x'}
    x = [[[c.numerator, c.denominator] for c in L.ptrim(p)] for p in family_polys(data)]
    named = L.classical_params_of(data['a'], data['m'], data['r'], x) if len(x) == 3 else None
    return dict({k: v for k, v in data.items() if k != 'x'}, p=named) if named else dict(data, x=x)


def least_start(polys, limit=64):
    """Smallest k0 with every polynomial positive from k0 on, by the checker's shifted-coefficient test."""
    for k0 in range(limit):
        if all(L.nonnegative_from(p, k0) for p in polys): return k0
    return None


def integral(polys):
    return all(L.integer_valued(p) for p in polys)


def ansatz(a, m, r, pairs, budget, limit=1):
    """Families of the divisor ansatz on the class n = m*k + r, in the order of the (s, c) pairs (see ansatz_steps)."""
    return L.drive(ansatz_steps(a, m, r, pairs, budget, limit))


def ansatz_steps(a, m, r, pairs, budget, limit=1):
    """Families of the divisor ansatz on the class n = m*k + r, in the order of the (s, c) pairs; an anytime search
    that breathes after each pair, so a scheduler may suspend it there and resume it later.

    Integer values at k = 0..4 prefilter every divisor shape; survivors are built
    as exact polynomials. Degrees are at most four, so five points decide integrality.
    """
    ks = range(5); nk = [m * k + r for k in ks]; found = []
    cont_n = gcd(m, r); n_p = [Q(r, cont_n), Q(m, cont_n)]
    for s, c in pairs:
        budget.use()
        if (yield) == 'checkpoint': return 'checkpoint'  # the call ends: no miss is recorded
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


def open_residues(data, budget):
    """Residues modulo the cover modulus that no family reaches. A cover with a chain of levels is sieved: only the
    classes left open at one level are lifted to the next, so the work follows the open classes, not the modulus."""
    M = data['modulus']
    if 'chain' not in data:
        covered = cover_set(data); budget.use(M)
        return [x for x in range(M) if x not in covered]
    by = {}
    for entry in data['entries']: by.setdefault(entry['family']['m'], set()).add(entry['family']['r'])
    level, prev = None, None
    for step in data['chain']:
        mods = [(m, rs) for m, rs in by.items() if step % m == 0 and (prev is None or prev % m)]
        candidates = range(step) if prev is None else [y for x in level for y in range(x, step, prev)]
        budget.use(len(candidates))
        level = [y for y in candidates if not any(y % m in rs for m, rs in mods)]; prev = step
    return sorted(level)


def covered_fraction(o, budget):
    d = o['data']; covered = o.get('evidence', {}).get('covered')
    if covered is None: covered = d['modulus'] - len(open_residues(d, budget))
    return Q(covered, d['modulus'])


def best_cover(rt, a, terms, modulus=None):
    covers = [o for o in rt.objects.values() if o['kind'] == 'cover' and o['status'] == 'checked'
              and o['data']['a'] == a and o['data']['terms'] == terms
              and (modulus is None or o['data']['modulus'] == modulus)]
    return max(covers, key=lambda o: (covered_fraction(o, rt.budget), -o['data']['bound']), default=None)


def level_chain(rt, a, terms, M):
    """The question's own refinement levels dividing M, as a divisibility chain ending at M (None for one level)."""
    levels = sorted({o['data']['modulus'] for o in rt.objects.values() if o['kind'] == 'esq' and o['data']['a'] == a
                     and o['data']['terms'] == terms and M % o['data']['modulus'] == 0} | {M})
    chain = []
    for m in levels:
        if not chain or m % chain[-1] == 0: chain.append(m)
    return chain if len(chain) > 1 and chain[0] <= 100_000 else None


def assemble(families, a, terms, M):
    """One entry per family whose modulus divides M and whose class no coarser included family contains, in the
    compact form: a classical family by its parameters, any other by the index of its identity in the cover's shape
    table, where each identity is written once as its denominators in n."""
    entries = []; bound = 1; kept = []
    for f in sorted(families, key=lambda o: (o['data']['m'], o['data']['r'], o['data']['k0'])):
        d = f['data']
        if M % d['m'] or any(d['m'] % m == 0 and d['r'] % m == r for m, r in kept): continue
        kept.append((d['m'], d['r'])); entries.append(compact_family(d))
        bound = max(bound, d['m'] * d['k0'] + d['r'])
    if not entries: return None
    shapes, lean = L.shape_table(entries)
    cover = dict(a=a, terms=terms, modulus=M, entries=[dict(family=d) for d in lean], bound=bound)
    return dict(cover, shapes=shapes) if shapes else cover


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


# ------------------------------------------------------------- classical fixed-parameter families

_CLASSICAL = {}
_CLASSICAL_SIZES = {}
CLASSICAL_ENTRIES = 3_000_000


def type1_triples(a, m, bound):
    """Type I parameters (u, v, w), u <= v, with a*u*v*w | (u+v)*m. With bound 0 the set is complete: writing
    u = d*u', v = d*v' with gcd(u', v') = 1 forces u'*v' | m and d*w | (u'+v')*m/(a*u'*v'), a finite set."""
    if bound:
        for u in range(1, bound + 1):
            for v in range(u, bound + 1):
                if ((u + v) * m) % (a * u * v): continue
                yield from ((u, v, w) for w in range(1, bound + 1) if ((u + v) * m) % (a * u * v * w) == 0)
        return
    ds = L.divisors(m)
    for up in ds:
        for vp in ds:
            if vp < up or gcd(up, vp) != 1 or m % (up * vp): continue
            X = (up + vp) * (m // (up * vp))
            if X % a: continue
            for t in L.divisors(X // a): yield from ((d * up, d * vp, t // d) for d in L.divisors(t))


def classical_tables(a, m, bound):
    """Per modulus: every class the classical families reach, indexed {class modulus: {residue: parameters}}, Type II
    and Type I apart. A family is recorded on the coarsest class its parameters need."""
    key = (a, m, bound)
    if key not in _CLASSICAL:
        type2 = {}
        for D in L.divisors(m):
            if D % a: continue
            uv = D // a
            for u in L.divisors(uv):
                v = uv // u
                if u > v: continue
                for e in L.divisors(u + v):
                    type2.setdefault(D, {}).setdefault((-e) % D, ('II', u, v, (u + v) // e, e))
        type1 = {}
        for u, v, w in type1_triples(a, m, bound):
            s = u + v; q = a * u * v * w; g = gcd(s, q)
            if w % g: continue
            mod = q // g; r0 = (-(w // g) * pow(s // g, -1, mod)) % mod if mod > 1 else 0
            type1.setdefault(mod, {}).setdefault(r0, ('I', u, v, w, None))
        # Bounded by count and by entries (near 10**10 one table holds over a million classes); the least recently
        # used tables leave first.
        entries = sum(len(row) for row in type2.values()) + sum(len(row) for row in type1.values())
        while _CLASSICAL and (len(_CLASSICAL) >= 16 or sum(_CLASSICAL_SIZES.values()) + entries > CLASSICAL_ENTRIES):
            oldest = next(iter(_CLASSICAL)); del _CLASSICAL[oldest]; del _CLASSICAL_SIZES[oldest]
        _CLASSICAL[key] = (type2, type1); _CLASSICAL_SIZES[key] = entries
    else:
        _CLASSICAL[key] = _CLASSICAL.pop(key); _CLASSICAL_SIZES[key] = _CLASSICAL_SIZES.pop(key)
    return _CLASSICAL[key]


def classical_search(a, m, r, bound, budget, limit=1):
    """Parameters of classical families on n = r (mod m), Type II first; the producer's own enumeration."""
    type2, type1 = classical_tables(a, m, bound); out = []
    for table in (type2, type1):
        for mod, row in table.items():
            budget.use()
            found = row.get(r % mod)
            if found:
                out.append(found)
                if len(out) >= limit: return out
    return out


def classical_family(a, m, r, params):
    """The family on the coarsest class its parameters need: modulus a*u*v (Type II) or a*u*v*w/gcd(a*u*v*w, u+v)."""
    kind, u, v, w, e = params
    if kind == 'II':
        m = D = a * u * v; r %= m; n = [Q(r), Q(m)]
        d = [Q(r + e, D), Q(m, D)]; dn = L.pmul(d, n)
        polys = [L.pscale(d, u * v), L.pscale(dn, u * w), L.pscale(dn, v * w)]
    else:
        q = a * u * v * w; m = q // gcd(q, u + v); r %= m; n = [Q(r), Q(m)]
        d = [Q((u + v) * r + w, q), Q((u + v) * m, q)]
        polys = [L.pscale(L.pmul(d, n), u * v), L.pscale(d, u * w), L.pscale(d, v * w)]
    k0 = least_start(polys + [n])
    return dict(family_data(a, m, r, 0 if k0 is None else k0, polys), p=[kind, u, v, e if kind == 'II' else w])


def local_nonresidues(x, powers):
    """Primes p of the modulus with x a quadratic non-residue modulo p**e (x coprime to the modulus)."""
    out = []
    for p, e in sorted(powers.items()):
        if p == 2:
            if (e == 2 and x % 4 != 1) or (e >= 3 and x % 8 != 1): out.append(2)
        elif L.legendre(x % p, p) != 1: out.append(p)
    return out


def uncovered_coprime(cover_data, budget):
    M = cover_data['modulus']
    return [x for x in open_residues(cover_data, budget) if gcd(x, M) == 1]


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
    d = fam['data']; xs = [L.univariate_expr(p, 'k') for p in family_polys(d)]
    n = L.add(L.mul(L.num(d['m']), L.var('k')), L.num(d['r']))
    rhs = L.mul(n, L.add(*[L.mul(L.num(1), *[x for j, x in enumerate(xs) if j != i]) for i in range(len(xs))]))
    claim = rt.transfer('identity', dict(vars=['k'], lhs=L.mul(L.num(d['a']), *xs), rhs=rhs), fam)
    return [claim] if rt.check(claim) else []


# ------------------------------------------------------------- family discovery

@op('egypt_divisor_ansatz', 'NWS', ('eclass',), ('ufam', 'residual'),
    'Base grammar: x = (s*n+c)/a with s < 13 and c < 40, and every divisor shape of N^2; a miss is a residual. An '
    'anytime move: it breathes after each (s, c) pair.')
def egypt_divisor_ansatz(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    found = yield from ansatz_steps(a, m, r, [(s, c) for s in BASE_S for c in BASE_C], rt.budget)
    if found == 'checkpoint': return []
    if not found: return [rt.residual(cls, ['base divisor grammar exhausted'], 'ansatz miss')]
    fam = rt.propose('ufam', found[0][0], (cls,))
    return [fam] if rt.check(fam) else []


@op('egypt_ansatz_extend', 'NWS', ('eclass',), ('ufam', 'template', 'residual'),
    'Invent a template outside the base grammar (s < 25, c < 240, polynomial excess); it becomes a reusable move. An '
    'anytime move: it breathes after each (s, c) pair.')
def egypt_ansatz_extend(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    pairs = [(s, c) for s in EXTENDED_S for c in EXTENDED_C if not (s in BASE_S and c in BASE_C)]
    found = yield from ansatz_steps(a, m, r, pairs, rt.budget)
    if found == 'checkpoint': return []
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


@op('egypt_classical_family', 'NWS', ('eclass',), ('ufam', 'residual'),
    'Classical fixed-parameter families: Type II over every modulus a*u*v dividing m, Type I over every a*u*v*w '
    'dividing (u+v)*m, stated on the coarsest class the parameters need; a miss is a residual.')
def egypt_classical_family(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3: return []
    found = classical_search(a, m, r, CLASSICAL_BOUND, rt.budget)
    if not found: return [rt.residual(cls, ['classical fixed-parameter families exhausted'], 'classical miss')]
    fam = rt.propose('ufam', classical_family(a, m, r, found[0]), (cls,))
    return [fam] if rt.check(fam) else []


@op('egypt_classical_exclusion', 'NWS', ('eclass',), ('nofamily',),
    'Claim that no fixed-parameter classical family reaches the class; the checker enumerates every such family.')
def egypt_classical_exclusion(rt, cls):
    a, terms, m, r = question_class(cls)
    if terms != 3 or m > WALL_CAP: return []
    claim = rt.propose('nofamily', dict(a=a, terms=terms, m=m, r=r, bound=CLASSICAL_BOUND), (cls,))
    return [claim] if rt.check(claim) else []


@op('egypt_classical_obstruction', 'NWS', ('esq',), ('obstruction', 'refutation'),
    'Claim that no classical fixed-parameter family reaches a coprime square class modulo the question modulus; the '
    'checker enumerates every reached class, and a reached square class refutes the claim.')
def egypt_classical_obstruction(rt, esq):
    d = esq['data']; a, terms, M = d['a'], d['terms'], d['modulus']
    if terms != 3 or M > WALL_CAP: return []
    claim = rt.propose('obstruction', dict(a=a, terms=terms, m=M, rule='classical_reach_nonsquare'), (esq,))
    if rt.check(claim): return [claim]
    for table in classical_tables(a, M, CLASSICAL_BOUND):
        for mod, row in table.items():
            for r0, params in row.items():
                rt.budget.use()
                if gcd(r0, mod) != 1 or local_nonresidues(r0, L.factor(mod)): continue
                kind, u, v = params[:3]
                witness = dict(modulus=mod, residue=r0, params=[kind, u, v, params[4] if kind == 'II' else params[3]])
                refutation = rt.refute(claim, witness)
                if refutation is not None: return [claim, refutation]
    return [claim]


def level_classes(rt, a, terms, M):
    """The class targets of one level: eclass objects of this question with modulus M, by residue."""
    return sorted((o for o in rt.objects.values() if o['kind'] == 'eclass' and o['data']['m'] == M
                   and o['data']['a'] == a and o['data']['terms'] == terms), key=lambda o: o['data']['r'])


def family_index(rt, a, terms):
    index = {}
    for f in checked_families(rt, a, terms): index.setdefault(f['data']['m'], set()).add(f['data']['r'])
    return index


def reached(index, M, r):
    return any(M % m == 0 and r % m in rs for m, rs in index.items())


def notes_of(rt, cls):
    return {o['data']['note'] for o in rt.objects.values() if o['kind'] == 'residual' and o['data'].get('of') == cls['id']}


def lemma_holds(rt, a, M):
    """A checked obstruction lemma at a multiple of M: no classical family reaches a coprime square class mod M."""
    return any(o['kind'] == 'obstruction' and o['status'] == 'checked' and o['data']['a'] == a and o['data']['m'] % M == 0
               for o in rt.objects.values())


@op('egypt_classical_sweep', 'NWS', ('esq',), ('ufam', 'residual'),
    'Run the classical generator over the classes of the question modulus that no checked family reaches, many in '
    'one move: a family for each class it reaches, stated on the coarsest class, and a classical miss for each other. '
    'An anytime move: it breathes after each class.')
def egypt_classical_sweep(rt, esq):
    d = esq['data']; a, terms, M = d['a'], d['terms'], d['modulus']
    if terms != 3 or M > WALL_CAP: return []
    index = family_index(rt, a, terms); squares_known = lemma_holds(rt, a, M); powers = L.factor(M); out = []; done = 0
    missed = {o['data']['of'] for o in rt.objects.values() if o['kind'] == 'residual' and o['data'].get('note') == 'classical miss'}
    for cls in level_classes(rt, a, terms, M):
        r = cls['data']['r']; rt.budget.use()
        if cls['id'] in missed or reached(index, M, r): continue
        if squares_known and gcd(r, M) == 1 and not local_nonresidues(r, powers): continue  # her lemma settles these
        if done >= SWEEP_CLASSES: break
        done += 1
        if (yield) == 'checkpoint': break  # the call ends: the classes swept so far are the result
        found = classical_search(a, M, r, CLASSICAL_BOUND, rt.budget)
        if not found:
            out.append(rt.residual(cls, ['classical fixed-parameter families exhausted'], 'classical miss')); continue
        fam = rt.propose('ufam', classical_family(a, M, r, found[0]), (cls,))
        if rt.check(fam):
            out.append(fam); index.setdefault(fam['data']['m'], set()).add(fam['data']['r'])
    return out


@op('egypt_wall_sweep', 'NWS', ('esq',), ('nofamily',),
    'Certify in one batch claim the classes of the question modulus that the classical generator missed and no family '
    'reaches: the checker enumerates every classical parameter set for each; square classes her lemma settles are left out.')
def egypt_wall_sweep(rt, esq):
    d = esq['data']; a, terms, M = d['a'], d['terms'], d['modulus']
    if terms != 3 or M > WALL_CAP: return []
    index = family_index(rt, a, terms); squares_known = lemma_holds(rt, a, M); powers = L.factor(M)
    missed = {o['data']['of'] for o in rt.objects.values() if o['kind'] == 'residual' and o['data'].get('note') == 'classical miss'}
    walled = set()
    for o in rt.objects.values():
        if o['kind'] == 'nofamily' and o['status'] == 'checked' and o['data']['m'] == M and o['data']['a'] == a:
            walled.update(o['data']['rs'] if 'rs' in o['data'] else [o['data']['r']])
    rs = []
    for cls in level_classes(rt, a, terms, M):
        r = cls['data']['r']; rt.budget.use()
        if cls['id'] not in missed or r in walled or reached(index, M, r): continue
        if squares_known and gcd(r, M) == 1 and not local_nonresidues(r, powers): continue
        rs.append(r)
        if len(rs) >= SWEEP_CLASSES: break
    if not rs: return []
    claim = rt.propose('nofamily', dict(a=a, terms=terms, m=M, rs=sorted(rs), bound=CLASSICAL_BOUND), (esq,))
    return [claim] if rt.check(claim) else []


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
    chain = level_chain(rt, d['a'], d['terms'], d['modulus'])
    if chain: data = dict(data, chain=chain)
    cover = rt.propose('cover', data, (esq,))
    return [cover] if rt.check(cover) else []


@op('egypt_cover_lift', 'NS', ('cover',), ('cover',),
    'Restate a cover modulo t*M for the least prime t not dividing M; each residue lifts to t residues.')
def egypt_cover_lift(rt, cover):
    d = cover['data']; M = d['modulus']
    t = next(p for p in PRIMES if M % p)
    if M * t > 10 ** 6: return []
    lifted = rt.propose('cover', dict(d, modulus=M * t, **({'chain': d['chain'] + [M * t]} if 'chain' in d else {})), (cover,))
    return [lifted] if rt.check(lifted) else []


@op('egypt_cover_merge', 'NS', ('cover', 'cover'), ('cover',),
    'Merge two covers of one question modulo the lcm of their moduli.')
def egypt_cover_merge(rt, first, second):
    d1, d2 = first['data'], second['data']
    if (d1['a'], d1['terms']) != (d2['a'], d2['terms']) or first['id'] == second['id']: return []
    M = L.lcm(d1['modulus'], d2['modulus'])
    if M > 10 ** 6: return []
    families = {}
    for d in (d1, d2):
        for e in d['entries']:
            f = L.unshape(e['family'], d.get('shapes')); families[L.digest(f)] = dict(data=f)
    data = assemble(list(families.values()), d1['a'], d1['terms'], M)
    if data is None: return []
    merged = rt.propose('cover', data, (first, second))
    return [merged] if rt.check(merged) else []


@op('egypt_residual', 'W', ('cover',), ('residual',),
    'Name the residues modulo the cover modulus that no checked family covers.')
def egypt_residual(rt, cover):
    d = cover['data']; left = open_residues(d, rt.budget)
    return [rt.residual(cover, left[:4096], str(len(left)) + ' residues mod ' + str(d['modulus']) + ' uncovered')]


@op('egypt_square_pattern', 'NWS', ('cover',), ('pattern', 'refutation'),
    'Conjecture that the uncovered coprime residues are exactly the coprime squares; check it or refute it.')
def egypt_square_pattern(rt, cover):
    d = cover['data']
    claim = rt.propose('pattern', dict(cover=d, rule='uncovered_coprime_are_squares'), (cover,))
    if rt.check(claim): return [claim]
    M = d['modulus']
    if 'chain' in d:
        # An open unit that is not a local square, or else a square of a unit that some family reaches.
        powers = L.factor(M); opened = uncovered_coprime(d, rt.budget)
        witness = next((x for x in opened if local_nonresidues(x, powers)), None)
        if witness is None:
            shut = set(opened)
            witness = next((y * y % M for y in range(1, min(M, 200_000)) if gcd(y, M) == 1 and y * y % M not in shut), None)
        refutation = rt.refute(claim, dict(residue=witness)) if witness is not None else None
        return [claim, refutation] if refutation is not None else [claim]
    covered = cover_set(d)
    squares = {x * x % M for x in range(M) if gcd(x, M) == 1}
    for x in range(M):
        if gcd(x, M) == 1 and (x in squares) == (x in covered):
            refutation = rt.refute(claim, dict(residue=x))
            if refutation is not None: return [claim, refutation]
    return [claim]


@op('egypt_signature_pattern', 'NS', ('cover',), ('pattern',),
    'Find the least set of primes outside which every uncovered coprime class is a local square, and claim it.')
def egypt_signature_pattern(rt, cover):
    d = cover['data']; powers = L.factor(d['modulus']); primes = set()
    for x in uncovered_coprime(d, rt.budget): primes.update(local_nonresidues(x, powers))
    claim = rt.propose('pattern', dict(cover=d, rule='uncovered_coprime_square_outside', primes=sorted(primes)), (cover,))
    return [claim] if rt.check(claim) else []


@op('egypt_local_pattern', 'NS', ('cover',), ('pattern',),
    'Record, for each prime-power factor of the modulus, the residues the uncovered coprime classes reduce to, '
    'and claim that every uncovered class stays inside them.')
def egypt_local_pattern(rt, cover):
    d = cover['data']; powers = L.factor(d['modulus'])
    images = {str(p ** e): set() for p, e in powers.items()}
    for x in uncovered_coprime(d, rt.budget):
        for p, e in powers.items(): images[str(p ** e)].add(x % p ** e)
    claim = rt.propose('pattern', dict(cover=d, rule='uncovered_coprime_local_images',
                                       images={k: sorted(v) for k, v in images.items()}), (cover,))
    return [claim] if rt.check(claim) else []


def lift_reach(a, M, p, classes, budget):
    """How many coprime lifts to M*p of the coprime classes x (mod M) a classical family reaches, counted exactly.

    Every table class has a modulus q dividing M*p. When q does not divide M, write P = p**(v_p(M) + 1): then q/p
    divides M, and n = x + M*j lies in the table class r0 (mod q) exactly when x = r0 (mod q/p) and n = r0 (mod P).
    As j runs over 0..p-1, n mod P runs once over the residues = x (mod P/p), so the reached lifts of x are the
    distinct values r0 mod P over the entries with r0 = x (mod q/p). When p does not divide M, the lift n = 0 (mod p)
    is not coprime and is not counted. Classes a family with modulus dividing M reaches must be left out of classes."""
    type2, type1 = classical_tables(a, M * p, CLASSICAL_BOUND)
    P = p
    while M % P == 0: P *= p
    split = {}
    for table in (type2, type1):
        for q, row in table.items():
            if M % q == 0: continue
            index = split.setdefault(q // p, {})
            for r0 in row: index.setdefault(r0 % (q // p), set()).add(r0 % P)
    reached = 0
    for x in classes:
        budget.use(len(split)); hit = set()
        for h, index in split.items():
            found = index.get(x % h)
            if found: hit |= found
        if M % p: hit.discard(0)
        reached += len(hit)
    return reached


@op('egypt_choose_lift', 'N', ('esq',), ('esq', 'eclass'),
    'Choose the next refinement prime by exact yield: for each candidate prime (new primes first, primes of the '
    'modulus only when no new prime reaches a lift), count every lift of the uncovered classes a classical family '
    'reaches, then refine every uncovered class by the prime that leaves the smallest fraction of residues open.')
def egypt_choose_lift(rt, esq):
    d = esq['data']; a, terms, M = d['a'], d['terms'], d['modulus']
    cover = best_cover(rt, a, terms, M)
    if cover is None or terms != 3: return []
    left = open_residues(cover['data'], rt.budget); stuck = [x for x in left if gcd(x, M) == 1]
    if not stuck: return []
    # A class some classical family with modulus dividing M already reaches lifts to reached classes by every prime; it
    # needs that family, not a refinement, so it is left out of the count.
    here = [row for table in classical_tables(a, M, CLASSICAL_BOUND) for row in table.items()]
    unreached = []
    for x in stuck:
        rt.budget.use(len(here))
        if not any(x % q in row for q, row in here): unreached.append(x)
    # The lifts to examine, not the size of the modulus, bound a refinement: covers are sieved along the levels.
    allowed = [p for p in PRIMES if len(left) * p <= LIFT_CLASSES and M * p <= WALL_CAP]
    best = None
    # New primes first: their lift divisible by p is not an open coprime class, and her measured yields for raising
    # a prime already in M were far lower (74 of 5,238 lifts for 2 at 1,580,040, against 14,560 of 31,428 for 13).
    # Primes of M are counted only when no new prime reaches a lift; each count needs the whole table for M*p.
    for group in ([p for p in allowed if M % p], [p for p in allowed if M % p == 0]):
        for p in group:
            reached = lift_reach(a, M, p, unreached, rt.budget)
            if not reached: continue
            share = Q(len(unreached) * (p if M % p == 0 else p - 1) - reached, M * p)
            if best is None or share < best[0]: best = (share, p)
        if best is not None: break
    if best is None: return []
    p = best[1]
    out = [rt.propose('esq', dict(d, modulus=M * p), (esq,))]
    for x in left:
        parent = rt.given('eclass', dict(a=a, terms=terms, m=M, r=x))
        out += [rt.propose('eclass', dict(a=a, terms=terms, m=M * p, r=x + M * j), (parent,)) for j in range(p)]
    return out


@op('egypt_reduction_theorem', 'NS', ('finite',), ('theorem',),
    'State the theorem a checked range and its cover prove together: every n >= min outside the open residue '
    'classes has a representation; the checker verifies the whole chain, class by class. Only the range that starts '
    'lowest states the theorem; a later chunk extends it through a derivation.')
def egypt_reduction_theorem(rt, finite):
    d = finite['data']
    if finite['status'] != 'checked' or d['cover'] is None: return []
    if any(o['kind'] == 'finite' and o['status'] == 'checked' and o['data']['a'] == d['a'] and o['data']['terms'] == d['terms']
           and o['data']['lo'] < d['lo'] for o in rt.objects.values()): return []
    claim = rt.propose('theorem', dict(a=d['a'], terms=d['terms'], lo=d['lo'], finite=d), (finite,))
    return [claim] if rt.check(claim) else []


# ------------------------------------------------------------- ranges beyond the checker's bound: chunks and derivations

def range_statements(rt, a, terms):
    """Every admitted range of this question, as (lo, hi, object): checked finite claims and derived range statements."""
    out = []
    for o in rt.objects.values():
        if o['status'] != 'checked': continue
        if o['kind'] == 'finite' and o['data']['a'] == a and o['data']['terms'] == terms:
            out.append((o['data']['lo'], o['data']['hi'], o))
        elif o['kind'] == 'derived' and o['data']['statement'].get('kind') == 'range' \
                and o['data']['statement']['a'] == a and o['data']['statement']['terms'] == terms:
            out.append((o['data']['statement']['lo'], o['data']['statement']['hi'], o))
    return out


def frontier(ranges, lo):
    """The largest hi reached from lo by admitted ranges that touch or overlap, and the range object reaching it."""
    reach, best = lo, None
    while True:
        step = max(((hi, o) for l, hi, o in ranges if l <= reach < hi), key=lambda x: x[0], default=None)
        if step is None: return reach, best
        reach, best = step


def theorem_statements(rt, a, terms):
    """Every admitted theorem of this question, as (lo, range_hi, modulus, object): theorem claims and derived ones."""
    out = []
    for o in rt.objects.values():
        if o['status'] != 'checked': continue
        if o['kind'] == 'theorem' and o['data']['a'] == a and o['data']['terms'] == terms:
            f = o['data']['finite']; out.append((o['data']['lo'], f['hi'], f['cover']['modulus'], o))
        elif o['kind'] == 'derived' and o['data']['statement'].get('kind') == 'theorem' \
                and o['data']['statement']['a'] == a and o['data']['statement']['terms'] == terms:
            s = o['data']['statement']; out.append((s['lo'], s['range_hi'], s['modulus'], o))
    return out


@op('egypt_range_chunk', 'NWS', ('esq',), ('derived', 'residual'),
    'Extend the admitted range from min past its frontier by a chunk as long as the base range, up to ten times '
    'verify_to: a range_extend derivation whose proof carries a witness only for each n that no cover class holds '
    'and no proper divisor at or past min reduces. An anytime move: it breathes after every 64 n.')
def egypt_range_chunk(rt, esq):
    d = esq['data']; a, terms, lo, size = d['a'], d['terms'], d['min'], d['verify_to'] - d['min']
    ranges = range_statements(rt, a, terms)
    spine = max(((hi, o) for l, hi, o in ranges if l == lo), key=lambda x: x[0], default=None)
    if spine is None: return []
    start, base = spine
    cap = lo + RANGE_FRONTIER * size
    if start < d['verify_to'] or start >= cap: return []
    hi = min(start + size, cap)
    cover = best_cover(rt, a, terms); thresholds = {}
    for entry in (cover['data']['entries'] if cover else []):
        f = entry['family']; row = thresholds.setdefault(f['m'], {})
        row[f['r']] = min(row.get(f['r'], f['m'] * f['k0'] + f['r']), f['m'] * f['k0'] + f['r'])
    witnesses, table, missing = {}, {}, []
    shapes = divisor_families(rt, a, terms); end = hi
    for n in range(start, hi):
        if (n - start) % BREATH == 0 and (yield) == 'checkpoint':
            end = n; break  # the call ends: the part verified so far is the chunk
        rt.budget.use(1 + len(thresholds) // 10)
        if any(n >= row.get(n % m, n + 1) for m, row in thresholds.items()): continue
        rt.budget.use(max(4, n.bit_length() // 2)); p = L.factor(n); p = min(p) if p else n
        if p < n and n // p >= lo: continue  # the checker finds this divisor itself
        # A divisor family before any search: a divisor of n + h, h n + 1 or a n + 1 in the family's class represents n.
        hit = next(((i, q) for i, (shape, h) in enumerate(shapes) for q in [dfam_divisor(rt, a, shape, h, n)] if q is not None), None)
        if hit is not None: table[str(n)] = [hit[0], hit[1]]; continue
        xs = witness(a, n, rt.budget, max_excess=4 * a * 256) if terms == 3 else None
        if xs is None: missing.append(n); continue
        witnesses[str(n)] = sorted(xs)[:-1]
    if missing: return [rt.residual(esq, missing[:4096], 'no witness found within the search bound past ' + str(start))]
    if end <= start: return []
    proof = dict(cover=cover['data'] if cover else None, witnesses=witnesses)
    if shapes: proof['families'] = dict(shapes=[[shape, h] for shape, h in shapes], table=table)
    claim = rt.propose('derived', dict(rule='range_extend', premises=[base['id']],
                                       statement=dict(kind='range', a=a, terms=terms, lo=lo, hi=end), proof=proof),
                       (esq, base) + ((cover,) if cover else ()))
    return [claim] if rt.check(claim) else []


DFAM_H = 6  # the divisor families she states first: plus 1..6, times 2..6, pair 2..6 and square
YIELD_MIN = 16  # numbers a family's last two steps must each have carried in her proofs for the next step to be stated


def dfam_list():
    return ([('plus', h) for h in range(1, DFAM_H + 1)] + [('times', h) for h in range(2, DFAM_H + 1)]
            + [('pair', h) for h in range(2, DFAM_H + 1)] + [('square', 1)])


def family_yield(rt, a, terms):
    """Numbers each (shape, h) carried in the family tables of her admitted base ranges and chunks of the question."""
    counts = {}
    for o in rt.objects.values():
        if o['status'] != 'checked': continue
        if o['kind'] == 'finite' and o['data']['a'] == a and o['data']['terms'] == terms: fam = o['data'].get('families')
        elif o['kind'] == 'derived' and o['data']['rule'] == 'range_extend' and o['data']['statement']['a'] == a \
                and o['data']['statement']['terms'] == terms: fam = o['data']['proof'].get('families')
        else: continue
        if not fam: continue
        for i, q in fam['table'].values():
            key = tuple(fam['shapes'][i]); counts[key] = counts.get(key, 0) + 1
    return counts


def dfam_wanted(rt, a, terms):
    """The families to state: the first list, and one step past the largest h of a shape kind whose last two steps each
    carried at least YIELD_MIN numbers in her admitted proofs. A family that pays earns its successor; the bound is the
    checker's MAX_DFAM_H."""
    have = {(o['data']['shape'], o['data']['h']) for o in rt.objects.values()
            if o['kind'] == 'dfam' and o['status'] == 'checked' and o['data']['a'] == a}
    wanted = [r for r in dfam_list() if r not in have]
    counts = family_yield(rt, a, terms)
    for kind in ('plus', 'times', 'pair'):
        top = max([h for s, h in have if s == kind], default=0)
        if DFAM_H <= top < rt.checker.MAX_DFAM_H and counts.get((kind, top), 0) >= YIELD_MIN \
                and counts.get((kind, top - 1), 0) >= YIELD_MIN and (kind, top + 1) not in wanted:
            wanted.append((kind, top + 1))
    return wanted


def divisor_families(rt, a, terms):
    """The admitted divisor families of the question as (shape, h), the ones that cover most first."""
    rows = {(o['data']['shape'], o['data']['h']) for o in rt.objects.values() if o['kind'] == 'dfam'
            and o['status'] == 'checked' and o['data']['a'] == a and o['data']['terms'] == terms}
    return sorted(rows, key=lambda r: (r != ('plus', 1), r[0] == 'square', r[0] != 'times', r[1]))


def dfam_divisor(rt, a, shape, h, n):
    """A divisor q = -1 (mod t) of the family's linear form at n that gives n the family's three denominators, by the
    checker's own conditions (a pair also needs h | e f, which the divisor's class does not decide), or None. The
    divisors are built from the prime factorization of the value; the first that the checker accepts is kept."""
    alpha, beta, t = rt.checker.dfam_form(a, shape, h)
    value = alpha * n + beta; rt.budget.use(max(4, value.bit_length() // 2)); divisors = {1}
    for p, k in L.factor(value).items():
        divisors |= {d * p ** j for d in divisors for j in range(1, k + 1)}
    for q in sorted(d for d in divisors if d % t == (-1) % t):
        try: rt.checker.dfam_terms(a, shape, h, n, q); return q
        except rt.checker.Invalid: continue
    return None


@op('egypt_divisor_families', 'NS', ('esq',), ('dfam',),
    'State the divisor families of the question: Type I solutions with the parameter free, one family for every '
    'divisor q = -1 (mod a h) of n + h or of h n + 1, the pairs (a h n + 1 = q q\', Type II with the common factor h) '
    'and the square (a n + 1); h up to 6 first, then one step further for a shape whose last steps still carried '
    'numbers in her proofs. The checker verifies each identity; her ranges then use them before any search.')
def egypt_divisor_families(rt, esq):
    d = esq['data']; a, terms = d['a'], d['terms']
    if terms != 3: return []
    out = []
    for shape, h in dfam_wanted(rt, a, terms):
        claim = rt.propose('dfam', dict(a=a, terms=3, shape=shape, h=h), (esq,))
        if rt.check(claim): out.append(claim)
    return out


@op('egypt_theorem_families', 'NS', ('esq',), ('derived',),
    'Compose her theorem with its admitted divisor families: a theorem_families derivation stating that an unresolved '
    'n lies in an open class and meets no family\'s divisor condition. Derived again when the families grow.')
def egypt_theorem_families(rt, esq):
    d = esq['data']; a, terms, lo = d['a'], d['terms'], d['min']
    fams = sorted((o for o in rt.objects.values() if o['kind'] == 'dfam' and o['status'] == 'checked'
                   and o['data']['a'] == a and o['data']['terms'] == terms), key=lambda o: (o['data']['shape'], o['data']['h']))
    if not fams: return []
    fams = fams[:rt.checker.MAX_PREMISES - 1]
    shapes = sorted([o['data']['shape'], o['data']['h']] for o in fams)
    rows = [(row[3], rt_statement(row[3])) for row in theorem_statements(rt, a, terms) if row[0] == lo]
    plain = [(o, s) for o, s in rows if 'families' not in s]
    if not plain: return []
    T, s = max(plain, key=lambda x: (x[1].get('closed_at', 0), 'closure' in x[1], x[1]['range_hi'], -open_count(*x)))
    statement = dict(s, families=shapes)
    if any(u == statement for o, u in rows): return []  # composed with these families at this theorem already
    claim = rt.propose('derived', dict(rule='theorem_families', premises=[T['id']] + [o['id'] for o in fams], statement=statement),
                       (T,) + tuple(fams))
    return [claim] if rt.check(claim) else []


@op('egypt_range_square', 'NS', ('esq',), ('derived',),
    'State what closure under multiples gives from the admitted range from min: every n below its end squared with a '
    'divisor in the range is represented (for min 2, every composite below the square). A composite_range derivation.')
def egypt_range_square(rt, esq):
    d = esq['data']; a, terms, lo = d['a'], d['terms'], d['min']
    ranges = range_statements(rt, a, terms)
    spine = max(((hi, o) for l, hi, o in ranges if l == lo), key=lambda x: x[0], default=None)
    if spine is None: return []
    hi, base = spine
    if any(o['kind'] == 'derived' and o['status'] == 'checked' and o['data']['rule'] == 'composite_range'
           and o['data']['statement']['a'] == a and o['data']['statement']['terms'] == terms
           and o['data']['statement']['hi'] >= hi for o in rt.objects.values()): return []
    statement = dict(kind='composites', a=a, terms=terms, lo=lo, hi=hi, reach=hi * hi)
    claim = rt.propose('derived', dict(rule='composite_range', premises=[base['id']], statement=statement), (base,))
    return [claim] if rt.check(claim) else []


@op('egypt_range_union', 'NS', ('esq',), ('derived',),
    'Derive the union of the admitted range from min with the chunk that touches its frontier: a derivation the '
    'checker admits from the two premises by the range_union rule, without verifying either range again.')
def egypt_range_union(rt, esq):
    d = esq['data']; a, terms, lo = d['a'], d['terms'], d['min']
    ranges = range_statements(rt, a, terms)
    # The spine is the longest admitted range from min; the chunk touches or overlaps its end and reaches past it.
    spine = max(((hi, o) for l, hi, o in ranges if l == lo), key=lambda x: x[0], default=None)
    if spine is None: return []
    reach, base = spine
    chunk = max(((hi, o) for l, hi, o in ranges if o is not base and l <= reach < hi), key=lambda x: x[0], default=None)
    if chunk is None: return []
    statement = dict(kind='range', a=a, terms=terms, lo=lo, hi=chunk[0])
    claim = rt.propose('derived', dict(rule='range_union', premises=[base['id'], chunk[1]['id']], statement=statement),
                       (base, chunk[1]))
    return [claim] if rt.check(claim) else []


def rt_statement(o):
    """What an admitted theorem object states, in the form the derivation rules compose (a theorem or a derived one)."""
    if o['kind'] == 'derived': return o['data']['statement']
    f = o['data']['finite']
    return dict(kind='theorem', a=o['data']['a'], terms=o['data']['terms'], lo=o['data']['lo'], modulus=f['cover']['modulus'],
                range_hi=f['hi'], cover_id=L.digest(dict(kind='cover', data=f['cover'])))


def theorem_key(s):
    """What the closures and extensions of a theorem are compared by: the cover it names, or its modulus for a statement
    made before theorems named their cover."""
    return s['cover_id'] if 'cover_id' in s else ('modulus', s['modulus'])


def open_count(o, s):
    """The residues a theorem leaves open: stated by a closed theorem, counted by the checker for a base theorem, the
    whole modulus for an extension of an unclosed theorem (its base carries the count)."""
    return s['open_residues'] if 'open_residues' in s else o.get('evidence', {}).get('open_residues', s['modulus'])


def theorem_object(rt, a, terms, lo):
    """The admitted theorem of the question from lo whose closure under multiples is due, its statement and the admitted
    cover object it names, or None. A closure is due for a theorem that names its cover while no theorem on that cover
    is closed at its range: the widest range first, then the fewest open residues."""
    rows = [(row[3], rt_statement(row[3])) for row in theorem_statements(rt, a, terms) if row[0] == lo and 'families' not in rt_statement(row[3])]
    closed = {(theorem_key(s), s['range_hi']) for o, s in rows if s.get('closed_at') == s['range_hi']}
    due = [(o, s) for o, s in rows if 'cover_id' in s and (theorem_key(s), s['range_hi']) not in closed]
    for T, s in sorted(due, key=lambda x: (x[1]['range_hi'], -open_count(*x), 'closure' in x[1]), reverse=True):
        cover = rt.objects.get(s['cover_id'])
        if cover is not None and cover['status'] == 'checked': return T, s, cover
    return None


@op('egypt_theorem_multiples', 'NS', ('esq',), ('derived',),
    'Close her theorem under divisors: a residue the cover leaves open but which reduces, by primes of the modulus, '
    'to a reached residue is represented too. A theorem_multiples derivation from the theorem and its cover.')
def egypt_theorem_multiples(rt, esq):
    d = esq['data']; a, terms, lo = d['a'], d['terms'], d['min']
    found = theorem_object(rt, a, terms, lo)
    if found is None: return []
    T, s, cover = found; M = cover['data']['modulus']
    if M > rt.checker.CLOSURE_RESIDUES: return []
    # The closure is derived at the theorem's own range even when it reduces nothing there: the statement records the
    # range it was closed at, so the theorem extended over a wider range gets its own closure and none is tried twice.
    opened, closed = rt.checker.closure_open(cover['data'], s['lo'], s['range_hi'], rt.budget)
    statement = dict(s, closure='multiples', closed_at=s['range_hi'], open_residues=len(opened),
                     open_coprime=sum(1 for x in opened if gcd(x, M) == 1))
    claim = rt.propose('derived', dict(rule='theorem_multiples', premises=[T['id'], cover['id']], statement=statement), (T, cover))
    return [claim] if rt.check(claim) else []


def dominates(u, us, T, s, reach):
    """Whether the theorem u (statement us) makes extending T (statement s) to reach pointless: u reaches at least as
    far and is closed when T is, and is on the same cover, or was closed at the same range and leaves fewer residues
    open (counts closed at different ranges are not compared; a wider range may reduce more)."""
    if u is T or us['range_hi'] < reach or ('closure' in s and 'closure' not in us): return False
    if 'closure' in us and 'closure' not in s: return True
    return theorem_key(us) == theorem_key(s) or (us.get('closed_at') == s.get('closed_at') and open_count(u, us) <= open_count(T, s))


@op('egypt_theorem_range', 'NS', ('esq',), ('derived',),
    'Extend the admitted theorem to the admitted range past its own: a derivation by the theorem_range rule.')
def egypt_theorem_range(rt, esq):
    d = esq['data']; a, terms, lo = d['a'], d['terms'], d['min']
    rows = [(row[3], rt_statement(row[3])) for row in theorem_statements(rt, a, terms) if row[0] == lo and 'families' not in rt_statement(row[3])]
    ranges = range_statements(rt, a, terms); due = []
    for T, s in rows:
        beyond = max(((hi, o) for l, hi, o in ranges if s['lo'] <= l <= s['range_hi'] < hi), key=lambda x: x[0], default=None)
        if beyond is None or any(dominates(u, us, T, s, beyond[0]) for u, us in rows): continue
        due.append((T, s, beyond))
    if not due: return []
    # The theorem closed under multiples at its own range is preferred, so its extension keeps the closure.
    T, s, beyond = max(due, key=lambda x: ('closure' in x[1], x[1].get('closed_at', 0), -open_count(x[0], x[1]), x[1]['range_hi']))
    statement = dict(s, range_hi=beyond[0])
    claim = rt.propose('derived', dict(rule='theorem_range', premises=[T['id'], beyond[1]['id']], statement=statement),
                       (T, beyond[1]))
    return [claim] if rt.check(claim) else []


@op('egypt_density', 'NS', ('cover',), ('density',),
    'State the exact fraction of residues a cover covers.')
def egypt_density(rt, cover):
    d = cover['data']
    claim = rt.propose('density', dict(cover=d, fraction=L.enc(Q(d['modulus'] - len(open_residues(d, rt.budget)),
                                                                   d['modulus']))), (cover,))
    return [claim] if rt.check(claim) else []


@op('egypt_finite_verify', 'NWS', ('esq',), ('finite', 'residual'),
    'Verify every n in [min, verify_to): cover classes, a checked prime divisor scaled up, or a new witness. An '
    'anytime move: it breathes after every 256 n.')
def egypt_finite_verify(rt, esq):
    d = esq['data']; a, terms, lo, hi = d['a'], d['terms'], d['min'], d['verify_to']
    cover = best_cover(rt, a, terms)
    thresholds = {}
    for entry in (cover['data']['entries'] if cover else []):
        f = entry['family']; row = thresholds.setdefault(f['m'], {})
        row[f['r']] = min(row.get(f['r'], f['m'] * f['k0'] + f['r']), f['m'] * f['k0'] + f['r'])
    # A part already admitted from min is not verified again: the claim starts where the spine ends. A divisor of an
    # earlier number in the part is written down; a divisor in the spine is found by the checker of a later chunk, so
    # the part past the spine relies on families and witnesses for numbers whose divisors all lie in the spine.
    start = max((h for l, h, o in range_statements(rt, a, terms) if l == lo), default=lo)
    if start >= hi: return []
    shapes = divisor_families(rt, a, terms)
    witnesses, divisors, table, done, missing = {}, {}, {}, set(), []
    end = hi
    for n in range(start, hi):
        if (n - start) % BREATH == 0 and (yield) == 'checkpoint':
            end = n; break  # the call ends: the part verified so far is the claim
        rt.budget.use(1 + len(thresholds) // 10)
        if any(n >= row.get(n % m, n + 1) for m, row in thresholds.items()): done.add(n); continue
        rt.budget.use(max(4, n.bit_length() // 2)); p = next((q for q in sorted(L.factor(n)) if q < n and q in done), None)
        if p is not None: divisors[str(n)] = p; done.add(n); continue
        hit = next(((i, q) for i, (shape, h) in enumerate(shapes) for q in [dfam_divisor(rt, a, shape, h, n)] if q is not None), None)
        if hit is not None: table[str(n)] = [hit[0], hit[1]]; done.add(n); continue
        xs = witness(a, n, rt.budget, max_excess=4 * a * 256) if terms == 3 else None
        if xs is None: missing.append(n); continue
        witnesses[str(n)] = sorted(xs)[:-1]; done.add(n)
    if missing: return [rt.residual(esq, missing[:4096], 'no witness found within the search bound')]
    if end <= start: return []
    data = dict(a=a, terms=terms, lo=start, hi=end, witnesses=witnesses, divisors=divisors, cover=cover['data'] if cover else None)
    if shapes: data['families'] = dict(shapes=[[shape, h] for shape, h in shapes], table=table)
    claim = rt.propose('finite', data, (esq,) + ((cover,) if cover else ()))
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


def _classical_families(rt, M, residues=None):
    fams = []
    for r in residues or range(1, M):
        found = classical_search(4, M, r, CLASSICAL_BOUND, rt.budget)
        if found: fams.append(_checked(rt, 'ufam', classical_family(4, M, r, found[0])))
    return fams


def _classical_cover(rt, M=120):
    """Every class mod M that a classical family reaches, as one checked cover."""
    return _checked(rt, 'cover', assemble(_classical_families(rt, M), 4, 3, M))


def _lift_inputs(rt):
    _classical_cover(rt)
    return [_esq(rt, 120)]


def _sieved_cover(rt, M=120, chain=(24, 120), residues=None):
    """Classical families on classes mod M (all, or the listed residues) as one cover checked through a sieve."""
    return _checked(rt, 'cover', dict(assemble(_classical_families(rt, M, residues), 4, 3, M), chain=list(chain)))


def _sieved_assembly(rt):
    _esq(rt, 24); _fam(rt, 24, 11); _fam(rt, 24, 23)
    for r in (1, 49):
        found = classical_search(4, 120, r, CLASSICAL_BOUND, rt.budget)
        if found: _checked(rt, 'ufam', classical_family(4, 120, r, found[0]))
    return [_esq(rt, 120)]


def _sweep_level(rt):
    """Classes mod 120 as class targets, before any family is known."""
    for r in range(1, 120, 2):
        if gcd(r, 120) == 1: _cls(rt, 120, r)
    return [_esq(rt, 120)]


def _walled_level(rt):
    """The same level after a sweep: the classical misses are ready to be certified as walls in one claim."""
    esq = _sweep_level(rt)[0]; L.drive(egypt_classical_sweep(rt, esq))
    return [esq]


def _sieved_range(rt):
    _sieved_cover(rt); return L.drive(egypt_finite_verify(rt, _esq(rt, 120, verify_to=400)))


def _ranged_level(rt, verify_to=400):
    """A level with a classical cover and its base range checked: the frontier a chunk extends."""
    esq = _esq(rt, 24, verify_to=verify_to); _classical_cover(rt, 24); L.drive(egypt_finite_verify(rt, esq)); return [esq]


def _chunked_level(rt):
    esq = _ranged_level(rt)[0]; L.drive(egypt_range_chunk(rt, esq)); return [esq]


def _two_ranges_level(rt):
    """A base range and a separately verified range that touches it: what range_union joins."""
    esq = _ranged_level(rt)[0]
    L.drive(egypt_finite_verify(rt, rt.given('esq', dict(a=4, terms=3, min=400, modulus=24, verify_to=800)))); return [esq]


def _theorem_level(rt):
    esq = _chunked_level(rt)[0]
    base = next(o for o in rt.objects.values() if o['kind'] == 'finite' and o['status'] == 'checked' and o['data']['lo'] == 2)
    egypt_reduction_theorem(rt, base); return [esq]


def _multiples_level(rt):
    """A cover of 4/n at modulus 8 with one family, on the class 3 mod 4, its range and theorem: the open residue 6
    reduces to 3 mod 4 by the prime 2, the others do not."""
    esq = rt.given('esq', dict(a=4, terms=3, min=2, modulus=8, verify_to=400))
    _fam(rt, 4, 3); egypt_cover_assemble(rt, esq); L.drive(egypt_finite_verify(rt, esq))
    base = next(o for o in rt.objects.values() if o['kind'] == 'finite' and o['status'] == 'checked')
    egypt_reduction_theorem(rt, base); return [esq]


def _extended_closure_level(rt):
    """The closed theorem of _multiples_level extended over the next chunk: its closure at the wider range is due."""
    esq = _multiples_level(rt)[0]
    egypt_theorem_multiples(rt, esq); L.drive(egypt_range_chunk(rt, esq)); egypt_range_union(rt, esq); egypt_theorem_range(rt, esq)
    return [esq]


def _families_level(rt):
    """A level with its base range checked and its divisor families stated: the chunk past it uses them first."""
    esq = _ranged_level(rt)[0]; egypt_divisor_families(rt, esq); return [esq]


def _composed_level(rt):
    """A level with its theorem, families and a chunk: what the composition and the square derive from."""
    esq = _theorem_level(rt)[0]; egypt_divisor_families(rt, esq); return [esq]


def _four_term_level(rt):
    """A four-term question whose base range is checked by hand; the chunk past it finds no witness (a residual)."""
    esq = rt.given('esq', dict(a=4, terms=4, min=2, modulus=24, verify_to=5))
    _checked(rt, 'finite', dict(a=4, terms=4, lo=2, hi=5, witnesses={'2': [1, 2, 4], '3': [1, 6, 12], '4': [2, 4, 8]}, divisors={},
                                cover=None))
    return [esq]


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
    'egypt_cover_assemble': [_assembly, _sieved_assembly],
    'egypt_cover_lift': [lambda rt: [_cover(rt)], lambda rt: [_sieved_cover(rt)]],
    'egypt_cover_merge': [_two_covers],
    'egypt_residual': [lambda rt: [_cover(rt)], lambda rt: [_sieved_cover(rt)]],
    'egypt_square_pattern': [lambda rt: [_cover(rt)], lambda rt: [_small_cover(rt)], lambda rt: [_sieved_cover(rt)],
                             lambda rt: [_sieved_cover(rt, 840, (120, 840))],
                             lambda rt: [_sieved_cover(rt, 120, (24, 120), (2, 3))]],
    'egypt_density': [lambda rt: [_cover(rt)], lambda rt: [_sieved_cover(rt)]],
    'egypt_finite_verify': [lambda rt: [_esq(rt, 24, verify_to=400)], lambda rt: [_esq(rt, 24, terms=4, verify_to=5)]],
    'egypt_classical_family': [lambda rt: [_cls(rt, 840, 11)], lambda rt: [_cls(rt, 840, 1)]],
    'egypt_classical_exclusion': [lambda rt: [_cls(rt, 840, 1)]],
    'egypt_classical_obstruction': [lambda rt: [_esq(rt, 840)], lambda rt: [_esq(rt, 840, a=5)]],
    'egypt_classical_sweep': [_sweep_level],
    'egypt_wall_sweep': [_walled_level],
    'egypt_signature_pattern': [lambda rt: [_classical_cover(rt)], lambda rt: [_sieved_cover(rt)]],
    'egypt_local_pattern': [lambda rt: [_classical_cover(rt)], lambda rt: [_sieved_cover(rt)]],
    'egypt_reduction_theorem': [lambda rt: L.drive(egypt_finite_verify(rt, _esq(rt, 24, verify_to=400)))
                                if _classical_cover(rt, 24) else [], _sieved_range],
    'egypt_range_chunk': [_ranged_level, _four_term_level, _families_level],
    'egypt_divisor_families': [_ranged_level, lambda rt: [_esq(rt, 24, terms=4, verify_to=5)]],
    'egypt_theorem_families': [_composed_level],
    'egypt_range_square': [_composed_level, _ranged_level],
    'egypt_range_union': [_two_ranges_level],
    'egypt_theorem_multiples': [_multiples_level, _extended_closure_level],
    'egypt_theorem_range': [_theorem_level],
    'egypt_choose_lift': [_lift_inputs],
}
