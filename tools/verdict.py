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

def family_verdict(f):
    """VERIFIED when a*prod(x) = n*sum(prod others) as polynomials in k, each x_i is integer on Z, and each x_i
    is positive for k >= k0; REFUTED with a witness k where a denominator is non-integral or nonpositive."""
    a, m, r, k0 = f['a'], f['m'], f['r'], f['k0']; xs = [expand(e) for e in f['x']]; n = [F(r), F(m)]
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
        f = e['family']
        if M % f['m']: return 'REFUTED', 'family modulus ' + str(f['m']) + ' does not divide ' + str(M)
        if cover['bound'] < f['m'] * f['k0'] + f['r']: return 'REFUTED', 'bound below a family threshold'
        verdict, detail = family_verdict(f)
        if verdict != 'VERIFIED': return verdict, 'family ' + str(f['m']) + ':' + str(f['r']) + ': ' + detail
    return 'VERIFIED', str(len(covered_residues(cover))) + ' residues covered'


def finite_verdict(d):
    a, terms, lo, hi = d['a'], d['terms'], d['lo'], d['hi']; rows = {}
    if d['cover'] is not None:
        verdict, detail = cover_verdict(d['cover'])
        if verdict != 'VERIFIED': return verdict, 'cover: ' + detail
        for e in d['cover']['entries']:
            f = e['family']; rows.setdefault(f['m'], []).append((f['r'], f['m'] * f['k0'] + f['r'], [expand(x) for x in f['x']]))
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


def divisor_list(n):
    out = set(); i = 1
    while i * i <= n:
        if n % i == 0: out.update((i, n // i))
        i += 1
    return sorted(out)


def classical_hit(a, m, r, bound):
    """Independent enumeration of fixed-parameter Type II and Type I families on n = r (mod m)."""
    for D in divisor_list(m):
        if D % a: continue
        uv = D // a; e = (-r) % D or D
        for u in divisor_list(uv):
            if u <= uv // u and (u + uv // u) % e == 0: return ('II', u, uv // u)
    for u in range(1, bound + 1):
        for v in range(u, bound + 1):
            if ((u + v) * m) % (a * u * v): continue
            for w in range(1, bound + 1):
                q = a * u * v * w
                if ((u + v) * m) % q == 0 and ((u + v) * r + w) % q == 0: return ('I', u, v, w)
    return None


def nofamily_verdict(d):
    if d['m'] > 10 ** 8: return 'UNRESOLVED', 'modulus beyond the independent enumeration bound'
    hit = classical_hit(d['a'], d['m'], d['r'], d['bound'])
    return ('REFUTED', 'classical family ' + str(hit)) if hit else ('VERIFIED', 'no classical parameters')


def theorem_verdict(d):
    """The chain: the range verifies, it carries its cover, and the cover bound lies inside the range."""
    f = d['finite']
    if f.get('cover') is None or (f['a'], f['terms'], f['lo']) != (d['a'], d['terms'], d['lo']):
        return 'REFUTED', 'the theorem and its range state different questions'
    if f['cover']['bound'] > f['hi']: return 'REFUTED', 'cover bound above the checked range'
    verdict, detail = finite_verdict(f)
    if verdict != 'VERIFIED': return verdict, 'range: ' + detail
    M = f['cover']['modulus']
    return 'VERIFIED', 'every n >= ' + str(d['lo']) + ' outside ' + str(M - len(covered_residues(f['cover']))) + \
        ' open residues mod ' + str(M) + ' is represented'


def density_verdict(d):
    verdict, detail = cover_verdict(d['cover'])
    if verdict != 'VERIFIED': return verdict, 'cover: ' + detail
    fraction = F(d['fraction'][0], d['fraction'][1])
    exact = F(len(covered_residues(d['cover'])), d['cover']['modulus'])
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

def verdict(kind, data):
    try:
        if kind == 'ufam': return family_verdict(data)
        if kind == 'cover': return cover_verdict(data)
        if kind == 'finite': return finite_verdict(data)
        if kind == 'pattern': return pattern_verdict(data)
        if kind == 'density': return density_verdict(data)
        if kind == 'theorem': return theorem_verdict(data)
        if kind == 'nofamily': return nofamily_verdict(data)
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
    }
    return all(checks.values()), checks


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
                    yield record['task_id'], kind, dict(unresolvable='cover reference not saved'); continue
                data = dict({k: v for k, v in data.items() if k != 'cover_ref'}, cover=covers[data['cover_ref']])
            if type(data) is dict and 'finite_ref' in data:
                ranges = {digest(r['data']): r['data'] for r in record.get('objects', []) if r.get('kind') == 'finite'}
                if data['finite_ref'] not in ranges:
                    yield record['task_id'], kind, dict(unresolvable='range reference not saved'); continue
                data = dict({k: v for k, v in data.items() if k != 'finite_ref'}, finite=ranges[data['finite_ref']])
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
    print(json.dumps(dict(status='VERDICT', version=VERSION, bit=bit, self_test=dict(ok=ok, checks=tests), counts=counts,
                          claims=rows[:512],
                          limits='Independent exact recomputation of saved claims only; a VERIFIED claim is correct in its '
                                 'stated scope, not a proof of the open problem.'), indent=1))
    return 0 if bit == 'verified' else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv))
