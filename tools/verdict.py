"""Independent three-valued verdict on the checked results saved by Ember's autonomous agent.

This verifier shares no code with Ember's producers or checkers. It first checks
itself on known-true and known-false claims; if it fails its own test, every
verdict is UNRESOLVED. Each saved claim then receives VERIFIED (an independent
exact recomputation confirms it), REFUTED (a concrete failing witness), or
UNRESOLVED (outside what this verifier can decide within its bounds). The one-bit
answer is "verified" only when every claim is VERIFIED; otherwise it is
"no, keep thinking". It names which claims failed and never supplies a solution.

    python -I -B -X utf8 tools/verdict.py STATE.json
"""
from fractions import Fraction as F
import importlib.util
import json
from math import gcd
from pathlib import Path
import sys

VERSION = 'ember.verdict.v1'
POSITIVITY_SEARCH = 10_000


# ------------------------------------------------------------- univariate polynomials, written independently

def expand(node):
    """Coefficient list (x**0 first) of an expression tree in one variable, or of a coefficient list itself."""
    if node and type(node[0]) is list: return trim([F(n, d) for n, d in node])
    head = node[0]
    if head == 'num': return trim([F(node[1], node[2])])
    if head == 'var': return [F(0), F(1)]
    if head == 'add':
        out = []
        for item in node[1:]: out = add(out, expand(item))
        return out
    if head == 'mul':
        out = [F(1)]
        for item in node[1:]: out = mul(out, expand(item))
        return out
    if head == 'sub': return add(expand(node[1]), [-c for c in expand(node[2])])
    if head == 'neg': return [-c for c in expand(node[1])]
    if head == 'pow':
        out, base = [F(1)], expand(node[1])
        for _ in range(node[2]): out = mul(out, base)
        return out
    raise ValueError('unknown expression head ' + str(head))


def trim(p):
    p = list(p)
    while p and p[-1] == 0: p.pop()
    return p


def add(a, b):
    return trim([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(max(len(a), len(b)))])


def mul(a, b):
    if not a or not b: return []
    out = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b): out[i + j] += x * y
    return trim(out)


def value(p, x):
    out = F(0)
    for c in reversed(p): out = out * x + c
    return out


def taylor_shift(p, t):
    """Coefficients of p(k + t), by repeated synthetic division."""
    coeffs = list(p); out = []
    for _ in range(len(coeffs)):
        remainder = F(0); quotient = []
        for c in reversed(coeffs):
            remainder = remainder * t + c; quotient.append(remainder)
        out.append(quotient[-1]); coeffs = list(reversed(quotient[:-1]))
    return trim(out)


# ------------------------------------------------------------- unit-fraction claims

def classical_denominators(f):
    """The denominators a family's named classical parameters give on its own class, derived here independently, or
    None when the parameters do not fit the class."""
    a, m, r = f['a'], f['m'], f['r']; kind, u, v, z = f['p']; n = [F(r), F(m)]
    if kind == 'II':
        if u > v or m != a * u * v or (u + v) % z or (r + z) % m: return None
        w = (u + v) // z; d = [F(r + z, m), F(1)]; dn = mul(d, n)
        return [trim([c * u * v for c in d]), trim([c * u * w for c in dn]), trim([c * v * w for c in dn])]
    q = a * u * v * z; s = u + v
    if kind != 'I' or u > v or (s * m) % q or m != q // gcd(q, s) or (s * r + z) % q: return None
    d = [F(s * r + z, q), F(s * m, q)]; dn = mul(d, n)
    return [trim([c * u * v for c in dn]), trim([c * u * z for c in d]), trim([c * v * z for c in d])]


def at_class(p, m, r):
    """p(m*k + r) for a polynomial p in n: the denominators in k of a family named by its identity in n."""
    out = []
    for c in reversed(p): out = add(mul(out, [F(r), F(m)]), [c])
    return trim(out)


def unshaped(f, shapes):
    """A family that names its identity s in a shape table, with its denominators in k written out; else f itself."""
    if 's' not in f: return f
    polys = [at_class(expand(e), f['m'], f['r']) for e in shapes[f['s']]]
    return dict({k: v for k, v in f.items() if k != 's'}, x=[[[c.numerator, c.denominator] for c in p] for p in polys])


def denominators(f):
    """A family's denominators: stated, or rebuilt from its named classical parameters."""
    return [expand(e) for e in f['x']] if 'x' in f else classical_denominators(f)


def family_verdict(f):
    """VERIFIED when a*prod(x) = n*sum(prod others) as polynomials in k, each x_i is integer on Z, and each x_i
    is positive for k >= k0; REFUTED with a witness k where a denominator is non-integral or nonpositive. A family
    that names classical parameters is rebuilt from them (and must match its stated denominators)."""
    a, m, r, k0 = f['a'], f['m'], f['r'], f['k0']; n = [F(r), F(m)]
    xs = [expand(e) for e in f['x']] if 'x' in f else None
    if 'p' in f:
        rebuilt = classical_denominators(f)
        if rebuilt is None: return 'REFUTED', 'named parameters do not fit the class'
        if xs is not None and [trim(x) for x in xs] != rebuilt: return 'REFUTED', 'named parameters give other denominators'
        xs = rebuilt
    left = [F(a)]
    for x in xs: left = mul(left, x)
    right = []
    for i in range(len(xs)):
        term = [F(1)]
        for j, x in enumerate(xs):
            if j != i: term = mul(term, x)
        right = add(right, term)
    if add(left, [-c for c in mul(n, right)]):
        for k in range(k0, k0 + 64):
            vals = [value(x, F(k)) for x in xs]
            if any(v == 0 for v in vals) or sum(1 / v for v in vals) != F(a, m * k + r):
                return 'REFUTED', 'identity fails at k=' + str(k)
        return 'UNRESOLVED', 'identity differs as polynomials but no failing k found below k0+64'
    for x in xs:
        if any(value(x, F(k)).denominator != 1 for k in range(len(x) + 1)):
            k = next(k for k in range(len(x) + 1) if value(x, F(k)).denominator != 1)
            return 'REFUTED', 'denominator not an integer at k=' + str(k)
        shifted = taylor_shift(x, F(k0))
        if not (shifted and shifted[0] > 0 and all(c >= 0 for c in shifted)):
            bad = next((k for k in range(k0, k0 + POSITIVITY_SEARCH) if value(x, F(k)) <= 0), None)
            if bad is not None: return 'REFUTED', 'denominator not positive at k=' + str(bad)
            return 'UNRESOLVED', 'positivity from k0 not decided by the shifted-coefficient test'
    return 'VERIFIED', 'identity in k, integer-valued, positive for k >= k0'


def covered_residues(cover):
    M = cover['modulus']; out = set()
    for e in cover['entries']:
        f = e['family']; out.update(range(f['r'] % f['m'], M, f['m']))
    return out


def cover_verdict(cover):
    M = cover['modulus']
    for e in cover['entries']:
        f = unshaped(e['family'], cover.get('shapes'))
        if M % f['m']: return 'REFUTED', 'family modulus ' + str(f['m']) + ' does not divide ' + str(M)
        if cover['bound'] < f['m'] * f['k0'] + f['r']: return 'REFUTED', 'bound below a family threshold'
        verdict, detail = family_verdict(f)
        if verdict != 'VERIFIED': return verdict, 'family ' + str(f['m']) + ':' + str(f['r']) + ': ' + detail
    if 'chain' in cover:
        if not chain_ok(cover): return 'REFUTED', 'the chain is not a divisibility chain ending at the modulus'
        return 'VERIFIED', str(M - len(open_set(cover))) + ' residues covered (sieved)'
    return 'VERIFIED', str(len(covered_residues(cover))) + ' residues covered'


def chain_ok(cover):
    chain = cover['chain']
    return (type(chain) is list and chain and chain[-1] == cover['modulus'] and 1 <= chain[0] <= 10 ** 5
            and all(type(c) is int for c in chain) and all(b > a and b % a == 0 for a, b in zip(chain, chain[1:])))


def open_set(cover):
    """Residues no family reaches. With a chain: start from every residue of the first modulus and carry only the
    unreached ones to each finer modulus, testing them against the families that first divide that modulus."""
    M = cover['modulus']
    if 'chain' not in cover: return set(range(M)) - covered_residues(cover)
    groups = {}
    for e in cover['entries']: groups.setdefault(e['family']['m'], set()).add(e['family']['r'] % e['family']['m'])
    chain = cover['chain']; alive = list(range(chain[0])); seen = 1
    for step in chain:
        tests = [(m, rs) for m, rs in groups.items() if step % m == 0 and seen % m != 0]
        if step != chain[0]: alive = [x + seen * j for x in alive for j in range(step // seen)]
        alive = [x for x in alive if all(x % m not in rs for m, rs in tests)]; seen = step
    return set(alive)


def unit_square_count(M):
    """Squares of units modulo M: counted by brute force on each prime-power factor, multiplied by CRT."""
    total, q, rest = 1, 2, M
    while rest > 1:
        if q * q > rest: q = rest
        if rest % q == 0:
            power = 1
            while rest % q == 0: rest //= q; power *= q
            total *= len({y * y % power for y in range(power) if y % q})
        q += 1
    return total


def finite_verdict(d):
    a, terms, lo, hi = d['a'], d['terms'], d['lo'], d['hi']; rows = {}
    if d['cover'] is not None:
        verdict, detail = cover_verdict(d['cover'])
        if verdict != 'VERIFIED': return verdict, 'cover: ' + detail
        for e in d['cover']['entries']:
            f = unshaped(e['family'], d['cover'].get('shapes'))
            rows.setdefault(f['m'], []).append((f['r'], f['m'] * f['k0'] + f['r'], denominators(f)))
    done = set()
    for n in range(lo, hi):
        hit = None
        for m, fams in rows.items():
            for r, threshold, xs in fams:
                if n % m == r and n >= threshold: hit = (m, r, xs); break
            if hit: break
        if hit:
            m, r, xs = hit; k = (n - r) // m; vals = [value(x, F(k)) for x in xs]
            if any(v.denominator != 1 or v <= 0 for v in vals) or sum(1 / v for v in vals) != F(a, n):
                return 'REFUTED', 'family value wrong at n=' + str(n)
            done.add(n); continue
        key = str(n)
        if key in d['witnesses']:
            xs = d['witnesses'][key]; rest = F(a, n) - sum(F(1, x) for x in xs)
            if len(xs) != terms - 1 or rest <= 0 or rest.numerator != 1: return 'REFUTED', 'witness fails at n=' + key
            done.add(n); continue
        q = d['divisors'].get(key)
        if type(q) is int and 1 < q < n and n % q == 0 and q in done: done.add(n); continue
        return 'REFUTED', 'no representation recorded for n=' + key
    return 'VERIFIED', 'every n in [' + str(lo) + ', ' + str(hi) + ') represented'


def is_local_square(x, M):
    """x coprime to M is a square mod M iff it is one modulo every prime power of M."""
    q = 2; rest = M
    while q * q <= rest:
        if rest % q == 0:
            e = 0
            while rest % q == 0: rest //= q; e += 1
            if not local_square(x, q, e): return False
        q += 1
    return rest == 1 or local_square(x, rest, 1)


def local_square(x, p, e):
    if p == 2: return e == 1 or (e == 2 and x % 4 == 1) or (e >= 3 and x % 8 == 1)
    return pow(x % p, (p - 1) // 2, p) == 1


def nonresidue_set(x, M):
    out = set(); q = 2; rest = M
    while q * q <= rest:
        if rest % q == 0:
            e = 0
            while rest % q == 0: rest //= q; e += 1
            if not local_square(x, q, e): out.add(q)
        q += 1
    if rest > 1 and not local_square(x, rest, 1): out.add(rest)
    return out


def pattern_verdict(d):
    verdict, detail = cover_verdict(d['cover'])
    if verdict != 'VERIFIED': return verdict, 'cover: ' + detail
    if 'chain' in d['cover']: return sieved_pattern_verdict(d)
    M = d['cover']['modulus']; covered = covered_residues(d['cover'])
    for x in range(M):
        if gcd(x, M) != 1: continue
        bad = nonresidue_set(x, M)
        if d['rule'] == 'uncovered_coprime_are_squares':
            if (not bad) == (x in covered): return 'REFUTED', 'residue ' + str(x) + ' breaks the square pattern'
        elif d['rule'] == 'uncovered_coprime_square_outside':
            if (not bad and x in covered) or (x not in covered and not bad <= set(d['primes'])):
                return 'REFUTED', 'residue ' + str(x) + ' breaks the signature pattern'
        elif d['rule'] == 'uncovered_coprime_local_images':
            if x not in covered and any(x % int(q) not in set(row) for q, row in d['images'].items()):
                return 'REFUTED', 'residue ' + str(x) + ' leaves a local image'
        else: return 'UNRESOLVED', 'unknown pattern rule'
    return 'VERIFIED', 'exhaustive over the coprime residues'


def sieved_pattern_verdict(d):
    """The same rules over a sieved cover: only open units are listed, so 'every square is open' is decided by
    counting the open squares against the number of squares of units."""
    M = d['cover']['modulus']; units = sorted(x for x in open_set(d['cover']) if gcd(x, M) == 1)
    squares = [x for x in units if not nonresidue_set(x, M)]
    if d['rule'] == 'uncovered_coprime_are_squares':
        if len(squares) != len(units): return 'REFUTED', 'open residue ' + str(min(set(units) - set(squares))) + ' is not a square'
        if len(squares) != unit_square_count(M): return 'REFUTED', 'some square class is covered'
    elif d['rule'] == 'uncovered_coprime_square_outside':
        bad = [x for x in units if not nonresidue_set(x, M) <= set(d['primes'])]
        if bad: return 'REFUTED', 'residue ' + str(bad[0]) + ' breaks the signature pattern'
        if len(squares) != unit_square_count(M): return 'REFUTED', 'some square class is covered'
    elif d['rule'] == 'uncovered_coprime_local_images':
        for x in units:
            if any(x % int(q) not in set(row) for q, row in d['images'].items()):
                return 'REFUTED', 'residue ' + str(x) + ' leaves a local image'
    else: return 'UNRESOLVED', 'unknown pattern rule'
    return 'VERIFIED', 'decided over the ' + str(len(units)) + ' open units'


_DIVISORS = {}


def divisor_list(n):
    if n not in _DIVISORS:
        out = set(); i = 1
        while i * i <= n:
            if n % i == 0: out.update((i, n // i))
            i += 1
        if len(_DIVISORS) > 256: _DIVISORS.clear()
        _DIVISORS[n] = sorted(out)
    return _DIVISORS[n]


def classical_hit(a, m, r, bound):
    """Independent enumeration of fixed-parameter Type II and Type I families on n = r (mod m)."""
    for D in divisor_list(m):
        if D % a: continue
        uv = D // a; e = (-r) % D or D
        for u in divisor_list(uv):
            if u <= uv // u and (u + uv // u) % e == 0: return ('II', u, uv // u)
    if bound == 0:
        for modulus, residues in type1_reach(a, m).items():
            if r % modulus in residues: return ('I',) + residues[r % modulus]
        return None
    for u in range(1, bound + 1):
        for v in range(u, bound + 1):
            if ((u + v) * m) % (a * u * v): continue
            for w in range(1, bound + 1):
                q = a * u * v * w
                if ((u + v) * m) % q == 0 and ((u + v) * r + w) % q == 0: return ('I', u, v, w)
    return None


_REACH = {}


def type1_reach(a, m):
    """For each Type I triple (u, v, w), u <= v, with a*u*v*w | (u+v)*m, the residues r modulo m with
    a*u*v*w | (u+v)*r + w. With g = gcd(u, v), u = g*x and v = g*y give a*g*x*y*w | (x+y)*m, where x*y is coprime to
    x+y; so x*y | m and g*w | (x+y)*(m/(x*y))/a. The congruence is solved directly: a single class modulo q/c
    (c = gcd(u+v, q), q = a*u*v*w) when c divides w, and none otherwise. Only the classes are kept."""
    if (a, m) not in _REACH:
        reach = {}; ds = divisor_list(m)
        for x in ds:
            for y in ds:
                if y < x or (m // x) % y or gcd(x, y) != 1: continue
                rest = (x + y) * (m // (x * y))
                if rest % a: continue
                for gw in divisor_list(rest // a):
                    for g in divisor_list(gw):
                        u, v, w = g * x, g * y, gw // g
                        q = a * u * v * w; s = u + v; c = gcd(s, q)
                        if w % c: continue
                        modulus = q // c; inverse = pow(s // c, -1, modulus) if modulus > 1 else 0
                        reach.setdefault(modulus, {}).setdefault((-(w // c) * inverse) % modulus, (u, v, w))
        if len(_REACH) >= 4: _REACH.clear()
        _REACH[(a, m)] = reach
    return _REACH[(a, m)]


def obstruction_verdict(d):
    """Every coprime class a classical fixed-parameter family reaches (modulus dividing m) must be a non-residue modulo
    its own modulus; a reached square class is the refuting witness."""
    a, m = d['a'], d['m']
    if m > 10 ** 12: return 'UNRESOLVED', 'modulus beyond the independent enumeration bound'
    classes = []
    for D in divisor_list(m):
        if D % a: continue
        for u in divisor_list(D // a):
            v = D // a // u
            if u <= v: classes += [(D, (-e) % D, ('II', u, v, e)) for e in divisor_list(u + v)]
    for modulus, residues in type1_reach(a, m).items():
        classes += [(modulus, r0, ('I',) + p) for r0, p in residues.items()]
    for modulus, r0, p in classes:
        if gcd(r0, modulus) == 1 and not nonresidue_set(r0, modulus):
            return 'REFUTED', 'classical family ' + str(p) + ' reaches the square class ' + str(r0) + ' mod ' + str(modulus)
    return 'VERIFIED', str(len(classes)) + ' reached classes, none a coprime square'


def obstruction_refutation_verdict(d):
    """A refutation of an obstruction claim is correct when its named family is a genuine classical family with
    modulus dividing m that reaches the named class, and the class is a coprime square."""
    claim, w = d['claim']['data'], d['witness']
    a, m, modulus, r0 = claim['a'], claim['m'], w['modulus'], w['residue']; kind, u, v, z = w['params']
    if m % modulus or gcd(r0, modulus) != 1 or nonresidue_set(r0, modulus): return 'REFUTED', 'the named class is not a coprime square dividing the modulus'
    if kind == 'II': reaches = modulus == a * u * v and (u + v) % z == 0 and (r0 + z) % modulus == 0
    else:
        q = a * u * v * z; s = u + v; c = gcd(s, q)
        reaches = (s * m) % q == 0 and z % c == 0 and modulus == q // c and (s * r0 + z) % q == 0
    if not reaches: return 'REFUTED', 'the named family does not reach the named class'
    fam = dict(a=a, m=modulus, r=r0, k0=0, p=[kind, u, v, z])
    verdict_, detail = family_verdict(dict(fam, k0=least_k0(fam)))
    return (verdict_, 'the named family itself: ' + detail) if verdict_ != 'VERIFIED' else \
        ('VERIFIED', 'a classical family reaches the square class ' + str(r0) + ' mod ' + str(modulus))


def least_k0(fam):
    """The least k0 from which the rebuilt denominators are positive (the family is valid from there on)."""
    xs = classical_denominators(fam) or []
    for k0 in range(0, 64):
        if all(value(x, F(k)) > 0 for x in xs for k in range(k0, k0 + 4)) and \
                all(taylor_shift(x, F(k0)) and taylor_shift(x, F(k0))[0] > 0 and all(c >= 0 for c in taylor_shift(x, F(k0))) for x in xs):
            return k0
    return 0


def nofamily_verdict(d):
    if 'rs' in d:
        for r in d['rs']:
            verdict_, detail = nofamily_verdict(dict({k: v for k, v in d.items() if k != 'rs'}, r=r))
            if verdict_ != 'VERIFIED': return verdict_, 'residue ' + str(r) + ': ' + detail
        return 'VERIFIED', str(len(d['rs'])) + ' walls'
    return single_wall_verdict(d)


def single_wall_verdict(d):
    if d['m'] > 10 ** 12: return 'UNRESOLVED', 'modulus beyond the independent enumeration bound'
    hit = classical_hit(d['a'], d['m'], d['r'], d['bound'])
    return ('REFUTED', 'classical family ' + str(hit)) if hit else ('VERIFIED', 'no classical parameters')


def theorem_verdict(d):
    """The chain: the range verifies and carries its cover, and every covered class has a family reaching it whose
    threshold is at most the class's first member at or past the range (members below the range are in the range)."""
    f = d['finite']
    if f.get('cover') is None or (f['a'], f['terms'], f['lo']) != (d['a'], d['terms'], d['lo']):
        return 'REFUTED', 'the theorem and its range state different questions'
    verdict, detail = finite_verdict(f)
    if verdict != 'VERIFIED': return verdict, 'range: ' + detail
    cover = f['cover']; M, hi = cover['modulus'], f['hi']; reached, safe = set(), set()
    if 'chain' in cover:
        x = sieved_gap(cover, hi)
        if x is not None:
            return 'REFUTED', 'chain gap: class ' + str(x) + ' has members past the range below every family threshold ' \
                              '(the certificate fails, not the statement)'
        return 'VERIFIED', 'every n >= ' + str(d['lo']) + ' outside ' + str(len(open_set(cover))) + \
            ' open residues mod ' + str(M) + ' is represented (sieved)'
    for e in cover['entries']:
        g = e['family']; threshold = g['m'] * g['k0'] + g['r']
        for x in range(g['r'] % g['m'], M, g['m']):
            reached.add(x)
            if x + M * max(0, -(-(hi - x) // M)) >= threshold: safe.add(x)
    if reached - safe:
        x = min(reached - safe)
        return 'REFUTED', 'chain gap: class ' + str(x) + ' mod ' + str(M) + \
            ' has members past the range below every family threshold (the certificate fails, not the statement)'
    return 'VERIFIED', 'every n >= ' + str(d['lo']) + ' outside ' + str(M - len(reached)) + \
        ' open residues mod ' + str(M) + ' is represented'


def sieved_gap(cover, hi):
    """Walk the chain; a class reached by some family whose least threshold is above its first member past hi is
    carried to the next modulus, and one still failing at the last modulus is a gap."""
    least = {}
    for e in cover['entries']:
        g = e['family']; key = (g['m'], g['r'] % g['m'])
        least[key] = min(least.get(key, g['m'] * g['k0'] + g['r']), g['m'] * g['k0'] + g['r'])
    chain = cover['chain']; todo = list(range(chain[0]))
    for i, Mi in enumerate(chain):
        keep = []
        for x in todo:
            ts = [t for (m, r), t in least.items() if Mi % m == 0 and x % m == r]
            if ts and x + Mi * max(0, -(-(hi - x) // Mi)) >= min(ts): continue
            if ts and i == len(chain) - 1: return x
            keep.append(x)
        if i < len(chain) - 1: todo = [x + Mi * j for x in keep for j in range(chain[i + 1] // Mi)]
    return None


def density_verdict(d):
    verdict, detail = cover_verdict(d['cover'])
    if verdict != 'VERIFIED': return verdict, 'cover: ' + detail
    fraction = F(d['fraction'][0], d['fraction'][1]); M = d['cover']['modulus']
    exact = F(M - len(open_set(d['cover'])), M) if 'chain' in d['cover'] else F(len(covered_residues(d['cover'])), M)
    return ('VERIFIED', str(exact)) if fraction == exact else ('REFUTED', 'covered fraction is ' + str(exact))


# ------------------------------------------------------------- residue-class maps

def step(cmap, x):
    i = x % cmap['d']
    return (cmap['a'][i] * x + cmap['b'][i]) // cmap['d']


def descent_verdict(cmap, M, r, steps, bound):
    """T^steps(M t + r) = alpha t + beta with branches fixed by M; alpha < M and every member >= bound descends."""
    d = cmap['d']; alpha, beta = F(M), F(r)
    for _ in range(steps):
        if alpha.denominator != 1 or int(alpha) % d: return 'REFUTED', 'branch not determined by the modulus'
        i = int(beta) % d
        if beta.denominator != 1: return 'REFUTED', 'nonintegral offset'
        alpha, beta = cmap['a'][i] * alpha / d, (cmap['a'][i] * beta + cmap['b'][i]) / d
    if alpha >= M: return 'REFUTED', 'iterate does not contract'
    t = 0 if r >= bound else -(-(bound - r) // M)
    if alpha * t + beta >= M * t + r: return 'REFUTED', 'member at the bound does not descend'
    for n in range(max(bound, r) + (r - max(bound, r)) % M, max(bound, r) + 64 * M, M):
        x = n
        for _ in range(steps): x = step(cmap, x)
        if x >= n: return 'REFUTED', 'n=' + str(n) + ' does not descend'
    return 'VERIFIED', 'affine iterate contracts past the bound'


def cfinite_verdict(d):
    cmap = d['map']; lo, hi, cap = d['lo'], d['hi'], d.get('cap', 10_000)
    for n in range(lo, hi):
        x, k = n, 0
        while x >= n and k < cap: x = step(cmap, x); k += 1
        if x >= n: return 'REFUTED', 'n=' + str(n) + ' does not fall below itself within the cap'
    return 'VERIFIED', 'every n in [' + str(lo) + ', ' + str(hi) + ') falls below itself'


def cycle_verdict(d):
    cmap = d['map']; x = d['start']; seen = []
    for _ in range(d['length']): seen.append(x); x = step(cmap, x)
    if x != d['start'] or 1 in seen: return 'REFUTED', 'not a cycle avoiding 1'
    return 'VERIFIED', 'periodic orbit avoiding 1'


# ------------------------------------------------------------- self-test and dispatch

def _windows():
    """The window rules: independent recomputation of window values and checks of window witnesses and proofs."""
    spec = importlib.util.spec_from_file_location('ember_verdict_windows', Path(__file__).with_name('verdict_windows.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


WINDOWS = _windows()


def verdict(kind, data):
    if type(data) is dict and set(data) == {'unresolvable'}: return 'UNRESOLVED', data['unresolvable']
    if kind in ('value', 'witness', 'proof'): return WINDOWS.verdict(kind, data)
    try:
        if kind == 'ufam': return family_verdict(data)
        if kind == 'cover': return cover_verdict(data)
        if kind == 'finite': return finite_verdict(data)
        if kind == 'pattern': return pattern_verdict(data)
        if kind == 'density': return density_verdict(data)
        if kind == 'theorem': return theorem_verdict(data)
        if kind == 'nofamily': return nofamily_verdict(data)
        if kind == 'obstruction': return obstruction_verdict(data)
        if kind == 'refutation' and data['claim']['kind'] == 'obstruction': return obstruction_refutation_verdict(data)
        if kind == 'descent': return descent_verdict(data['map'], data['modulus'], data['residue'], data['steps'], data['bound'])
        if kind == 'cfinite': return cfinite_verdict(data)
        if kind == 'cycle': return cycle_verdict(data)
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as exc:
        return 'UNRESOLVED', 'malformed ' + kind + ': ' + type(exc).__name__
    return 'UNRESOLVED', 'no independent rule for kind ' + kind


def poly_node(coeffs):
    return ['add'] + [['mul', ['num', c.numerator, c.denominator], ['pow', ['var', 'k'], i]] for i, c in enumerate(coeffs) if c]


def self_test():
    """Known-true claims must verify and known-false claims must fail, or no verdict of this run counts."""
    collatz = dict(d=2, a=[1, 3], b=[0, 1])
    # n = 4k + 3: 4/n = 1/(k+1) + 2/(n(k+1)) = 1/(k+1) + 1/(n(k+1)/2) + 1/(n(k+1)/2), n(k+1)/2 = (4k+3)(k+1)/2 ... use
    # the classical n = 3 (mod 4) family: x = (n+1)/4 = k+1, y = z = n(n+1)/2 = (4k+3)(2k+2).
    good = dict(a=4, m=4, r=3, k0=0, x=[poly_node([F(1), F(1)]), poly_node([F(6), F(14), F(8)]), poly_node([F(6), F(14), F(8)])])
    bad = dict(good, x=[poly_node([F(1), F(1)]), poly_node([F(6), F(14), F(8)]), poly_node([F(6), F(14), F(9)])])
    checks = {
        'true family verifies': verdict('ufam', good)[0] == 'VERIFIED',
        'false family refuted': verdict('ufam', bad)[0] == 'REFUTED',
        'square class has no classical family': verdict('nofamily', dict(a=4, terms=3, m=840, r=1, bound=40))[0] == 'VERIFIED',
        'reachable class refuted as a wall': verdict('nofamily', dict(a=4, terms=3, m=840, r=11, bound=40))[0] == 'REFUTED',
        'true descent verifies': verdict('descent', dict(map=collatz, modulus=4, residue=1, steps=2, bound=5))[0] == 'VERIFIED',
        'false descent refuted': verdict('descent', dict(map=collatz, modulus=4, residue=3, steps=2, bound=3))[0] == 'REFUTED',
        'short range verifies': verdict('cfinite', dict(map=collatz, lo=2, hi=500, cap=1000))[0] == 'VERIFIED',
        'theorem chain verifies': verdict('theorem', theorem_case(good, 0))[0] == 'VERIFIED',
        'theorem chain with a gap refuted': verdict('theorem', theorem_case(good, 5))[0] == 'REFUTED',
        'sieve agrees with enumeration': all(open_set(dict(c, chain=[2, 4])) == open_set(c) for c in
                                             (theorem_case(good, 0)['finite']['cover'], theorem_case(good, 5)['finite']['cover'])),
        'sieved theorem chain verifies': verdict('theorem', sieved(theorem_case(good, 0)))[0] == 'VERIFIED',
        'sieved theorem chain with a gap refuted': verdict('theorem', sieved(theorem_case(good, 5)))[0] == 'REFUTED',
        'obstruction holds for 4/n at 840': verdict('obstruction', dict(a=4, terms=3, m=840, rule='classical_reach_nonsquare'))[0] == 'VERIFIED',
        'obstruction refuted for 5/n at 840': verdict('obstruction', dict(a=5, terms=3, m=840, rule='classical_reach_nonsquare'))[0] == 'REFUTED',
        'named classical parameters verify': verdict('ufam', dict(a=4, m=4, r=3, k0=0, p=['II', 1, 1, 1]))[0] == 'VERIFIED',
        'misfit classical parameters refuted': verdict('ufam', dict(a=4, m=4, r=1, k0=0, p=['II', 1, 1, 1]))[0] == 'REFUTED',
        'refutation of the 5/n obstruction verifies': verdict('refutation', dict(
            claim=dict(kind='obstruction', data=dict(a=5, terms=3, m=840, rule='classical_reach_nonsquare')),
            witness=dict(modulus=5, residue=4, params=['II', 1, 1, 1])))[0] == 'VERIFIED',
        'false refutation of the 4/n obstruction refuted': verdict('refutation', dict(
            claim=dict(kind='obstruction', data=dict(a=4, terms=3, m=840, rule='classical_reach_nonsquare')),
            witness=dict(modulus=4, residue=1, params=['II', 1, 1, 1])))[0] == 'REFUTED',
        'broken sieve chain refuted': verdict('cover', dict(theorem_case(good, 0)['finite']['cover'], chain=[3, 4]))[0] == 'REFUTED',
        'compact cover verifies': verdict('cover', compact_case(False))[0] == 'VERIFIED',
        'compact cover with a false identity refuted': verdict('cover', compact_case(True))[0] == 'REFUTED',
        'compact family rebuilds the written one': [trim(expand(e)) for e in unshaped(
            dict(a=4, m=4, r=3, k0=0, s=0), compact_case(False)['shapes'])['x']] == [trim(expand(e)) for e in good['x']],
        'window rules tell true from false claims': WINDOWS.self_test()[0],
    }
    return all(checks.values()), checks


def theorem_case(family, k0):
    """4/n on n = 3 (mod 4) with a range below 10. With k0 = 0 the chain is complete; with k0 = 5 the family starts
    at 23, so 11, 15 and 19 lie past the range and below the family: a gap in the chain, whatever the truth."""
    f = dict(family, k0=k0); start = 4 * k0 + 3
    cover = dict(a=4, terms=3, modulus=4, entries=[dict(family=f)], bound=start)
    witnesses = {'2': [1, 2], '4': [2, 3], '5': [2, 4]}
    if k0: witnesses.update({'3': [1, 4], '7': [2, 15]})
    finite = dict(a=4, terms=3, lo=2, hi=10, witnesses=witnesses, divisors={'6': 3, '8': 4, '9': 3}, cover=cover)
    return dict(a=4, terms=3, lo=2, finite=finite)


def compact_case(forged):
    """The n = 3 (mod 4) family as an identity in n: x = (n+1)/4, y = z = n(n+1)/2; forged, z becomes n(n+2)/2."""
    z = [[0, 1], [1, 1], [1, 2]] if forged else [[0, 1], [1, 2], [1, 2]]
    shape = [[[1, 4], [1, 4]], [[0, 1], [1, 2], [1, 2]], z]
    return dict(a=4, terms=3, modulus=4, bound=3, shapes=[shape], entries=[dict(family=dict(a=4, m=4, r=3, k0=0, s=0))])


def sieved(case):
    cover = dict(case['finite']['cover'], chain=[2, 4])
    return dict(case, finite=dict(case['finite'], cover=cover))


def digest(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def claims_of(state):
    """Every checked claim an agent record saved, expanded from compact rows."""
    for record in state.get('observations', []):
        if record.get('kind') != 'autonomous_research': continue
        covers = {digest(row['data']): row['data'] for row in record.get('objects', []) if row.get('kind') == 'cover'}
        for row in record.get('objects', []):
            kind, data = row.get('kind'), row.get('data')
            if kind in ('template', 'cover_tree', 'descent_tree'): continue  # bookkeeping, not claims
            if type(data) is dict and 'cover_ref' in data:
                if data['cover_ref'] not in covers:
                    yield record['task_id'], kind, dict(unresolvable='no saved cover has the referenced digest'); continue
                data = dict({k: v for k, v in data.items() if k != 'cover_ref'}, cover=covers[data['cover_ref']])
            if type(data) is dict and 'finite_ref' in data:
                ranges = {}
                for r in record.get('objects', []):
                    if r.get('kind') != 'finite': continue
                    body = r['data']
                    if 'cover_ref' in body and body['cover_ref'] in covers:
                        body = dict({k: v for k, v in body.items() if k != 'cover_ref'}, cover=covers[body['cover_ref']])
                    ranges[digest(body)] = body
                if data['finite_ref'] not in ranges:
                    yield record['task_id'], kind, dict(unresolvable='no saved range has the referenced digest'); continue
                data = dict({k: v for k, v in data.items() if k != 'finite_ref'}, finite=ranges[data['finite_ref']])
            if kind == 'ufam' and type(data) is dict and 'members' in data:
                for f in data['members']: yield record['task_id'], 'ufam', unshaped(f, data['shapes'])
                continue
            if kind == 'nofamily' and type(data) is dict and 'rs' in data:
                for r in data['rs']:
                    yield record['task_id'], 'nofamily', dict({k: v for k, v in data.items() if k != 'rs'}, r=r)
                continue
            if kind == 'descent_rows':
                for M, r, steps, bound in data['rows']:
                    yield record['task_id'], 'descent', dict(map=data['map'], modulus=M, residue=r, steps=steps, bound=bound)
                continue
            yield record['task_id'], kind, data


def main(argv):
    if len(argv) != 2: print(__doc__); return 2
    state = json.loads(Path(argv[1]).read_text(encoding='utf-8'))
    ok, tests = self_test(); rows = []
    for task, kind, data in claims_of(state):
        v, detail = verdict(kind, data) if ok else ('UNRESOLVED', 'the verifier failed its own self-test')
        rows.append(dict(task_id=task[:16], kind=kind, verdict=v, detail=detail))
    counts = {k: sum(r['verdict'] == k for r in rows) for k in ('VERIFIED', 'REFUTED', 'UNRESOLVED')}
    bit = 'verified' if rows and counts['VERIFIED'] == len(rows) else 'no, keep thinking'
    walls = [r for r in rows if r['kind'] == 'nofamily']
    listed = [r for r in rows if r['kind'] != 'nofamily' or r['verdict'] != 'VERIFIED']
    print(json.dumps(dict(status='VERDICT', version=VERSION, bit=bit, self_test=dict(ok=ok, checks=tests), counts=counts,
                          walls=dict(total=len(walls), verified=sum(r['verdict'] == 'VERIFIED' for r in walls)),
                          claims=listed[:4096],
                          limits='Independent exact recomputation of saved claims only; a VERIFIED claim is correct in its '
                                 'stated scope, not a proof of the open problem.'), indent=1))
    return 0 if bit == 'verified' else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv))
