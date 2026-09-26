"""Independent verdicts on Ember's window claims (value, witness and proof claims of her window tools).

This module shares no code with Ember's producers or checkers: every rule below recomputes a value, or checks a
witness or proof, with its own implementation. A rule answers VERIFIED (the claim holds as stated), REFUTED (the
recomputation or check fails, with the failing part named) or UNRESOLVED (no independent rule for the family, or out
of this verifier's bounds). tools/verdict.py loads it for the kinds value, witness and proof.
"""
from fractions import Fraction as F
from itertools import combinations, permutations, product
import json
from math import gcd, isqrt, prod

# ------------------------------------------------------------- integers

_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
MR_BOUND = 3317044064679887385961981  # the first 13 prime bases decide every n below it


def is_prime(n):
    if n < 2: return False
    for p in _BASES:
        if n % p == 0: return n == p
    if n >= MR_BOUND: raise OverflowError('primality beyond the deterministic range')
    d = n - 1; s = (d & -d).bit_length() - 1; d >>= s
    for a in _BASES:
        x = pow(a, d, n)
        if x == 1 or x == n - 1: continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True


def primes_below(n):
    flags = bytearray([1]) * max(n, 2); flags[0] = flags[1] = 0
    for p in range(2, isqrt(n - 1) + 1 if n > 1 else 0):
        if flags[p]: flags[p * p::p] = bytes(len(flags[p * p::p]))
    return flags


def factorize(n):
    """{p: e} by trial division up to 10^5 and Brent's rho beyond."""
    out = {}
    for p in (2, 3, 5):
        while n % p == 0: out[p] = out.get(p, 0) + 1; n //= p
    f, step = 7, 4
    while f * f <= n and f < 100_000:
        while n % f == 0: out[f] = out.get(f, 0) + 1; n //= f
        f += step; step = 6 - step
    todo = [n] if n > 1 else []
    while todo:
        m = todo.pop()
        if m < 10 ** 10 and all(m % q for q in range(2, isqrt(m) + 1)) or is_prime(m):
            out[m] = out.get(m, 0) + 1; continue
        c = 1
        while True:
            x = y = 2; g = 1
            while g == 1:
                x = (x * x + c) % m; y = (y * y + c) % m; y = (y * y + c) % m; g = gcd(abs(x - y), m)
            if g != m: break
            c += 1
        todo += [g, m // g]
    return out


def sigma(n): return prod((p ** (e + 1) - 1) // (p - 1) for p, e in factorize(n).items())


def phi(n): return prod((p - 1) * p ** (e - 1) for p, e in factorize(n).items())


def iroot(n, k):
    r = int(round(n ** (1.0 / k))) if n < 1 << 1000 else 1 << (n.bit_length() // k)
    while r ** k > n: r -= 1
    while (r + 1) ** k <= n: r += 1
    return r


def fib2(n, m=None):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        a, b = a * (2 * b - a), a * a + b * b
        if bit == '1': a, b = b, a + b
        if m: a, b = a % m, b % m
    return a


# ------------------------------------------------------------- the tally expression language, read independently

def evaluate(e, env):
    if type(e) is int: return e
    if type(e) is str: return env[e]
    head, args = e[0], e[1:]
    if head == 'and': return all(evaluate(a, env) for a in args)
    if head == 'or': return any(evaluate(a, env) for a in args)
    if head in ('exists', 'forall'):
        var, lo, hi, body = args; rng = range(evaluate(lo, env), evaluate(hi, env))
        test = (evaluate(body, dict(env, **{var: v})) for v in rng)
        return any(test) if head == 'exists' else all(test)
    v = [evaluate(a, env) for a in args]
    x = v[0] if v else None
    table = {
        'add': lambda: v[0] + v[1], 'sub': lambda: v[0] - v[1], 'mul': lambda: v[0] * v[1], 'neg': lambda: -x,
        'pow': lambda: v[0] ** v[1], 'mod': lambda: v[0] % v[1] if v[1] else None,
        'fdiv': lambda: v[0] // v[1] if v[1] else None, 'abs': lambda: abs(x), 'pow2': lambda: 2 ** x,
        'gcd': lambda: gcd(v[0], v[1]), 'isqrt': lambda: isqrt(x), 'digitsum': lambda: sum(int(c) for c in str(abs(x))),
        'fact': lambda: prod(range(2, x + 1)), 'rev': lambda: int(str(x)[::-1]), 'fib': lambda: fib2(x),
        'eq': lambda: v[0] == v[1], 'ne': lambda: v[0] != v[1], 'lt': lambda: v[0] < v[1], 'le': lambda: v[0] <= v[1],
        'gt': lambda: v[0] > v[1], 'ge': lambda: v[0] >= v[1], 'not': lambda: not x,
        'divides': lambda: v[0] != 0 and v[1] % v[0] == 0, 'even': lambda: x % 2 == 0, 'odd': lambda: x % 2 == 1,
        'square': lambda: x >= 0 and isqrt(x) ** 2 == x, 'cube': lambda: iroot(abs(x), 3) ** 3 == abs(x),
        'palindrome': lambda: str(abs(x)) == str(abs(x))[::-1], 'prime': lambda: is_prime(x),
        'nextprime': lambda: next(m for m in range(max(x + 1, 2), 2 * x + 3) if is_prime(m)),
        'prevprime': lambda: next((m for m in range(x - 1, 1, -1) if is_prime(m)), None),
        'goldbach': lambda: x >= 4 and x % 2 == 0 and any(is_prime(p) and is_prime(x - p) for p in range(2, x // 2 + 1)),
        'sigma': lambda: sigma(x), 'phi': lambda: phi(x), 'tau': lambda: prod(e + 1 for e in factorize(x).values()),
        'aliquot': lambda: sigma(x) - x, 'rad': lambda: prod(factorize(x)), 'omega': lambda: len(factorize(x)),
        'squarefree': lambda: all(e == 1 for e in factorize(x).values()),
        'mersenne': lambda: is_prime(x) and lucas_lehmer(x), 'fermat': lambda: pepin(x),
        'wieferich': lambda: x > 2 and pow(2, x - 1, x * x) == 1,
        'primroot': lambda: v[1] > 2 and is_prime(v[1]) and v[0] % v[1] != 0 and all(
            pow(v[0], (v[1] - 1) // q, v[1]) != 1 for q in factorize(v[1] - 1)),
        'regular': lambda: is_prime(x) and x > 2 and not any(b % x == 0 for b in bernoulli_numerators_mod(x)),
    }
    if head not in table: raise LookupError('no independent reading of ' + head)
    return table[head]()


def lucas_lehmer(p):
    if p == 2: return True
    M = 2 ** p - 1; s = 4
    for _ in range(p - 2): s = (s * s - 2) % M
    return s == 0


def pepin(n):
    F_ = 2 ** 2 ** n + 1
    return True if n == 0 else pow(3, F_ // 2, F_) == F_ - 1


def bernoulli_numerators_mod(p):
    """B_2, B_4, ..., B_(p-3) modulo p by the recurrence sum_(j<=m) C(m+1, j) B_j = 0 (m < p - 1), mod p."""
    B = [1]
    inv = [0, 1] + [pow(i, p - 2, p) for i in range(2, p + 1)]
    for m in range(1, p - 2):
        c = 1; acc = 0
        for j in range(m):
            acc = (acc + c * B[j]) % p
            c = c * (m + 1 - j) % p * inv[j + 1] % p
        B.append(-acc * inv[m + 1] % p)
    return [B[k] for k in range(2, p - 2, 2)]


# ------------------------------------------------------------- value rules (each returns the value it recomputes)

def v_tally(p):
    lo, bounds = p['lo'], p['bounds']; counts = []; c = 0; n = lo
    for b in bounds:
        while n < b:
            if evaluate(p['pred'], {'n': n}): c += 1
            n += 1
        counts.append(c)
    return counts


def v_members(p): return [n for n in range(p['lo'], p['hi']) if evaluate(p['pred'], {'n': n})]


def v_gap_records(p):
    flags = primes_below(2 * p['hi'] + 1000); out = []; best = 0
    ps = [q for q in range(p['lo'], len(flags)) if flags[q]]
    for a, b in zip(ps, ps[1:]):
        if a >= p['hi']: break
        if b - a > best: best = b - a; out.append([a, best])
    return out


def v_goldbach(p):
    flags = primes_below(p['hi'] + 1); ps = [q for q in range(len(flags)) if flags[q]]
    worst = None; failures = []
    for n in range(p['lo'] + p['lo'] % 2, p['hi'], 2):
        q = next((q for q in ps if q <= n // 2 and flags[n - q]), None)
        if q is None: failures.append(n)
        elif worst is None or q > worst[1]: worst = [n, q]
    return dict(all=not failures, failures=failures, worst=worst)


def v_gilbreath(p):
    flags = primes_below(max(1000, p['k'] * 12 + 100)); row = [q for q in range(len(flags)) if flags[q]][:p['k']]
    for i in range(1, p['k']):
        row = [abs(b - a) for a, b in zip(row, row[1:])]
        if row[0] != 1: return i
    return 0


def v_totient_singletons(p):
    lo, hi = p['lo'], p['hi']; top = max(7, hi * hi); count = {}
    # phi(x) >= sqrt(x / 2) for every x, so phi(x) < hi needs x < 2 hi^2; a totient table by smallest prime factors
    top = 2 * hi * hi + 2; spf = list(range(top + 1))
    for q in range(2, isqrt(top) + 1):
        if spf[q] == q:
            for m in range(q * q, top + 1, q):
                if spf[m] == m: spf[m] = q
    tot = [0, 1] + [0] * (top - 1)
    for x in range(2, top + 1):
        q = spf[x]; y = x // q
        tot[x] = tot[y] * (q if y % q == 0 else q - 1)
        if lo <= tot[x] < hi: count[tot[x]] = count.get(tot[x], 0) + 1
    if lo <= 1 < hi: count[1] = count.get(1, 0) + 1  # phi(1) = 1
    return sorted(m for m, c in count.items() if c == 1)


def v_erdos_moser(p):
    out = []
    for k in range(1, p['k_max'] + 1):
        total = 0
        for m in range(2, p['m_max'] + 1):
            total += (m - 1) ** k
            if total == m ** k: out.append([m, k])
    return out


def v_euler_bricks(p):
    N = p['max_edge']; out = []
    sq = lambda s: isqrt(s) ** 2 == s
    legs = {a: [b for b in range(a + 1, N + 1) if sq(a * a + b * b)] for a in range(1, N + 1)}
    for a in range(1, N + 1):
        for b, c in combinations(legs[a], 2):
            if sq(b * b + c * c) and gcd(a, gcd(b, c)) == 1: out.append([a, b, c, sq(a * a + b * b + c * c)])
    return sorted(out)


def v_abc_hits(p):
    C = p['c_max']; num, den = p['q']; rad = [prod(factorize(n)) if n > 1 else 1 for n in range(C)]; out = []
    for c in range(3, C):
        for a in range(1, c // 2 + 1):
            b = c - a
            if gcd(a, b) == 1 and c ** den >= (rad[a] * rad[b] * rad[c]) ** num: out.append([a, b, c])
    return out


def v_pascal(p):
    N, K = p['n_max'], p['min_count']; count = {}
    if K < 3: raise LookupError('multiplicities below 3 are not recomputed here')
    n = 2
    while n * (n - 1) // 2 <= N:
        c = 1
        for k in range(0, n // 2 + 1):
            if k > 0: c = c * (n - k + 1) // k
            if c > N: break
            if c > 1: count[c] = count.get(c, 0) + (1 if 2 * k == n else 2)
        n += 1
    # values v with C(v, 1) beyond the loop: every v >= n appears as C(v, 1) and C(v, v - 1) only
    return {str(v): c for v, c in sorted(count.items()) if c >= K}


def v_three_cubes(p):
    N, B = p['n_max'], p['bound']; found = set()
    targets = [n for n in range(1, N) if n % 9 not in (4, 5)]
    def cube_floor(v):  # the largest z with z^3 <= v
        r = iroot(abs(v), 3)
        return r if v >= 0 else (-r if r ** 3 == -v else -r - 1)
    for x in range(-B, B + 1):
        for y in range(x, B + 1):
            s = x ** 3 + y ** 3
            for z in range(max(-B, cube_floor(1 - s - 1) + 1), min(B, cube_floor(N - 1 - s)) + 1):
                n = s + z ** 3
                if 0 < n < N: found.add(n)
    found &= set(targets)
    return dict(represented=len(found), missing=[n for n in targets if n not in found])


def v_irregular_pairs(p):
    out = []
    for q in range(5, p['p_max'] + 1):
        if not is_prime(q): continue
        for i, b in enumerate(bernoulli_numerators_mod(q)):
            if b == 0: out.append([q, 2 * i + 2])
    return out


def v_mersenne(p): return [q for q in range(2, p['p_max'] + 1) if is_prime(q) and lucas_lehmer(q)]


def v_fermat(p): return [n for n in range(p['n_max'] + 1) if pepin(n)]


def v_wall_sun_sun(p):
    flags = primes_below(p['p_max'] + 1)
    return [q for q in range(7, p['p_max']) if flags[q] and fib2(q - (1 if q % 5 in (1, 4) else -1), q * q) == 0]


def v_reverse_add(p):
    n = p['start']
    for i in range(1, p['steps'] + 1):
        n += int(str(n)[::-1]); t = str(n)
        if t == t[::-1]: return dict(palindrome_at=i, digits=len(t))
    return dict(palindrome_at=None, digits=len(str(n)))


def v_affine_orbit(p):
    d, A, B = p['map']['d'], p['map']['a'], p['map']['b']; n = p['start']; seen = {n}; top = n.bit_length()
    for i in range(1, p['steps'] + 1):
        r = n % d; n = (A[r] * n + B[r]) // d; top = max(top, n.bit_length())
        if n in seen: return dict(repeat_at=i, max_bits=top, last_bits=n.bit_length())
        if len(seen) < 100_000: seen.add(n)
    return dict(repeat_at=None, max_bits=top, last_bits=n.bit_length())


def v_amusical(p):
    out = {}
    for name in ('forward', 'backward'):
        n = s0 = p['start']; top = n.bit_length(); back = None
        for i in range(1, p['steps'] + 1):
            if name == 'forward': n = {0: 3 * n // 2, 1: (3 * n + 1) // 4, 3: (3 * n - 1) // 4}[n % 4 if n % 2 else 0]
            else: n = {0: 2 * n // 3, 1: (4 * n - 1) // 3, 2: (4 * n + 1) // 3}[n % 3]
            top = max(top, n.bit_length())
            if n == s0: back = i; break
        out[name] = dict(returns_at=back, max_bits=top)
    return out


def v_aliquot(p):
    n = p['start']; seen = {n: 0}; top = len(str(n))
    for i in range(1, p['steps'] + 1):
        if n == 1: return dict(ends_at=i, cycle=None, stopped=None, max_digits=top)
        n = sigma(n) - n; top = max(top, len(str(n)))
        if n == 0: return dict(ends_at=i, cycle=None, stopped=None, max_digits=top)
        if n in seen: return dict(ends_at=None, cycle=[seen[n], i], stopped=None, max_digits=top)
        if len(str(n)) > p['digits_max']: return dict(ends_at=None, cycle=None, stopped=i, max_digits=top)
        seen[n] = i
    return dict(ends_at=None, cycle=None, stopped=p['steps'], max_digits=top)


def v_x2x3(p):
    q = p['q']; left = set(range(1, q)); sizes = {}
    while left:
        a = min(left); orbit = {a}; frontier = [a]
        while frontier:
            x = frontier.pop()
            for y in (2 * x % q, 3 * x % q):
                if y not in orbit: orbit.add(y); frontier.append(y)
        left -= orbit; sizes[len(orbit)] = sizes.get(len(orbit), 0) + 1
    return {str(k): v for k, v in sorted(sizes.items())}


def v_srg(p):
    v, k, l, m = p['v'], p['k'], p['l'], p['m']
    out = dict(counting=k * (k - l - 1) == (v - k - 1) * m)
    D = (l - m) ** 2 + 4 * (k - m); rD = isqrt(D)
    if rD * rD == D:
        r, s = F(l - m + rD, 2), F(l - m - rD, 2)
        f = F(-k - s * (v - 1), 1) / (r - s)  # from k + f r + g s = 0 and f + g = v - 1
        out['multiplicities_integral'] = f.denominator == 1
        if f.denominator == 1:
            f = int(f); g = v - 1 - f
            out['krein'] = ((r + 1) * (k + r + 2 * r * s) <= (k + r) * (s + 1) ** 2
                            and (s + 1) * (k + s + 2 * r * s) <= (k + s) * (r + 1) ** 2)
            out['absolute_bound'] = 2 * v <= f * (f + 3) and 2 * v <= g * (g + 3)
            out['eigenvalues'] = [str(r), str(s)]; out['multiplicities'] = [f, g]
    else:
        out['multiplicities_integral'] = 2 * k + (v - 1) * (l - m) == 0 and (v - 1) % 2 == 0
        out['conference'] = 2 * k + (v - 1) * (l - m) == 0
    return out


def v_plane_orders(p):
    out = {}
    for n in range(2, p['n_max'] + 1):
        fs = factorize(n)
        if len(fs) == 1: out[str(n)] = 'constructible'
        elif n % 4 in (1, 2) and not any(isqrt(n - a * a) ** 2 == n - a * a for a in range(isqrt(n) + 1)):
            out[str(n)] = 'excluded'
        else: out[str(n)] = 'unknown'
    return out


def v_sum_product(p):
    n = p['n']
    A = dict(ap=lambda: list(range(1, n + 1)), gp=lambda: [2 ** i for i in range(n)],
             squares=lambda: [i * i for i in range(1, n + 1)],
             primes=lambda: [q for q in range(2, 40 * n) if is_prime(q)][:n])[p['kind']]()
    return dict(sums=len({a + b for a in A for b in A}), products=len({a * b for a in A for b in A}), n=n)


def v_four_cubes(p):
    N = p['N']; cubes = [c ** 3 for c in range(1, iroot(N, 3) + 2) if c ** 3 < N]
    two = bytearray(N)
    for a in cubes:
        for b in cubes:
            if a + b < N: two[a + b] = 1
    twos = [t for t in range(N) if two[t]]; four = bytearray(N)
    for s in twos:
        for t in twos:
            if s + t >= N: break
            four[s + t] = 1
    missing = [n for n in range(1, N) if not four[n]]
    return dict(count=len(missing), largest=missing[-1] if missing else None, last=missing[-12:])


def v_sidon_max(p):
    n = p['n']; best = 0
    def grow(S, diffs, nxt):
        nonlocal best
        best = max(best, len(S))
        for y in range(nxt, n + 1):
            if len(S) + 1 + (n - y) <= best: return
            nd = {y - s for s in S}
            if not nd & diffs: grow(S + [y], diffs | nd, y + 1)
    grow([], set(), 1)
    return best


def v_unique_game(p):
    n, k, cs = p['n'], p['k'], p['constraints']
    return [max(sum(pi[lab[u]] == lab[v] for u, v, pi in cs) for lab in product(range(k), repeat=n)), len(cs)]


def v_rota(p):
    vs = range(1, 8)
    bases = [b for b in combinations(vs, 3) if b[0] ^ b[1] ^ b[2] != 0]
    ok = lambda a, b, c: len({a, b, c}) == 3 and a ^ b ^ c != 0
    fails = sum(1 for B1 in bases for B2 in bases for B3 in bases
                if not any(all(ok(B1[j], x[j], y[j]) for j in range(3)) for x in permutations(B2) for y in permutations(B3)))
    return dict(triples=len(bases) ** 3, failures=fails)


def v_frankl(p):
    m = p['m']; U = 1 << m; count = bad = 0
    for mask in range(1, 1 << U):
        fam = [s for s in range(U) if mask >> s & 1]; S = set(fam)
        if not any(fam) or any((a | b) not in S for a in fam for b in fam): continue
        count += 1
        if all(2 * sum(s >> x & 1 for s in fam) < len(fam) for x in range(m)): bad += 1
    return dict(families=count, counterexamples=bad)


def v_mahler_polygon(p):
    P = [tuple(F(c) if type(c) is int else F(*c) for c in v) for v in p['vertices']]
    area = lambda Q: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(Q, Q[1:] + Q[:1]))) / 2
    # the polar body's vertices are the normals of the edges scaled so that <x, v> = 1 on each edge
    polar = []
    for a, b in zip(P, P[1:] + P[:1]):
        nx, ny = b[1] - a[1], a[0] - b[0]; h = nx * a[0] + ny * a[1]; polar.append((nx / h, ny / h))
    r = area(P) * area(polar)
    return [r.numerator, r.denominator]


def v_ising(p):
    L, M = p['L'], p['M']; N = L * M; counts = [0] * (2 * N + 1)
    for s in range(1 << N):
        spin = lambda i, j: s >> ((i % L) * M + (j % M)) & 1
        bad = sum(spin(i, j) != spin(i, j + 1) for i in range(L) for j in range(M))
        bad += sum(spin(i, j) != spin(i + 1, j) for i in range(L) for j in range(M))
        counts[bad] += 1
    while counts and counts[-1] == 0: counts.pop()
    return counts


def v_point_count(p):
    q, k = p['p'], p['nvars']; zeros = 0
    for x in product(range(q), repeat=k):
        if not any(x): continue
        if sum(c * prod(xi ** e for xi, e in zip(x, ex)) for c, ex in p['poly']) % q == 0: zeros += 1
    return zeros // (q - 1)


def v_elliptic_ap(p):
    a, b, P = p['a'], p['b'], p['p_max']; aps = {}; v = F(1)
    for q in range(5, P + 1):
        if not is_prime(q) or (4 * a ** 3 + 27 * b * b) % q == 0: continue
        sq = [0] * q
        for y in range(q): sq[y * y % q] += 1
        count = 1 + sum(sq[(x * x * x + a * x + b) % q] for x in range(q))  # affine points and the point at infinity
        aps[str(q)] = q + 1 - count; v *= F(count, q)
    return dict(ap=aps, product=[v.numerator.bit_length() - v.denominator.bit_length(), str(round(float(v), 6))])


def v_power_sums(p):
    A, e0, e1, mode = p['base_max'], p['exp_min'], p['exp_max'], p['mode']; found = set()
    for a in range(1, A + 1):
        for b in range(1, A + 1):
            if gcd(a, b) != 1: continue
            for x in range(e0, e1 + 1):
                for y in range(e0, e1 + 1):
                    s = a ** x + b ** y
                    for z in range(e0, e1 + 1):
                        c = iroot(s, z)
                        if c ** z != s: continue
                        if mode == 'fermat_catalan' and F(1, x) + F(1, y) + F(1, z) >= 1: continue
                        if mode == 'beal' and min(x, y, z) < 3: continue
                        found.add(tuple(sorted([(a, x), (b, y)])) + ((c, z),))
    return [[list(t) for t in key] for key in sorted(found)]


def v_power_differences(p):
    X, D, K = p['x_max'], p['d_max'], p['min_count']; powers = {1}
    k = 2
    while 2 ** k <= X:
        c = 2
        while c ** k <= X: powers.add(c ** k); c += 1
        k += 1
    ps = sorted(powers); count = {}
    for i, u in enumerate(ps):
        j = i + 1
        while j < len(ps) and ps[j] - u <= D: count[ps[j] - u] = count.get(ps[j] - u, 0) + 1; j += 1
    return {str(d): c for d, c in sorted(count.items()) if c >= K}


def v_representation(p):
    N = p['N']; B = sorted(x for x in range(N + 1) if all((x >> b) & 1 == 0 for b in range(0, 40, 2))
                             or all((x >> b) & 1 == 0 for b in range(1, 41, 2)))
    reps = [0] * (N + 1)
    for i, a in enumerate(B):
        for b in B[i:]:
            if a + b > N: break
            reps[a + b] += 1
    best = max(range(N + 1), key=lambda n: (reps[n], -n))
    return dict(max_representations=reps[best], at=best)


def v_galerkin(p):
    K = p['K']; modes = [(a, b) for a in range(-K, K + 1) for b in range(-K, K + 1) if 0 < a * a + b * b <= K * K]
    S = set(modes); triads = 0; energy = enstrophy = True
    n2 = lambda v: v[0] ** 2 + v[1] ** 2
    for q, r in combinations(sorted(modes), 2):
        k = (-q[0] - r[0], -q[1] - r[1])
        if k not in S or not (r < k): continue
        triads += 1
        # c(a, b): the coefficient with which modes a and b feed the third; energy and enstrophy identities
        c = lambda a, b: (a[0] * b[1] - a[1] * b[0]) * (F(1, n2(b)) - F(1, n2(a)))
        c1, c2, c3 = c(q, r), c(r, k), c(k, q)
        enstrophy &= c1 + c2 + c3 == 0
        energy &= c1 / n2(k) + c2 / n2(q) + c3 / n2(r) == 0
    return dict(triads=triads, energy=energy, enstrophy=enstrophy)


def pi_digits(n):
    """The first n decimals of pi by Machin's formula in integers with guard digits."""
    guard = 12; scale = 10 ** (n + guard)
    def arctan_inv(x):
        # each summand is off by less than 2 units (two floor divisions); the omitted tail is below 1 unit
        total = term = scale // x; k = 1; x2 = x * x; terms = 1
        while term:
            term //= x2; k += 2; terms += 1
            total += term // k if (k // 2) % 2 == 0 else -(term // k)
        return total, 2 * terms + 1
    a5, e5 = arctan_inv(5); a239, e239 = arctan_inv(239)
    pi = 4 * (4 * a5 - a239); slack = 16 * e5 + 4 * e239
    lo, hi = (pi - slack) // 10 ** guard, (pi + slack) // 10 ** guard
    if lo != hi: raise OverflowError('guard digits did not decide the last digit')
    def text(v, width):  # decimal digits of v, zero-padded to width, by halving (no long int-to-str conversion)
        if width <= 1000: return str(v).rjust(width, '0')
        half = width // 2; top, bottom = divmod(v, 10 ** half)
        return text(top, width - half) + text(bottom, half)
    return text(lo - 3 * 10 ** n, n)


def v_digit_counts(p):
    if p['expr'] != 'pi': raise LookupError('only pi is recomputed here')
    d = pi_digits(p['n'])
    counts = [d.count(str(i)) for i in range(10)]
    pairs = {}
    for a, b in zip(d, d[1:]): pairs[a + b] = pairs.get(a + b, 0) + 1
    return dict(counts=counts, first=d[:20], last=d[-20:], pairs=dict(sorted(pairs.items())))


def v_distinct_cover(p):
    mods = sorted(p['moduli']); L = 1
    for m in mods: L = L * m // gcd(L, m)
    if sum(F(1, m) for m in mods) < 1: return dict(exists=False, reason='density below 1')
    # exhaustive: choose residues in order, tracking the uncovered set; prune when the rest cannot cover it
    def search(i, uncovered):
        if not uncovered: return True
        if i == len(mods): return False
        if sum(-(-L // m) for m in mods[i:]) < len(uncovered): return False
        m = mods[i]
        return any(search(i + 1, {x for x in uncovered if x % m != r}) for r in range(m))
    return dict(exists=search(0, set(range(L))), reason='exhaustive search')


def edges_of(g): n, E = graph_spec(g); return n, [tuple(sorted(e)) for e in E]


def v_chromatic_index(p):
    n, E = edges_of(p['graph']); deg = [0] * n
    for a, b in E: deg[a] += 1; deg[b] += 1
    D = max(deg)
    def colorable(k):
        col = {}
        order = sorted(E)
        def go(i):
            if i == len(order): return True
            a, b = order[i]
            used = {c for e, c in col.items() if a in e or b in e}
            for c in range(k):
                if c not in used:
                    col[order[i]] = c
                    if go(i + 1): return True
                    del col[order[i]]
            return False
        return go(0)
    return D if colorable(D) else D + 1


def v_isomorphic(p):
    n1, E1 = graph_spec(p['G']); n2, E2 = graph_spec(p['H'])
    if n1 != n2 or len(E1) != len(E2): return False
    n = n1; adj1 = [set() for _ in range(n)]; adj2 = [set() for _ in range(n)]
    for e in E1: a, b = tuple(e); adj1[a].add(b); adj1[b].add(a)
    for e in E2: a, b = tuple(e); adj2[a].add(b); adj2[b].add(a)
    if sorted(map(len, adj1)) != sorted(map(len, adj2)): return False
    image = {}
    def go(v):
        if v == n: return True
        for w in range(n):
            if w in image.values() or len(adj2[w]) != len(adj1[v]): continue
            if all((u in adj1[v]) == (image[u] in adj2[w]) for u in image):
                image[v] = w
                if go(v + 1): return True
                del image[v]
        return False
    return go(0)


def v_hadamard_orders(p):
    top = 4 * p['k_max']; have = {1, 2}
    for q in range(3, top):
        if len(factorize(q)) == 1:
            if q % 4 == 3: have.add(q + 1)
            if q % 4 == 1: have.add(2 * q + 2)
    grew = True
    while grew:
        grew = False
        for a in list(have):
            for b in list(have):
                if a * b <= top and a * b not in have: have.add(a * b); grew = True
    return [n for n in range(4, top + 1, 4) if n not in have]


def v_oriented(p):
    n, prop, r = p['n'], p['property'], p['r']; pairs = list(combinations(range(n), 2)); checked = bad = 0
    for code in product(range(3), repeat=len(pairs)):
        out = [set() for _ in range(n)]
        for (u, v), c in zip(pairs, code):
            if c == 1: out[u].add(v)
            if c == 2: out[v].add(u)
        if prop == 'second_neighborhood':
            checked += 1
            second = lambda v: {x for u in out[v] for x in out[u]} - out[v] - {v}
            if all(len(second(v)) < len(out[v]) for v in range(n)): bad += 1
        else:
            if r == 0 or min(map(len, out)) < r: continue
            checked += 1; limit = -(-n // r)
            # a directed cycle of length <= limit: walks of length <= limit returning to their start
            short = False
            for s in range(n):
                reach = {s}
                for step in range(1, limit + 1):
                    reach = {x for u in reach for x in out[u]}
                    if s in reach: short = True; break
                if short: break
            if not short: bad += 1
    return dict(checked=checked, violations=bad)


def v_circuit_sizes(p):
    n, S = p['n'], p['max_size']; size = 1 << n; full = (1 << size) - 1
    inputs = [sum(1 << r for r in range(size) if r >> (n - 1 - i) & 1) for i in range(n)]
    gate = lambda op, a, b: sum(((op >> (2 * (a >> r & 1) + (b >> r & 1))) & 1) << r for r in range(size))
    best = {t: 0 for t in inputs}; layer = {frozenset(inputs)}
    for s in range(1, S + 1):
        nxt = set()
        for wires in layer:
            ws = list(wires)
            for i in range(len(ws)):
                for j in range(i, len(ws)):
                    for op in range(16):
                        t = gate(op, ws[i], ws[j])
                        if t in wires: continue
                        best.setdefault(t, s)
                        if s < S: nxt.add(wires | {t})
        layer = nxt
    hist = {}
    for s in best.values(): hist[str(s)] = hist.get(str(s), 0) + 1
    out = dict(sorted(hist.items(), key=lambda kv: int(kv[0]))); out['more'] = (1 << size) - len(best)
    return out


def v_lienard(p):
    cs = p['coeffs']; deg = (len(cs) + 1) // 2
    P = [F(0)] * (deg + 1)
    for k, a in enumerate(cs):
        if k % 2: P[(k - 1) // 2] += F(a) * F(prod(range(k + 1, (k + 1) // 2, -1)), prod(range(1, (k + 1) // 2 + 1))) / 2 ** (k + 1)
    while len(P) > 1 and P[-1] == 0: P.pop()
    if len(P) <= 1: return dict(simple_positive_zeros=0, degree=0)
    def rem(a, b):
        a = list(a)
        while len(a) >= len(b) and any(a):
            c = a[-1] / b[-1]; shift = len(a) - len(b)
            for i, x in enumerate(b): a[shift + i] -= c * x
            a.pop()
        while a and a[-1] == 0: a.pop()
        return a
    def gcd_p(a, b):
        while b: a, b = b, rem(a, b)
        return a
    def positive_roots(f):
        # Sturm's theorem on (0, bound] with Cauchy's root bound
        if len(f) <= 1: return 0
        chain = [f, [i * c for i, c in enumerate(f)][1:]]
        while len(chain[-1]) > 1:
            r = rem(chain[-2], chain[-1])
            if not r: break
            chain.append([-x for x in r])
        bound = 1 + max(abs(c / f[-1]) for c in f[:-1])
        def changes(x):
            vals = [sum(c * x ** i for i, c in enumerate(g)) for g in chain]; vals = [v for v in vals if v != 0]
            return sum(1 for a, b in zip(vals, vals[1:]) if (a > 0) != (b > 0))
        return changes(F(0)) - changes(bound)
    total = positive_roots(P)
    g = gcd_p(P, [i * c for i, c in enumerate(P)][1:])
    return dict(simple_positive_zeros=total - (positive_roots(g) if len(g) > 1 else 0), degree=len(P) - 1)


def v_mahler_z(p):
    lo, hi = rat(p['lo']), rat(p['hi']); pieces = [(lo, hi)]; scale = F(1); empty = None
    for step in range(p['steps']):
        # x (3/2)^step has fractional part below 1/2 exactly on [j, j + 1/2) (2/3)^step
        pieces = [(max(a, j * scale), min(b, (j + F(1, 2)) * scale)) for a, b in pieces
                  for j in range(int(a / scale), int(b / scale) + 2) if max(a, j * scale) < min(b, (j + F(1, 2)) * scale)]
        scale *= F(2, 3)
        if not pieces: empty = step; break
    total = sum((b - a for a, b in pieces), F(0))
    return dict(intervals=len(pieces), length=[total.numerator, total.denominator], empty_at=empty)


def v_erdos_gyarfas(p):
    fails = []
    for m in range(3, p['n_max'] + 1):
        for k in range(1, (m + 1) // 2):
            if 2 * k == m: continue
            n, E = graph_spec(dict(named='gp', n=m, k=k)); adj = [set() for _ in range(n)]
            for e in E: a, b = tuple(e); adj[a].add(b); adj[b].add(a)
            lengths = set()
            def walk(start, v, seen):
                for u in adj[v]:
                    if u == start and len(seen) >= 3: lengths.add(len(seen))
                    elif u > start and u not in seen: walk(start, u, seen | {u})
            for s0 in range(n): walk(s0, s0, {s0})
            if not any(L & (L - 1) == 0 for L in lengths): fails.append([m, k])
    return fails


def v_sidorenko(p):
    Hn, HE = graph_spec(p['H']); HE = [tuple(e) for e in HE]; n = p['n']; pairs = list(combinations(range(n), 2))
    checked = bad = 0
    for mask in range(1 << len(pairs)):
        E = {frozenset(pairs[i]) for i in range(len(pairs)) if mask >> i & 1}; checked += 1
        homs = sum(1 for f in product(range(n), repeat=Hn) if all(frozenset((f[a], f[b])) in E for a, b in HE))
        if homs * n ** (2 * len(HE)) < (2 * len(E)) ** len(HE) * n ** Hn: bad += 1
    return dict(checked=checked, counterexamples=bad)


def v_hadwiger_small(p):
    n = p['n']; pairs = list(combinations(range(n), 2)); bad = 0
    for mask in range(1 << len(pairs)):
        E = {frozenset(pairs[i]) for i in range(len(pairs)) if mask >> i & 1}
        chi = next(k for k in range(1, n + 1) if any(all(c[a] != c[b] for a, b in map(tuple, E))
                                                     for c in product(range(k), repeat=n)))
        # the largest complete minor: disjoint connected branch sets, pairwise joined by an edge
        def connected(S):
            S = set(S); seen = {min(S)}; todo = [min(S)]
            while todo:
                v = todo.pop()
                for u in S:
                    if u not in seen and frozenset((u, v)) in E: seen.add(u); todo.append(u)
            return seen == S
        best = 1
        for assign in product(range(n + 1), repeat=n):  # 0 = unused, else the branch set index
            sets = [[v for v in range(n) if assign[v] == i] for i in range(1, n + 1)]
            sets = [S for S in sets if S]
            if len(sets) <= best or any(not connected(S) for S in sets): continue
            if all(any(frozenset((a, b)) in E for a in S for b in T) for S, T in combinations(sets, 2)): best = len(sets)
        if chi > best: bad += 1
    return dict(graphs=1 << len(pairs), violations=bad)


def v_balanced_pair(p):
    n = p['n']; worst = None
    for rel in product((0, 1), repeat=n * (n - 1)):
        less = {(i, j) for (i, j), b in zip(permutations(range(n), 2), rel) if b}
        if any((j, i) in less for i, j in less): continue
        if any((a, d) not in less for a, b in less for c, d in less if b == c): continue
        incomparable = [(x, y) for x, y in combinations(range(n), 2) if (x, y) not in less and (y, x) not in less]
        if not incomparable: continue
        exts = [perm for perm in permutations(range(n))
                if all(perm.index(i) < perm.index(j) for i, j in less)]
        best = max(min(F(sum(1 for e in exts if e.index(x) < e.index(y)), len(exts)),
                       1 - F(sum(1 for e in exts if e.index(x) < e.index(y)), len(exts))) for x, y in incomparable)
        worst = best if worst is None or best < worst else worst
    return [worst.numerator, worst.denominator]


def chromatic(n, E):
    adj = [set() for _ in range(n)]
    for e in E: a, b = tuple(e); adj[a].add(b); adj[b].add(a)
    order = sorted(range(n), key=lambda v: -len(adj[v]))
    def colorable(k):
        col = {}
        def go(i):
            if i == n: return True
            v = order[i]; used = {col[u] for u in adj[v] if u in col}
            for c in range(min(k, max(col.values(), default=-1) + 2)):
                if c not in used:
                    col[v] = c
                    if go(i + 1): return True
                    del col[v]
            return False
        return go(0)
    return next(k for k in range(1, n + 1) if colorable(k)) if n else 0


def v_chromatic(p):
    n, E = graph_spec(p['graph']); return chromatic(n, E)


def pmul(a, b):
    out = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b): out[i + j] += x * y
    return out


def pgcd_degree(a, b):
    a = [F(x) for x in a]; b = [F(x) for x in b]
    while b and b[-1] == 0: b.pop()
    while b:
        r = list(a)
        while len(r) >= len(b):
            c = r[-1] / b[-1]; shift = len(r) - len(b)
            for i, x in enumerate(b): r[shift + i] -= c * x
            r.pop()
            while r and r[-1] == 0: r.pop()
        a, b = b, r
    return len(a) - 1


def v_casas_alvero(p):
    d, H = p['degree'], p['h_max']; out = []
    for cs in product(range(-H, H + 1), repeat=d):
        f = list(cs) + [1]; g = f; shares = True
        for _ in range(1, d):
            g = [i * c for i, c in enumerate(g)][1:]
            if pgcd_degree(f, g) < 1: shares = False; break
        if not shares: continue
        a = F(-f[d - 1], d); power = [F(1)]
        for _ in range(d): power = pmul(power, [-a, F(1)])
        if power != [F(c) for c in f]: out.append(f)
    return out


def squarefree(n): return all(e == 1 for e in factorize(n).values()) if n > 1 else n == 1


def core(n):
    out = 1
    for q, e in factorize(n).items():
        if e % 2: out *= q
    return out


def v_congruent(p):
    N, S = p['n_max'], p['search']
    def reps(target, a, b, c):
        count = 0; X = isqrt(target // a)
        for x in range(-X, X + 1):
            r = target - a * x * x; Y = isqrt(r // b)
            for y in range(-Y, Y + 1):
                t = r - b * y * y
                if t % c == 0 and isqrt(t // c) ** 2 == t // c: count += 1 if t == 0 else 2
        return count
    cores = {}
    for m in range(2, S + 1):
        for k in range(1, m):
            if (m - k) % 2 and gcd(m, k) == 1:
                cores.setdefault(core(m * k * (m - k) * (m + k)), []).append([m, k])
    out = dict(not_congruent=[], triangle={}, tunnell_equal_only=[])
    for n in range(1, N + 1):
        if not squarefree(n): continue
        A, B = (reps(n, 2, 1, 8), reps(n, 2, 1, 32)) if n % 2 else (reps(n // 2, 4, 1, 8), reps(n // 2, 4, 1, 32))
        if A != 2 * B: out['not_congruent'].append(n)
        elif n in cores: out['triangle'][str(n)] = cores[n]
        else: out['tunnell_equal_only'].append(n)
    return out


def check_congruent(p, claimed):
    """The value names one pair (m, k) per triangle; any pair of hers from the full list verifies it."""
    got = v_congruent(p)
    if got['not_congruent'] != claimed['not_congruent'] or got['tunnell_equal_only'] != claimed['tunnell_equal_only']:
        return False
    return set(got['triangle']) == set(claimed['triangle']) and all(
        claimed['triangle'][n] in got['triangle'][n] for n in got['triangle'])


def real_class_number(d):
    """h(Q(sqrt d)): the number of cycles of reduced forms of discriminant D under the reduction operator (the narrow
    class number), halved when the fundamental unit has norm +1 (an even continued fraction period)."""
    D = d if d % 4 == 1 else 4 * d; r = isqrt(D)
    forms = set()
    for b in range(1, r + 1):
        if (b - D) % 2: continue
        prod_ = (D - b * b) // 4  # = -a c > 0
        for a in range(1, prod_ + 1):
            if prod_ % a: continue
            # reduced: sqrt D - b < 2|a| < sqrt D + b
            lo_ok = 2 * a + b > r  # 2|a| > sqrt D - b
            hi_ok = 2 * a - b < 0 or (2 * a - b) ** 2 < D  # 2|a| < sqrt D + b
            if lo_ok and hi_ok:
                c = prod_ // a
                forms.add((a, b, -c)); forms.add((-a, b, c))
    def rho(f):
        a, b, c = f; m = 2 * abs(c)
        bb = (-b) % m
        # the b' = -b (mod 2|c|) with sqrt D - 2|c| < b' < sqrt D
        bb += m * ((r - bb) // m)
        if bb > r: bb -= m
        return (c, bb, (bb * bb - D) // (4 * c))
    seen = set(); cycles = 0
    for f in sorted(forms):
        if f in seen: continue
        cycles += 1; g = f
        while g not in seen:
            seen.add(g); g = rho(g)
            if g not in forms: raise ValueError('reduction left the reduced forms at d = ' + str(d))
    # the norm of the fundamental unit: the parity of the continued fraction period of omega
    if d % 4 == 1: P, Q_, = 1, 2  # omega = (1 + sqrt d) / 2 = (P + sqrt d) / Q
    else: P, Q_ = 0, 1
    # expansion of (P + sqrt d)/Q with the reduced-period detection on (P, Q) pairs
    if (d - P * P) % Q_: d2, P, Q_ = d * Q_ * Q_, P * Q_, Q_ * Q_
    else: d2 = d
    seen_pq = {}; step = 0; s = isqrt(d2)
    while (P, Q_) not in seen_pq:
        seen_pq[(P, Q_)] = step
        a = (P + s) // Q_; P = a * Q_ - P; Q_ = (d2 - P * P) // Q_; step += 1
    period = step - seen_pq[(P, Q_)]
    return cycles if period % 2 else cycles // 2


def v_class_numbers(p):
    hist = {}
    for d in range(2, p['d_max'] + 1):
        if not squarefree(d): continue
        h = real_class_number(d); hist[h] = hist.get(h, 0) + 1
    return {str(h): c for h, c in sorted(hist.items())}


def v_erdos_hajnal(p):
    Hn, HE = graph_spec(p['H']); n = p['n']; pairs = list(combinations(range(n), 2))
    Hdeg = sorted(sum(v in e for e in HE) for v in range(Hn)); Hm = len(HE)
    def iso_to_H(S, E):
        # small H: compare by trying every bijection
        sub = {frozenset((a, b)) for a, b in combinations(S, 2) if frozenset((a, b)) in E}
        if len(sub) != Hm: return False
        return any(all((frozenset((S[i], S[j])) in sub) == (frozenset((i, j)) in HE) for i, j in combinations(range(Hn), 2))
                   for S in permutations(S))
    best = None; count = 0
    for mask in range(1 << len(pairs)):
        E = {frozenset(pairs[i]) for i in range(len(pairs)) if mask >> i & 1}
        if any(iso_to_H(list(S), E) for S in combinations(range(n), Hn)): continue
        count += 1
        clique = max(len(S) for r in range(1, n + 1) for S in combinations(range(n), r)
                     if all(frozenset(e) in E for e in combinations(S, 2)))
        indep = max(len(S) for r in range(1, n + 1) for S in combinations(range(n), r)
                    if all(frozenset(e) not in E for e in combinations(S, 2)))
        m = max(clique, indep); best = m if best is None or m < best else best
    return dict(graphs=count, least_max_clique_or_independent=best)


def coset_order(k, rels, limit):
    """Todd-Coxeter coset enumeration (the HLT strategy with coincidence handling) of the trivial subgroup."""
    letters = [g for i in range(1, k + 1) for g in (i, -i)]
    table = [dict()]; rep_ = [0]
    def find(c):
        while rep_[c] != c: rep_[c] = rep_[rep_[c]]; c = rep_[c]
        return c
    def define(c, x):
        if len(table) >= limit: raise OverflowError('coset limit')
        d = len(table); table.append(dict()); rep_.append(d); table[c][x] = d; table[d][-x] = c
    def coincidence(a, b):
        queue = []
        def merge(u, v):
            u, v = find(u), find(v)
            if u == v: return
            if u > v: u, v = v, u
            rep_[v] = u; queue.append(v)
        merge(a, b); i = 0
        while i < len(queue):
            e = queue[i]; i += 1
            for x, f in list(table[e].items()):
                table[f].pop(-x, None)
                e1, f1 = find(e), find(f)
                if x in table[e1]: merge(f1, table[e1][x])
                elif -x in table[f1]: merge(e1, table[f1][-x])
                else: table[e1][x] = f1; table[f1][-x] = e1
            table[e] = {}
    def scan_fill(c, w):
        f = b = c; i, j = 0, len(w) - 1
        while True:
            while i <= j and w[i] in table[f]: f = table[f][w[i]]; i += 1
            if i > j:
                if f != b: coincidence(f, b)
                return
            while j >= i and -w[j] in table[b]: b = table[b][-w[j]]; j -= 1
            if j < i: coincidence(f, b); return
            if i == j: table[f][w[i]] = b; table[b][-w[i]] = f; return
            define(f, w[i])
    c = 0
    while c < len(table):
        if find(c) == c:
            for w in rels:
                scan_fill(c, w)
                if find(c) != c: break
            if find(c) == c:
                for x in letters:
                    if x not in table[c]: define(c, x)
        c += 1
    return sum(1 for c in range(len(table)) if find(c) == c)


def v_coset_order(p):
    try: return coset_order(p['ngens'], [list(r) for r in p['relators']], p['limit'])
    except OverflowError: return None


def v_packing(p):
    B = p['basis']; R = p['box']; d = len(B); best = None
    for c in product(range(-R, R + 1), repeat=d):
        if any(c):
            v = [sum(c[i] * B[i][j] for i in range(d)) for j in range(d)]; n2 = sum(x * x for x in v)
            best = n2 if best is None or n2 < best else best
    # the determinant by cofactor expansion (d <= 8)
    def det(M):
        if len(M) == 1: return M[0][0]
        return sum((-1) ** j * M[0][j] * det([r[:j] + r[j + 1:] for r in M[1:]]) for j in range(len(M)) if M[0][j])
    return dict(min_norm2=best, det=abs(det(B)))


def inertia_negative(S):
    """The number of negative eigenvalues of a rational symmetric matrix, by congruence with symmetric pivoting: a
    nonzero diagonal pivot, or a 2 x 2 block [[0, b], [b, c]] (b != 0) that holds one eigenvalue of each sign."""
    M = [[F(x) for x in r] for r in S]; neg = 0
    while M:
        n = len(M)
        k = next((i for i in range(n) if M[i][i] != 0), None)
        if k is not None:
            piv = M[k][k]; neg += piv < 0
            rest = [i for i in range(n) if i != k]
            M = [[M[i][j] - M[i][k] * M[k][j] / piv for j in rest] for i in rest]
            continue
        pair = next(((i, j) for i in range(n) for j in range(i + 1, n) if M[i][j] != 0), None)
        if pair is None: break  # the rest is zero: zero eigenvalues
        i, j = pair; neg += 1
        # eliminate rows and columns i and j with the 2 x 2 block's inverse
        a, b, c = M[i][i], M[i][j], M[j][j]; det = a * c - b * b
        inv = [[c / det, -b / det], [-b / det, a / det]]
        rest = [r for r in range(n) if r not in (i, j)]
        M = [[M[r][t] - sum(M[r][u] * inv[x][y] * M[w][t] for x, u in enumerate((i, j)) for y, w in enumerate((i, j)))
              for t in rest] for r in rest]
    return neg


def v_eigen_counts(p):
    cells = [tuple(c) for c in p['cells']]; index = {c: i for i, c in enumerate(cells)}; n = len(cells)
    L = [[0] * n for _ in range(n)]
    for (x, y), i in index.items():
        for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nb in index: L[i][index[nb]] = -1; L[i][i] += 1
    return [inertia_negative([[L[i][j] - (rat(t) if i == j else 0) for j in range(n)] for i in range(n)])
            for t in p['thresholds']]


def check_eigen_counts(p, claimed):
    """A null in the claim abstains (the producer's elimination met a zero pivot); every number must be exact."""
    got = v_eigen_counts(p)
    return len(got) == len(claimed) and all(c is None or c == g for c, g in zip(claimed, got))


def canonical_code(n, E):
    """The least edge bit string over the relabelings that respect a refined vertex invariant."""
    adj = [set() for _ in range(n)]
    for e in E: a, b = tuple(e); adj[a].add(b); adj[b].add(a)
    inv = [(len(adj[v]), tuple(sorted(len(adj[u]) for u in adj[v]))) for v in range(n)]
    classes = [sorted(v for v in range(n) if inv[v] == key) for key in sorted(set(inv))]
    pairs = list(combinations(range(n), 2)); best = None
    for parts in product(*[permutations(c) for c in classes]):
        order = [v for part in parts for v in part]; pos = {v: i for i, v in enumerate(order)}
        code = sum(1 << pairs.index((min(pos[a], pos[b]), max(pos[a], pos[b]))) for a, b in map(tuple, E))
        best = code if best is None or code < best else best
    return best


def v_reconstruction(p):
    n = p['n']; pairs = list(combinations(range(n), 2)); graphs = {}
    for mask in range(1 << len(pairs)):
        E = [frozenset(pairs[i]) for i in range(len(pairs)) if mask >> i & 1]
        graphs.setdefault(canonical_code(n, E), E)
    decks = set()
    for E in graphs.values():
        deck = []
        for v in range(n):
            keep = [u for u in range(n) if u != v]; idx = {u: i for i, u in enumerate(keep)}
            deck.append(canonical_code(n - 1, [frozenset(idx[x] for x in e) for e in E if v not in e]))
        decks.add(tuple(sorted(deck)))
    return dict(graphs=len(graphs), distinct_decks=len(decks) == len(graphs))


def pi_interval(digits=40):
    d = pi_digits(digits)
    return F(int('3' + d), 10 ** digits), F(int('3' + d) + 1, 10 ** digits)


def check_circle(p, claimed):
    R = p['r_max']; lo_pi, hi_pi = pi_interval(); best_lo = F(0); uppers = {}; N = 0
    for r in range(1, R + 1):
        N = sum(2 * isqrt(r * r - x * x) + 1 for x in range(-r, r + 1))
        e1, e2 = N - lo_pi * r * r, N - hi_pi * r * r
        top = max(abs(e1), abs(e2)); bottom = F(0) if e1 * e2 <= 0 else min(abs(e1), abs(e2))
        s_lo = F(isqrt(r * 10 ** 40), 10 ** 20); s_hi = s_lo + F(1, 10 ** 20)
        uppers[r] = top / s_lo; best_lo = max(best_lo, bottom / s_hi)
    U = F(claimed['max_ratio_upper'])
    return (claimed['last_count'] == N and max(uppers.values()) <= U and uppers[claimed['at']] >= best_lo)


VALUE_RULES = {
    'tally': v_tally, 'members': v_members, 'gap_records': v_gap_records, 'goldbach': v_goldbach,
    'gilbreath': v_gilbreath, 'totient_singletons': v_totient_singletons, 'erdos_moser': v_erdos_moser,
    'euler_bricks': v_euler_bricks, 'abc_hits': v_abc_hits, 'pascal': v_pascal, 'three_cubes': v_three_cubes,
    'irregular_pairs': v_irregular_pairs, 'mersenne': v_mersenne, 'fermat': v_fermat, 'wall_sun_sun': v_wall_sun_sun,
    'reverse_add': v_reverse_add, 'affine_orbit': v_affine_orbit, 'amusical': v_amusical, 'aliquot': v_aliquot,
    'x2x3_orbits': v_x2x3, 'srg_feasible': v_srg, 'plane_orders': v_plane_orders, 'sum_product': v_sum_product,
    'four_cubes': v_four_cubes, 'sidon_max': v_sidon_max, 'unique_game': v_unique_game, 'rota_f2': v_rota,
    'frankl_small': v_frankl, 'mahler_polygon': v_mahler_polygon, 'ising': v_ising, 'point_count': v_point_count,
    'elliptic_ap': v_elliptic_ap, 'power_sums': v_power_sums, 'power_differences': v_power_differences,
    'representation_max': v_representation, 'galerkin_2d': v_galerkin, 'digit_counts': v_digit_counts,
    'distinct_cover_search': v_distinct_cover, 'chromatic_index': v_chromatic_index, 'isomorphic': v_isomorphic,
    'hadamard_orders': v_hadamard_orders, 'oriented_census': v_oriented, 'circuit_sizes': v_circuit_sizes,
    'lienard': v_lienard, 'mahler_z': v_mahler_z, 'erdos_gyarfas_gp': v_erdos_gyarfas, 'sidorenko': v_sidorenko,
    'hadwiger_small': v_hadwiger_small, 'balanced_pair': v_balanced_pair, 'chromatic': v_chromatic,
    'casas_alvero': v_casas_alvero, 'class_numbers': v_class_numbers, 'erdos_hajnal': v_erdos_hajnal,
    'coset_order': v_coset_order, 'packing': v_packing, 'reconstruction': v_reconstruction,
}


# ------------------------------------------------------------- witness and proof rules (each raises on failure)

class Fails(Exception): pass


def must(ok, why):
    if not ok: raise Fails(why)


def rat(x): return F(x) if type(x) is int else F(x[0], x[1])


def graph_spec(g):
    """(n, set of edges) for a graph specification, read independently."""
    if 'edges' in g: return g['n'], {frozenset(e) for e in g['edges']}
    name = g['named']
    if name == 'petersen': return graph_spec(dict(named='gp', n=5, k=2))
    if name == 'gp':
        m, k = g['n'], g['k']
        E = {frozenset((i, (i + 1) % m)) for i in range(m)} | {frozenset((i, i + m)) for i in range(m)}
        E |= {frozenset((m + i, m + (i + k) % m)) for i in range(m)}
        return 2 * m, E
    if name == 'cycle': return g['n'], {frozenset((i, (i + 1) % g['n'])) for i in range(g['n'])}
    if name == 'complete': return g['n'], {frozenset(e) for e in combinations(range(g['n']), 2)}
    if name == 'hypercube':
        d = g['d']; return 1 << d, {frozenset((v, v ^ (1 << b))) for v in range(1 << d) for b in range(d)}
    if name == 'paley':
        q = g['q']; R = {x * x % q for x in range(1, q)}
        return q, {frozenset((i, j)) for i, j in combinations(range(q), 2) if (j - i) % q in R}
    if name == 'cayley':
        gens = [tuple(x) for x in g['perms']]; start = tuple(range(len(gens[0])))
        elems = [start]; index = {start: 0}
        for e in elems:
            for s in gens:
                h = tuple(s[i] for i in e)
                if h not in index: index[h] = len(elems); elems.append(h)
        E = set()
        for e in elems:
            for s in gens:
                h = tuple(s[i] for i in e)
                if index[h] != index[e]: E.add(frozenset((index[e], index[h])))
        return len(elems), E
    raise LookupError('graph ' + str(name))


def w_ham_path(p, w):
    n, E = graph_spec(p['graph'])
    must(sorted(w) == list(range(n)), 'not a permutation of the vertices')
    must(all(frozenset((a, b)) in E for a, b in zip(w, w[1:])), 'consecutive vertices not adjacent')


def w_coloring(p, w):
    n, E = graph_spec(p['graph'])
    must(len(w) == n and all(0 <= c < p['k'] for c in w), 'colors')
    must(all(w[a] != w[b] for a, b in map(tuple, E)), 'an edge joins two vertices of one color')


def w_total_coloring(p, w):
    n, E = graph_spec(p['graph']); deg = [0] * n
    for e in E:
        for v in e: deg[v] += 1
    k = max(deg) + 2; vc = w['vertices']; ec = w['edges']
    must(len(vc) == n and all(0 <= c < k for c in vc), 'vertex colors')
    edge_color = {}
    for key, c in ec.items():
        a, b = map(int, key.split('-')); must(frozenset((a, b)) in E and 0 <= c < k, 'edge color'); edge_color[frozenset((a, b))] = c
    must(set(edge_color) == E, 'every edge colored once')
    for e, c in edge_color.items():
        a, b = tuple(e); must(vc[a] != vc[b] and c not in (vc[a], vc[b]), 'an edge clashes with its ends')
    for v in range(n):
        at = [c for e, c in edge_color.items() if v in e]; must(len(at) == len(set(at)), 'two edges at a vertex share a color')


def w_ramsey(p, w):
    n, s, t = p['n'], p['s'], p['t']; E = {frozenset(e) for e in w}
    must(all(len(e) == 2 and max(e) < n for e in E), 'edges')
    must(not any(all(frozenset(x) in E for x in combinations(S, 2)) for S in combinations(range(n), s)), 'a clique of size s')
    must(not any(all(frozenset(x) not in E for x in combinations(S, 2)) for S in combinations(range(n), t)),
         'an independent set of size t')


def w_cycle_double_cover(p, w):
    n, E = graph_spec(p['graph']); count = {}
    for cyc in w:
        must(len(cyc) >= 3 and len(set(cyc)) == len(cyc), 'simple cycle')
        for a, b in zip(cyc, cyc[1:] + cyc[:1]):
            e = frozenset((a, b)); must(e in E, 'not an edge'); count[e] = count.get(e, 0) + 1
    must(set(count) == E and set(count.values()) == {2}, 'not every edge covered exactly twice')


def w_prime_ap(p, w):
    a, d = w; must(d >= 1 and all(is_prime(a + i * d) for i in range(p['k'])), 'a term is not prime')


def w_sidon(p, w):
    must(len(set(w)) == p['size'] == len(w) and all(1 <= x <= p['n'] for x in w), 'set')
    sums = [a + b for a, b in combinations(sorted(w), 2)] + [2 * a for a in w]
    must(len(sums) == len(set(sums)), 'two pairs share a sum')


def w_sunflower(p, w):
    sets = [frozenset(s) for s in w]
    must(len(sets) == p['size'] == len(set(sets)) and all(len(s) == p['w'] for s in sets), 'family')
    for group in combinations(sets, p['k']):
        core = frozenset.intersection(*group)
        must(not all(a & b == core for a, b in combinations(group, 2)), 'a sunflower')


def w_hadamard(p, w):
    n = p['n']; rows = [[1 if c == '+' else -1 for c in r] for r in w]
    must(len(rows) == n and all(len(r) == n for r in rows), 'shape')
    must(all(sum(x * y for x, y in zip(rows[i], rows[j])) == (n if i == j else 0)
             for i in range(n) for j in range(i, n)), 'H H^T is not n I')


def w_projective_plane(p, w):
    q = p['q']; N = q * q + q + 1; lines = [frozenset(l) for l in w]
    must(len(lines) == N and all(len(l) == q + 1 and l <= set(range(N)) for l in lines), 'lines')
    for a, b in combinations(range(N), 2):
        must(sum(1 for l in lines if a in l and b in l) == 1, 'two points not on exactly one line')


def w_mols(p, w):
    n, k = p['n'], p['k']; must(len(w) == k, 'count')
    for L in w:
        must(all(sorted(r) == list(range(n)) for r in L) and all(sorted(L[i][j] for i in range(n)) == list(range(n))
                                                              for j in range(n)), 'not a Latin square')
    for A, B in combinations(w, 2):
        must(len({(A[i][j], B[i][j]) for i in range(n) for j in range(n)}) == n * n, 'not orthogonal')


def clauses_for(encoder, a):
    """CNF encodings written independently: variables 1..V, a list of clauses."""
    if encoder == 'php':
        n = a['n']; var = lambda i, h: i * n + h + 1
        return (n + 1) * n, [[var(i, h) for h in range(n)] for i in range(n + 1)] + \
            [[-var(i, h), -var(j, h)] for h in range(n) for i, j in combinations(range(n + 1), 2)]
    if encoder == 'ramsey':
        n, s, t = a['n'], a['s'], a['t']; ids = {e: i + 1 for i, e in enumerate(combinations(range(n), 2))}
        return len(ids), ([[-ids[e] for e in combinations(S, 2)] for S in combinations(range(n), s)] +
                          [[ids[e] for e in combinations(S, 2)] for S in combinations(range(n), t)])
    if encoder == 'schur':
        n, k = a['n'], a['k']; var = lambda i, c: (i - 1) * k + c + 1
        cl = [[var(i, c) for c in range(k)] for i in range(1, n + 1)]
        cl += [sorted({-var(x, c), -var(y, c), -var(x + y, c)}) for c in range(k) for x in range(1, n + 1)
               for y in range(x, n + 1) if x + y <= n]
        return n * k, cl
    if encoder == 'waerden':
        n, L = a['n'], a['k']; cl = []
        for s in range(1, n + 1):
            for d in range(1, n):
                ap = [s + i * d for i in range(L)]
                if ap[-1] > n: break
                cl += [ap, [-x for x in ap]]
        return n, cl
    raise LookupError('encoder ' + str(encoder))


def w_sat(p, w):
    V, cl = clauses_for(p['encoder'], p['args'])
    must(len(w) == V and set(w) <= {'0', '1'}, 'assignment')
    must(all(any((w[abs(l) - 1] == '1') == (l > 0) for l in c) for c in cl), 'an unsatisfied clause')


def unit_refutes(clauses, assumption):
    """Plain unit propagation (no watches): True when the clauses and the assumed literals reach a conflict."""
    val = {}
    for l in assumption:
        if val.get(abs(l), l > 0) != (l > 0): return True
        val[abs(l)] = l > 0
    changed = True
    while changed:
        changed = False
        for c in clauses:
            free = None; n_free = 0; sat = False
            for l in c:
                v = val.get(abs(l))
                if v is None:
                    if free != l: n_free += 1
                    free = l
                elif v == (l > 0): sat = True; break
            if sat: continue
            if n_free == 0: return True
            if n_free == 1: val[abs(free)] = free > 0; changed = True
    return False


def w_unsat(p, proof):
    V, cl = clauses_for(p['encoder'], p['args']); db = [list(set(c)) for c in cl]
    must(proof and proof[-1] == [], 'the proof does not end with the empty clause')
    must(len(proof) <= 5000, 'proof longer than this verifier replays')
    for lemma in proof:
        must(all(type(l) is int and 0 < abs(l) <= V for l in lemma), 'literal')
        must(unit_refutes(db, [-l for l in lemma]), 'a lemma does not follow by unit propagation')
        if lemma: db.append(list(set(lemma)))


def w_circuit(p, w):
    n = p['n']; size = 1 << n; wires = []
    for i in range(n): wires.append(sum(1 << r for r in range(size) if r >> (n - 1 - i) & 1))
    full = (1 << size) - 1
    for op, i, j in w:
        a, b = wires[i], wires[j]; out = 0
        for r in range(size):
            out |= (op >> (2 * (a >> r & 1) + (b >> r & 1)) & 1) << r
        wires.append(out)
    must(len(w) <= p['size'], 'gate count')
    must((wires[-1] if w else None) == p['table'] or (not w and p['table'] in wires), 'computes another function')


def w_proth(p, w):
    ks = {k for k in range(p['k_lo'], p['k_hi']) if k % 2}
    must(set(map(int, w['primes'])) | set(w['unresolved']) == ks and not set(map(int, w['primes'])) & set(w['unresolved']),
         'every odd k witnessed or unresolved')
    for key, (n, a) in w['primes'].items():
        k = int(key); N = k * 2 ** n + 1; must(1 <= n <= p['n_max'], 'n bound')
        if N < MR_BOUND: must(is_prime(N), 'k 2^n + 1 is not prime for k = ' + key)
        else: must(k < 2 ** n and pow(a, (N - 1) // 2, N) == N - 1, 'Proth test fails for k = ' + key)


def lucas_v(P, m, N):
    """V_m(P, 1) mod N by the ladder (V_j, V_(j+1))."""
    lo, hi = 2, P % N
    for bit in bin(m)[2:]:
        if bit == '1': lo, hi = (lo * hi - P) % N, (hi * hi - 2) % N
        else: lo, hi = (lo * lo - 2) % N, (lo * hi - P) % N
    return lo, hi


def jacobi_symbol(a, n):
    a %= n; t = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5): t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3: t = -t
        a %= n
    return t if n == 1 else 0


def w_riesel(p, w):
    ks = {k for k in range(p['k_lo'], p['k_hi']) if k % 2}
    must(set(map(int, w['primes'])) | set(w['unresolved']) == ks and not set(map(int, w['primes'])) & set(w['unresolved']),
         'every odd k witnessed or unresolved')
    for key, (n, P) in w['primes'].items():
        k = int(key); N = k * 2 ** n - 1; must(1 <= n <= p['n_max'], 'n bound')
        if N < MR_BOUND: must(is_prime(N), 'k 2^n - 1 is not prime for k = ' + key); continue
        must(k < 2 ** n and jacobi_symbol(P * P - 4, N) == -1, 'N+1 test conditions for k = ' + key)
        # V_((N+1)/2) = -2, and for odd q | k: U_((N+1)/q) is a unit, with U_m = (2 V_(m+1) - P V_m) / D
        must(lucas_v(P, (N + 1) // 2, N)[0] == N - 2, 'V_((N+1)/2) is not -2 for k = ' + key)
        D = (P * P - 4) % N
        for q in factorize(k):
            vm, vm1 = lucas_v(P, (N + 1) // q, N)
            must(gcd((2 * vm1 - P * vm) * pow(D, -1, N) % N, N) == 1, 'a Lucas term shares a factor with N, k = ' + key)


def w_pratt(p, cert):
    def check(m, c, depth):
        must(depth < 64, 'depth')
        if m < 1000: must(m > 1 and all(m % d for d in range(2, isqrt(m) + 1)), str(m) + ' is not prime'); return
        fs = {int(q): (e, sub) for q, (e, sub) in c['factors'].items()}
        must(prod(q ** e for q, (e, _) in fs.items()) == m - 1, 'factorization of m - 1')
        for q, (e, sub) in fs.items(): check(q, sub, depth + 1)
        a = c['a']; must(pow(a, m - 1, m) == 1 and all(pow(a, (m - 1) // q, m) != 1 for q in fs), 'order of the base')
    check(p['n'], cert, 0)


def w_covering(p, w):
    L = 1
    for r, m in w: must(m >= 2 and 0 <= r < m, 'class'); L = L * m // gcd(L, m)
    must(L <= p['lcm_max'], 'lcm bound')
    mods = [m for _, m in w]
    if p['distinct']: must(len(set(mods)) == len(mods), 'moduli repeat')
    if p['odd']: must(all(m % 2 for m in mods), 'an even modulus')
    must(all(any(x % m == r for r, m in w) for x in range(L)), 'a residue is not covered')


def w_min_modulus_covering(p, w):
    L = 1; mods = []
    for rm in w:
        must(type(rm) is list and len(rm) == 2, 'class shape'); r, m = rm
        must(type(m) is int and m >= p['m0'] and type(r) is int and 0 <= r < m, 'class'); L = L * m // gcd(L, m); mods.append(m)
    must(L <= p['lcm_max'] <= 10 ** 7, 'lcm bound'); must(len(set(mods)) == len(mods), 'moduli repeat')
    must(all(any(x % m == r for r, m in w) for x in range(L)), 'a residue is not covered')


def w_waerden_coloring(p, w):
    n, r, k = p['n'], p['r'], p['k']
    must(type(w) is str and len(w) == n and len(set(w)) <= r and set(w) <= set('0123456789abcdefghijklmnopqrstuv'[:r]), 'a color letter per number')
    for a in range(n):
        for d in range(1, (n - 1 - a) // (k - 1) + 1):
            must(len({w[a + i * d] for i in range(k)}) > 1, 'a monochromatic progression at %d with step %d' % (a + 1, d))


def w_circulant_ramsey(p, w):
    n, s, t = p['n'], p['s'], p['t']
    must(type(w) is list and w == sorted(set(w)) and all(type(d) is int and 1 <= d <= n // 2 for d in w), 'distances')
    S = set(w) | {n - d for d in w}
    nbr = [{(v + d) % n for d in S} for v in range(n)]
    non = [set(range(n)) - nbr[v] - {v} for v in range(n)]
    def clique_through_zero(adj, size):
        # the largest clique containing 0, by branch and bound; a greedy partition into independent sets bounds the rest
        def bound(P):
            classes = 0; P = set(P)
            while P:
                classes += 1; Q = set(P)
                while Q:
                    v = Q.pop(); P.discard(v); Q -= adj[v]
            return classes
        def go(have, P):
            if have >= size: return True
            if have + len(P) < size or have + bound(P) < size: return False
            P = set(P)
            while P:
                v = min(P); P.discard(v)
                if go(have + 1, P & adj[v]): return True
            return False
        return go(1, set(adj[0]))
    must(not clique_through_zero(nbr, s), 'a clique of size s through vertex 0')
    must(not clique_through_zero(non, t), 'an independent set of size t through vertex 0')


def w_sierpinski_covering(p, w):
    k, sign = p['k'], p['sign']; ps, T = w['primes'], w['period']
    must(all(is_prime(q) and pow(2, T, q) == 1 for q in ps), 'primes and period')
    must(all(any((k * pow(2, e, q) + sign) % q == 0 for q in ps) for e in range(1, T + 1)), 'an exponent class is not covered')
    must(k > max(ps), 'k does not exceed the primes')


def w_odd_weird(p, w):
    hi = p['hi']
    abundant = [n for n in range(1, hi, 2) if sigma(n) - n > n]
    must(set(w) == {str(n) for n in abundant}, 'exactly the odd abundant numbers')
    for n in abundant:
        parts = w[str(n)]
        must(len(set(parts)) == len(parts) and all(0 < d < n and n % d == 0 for d in parts) and sum(parts) == n,
             'distinct proper divisors summing to ' + str(n))


def w_lonely(p, w):
    k, S = p['k'], p['s_max']; bound = F(1, k + 1)
    for vs in combinations(range(1, S + 1), k):
        key = ','.join(map(str, vs)); must(key in w, 'no time for ' + key); t = F(w[key][0], w[key][1])
        for v in vs:
            f = (t * v) % 1; must(min(f, 1 - f) >= bound, 'speed ' + str(v) + ' too close at ' + key)


def w_kakeya(p, w):
    q, n = p['q'], p['n']; S = {tuple(x) for x in w}
    must(all(len(x) == n and all(0 <= c < q for c in x) for x in S), 'points')
    dirs = set()
    for d in product(range(q), repeat=n):
        if not any(d): continue
        lead = next(c for c in d if c); inv = pow(lead, q - 2, q)
        dirs.add(tuple(c * inv % q for c in d))
    for d in dirs:
        must(any(all(tuple((b[i] + t * d[i]) % q for i in range(n)) in S for t in range(q)) for b in S),
             'no line in direction ' + str(d))


def w_invariant_subspace(p, w):
    A = [[rat(x) for x in r] for r in p['matrix']]; n = len(A); V = [[rat(x) for x in v] for v in w]
    def rank(rows):
        rows = [list(r) for r in rows]; r = 0
        for c in range(n):
            piv = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
            if piv is None: continue
            rows[r], rows[piv] = rows[piv], rows[r]
            for i in range(len(rows)):
                if i != r and rows[i][c] != 0:
                    f = rows[i][c] / rows[r][c]; rows[i] = [x - f * y for x, y in zip(rows[i], rows[r])]
            r += 1
        return r
    must(0 < len(V) < n and rank(V) == len(V), 'dimension')
    for v in V:
        Av = [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]
        must(rank(V + [Av]) == len(V), 'not invariant')


def w_tensor(p, w):
    n, m, q = p['n'], p['m'], p['p']; must(len(w) <= p['rank'], 'rank')
    T = {}
    for A, B, C in w:
        for i, x in enumerate(A):
            for j, y in enumerate(B):
                for k, z in enumerate(C):
                    if x and y and z: T[(i, j, k)] = T.get((i, j, k), 0) + x * y * z
    want = {(i * m + j, j * q + k, k * n + i): 1 for i in range(n) for j in range(m) for k in range(q)}
    must({key: v for key, v in T.items() if v} == want, 'not the matrix multiplication tensor')


def w_ac(p, w):
    def red(word):
        out = []
        for x in word:
            if out and out[-1] == -x: out.pop()
            else: out.append(x)
        return out
    R = [red(r) for r in p['relators']]
    for mv in w:
        kind, i = mv[0], mv[1]
        if kind == 'inv': R[i] = red([-x for x in reversed(R[i])])
        elif kind == 'mul': R[i] = red(R[i] + R[1 - i])
        elif kind == 'mulinv': R[i] = red(R[i] + [-x for x in reversed(R[1 - i])])
        elif kind == 'conj': R[i] = red([mv[2]] + R[i] + [-mv[2]])
        else: raise Fails('move ' + str(kind))
    def cyc(word):
        word = red(word)
        while len(word) > 1 and word[0] == -word[-1]: word = word[1:-1]
        return word
    must(sorted(abs(cyc(r)[0]) for r in R if len(cyc(r)) == 1) == [1, 2], 'not trivialized')


def w_square(p, w):
    P = [tuple(rat(c) for c in v) for v in p['vertices']]; S = [tuple(rat(c) for c in v) for v in w]
    def on(x):
        for a, b in zip(P, P[1:] + P[:1]):
            cr = (b[0] - a[0]) * (x[1] - a[1]) - (b[1] - a[1]) * (x[0] - a[0])
            if cr == 0 and min(a[0], b[0]) <= x[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= x[1] <= max(a[1], b[1]):
                return True
        return False
    must(len(S) == 4 and all(on(x) for x in S), 'a corner is off the boundary')
    sides = [(S[(i + 1) % 4][0] - S[i][0], S[(i + 1) % 4][1] - S[i][1]) for i in range(4)]
    must(sides[0] != (0, 0) and all(sides[i + 1] in ((-sides[i][1], sides[i][0]), (sides[i][1], -sides[i][0]))
                                    for i in range(3)), 'not a square')


def w_polynomial_inverse(p, w):
    def poly(terms):
        out = {}
        for c, e in terms: out[tuple(e)] = out.get(tuple(e), 0) + rat(c)
        return {k: v for k, v in out.items() if v}
    def mul(a, b):
        out = {}
        for (i, j), x in a.items():
            for (k, l), y in b.items(): out[(i + k, j + l)] = out.get((i + k, j + l), 0) + x * y
        return {k: v for k, v in out.items() if v}
    def compose(f, g):
        out = {}
        for (i, j), c in f.items():
            t = {(0, 0): F(c)}
            for _ in range(i): t = mul(t, g[0])
            for _ in range(j): t = mul(t, g[1])
            for k, v in t.items(): out[k] = out.get(k, 0) + v
        return {k: v for k, v in out.items() if v}
    Fm = [poly(f) for f in p['F']]; G = [poly(g) for g in w]; X, Y = {(1, 0): 1}, {(0, 1): 1}
    must([compose(f, G) for f in Fm] == [X, Y] and [compose(g, Fm) for g in G] == [X, Y], 'not a two-sided inverse')


def area2(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def w_heilbronn(p, w):
    P = [tuple(rat(c) for c in v) for v in w]; A = rat(p['area'])
    must(len(P) == p['n'] and all(0 <= x <= 1 and 0 <= y <= 1 for x, y in P), 'points in the unit square')
    must(all(abs(area2(a, b, c)) >= 2 * A for a, b, c in combinations(P, 3)), 'a small triangle')


def w_no_three(p, w):
    P = [tuple(v) for v in w]; n = p['n']
    must(len(set(P)) == 2 * n == len(P) and all(0 <= x < n and 0 <= y < n for x, y in P), 'grid points')
    must(all(area2(a, b, c) != 0 for a, b, c in combinations(P, 3)), 'three in a line')


def w_convex_free(p, w):
    P = [tuple(rat(c) for c in v) for v in w]
    must(len(P) == p['n'] and all(area2(a, b, c) != 0 for a, b, c in combinations(P, 3)), 'general position')
    def convex(S):
        # in convex position when no point lies inside a triangle of the others
        for x in S:
            for a, b, c in combinations([y for y in S if y != x], 3):
                s1, s2, s3 = area2(a, b, x), area2(b, c, x), area2(c, a, x)
                if (s1 > 0) == (s2 > 0) == (s3 > 0): return False
        return True
    must(not any(convex(S) for S in combinations(P, p['k'])), 'a convex k-gon')


def w_kissing(p, w):
    must(len(w) == p['count'] and all(len(v) == p['dim'] for v in w), 'vectors')
    N = sum(x * x for x in w[0]); must(N > 0 and all(sum(x * x for x in v) == N for v in w), 'equal lengths')
    must(all(2 * sum(x * y for x, y in zip(u, v)) <= N for u, v in combinations(w, 2)), 'two vectors too close')


def w_unit_distances(p, w):
    P = [tuple(rat(c) for c in v) for v in w]
    must(len(P) == p['n'] == len(set(P)), 'distinct points')
    must(sum(1 for a, b in combinations(P, 2) if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 == 1) >= p['count'],
         'fewer unit distances')


def w_rational_distances(p, w):
    P = [tuple(rat(c) for c in v) for v in w]; must(len(P) == p['n'], 'count')
    def square(q): return q >= 0 and isqrt(q.numerator) ** 2 == q.numerator and isqrt(q.denominator) ** 2 == q.denominator
    must(all(square((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) for a, b in combinations(P, 2)), 'an irrational distance')
    must(all(area2(a, b, c) != 0 for a, b, c in combinations(P, 3)), 'three collinear')
    for S in combinations(P, 4):
        rows = [[x * x + y * y, x, y, 1] for x, y in S]
        det = lambda M: M[0][0] if len(M) == 1 else sum((-1) ** j * M[0][j] * det([r[:j] + r[j + 1:] for r in M[1:]])
                                                        for j in range(len(M)))
        must(det(rows) != 0, 'four concyclic points')


def w_borsuk(p, w):
    P = [tuple(rat(c) for c in v) for v in p['points']]; d = len(P[0])
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    D = max(d2(a, b) for a, b in combinations(P, 2))
    must(len(w) == len(P) and all(0 <= c <= d for c in w), 'parts')
    must(all(d2(P[i], P[j]) < D for i, j in combinations(range(len(P)), 2) if w[i] == w[j]), 'a part keeps the diameter')


def w_illumination(p, w):
    P = [tuple(rat(c) for c in v) for v in p['vertices']]; D = [tuple(rat(c) for c in v) for v in w]
    must(len(D) <= p['count'], 'count'); n = len(P)
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        n1 = (-(b[1] - a[1]), b[0] - a[0]); n2 = (-(c[1] - b[1]), c[0] - b[0])
        must(any(d[0] * n1[0] + d[1] * n1[1] > 0 and d[0] * n2[0] + d[1] * n2[1] > 0 for d in D), 'a dark vertex')


def w_sphere_energy(p, w):
    P = [tuple(rat(c) for c in v) for v in w]
    must(len(P) == p['n'] == len(set(P)) and all(sum(c * c for c in x) == 1 for x in P), 'points on the sphere')
    total = F(0)
    for a, b in combinations(P, 2):
        d2 = sum((x - y) ** 2 for x, y in zip(a, b))
        # 1/sqrt(d2) <= (isqrt(N 10^20 / D ... )): bound sqrt(den/num) above with 10^-12 resolution
        s = F(d2.denominator, d2.numerator); top = isqrt(s.numerator * 10 ** 24 // s.denominator) + 1
        total += F(top, 10 ** 12)
    must(total <= rat(p['energy']), 'energy above the bound')


def preorder_edges(code):
    """Edges of the rooted tree a parenthesis code describes, vertices numbered as their '(' appear."""
    edges = []; open_ = []; seen = 0
    for ch in code:
        if ch == '(':
            if open_: edges.append((open_[-1], seen))
            open_.append(seen); seen += 1
        elif ch == ')': open_.pop()
    return edges


def w_graceful(p, w):
    n = p['n']; must(n <= 12, 'tree enumeration bound of this verifier')
    trees = all_trees(n); must(set(w) == set(trees), 'one labeling for each tree')
    for code in trees:
        edges = preorder_edges(code); lab = w[code]; must(sorted(lab) == list(range(n)), 'labels')
        must(sorted(abs(lab[u] - lab[v]) for u, v in edges) == list(range(1, n)), 'not graceful')


def all_trees(n):
    """Every tree on n vertices up to isomorphism, grown one leaf at a time from the single vertex and keyed by the
    code the claims use: the least parenthesis code of the tree rooted at a center."""
    level = {'()': []}
    for size in range(1, n):
        nxt = {}
        for edges in level.values():
            for v in range(size):
                grown = edges + [(v, size)]; nxt.setdefault(tree_code(size + 1, grown), grown)
        level = nxt
    return level


def tree_code(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges: adj[a].append(b); adj[b].append(a)
    layer = [v for v in range(n) if len(adj[v]) <= 1]; left = n; deg = [len(a) for a in adj]; removed = set()
    while left > 2:
        left -= len(layer); nxt = []
        for v in layer:
            removed.add(v)
            for u in adj[v]:
                if u not in removed:
                    deg[u] -= 1
                    if deg[u] == 1: nxt.append(u)
        layer = nxt
    centers = [v for v in range(n) if v not in removed]
    def enc(v, parent): return '(' + ''.join(sorted(enc(u, v) for u in adj[v] if u != parent)) + ')'
    return min(enc(c, -1) for c in centers)


def w_unit_distance_graph(p, w):
    a, b, k = p['a'], p['b'], p['colors']
    def mul(x, y):
        return (x[0] * y[0] + a * x[1] * y[1] + b * x[2] * y[2] + a * b * x[3] * y[3],
                x[0] * y[1] + x[1] * y[0] + b * (x[2] * y[3] + x[3] * y[2]),
                x[0] * y[2] + x[2] * y[0] + a * (x[1] * y[3] + x[3] * y[1]),
                x[0] * y[3] + x[3] * y[0] + x[1] * y[2] + x[2] * y[1])
    # the four coordinates are independent over Q only when a, b and ab are not squares
    must(all(isqrt(v) ** 2 != v for v in (a, b, a * b)), 'Q(sqrt a, sqrt b) is not of degree 4')
    pts = [[tuple(rat(x) for x in c) for c in pt] for pt in w['points']]; n = len(pts)
    E = set()
    for u, v in w['edges']:
        dx = tuple(x - y for x, y in zip(pts[u][0], pts[v][0])); dy = tuple(x - y for x, y in zip(pts[u][1], pts[v][1]))
        s2 = tuple(x + y for x, y in zip(mul(dx, dx), mul(dy, dy)))
        must(s2 == (1, 0, 0, 0), 'an edge is not of length 1'); E.add(frozenset((u, v)))
    must(chromatic(n, E) >= k, 'colorable with fewer colors')


def w_rational_points(p, w):
    for pt in w:
        x, y = rat(pt[0]), rat(pt[1]); must(y * y == x ** 3 + p['a'] * x + p['b'], 'a point is off the curve')


WITNESS_RULES = {
    'ham_path': w_ham_path, 'coloring': w_coloring, 'total_coloring': w_total_coloring, 'ramsey_coloring': w_ramsey,
    'cycle_double_cover': w_cycle_double_cover, 'prime_ap': w_prime_ap, 'sidon_set': w_sidon,
    'sunflower_free': w_sunflower, 'hadamard': w_hadamard, 'projective_plane': w_projective_plane, 'mols': w_mols,
    'sat': w_sat, 'circuit': w_circuit, 'proth_primes': w_proth, 'riesel_primes': w_riesel, 'covering': w_covering,
    'sierpinski_covering': w_sierpinski_covering, 'odd_weird': w_odd_weird, 'lonely_runner': w_lonely,
    'min_modulus_covering': w_min_modulus_covering, 'waerden_coloring': w_waerden_coloring, 'circulant_ramsey': w_circulant_ramsey,
    'kakeya_set': w_kakeya, 'invariant_subspace': w_invariant_subspace, 'tensor': w_tensor, 'ac_trivial': w_ac,
    'inscribed_square': w_square, 'polynomial_inverse': w_polynomial_inverse, 'heilbronn': w_heilbronn,
    'no_three_in_line': w_no_three, 'convex_free': w_convex_free, 'kissing': w_kissing, 'unit_distances': w_unit_distances,
    'rational_distances': w_rational_distances, 'borsuk': w_borsuk, 'illumination': w_illumination,
    'sphere_energy': w_sphere_energy, 'graceful_trees': w_graceful, 'unit_distance_graph': w_unit_distance_graph,
    'rational_points': w_rational_points,
}
PROOF_RULES = {'unsat': w_unsat, 'pratt': w_pratt}


def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'))


def verdict(kind, data):
    """(VERIFIED | REFUTED | UNRESOLVED, detail) for one window claim."""
    try:
        family, params = data['family'], data['params']
        if kind == 'value':
            if family in ('eigen_counts', 'circle_errors'):
                ok = (check_eigen_counts if family == 'eigen_counts' else check_circle)(params, data['value'])
                return ('VERIFIED', 'independent recomputation agrees') if ok else \
                    ('REFUTED', 'independent exact recomputation disagrees')
            if family == 'congruent':
                return (('VERIFIED', 'independent recomputation agrees') if check_congruent(params, data['value'])
                        else ('REFUTED', 'independent Tunnell counts or triangle cores differ'))
            rule = VALUE_RULES.get(family)
            if rule is None: return 'UNRESOLVED', 'no independent rule for the family ' + family
            got = rule(params)
            if canonical(got) == canonical(data['value']): return 'VERIFIED', 'independent recomputation agrees'
            return 'REFUTED', 'independent recomputation gives ' + canonical(got)[:200]
        rules = WITNESS_RULES if kind == 'witness' else PROOF_RULES
        rule = rules.get(family)
        if rule is None: return 'UNRESOLVED', 'no independent rule for the family ' + family
        rule(params, data[kind])
        return 'VERIFIED', 'the ' + kind + ' passes an independent check'
    except Fails as exc: return 'REFUTED', str(exc)[:200]
    except (LookupError, OverflowError, TypeError, ValueError, ZeroDivisionError, AttributeError) as exc:
        return 'UNRESOLVED', 'outside this verifier: ' + type(exc).__name__ + ': ' + str(exc)[:120]


def self_test():
    """Known-true and known-false window claims; the verifier must tell them apart."""
    cases = [
        ('value', dict(family='tally', params=dict(pred=['prime', 'n'], lo=2, bounds=[100, 1000]), value=[25, 168]), 'VERIFIED'),
        ('value', dict(family='tally', params=dict(pred=['prime', 'n'], lo=2, bounds=[100]), value=[26]), 'REFUTED'),
        ('value', dict(family='mersenne', params=dict(p_max=130), value=[2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127]), 'VERIFIED'),
        ('witness', dict(family='hadamard', params=dict(n=4), witness=['++++', '+-+-', '++--', '+--+']), 'VERIFIED'),
        ('witness', dict(family='hadamard', params=dict(n=4), witness=['++++', '+-+-', '++--', '++-+']), 'REFUTED'),
        ('proof', dict(family='unsat', params=dict(encoder='php', args=dict(n=1)), proof=[[]]), 'VERIFIED'),
        ('proof', dict(family='unsat', params=dict(encoder='php', args=dict(n=2)), proof=[[]]), 'REFUTED'),
        ('witness', dict(family='tensor', params=dict(n=1, m=1, p=1, rank=1), witness=[[[1], [1], [1]]]), 'VERIFIED'),
        ('witness', dict(family='tensor', params=dict(n=1, m=1, p=1, rank=1), witness=[[[1], [1], [2]]]), 'REFUTED'),
    ]
    results = [verdict(kind, data)[0] == want for kind, data, want in cases]
    return all(results), len(results)
