"""Real-number windows: rigorous interval arithmetic and the families built on it.

An interval is a pair of integers [a, b] read as [a / 2^P, b / 2^P] at a fixed precision P; every operation rounds
outward, and every series is summed with an explicit bound on its tail, so a computed interval always contains the
true value. Families here compute values from such intervals (signs of the Hardy Z-function, digits of pi, certified
exclusions of small rationals) and report only what the intervals decide. Loaded by window_check.py, which passes
its namespace as CORE.
"""
from fractions import Fraction as Q
from math import comb, gcd, isqrt

core = CORE  # noqa: F821 (set by window_check before this module runs)
family, need, integer, Invalid = core.family, core.need, core.integer, core.Invalid


# ------------------------------------------------------------- real intervals at precision P

class I:
    """[a, b] / 2^P with integers a <= b."""
    __slots__ = ('a', 'b', 'P')

    def __init__(self, a, b, P):
        self.a, self.b, self.P = a, b, P

    @staticmethod
    def exact(q, P):
        q = Q(q); s = q.numerator << P
        return I(s // q.denominator, -((-s) // q.denominator), P)

    def __add__(self, o):
        o = _lift(o, self.P); return I(self.a + o.a, self.b + o.b, self.P)

    __radd__ = __add__

    def __neg__(self): return I(-self.b, -self.a, self.P)

    def __sub__(self, o):
        o = _lift(o, self.P); return I(self.a - o.b, self.b - o.a, self.P)

    def __rsub__(self, o): return _lift(o, self.P) - self

    def __mul__(self, o):
        o = _lift(o, self.P); P = self.P
        ps = (self.a * o.a, self.a * o.b, self.b * o.a, self.b * o.b)
        return I(min(ps) >> P, -((-max(ps)) >> P), P)

    __rmul__ = __mul__

    def inv(self):
        need(self.a > 0 or self.b < 0, 'division by an interval containing 0')
        P = self.P; one = 1 << (2 * P)
        if self.a > 0: return I(one // self.b, -((-one) // self.a), P)
        return -((-self).inv())

    def __truediv__(self, o): return self * _lift(o, self.P).inv()

    def __rtruediv__(self, o): return _lift(o, self.P) * self.inv()

    def mid(self): return (self.a + self.b) >> 1

    def rad(self): return (self.b - self.a + 1) >> 1

    def lo(self): return Q(self.a, 1 << self.P)

    def hi(self): return Q(self.b, 1 << self.P)

    def positive(self): return self.a > 0

    def negative(self): return self.b < 0

    def sign(self): return 1 if self.a > 0 else -1 if self.b < 0 else 0

    def abs_hi(self): return max(abs(self.a), abs(self.b))

    def widen(self, r): return I(self.a - r, self.b + r, self.P)

    def hull(self, o): return I(min(self.a, o.a), max(self.b, o.b), self.P)


def _lift(x, P):
    if isinstance(x, I): return x
    return I.exact(x, P)


def sqrt_i(x):
    need(x.b >= 0, 'square root of a negative interval')
    P = x.P
    return I(isqrt(max(x.a, 0) << P), isqrt(x.b << P) + 1, P)


_CONST = {}


def _atan_recip(k, P):
    """atan(1/k) for an integer k >= 2 as an interval: alternating series, tail below the first omitted term."""
    G = P + 20; one = 1 << G; total = 0; term = one // k; n = 0; k2 = k * k
    while term:
        total += term // (2 * n + 1) if n % 2 == 0 else -(term // (2 * n + 1)); term //= k2; n += 1
    err = n + 4  # each truncated division loses under one unit
    return I((total - err) >> 20, ((total + err) >> 20) + 1, P)


def pi_i(P):
    key = ('pi', P)
    if key not in _CONST: _CONST[key] = 16 * _atan_recip(5, P + 8) - 4 * _atan_recip(239, P + 8)
    v = _CONST[key]
    return I(v.a >> 8, -((-v.b) >> 8), P) if v.P == P + 8 else v


def _atanh_recip(k, P):
    """atanh(1/k) = sum 1/((2j+1) k^(2j+1)) for integer k >= 2, positive terms, tail by a geometric bound."""
    G = P + 20; one = 1 << G; total = 0; term = one // k; j = 0; k2 = k * k
    while term:
        total += term // (2 * j + 1); term //= k2; j += 1
    err = j + 4 + (one // k2 ** j if j else 0)
    return I((total - err) >> 20, ((total + err) >> 20) + 1, P)


def ln2_i(P):
    key = ('ln2', P)
    if key not in _CONST: _CONST[key] = 2 * _atanh_recip(3, P)
    return _CONST[key]


def log_point(q, P):
    """ln(q) for a positive rational q: q = 2^e y with y in [3/4, 3/2), ln y = 2 atanh((y-1)/(y+1)), |z| <= 1/5."""
    q = Q(q); need(q > 0, 'logarithm of a nonpositive number')
    e = q.numerator.bit_length() - q.denominator.bit_length()
    y = q / Q(2) ** e
    while y >= Q(3, 2): y /= 2; e += 1
    while y < Q(3, 4): y *= 2; e -= 1
    z = (y - 1) / (y + 1); G = P + 24
    zi = I.exact(z, G); z2 = zi * zi; term = zi; total = I(0, 0, G); j = 0
    while True:
        total = total + term * I.exact(Q(1, 2 * j + 1), G)
        term = term * z2; j += 1
        if term.abs_hi() < 4: break
    # tail: sum over later terms is at most |z|^(2j+1)/(2j+1) / (1 - z^2) <= 2 |term| here
    tail = 2 * term.abs_hi() + 4
    total = total.widen(tail)
    out = 2 * total + e * ln2_i(G)
    return I(out.a >> 24, -((-out.b) >> 24), P)


def log_i(x):
    need(x.a > 0, 'logarithm of an interval reaching 0')
    lo = log_point(x.lo(), x.P); hi = log_point(x.hi(), x.P)
    return I(lo.a, hi.b, x.P)


def exp_point(q, P):
    """exp(q) for a rational q: exp(q) = exp(q / 2^s)^(2^s) with |q / 2^s| <= 1/2 and a Taylor tail bound."""
    q = Q(q); s = 0
    while abs(q) > Q(1, 2): q /= 2; s += 1
    G = P + 24 + 2 * s
    x = I.exact(q, G); term = I.exact(1, G); total = I.exact(1, G); k = 1
    while True:
        term = term * x * I.exact(Q(1, k), G); total = total + term; k += 1
        if term.abs_hi() < 4: break
    total = total.widen(2 * term.abs_hi() + 4)  # later terms: |x|^k / k! summed, at most twice the last
    for _ in range(s): total = total * total
    return I(total.a >> (G - P), -((-total.b) >> (G - P)), P)


def exp_i(x):
    lo = exp_point(x.lo(), x.P); hi = exp_point(x.hi(), x.P)
    return I(lo.a, hi.b, x.P)


def _sincos_small(q, P):
    """(sin q, cos q) for a rational |q| <= 1 by Taylor series with tails bounded by the last term."""
    G = P + 24; x = I.exact(q, G); x2 = x * x
    s_term, c_term = x, I.exact(1, G); s, c = s_term, c_term; k = 1
    while True:
        s_term = -(s_term * x2 * I.exact(Q(1, (2 * k) * (2 * k + 1)), G))
        c_term = -(c_term * x2 * I.exact(Q(1, (2 * k - 1) * (2 * k)), G))
        s, c = s + s_term, c + c_term; k += 1
        if max(s_term.abs_hi(), c_term.abs_hi()) < 4: break
    tail = 2 * max(s_term.abs_hi(), c_term.abs_hi()) + 4
    s, c = s.widen(tail), c.widen(tail)
    return I(s.a >> 24, -((-s.b) >> 24), P), I(c.a >> 24, -((-c.b) >> 24), P)


def sincos_i(x):
    """(sin x, cos x): reduce the midpoint by multiples of pi/2 and halve it, then widen by the radius (Lipschitz 1)."""
    P = x.P; G = P + 32
    m = Q(x.mid(), 1 << P); r = x.rad() + 2
    half_pi = pi_i(G) * I.exact(Q(1, 2), G)
    k = int(m / Q(half_pi.mid(), 1 << G)) if m >= 0 else -int(-m / Q(half_pi.mid(), 1 << G)) - 1
    y = I.exact(m, G) - k * half_pi  # y = m - k pi/2, a small interval
    halvings = 0; ym = y
    while abs(Q(ym.mid(), 1 << G)) > Q(1, 4): ym = ym * I.exact(Q(1, 2), G); halvings += 1
    s, c = _sincos_small(Q(ym.mid(), 1 << G), G)
    s, c = s.widen(ym.rad() + 2), c.widen(ym.rad() + 2)
    for _ in range(halvings):
        s, c = 2 * s * c, 2 * c * c - 1
    for _ in range(k % 4):
        s, c = c, -s
    s, c = s.widen((r << (G - P)) + 4), c.widen((r << (G - P)) + 4)
    return I(s.a >> (G - P), -((-s.b) >> (G - P)), P), I(c.a >> (G - P), -((-c.b) >> (G - P)), P)


def atan_point(q, P):
    """atan(q) for a rational q: atan(x) = pi/2 - atan(1/x) for |x| > 1, halving by atan(x) = 2 atan(x / (1 +
    sqrt(1 + x^2))) until |x| <= 1/8, then the alternating Taylor series."""
    q = Q(q)
    if q < 0: return -atan_point(-q, P)
    G = P + 32
    if q > 1: return pi_i(P) * I.exact(Q(1, 2), P) - atan_point(1 / q, P)
    x = I.exact(q, G); doublings = 0
    while x.hi() > Q(1, 8):
        x = x / (1 + sqrt_i(1 + x * x)); doublings += 1
    x2 = x * x; term = x; total = x; k = 1
    while True:
        term = -(term * x2); t = term * I.exact(Q(1, 2 * k + 1), G); total = total + t; k += 1
        if t.abs_hi() < 4: break
    total = total.widen(2 * term.abs_hi() + 4)
    total = total * (1 << doublings)
    return I(total.a >> (G - P), -((-total.b) >> (G - P)), P)


def atan_i(x):
    lo = atan_point(x.lo(), x.P); hi = atan_point(x.hi(), x.P)
    return I(lo.a, hi.b, x.P)


# ------------------------------------------------------------- complex intervals

class C:
    __slots__ = ('re', 'im')

    def __init__(self, re, im): self.re, self.im = re, im

    def __add__(self, o):
        o = _clift(o, self.re.P); return C(self.re + o.re, self.im + o.im)

    __radd__ = __add__

    def __sub__(self, o):
        o = _clift(o, self.re.P); return C(self.re - o.re, self.im - o.im)

    def __neg__(self): return C(-self.re, -self.im)

    def __mul__(self, o):
        o = _clift(o, self.re.P)
        return C(self.re * o.re - self.im * o.im, self.re * o.im + self.im * o.re)

    __rmul__ = __mul__

    def abs2(self): return self.re * self.re + self.im * self.im

    def inv(self):
        d = self.abs2(); return C(self.re / d, -self.im / d)

    def __truediv__(self, o): return self * _clift(o, self.re.P).inv()

    def abs_hi(self):
        """An upper bound on |z| as a rational."""
        return sqrt_i(self.abs2()).hi()


def _clift(x, P):
    if isinstance(x, C): return x
    if isinstance(x, I): return C(x, I(0, 0, P))
    return C(I.exact(x, P), I(0, 0, P))


def cexp_i(theta):
    """e^(i theta) for a real interval theta."""
    s, c = sincos_i(theta); return C(c, s)


# ------------------------------------------------------------- Bernoulli numbers (exact)

_BERN = [Q(1)]


def bernoulli(n):
    while len(_BERN) <= n:
        m = len(_BERN)
        _BERN.append(-sum(comb(m + 1, k) * _BERN[k] for k in range(m)) / (m + 1))
    return _BERN[n]


# ------------------------------------------------------------- log Gamma, theta, zeta

def imlog_gamma(re, im, P):
    """Im log Gamma(re + i im) for re > 0 (a rational point): shift until |w| >= 16, then Stirling with the remainder
    bound |R_K| <= |B_2K| sec^(2K)(arg w / 2) / (2K (2K - 1) |w|^(2K-1)) (DLMF 5.11(ii))."""
    re, im = Q(re), Q(im); need(re > 0, 'right half plane')
    G = P + 32; shift = 0; total = I(0, 0, G)
    while re + shift < 16 and (re + shift) ** 2 + im ** 2 < 256:
        total = total - _arg_point(re + shift, im, G); shift += 1
    wr, wi = re + shift, im
    w = C(I.exact(wr, G), I.exact(wi, G))
    logw = C(log_i(sqrt_i(w.abs2())), _arg_point(wr, wi, G))
    main = (w - Q(1, 2)) * logw - w  # Im of (1/2) ln(2 pi) is zero
    K = 12; winv = w.inv(); w2inv = winv * winv; power = winv; series = C(I(0, 0, G), I(0, 0, G))
    for k in range(1, K):
        series = series + power * I.exact(bernoulli(2 * k) / (2 * k * (2 * k - 1)), G); power = power * w2inv
    absw = Q(isqrt(int((wr * wr + wi * wi) * 10 ** 12)), 10 ** 6)  # a lower bound on |w|
    sec2 = 2 / (1 + wr / (absw + 1))  # sec^2(arg w / 2) = 2 |w| / (|w| + Re w) <= 2 / (1 + Re w / (|w| + 1))
    bound = abs(bernoulli(2 * K)) * sec2 ** K / (2 * K * (2 * K - 1) * absw ** (2 * K - 1))
    out = (total + main.im + series.im).widen(int(bound * (1 << G)) + 4)
    return I(out.a >> 32, -((-out.b) >> 32), P)


def _arg_point(x, y, P):
    """arg(x + i y) for x > 0: atan(y / x)."""
    return atan_point(Q(y) / Q(x), P)


def theta_i(t, P):
    """The Riemann-Siegel theta function: Im log Gamma(1/4 + i t/2) - (t/2) ln pi."""
    t = Q(t)
    return imlog_gamma(Q(1, 4), t / 2, P) - I.exact(t / 2, P) * log_i(pi_i(P))


_LOGN = {}


def _log_int(n, P):
    key = (n, P)
    if key not in _LOGN:
        if len(_LOGN) > 20_000: _LOGN.clear()
        _LOGN[key] = log_point(n, P)
    return _LOGN[key]


def zeta_half(t, P, budget, a=None):
    """zeta(1/2 + i t) (or, with a in (0, 1], the Hurwitz zeta(1/2 + i t, a)) by Euler-Maclaurin with N terms and
    M corrections; the remainder is at most the first omitted correction times |s + 2M + 1| / (sigma + 2M + 1)."""
    t = Q(t); s = C(I.exact(Q(1, 2), P), I.exact(t, P))
    # the corrections shrink by about (|s| / (2 pi N))^2 each: N grows with the precision asked
    N = int(abs(t) * P / 192) + 20; M = min(40, P // 4)
    total = C(I(0, 0, P), I(0, 0, P))
    offset = Q(0) if a is None else Q(a)
    for n in range(1 if a is None else 0, N):
        budget.use(40)
        x = Q(n) + offset
        lg = _log_int(n, P) if a is None else log_point(x, P)
        # x^(-s) = x^(-1/2) (cos(t ln x) - i sin(t ln x))
        sn, cs = sincos_i(I.exact(t, P) * lg)
        mag = sqrt_i(I.exact(x, P)).inv()  # x^(-1/2)
        total = total + C(mag * cs, -(mag * sn))
    X = Q(N) + offset
    lX = log_point(X, P); sn, cs = sincos_i(I.exact(t, P) * lX); mX = sqrt_i(I.exact(X, P)).inv()
    Xs = C(mX * cs, -(mX * sn))  # X^(-s)
    total = total + Xs * I.exact(X, P) / (s - 1) + Xs * I.exact(Q(1, 2), P)
    # T_k = B_2k/(2k)! s(s+1)...(s+2k-2) X^(-s-2k+1) = B_2k/(2k)! X^(-s) w_k with w_k = s...(s+2k-2) / X^(2k-1),
    # kept as one moderate quantity so that fixed-point rounding stays small
    w = s * I.exact(1 / X, P); invX2 = I.exact(1 / (X * X), P)
    for k in range(1, M + 1):
        budget.use(20)
        total = total + Xs * w * I.exact(bernoulli(2 * k) / _fact(2 * k), P)
        w = w * (s + (2 * k - 1)) * (s + 2 * k) * invX2
    # first omitted correction: |B_(2M+2)|/(2M+2)! |w_(M+1)| |X^-s|, and |X^-s| = X^(-1/2)
    omitted = abs(bernoulli(2 * M + 2)) / _fact(2 * M + 2) * w.abs_hi() / _sqrt_lo(X)
    factor = (Q(1, 2) + 2 * M + 1 + abs(t)) / (Q(1, 2) + 2 * M + 1)
    r = int(omitted * factor * (1 << P)) + 4
    return C(total.re.widen(r), total.im.widen(r))


def _fact(n):
    out = 1
    for i in range(2, n + 1): out *= i
    return out


def _sqrt_lo(x):
    """A positive rational lower bound on sqrt(x)."""
    x = Q(x); return Q(isqrt(x.numerator * x.denominator * 10 ** 12), x.denominator * 10 ** 6)


def hardy_z(t, P, budget):
    """Z(t) = e^(i theta(t)) zeta(1/2 + i t), real; the real part of the product interval."""
    z = zeta_half(t, P, budget) * cexp_i(theta_i(t, P))
    return z.re


def z_sign(t, budget):
    for P in (96, 192, 384):
        s = hardy_z(t, P, budget).sign()
        if s: return s
    return 0


@family('zeta_q', 'zeta_signs', 'value',
        'The sign of the Hardy function Z(t) at t = t0 + j h for j = 0..count-1 (+, - or ? where 96 to 384 bits do '
        'not decide it), and the number of sign changes between decided neighbours: each is a zero of zeta on the '
        'critical line, so zeta has at least that many zeros with real part 1/2 there.')
def fam_zeta_signs(params, budget):
    need(set(params) == {'t0', 'h', 'count'}, 'zeta sign fields')
    t0, h = _rat(params['t0']), _rat(params['h']); n = integer(params['count'], 2, 4000)
    need(0 < t0 and 0 < h and t0 + h * n <= 2000, 'range of t')
    signs = []
    for j in range(n): signs.append({1: '+', -1: '-', 0: '?'}[z_sign(t0 + j * h, budget)])
    decided = [c for c in signs if c != '?']
    changes = sum(1 for x, y in zip(decided, decided[1:]) if x != y)
    return dict(signs=''.join(signs), changes=changes)


@family('config_q', 'sphere_energy', 'witness',
        'The witness places n distinct points with rational coordinates exactly on the unit sphere whose Coulomb '
        'energy, the sum over pairs of 1/distance, is at most the stated bound (each term bounded above by an exact '
        'rational): an upper bound on the least energy of n points (Thomson\'s problem).')
def fam_sphere_energy(params, witness, budget):
    need(set(params) == {'n', 'energy'}, 'energy fields'); n = integer(params['n'], 2, 200); E = _rat(params['energy'])
    need(type(witness) is list and len(witness) == n, 'point count'); P = []
    for pt in witness:
        need(type(pt) is list and len(pt) == 3, 'point'); x = tuple(_rat(c) for c in pt)
        need(x[0] ** 2 + x[1] ** 2 + x[2] ** 2 == 1, 'a point is not on the unit sphere'); P.append(x)
    need(len(set(P)) == n, 'distinct points')
    units = 0  # the energy bound in units of 10^-15
    for i in range(n):
        for j in range(i + 1, n):
            budget.use(4)
            d2 = sum((a - b) ** 2 for a, b in zip(P[i], P[j])); a, b = d2.numerator, d2.denominator
            # 1/sqrt(d2) = sqrt(a b)/a <= (isqrt(a b 10^30) + 1)/(a 10^15)
            units += -(-(isqrt(a * b * 10 ** 30) + 1) // a)
    need(Q(units, 10 ** 15) <= E, 'the energy exceeds the stated bound')
    return dict(energy_upper=_frac_str(Q(units, 10 ** 15), 9))


@family('zeta_q', 'zeta_max', 'value',
        'Over the grid t = t0 + j h (j = 0..count-1): the point where the certified lower bound on |zeta(1/2 + i t)| = '
        '|Z(t)| is largest, with that lower bound and the matching upper bound (decimal, rounded toward zero): a '
        'certified lower bound on the largest value of |zeta| on the critical line over [t0, t0 + (count - 1) h].')
def fam_zeta_max(params, budget):
    need(set(params) == {'t0', 'h', 'count'}, 'zeta size fields')
    t0, h = _rat(params['t0']), _rat(params['h']); n = integer(params['count'], 1, 2000)
    need(0 < t0 and 0 < h and t0 + h * n <= 1000, 'range of t')
    best = None
    for j in range(n):
        z = hardy_z(t0 + j * h, 96, budget); lo, hi = z.lo(), z.hi()
        low = max(lo, -hi, 0); top = max(abs(lo), abs(hi))
        if best is None or low > best[0]: best = (low, top, t0 + j * h)
    return dict(at=[best[2].numerator, best[2].denominator], lower=_frac_str(best[0], 9), upper=_frac_str(best[1] + Q(1, 10 ** 9), 9))


@family('zeta_q', 'zero_count_bound', 'value',
        'An upper bound on N(T), the number of zeros of zeta with 0 < Im s < T, from N(T) = theta(T)/pi + 1 + S(T) and '
        'Trudgian\'s bound |S(T)| <= 0.112 ln T + 0.278 ln ln T + 2.510 (T >= e), with the interval for theta.')
def fam_zero_count_bound(params, budget):
    need(set(params) == {'T'}, 'zero count fields'); T = _rat(params['T']); need(3 <= T <= 10 ** 6, 'height')
    P = 96; th = theta_i(T, P) / pi_i(P); lT = log_point(T, P); llT = log_i(lT)
    S = I.exact(Q(112, 1000), P) * lT + I.exact(Q(278, 1000), P) * llT + I.exact(Q(2510, 1000), P)
    top = (th + 1 + S).hi()
    return dict(upper=int(top), theta_over_pi=[_frac_str(th.lo()), _frac_str(th.hi())])


def _rat(x):
    if type(x) is int: return Q(x)
    need(type(x) is list and len(x) == 2 and all(type(v) is int for v in x) and x[1] > 0, 'rational pair')
    return Q(x[0], x[1])


def _frac_str(q, digits=12):
    """A decimal string rounded toward zero (for display of interval ends; the ends are the claim)."""
    s = '-' if q < 0 else ''; q = abs(q); whole = int(q); frac = int((q - whole) * 10 ** digits)
    return s + str(whole) + '.' + str(frac).rjust(digits, '0')


# ------------------------------------------------------------- Dirichlet L-function of the character mod 4

def l4_z(t, P, budget):
    """Z(t, chi_4) = e^(i theta(t)) L(1/2 + i t, chi_4), real: L(s, chi_4) = 4^(-s) (zeta(s, 1/4) - zeta(s, 3/4)) and
    theta(t) = Im log Gamma(3/4 + i t/2) + (t/2) ln(4/pi) (odd character of conductor 4, root number 1)."""
    t = Q(t)
    a = zeta_half(t, P, budget, Q(1, 4)); b = zeta_half(t, P, budget, Q(3, 4))
    l4 = log_point(4, P); sn, cs = sincos_i(I.exact(t, P) * l4); m = I.exact(Q(1, 2), P)  # 4^(-1/2)
    four = C(m * cs, -(m * sn))  # 4^(-s)
    L = four * (a - b)
    th = imlog_gamma(Q(3, 4), t / 2, P) + I.exact(t / 2, P) * (l4 - log_i(pi_i(P)))
    return (L * cexp_i(th)).re


@family('zeta_q', 'l4_signs', 'value',
        'The sign of Z(t, chi_4), the real form of the Dirichlet L-function of the nontrivial character mod 4 on the '
        'critical line, at t = t0 + j h (? where undecided), and its sign changes: each is a zero of L(s, chi_4) with '
        'real part 1/2.')
def fam_l4_signs(params, budget):
    need(set(params) == {'t0', 'h', 'count'}, 'L sign fields')
    t0, h = _rat(params['t0']), _rat(params['h']); n = integer(params['count'], 2, 2000)
    need(0 < t0 and 0 < h and t0 + h * n <= 500, 'range of t')
    signs = []
    for j in range(n):
        sg = 0
        for P in (96, 192):
            sg = l4_z(t0 + j * h, P, budget).sign()
            if sg: break
        signs.append({1: '+', -1: '-', 0: '?'}[sg])
    decided = [c for c in signs if c != '?']
    return dict(signs=''.join(signs), changes=sum(1 for x, y in zip(decided, decided[1:]) if x != y))


# ------------------------------------------------------------- lattice points and the divisor problem

@family('zeta_q', 'circle_errors', 'value',
        'For integers 1 <= r <= r_max: N(r) = #{(x, y) : x^2 + y^2 <= r^2} exactly, and an upper bound on the largest '
        '|N(r) - pi r^2| / r^(1/2), with the r where it occurs (Gauss circle problem; the conjectured exponent is 1/2).')
def fam_circle_errors(params, budget):
    need(set(params) == {'r_max'}, 'circle fields'); R = integer(params['r_max'], 1, 20_000)
    P = 80; pi = pi_i(P); best = (Q(-1), 0); last = 0
    for r in range(1, R + 1):
        budget.use(r)
        N = 0; r2 = r * r
        for x in range(-r, r + 1): N += 2 * isqrt(r2 - x * x) + 1
        E = I.exact(N, P) - pi * r2
        ratio = I(-(max(abs(E.a), abs(E.b))), max(abs(E.a), abs(E.b)), P).hi() / _sqrt_lo(r)
        if ratio > best[0]: best = (ratio, r)
        last = N
    return dict(max_ratio_upper=_frac_str(best[0] + Q(1, 10 ** 12)), at=best[1], last_count=last)


def euler_gamma_i(P):
    """gamma = H_n - ln n - 1/(2n) + sum_{k<=M} B_2k / (2k n^2k), remainder at most |B_(2M+2)| / ((2M+2) n^(2M+2))."""
    key = ('gamma', P)
    if key in _CONST: return _CONST[key]
    n = P // 4 + 10; M = P // 4 + 4; G = P + 16
    H = sum(Q(1, k) for k in range(1, n + 1))
    corr = sum(bernoulli(2 * k) / (2 * k * Q(n) ** (2 * k)) for k in range(1, M + 1))
    rem = abs(bernoulli(2 * M + 2)) / ((2 * M + 2) * Q(n) ** (2 * M + 2))
    v = I.exact(H - Q(1, 2 * n) + corr, G) - log_point(n, G)
    v = v.widen(int(rem * (1 << G)) + 2)
    _CONST[key] = I(v.a >> 16, -((-v.b) >> 16), P)
    return _CONST[key]


@family('zeta_q', 'divisor_errors', 'value',
        'For x = step, 2 step, ..., x_max: D(x) = sum of the divisor counts d(n) for n <= x exactly, and an upper bound '
        'on the largest |D(x) - x ln x - (2 gamma - 1) x| / x^(1/4) among these x (Dirichlet divisor problem).')
def fam_divisor_errors(params, budget):
    need(set(params) == {'x_max', 'step'}, 'divisor fields')
    X, S = integer(params['x_max'], 2, 2_000_000), integer(params['step'], 1)
    need(X // S <= 2000, 'checkpoint count')
    P = 96; g = euler_gamma_i(P); D = 0; n = 0; best = (Q(-1), 0)
    budget.use(X)
    tau = [0] * (X + 1)
    for d in range(1, X + 1):
        for m in range(d, X + 1, d): tau[m] += 1
    for x in range(S, X + 1, S):
        while n < x: n += 1; D += tau[n]
        E = I.exact(D, P) - I.exact(x, P) * log_point(x, P) - (2 * g - 1) * x
        q4 = Q(isqrt(isqrt(x * 10 ** 24)), 10 ** 6)  # a lower bound on x^(1/4)
        ratio = Q(max(abs(E.a), abs(E.b)), 1 << P) / q4
        if ratio > best[0]: best = (ratio, x)
    return dict(max_ratio_upper=_frac_str(best[0] + Q(1, 10 ** 12)), at=best[1])


# ------------------------------------------------------------- constants

def const_i(e, P, depth=0):
    """An interval for a constant expression: integers, [num, den], e, pi, gamma, catalan, [zeta k], [log x],
    [exp x], [sqrt x], [add|sub|mul|div x y], [pow x k]."""
    need(depth < 20, 'expression depth')
    if type(e) is int: return I.exact(e, P)
    if e in ('e', 'pi', 'gamma', 'catalan', 'ln2'):
        return dict(e=lambda: exp_point(1, P), pi=lambda: pi_i(P), gamma=lambda: euler_gamma_i(P),
                    catalan=lambda: catalan_i(P), ln2=lambda: ln2_i(P))[e]()
    need(type(e) is list and e, 'constant expression')
    head = e[0]
    if all(type(x) is int for x in e) and len(e) == 2 and type(head) is int:
        need(e[1] > 0, 'denominator'); return I.exact(Q(e[0], e[1]), P)
    if head == 'zeta': return zeta_int_i(integer(e[1], 2, 64), P)
    args = [const_i(a, P, depth + 1) for a in e[1:] if not (head == 'pow' and a is e[2])]
    if head == 'add': return args[0] + args[1]
    if head == 'sub': return args[0] - args[1]
    if head == 'mul': return args[0] * args[1]
    if head == 'div': return args[0] / args[1]
    if head == 'log': return log_i(args[0])
    if head == 'exp': return exp_i(args[0])
    if head == 'sqrt': return sqrt_i(args[0])
    if head == 'pow':
        k = integer(e[2], 0, 64); out = I.exact(1, P)
        for _ in range(k): out = out * args[0]
        return out
    raise Invalid('unknown constant ' + str(head))


def catalan_i(P):
    """Catalan's constant: G = (pi / 8) ln(2 + sqrt 3) + (3/8) sum_n 1 / ((2n+1)^2 C(2n, n)) (Ramanujan), with the
    tail after N terms at most (4/3) / ((2N+1) 4^N)."""
    key = ('catalan', P)
    if key in _CONST: return _CONST[key]
    G = P + 16; N = P // 2 + 8
    s = sum(Q(1, (2 * n + 1) ** 2 * comb(2 * n, n)) for n in range(N))
    tail = Q(4, 3) / ((2 * N + 1) * 4 ** N)
    v = pi_i(G) * I.exact(Q(1, 8), G) * log_i(2 + sqrt_i(I.exact(3, G))) + I.exact(Q(3, 8) * s, G).widen(
        int(Q(3, 8) * tail * (1 << G)) + 2)
    _CONST[key] = I(v.a >> 16, -((-v.b) >> 16), P)
    return _CONST[key]


def zeta_int_i(k, P):
    """zeta(k) for an integer k >= 2 by Euler-Maclaurin in exact rationals; for real s > 1 the remainder is at most
    the first omitted correction."""
    key = ('zeta', k, P)
    if key in _CONST: return _CONST[key]
    N = P // 4 + 20; M = P // 5 + 10; G = P + 16
    total = I(0, 0, G)
    for n in range(1, N): total = total + I.exact(Q(1, n ** k), G)
    X = Q(N)
    total = total + I.exact(X ** (1 - k) / (k - 1) + X ** (-k) / 2, G)
    rising = Q(k)  # k (k+1) ... (k + 2j - 2)
    for j in range(1, M + 1):
        total = total + I.exact(bernoulli(2 * j) / _fact(2 * j) * rising / X ** (k + 2 * j - 1), G)
        rising *= (k + 2 * j - 1) * (k + 2 * j)
    omitted = abs(bernoulli(2 * M + 2)) / _fact(2 * M + 2) * rising / X ** (k + 2 * M + 1)
    total = total.widen(int(omitted * (1 << G)) + 2)
    _CONST[key] = I(total.a >> 16, -((-total.b) >> 16), P)
    return _CONST[key]


def simplest_rational(lo, hi):
    """The rational with the smallest denominator in [lo, hi] (lo <= hi): an integer if one lies there, else found on
    the reciprocal interval (the Stern-Brocot descent)."""
    a = lo.numerator // lo.denominator
    if a == lo or a + 1 <= hi: return Q(a) if a == lo else Q(a + 1)
    return a + 1 / simplest_rational(1 / (hi - a), 1 / (lo - a))


@family('const_q', 'enclosure', 'value',
        'Decimal bounds lo <= x <= hi on the constant, to the requested number of digits, from an interval computed with '
        'rigorous error bounds.')
def fam_enclosure(params, budget):
    need(set(params) == {'expr', 'digits'}, 'enclosure fields'); d = integer(params['digits'], 1, 2000)
    P = int(d * 3.33) + 40; budget.use(P * P // 64)
    v = const_i(params['expr'], P)
    lo = v.lo(); hi = v.hi(); scale = 10 ** d
    return dict(lo=_dec(lo, d, floor=True), hi=_dec(hi, d, floor=False))


def _dec(q, d, floor):
    scale = 10 ** d; x = q * scale
    n = x.numerator // x.denominator if floor else -((-x.numerator) // x.denominator)
    s = '-' if n < 0 else ''; n = abs(n)
    return s + str(n // scale) + '.' + str(n % scale).rjust(d, '0')


@family('const_q', 'no_small_rational', 'value',
        'Whether the constant differs from every rational p/q with 1 <= q <= q_max: decided by an interval containing '
        'the constant whose simplest rational has a larger denominator (reported, with its size in digits).')
def fam_no_small_rational(params, budget):
    need(set(params) == {'expr', 'q_max'}, 'rational exclusion fields'); qmax = integer(params['q_max'], 1, 10 ** 200)
    P = 2 * qmax.bit_length() + 64; budget.use(P * P // 64)
    v = const_i(params['expr'], P)
    s = simplest_rational(v.lo(), v.hi())
    return dict(excluded=s.denominator > qmax, simplest_denominator_digits=len(str(s.denominator)))


@family('const_q', 'cf_prefix', 'value',
        'The partial quotients of the continued fraction of the constant that an interval containing it certifies, '
        'up to the requested count (fewer when the interval does not decide more).')
def fam_cf_prefix(params, budget):
    need(set(params) == {'expr', 'terms'}, 'continued fraction fields'); k = integer(params['terms'], 1, 2000)
    P = 8 * k + 64; budget.use(P * P // 64)
    v = const_i(params['expr'], P); lo, hi = v.lo(), v.hi(); out = []
    while len(out) < k:
        a = lo.numerator // lo.denominator
        if hi.numerator // hi.denominator != a or lo == a: break
        out.append(a)
        lo, hi = 1 / (hi - a), 1 / (lo - a)
    return out


@family('const_q', 'no_small_relation', 'value',
        'Whether c0 + c1 x + c2 y = 0 has no solution in integers with 0 < max |c_i| <= h_max, for the two constants x '
        'and y: every candidate (c1, c2) is excluded by an interval, or counted as undecided.')
def fam_no_small_relation(params, budget):
    need(set(params) == {'exprs', 'h_max'}, 'relation fields'); H = integer(params['h_max'], 1, 400)
    xs = params['exprs']; need(type(xs) is list and len(xs) == 2, 'two constants')
    P = 3 * H.bit_length() + 80
    x, y = const_i(xs[0], P), const_i(xs[1], P); undecided = 0
    for c1 in range(0, H + 1):
        for c2 in range(-H, H + 1):
            if c1 == 0 and c2 <= 0: continue  # one of each pair +-(c1, c2); (0, 0) needs c0 = 0
            budget.use(4)
            v = x * c1 + y * c2
            lo, hi = v.lo(), v.hi()
            c = -(lo.numerator // lo.denominator)  # an integer c0 with c0 + v = 0 must lie in [-hi, -lo]
            if any(abs(c0) <= H for c0 in range(-(hi.numerator // hi.denominator) - 1, c + 2)
                   if -hi <= c0 <= -lo):
                undecided += 1
    return dict(excluded=undecided == 0, undecided=undecided)


@family('const_q', 'no_small_polynomial', 'value',
        'Whether no nonzero integer polynomial of the given total degree in the listed constants, with coefficients of '
        'size at most h_max, vanishes at them: every coefficient vector is excluded by an interval, or counted as '
        'undecided.')
def fam_no_small_polynomial(params, budget):
    need(set(params) == {'exprs', 'degree', 'h_max'}, 'polynomial fields')
    xs = params['exprs']; need(type(xs) is list and 1 <= len(xs) <= 2, 'one or two constants')
    d, H = integer(params['degree'], 1, 6), integer(params['h_max'], 1, 20)
    P = 64 + 8 * d * H.bit_length() + 16 * d
    vals = [const_i(x, P) for x in xs]
    monos = [(i, j) for i in range(d + 1) for j in range(d + 1 - i)] if len(xs) == 2 else [(i, 0) for i in range(d + 1)]
    need(len(monos) <= 10 and (2 * H + 1) ** len(monos) <= 3_000_000, 'enumeration bound')
    one = I.exact(1, P)
    def power(v, k):
        out = one
        for _ in range(k): out = out * v
        return out
    mv = [power(vals[0], i) * (power(vals[1], j) if len(xs) == 2 else one) for i, j in monos]
    from itertools import product
    undecided = 0
    for cs in product(range(-H, H + 1), repeat=len(monos)):
        first = next((c for c in cs if c), 0)
        if first <= 0: continue  # skip zero and one of each sign pair
        budget.use(len(cs))
        total = I(0, 0, P)
        for c, m in zip(cs, mv):
            if c: total = total + m * c
        if total.a <= 0 <= total.b: undecided += 1
    return dict(excluded=undecided == 0, undecided=undecided, monomials=len(monos))


@family('digits_q', 'digit_counts', 'value',
        'The first n decimal digits after the point of the constant, certified by an interval, and how often each digit '
        'and each pair of consecutive digits occurs among them.')
def fam_digit_counts(params, budget):
    need(set(params) == {'expr', 'n'}, 'digit fields'); n = integer(params['n'], 10, 100_000)
    P = int(n * 3.33) + 64; budget.use(P * P // 256)
    v = const_i(params['expr'], P); scale = 10 ** n
    lo, hi = v.lo() * scale, v.hi() * scale
    a, b = lo.numerator // lo.denominator, hi.numerator // hi.denominator
    need(a == b, 'the interval does not decide the digits')
    digits = _digit_string(a % scale, n)
    counts = [digits.count(str(i)) for i in range(10)]
    pairs = {}
    for i in range(n - 1): pairs[digits[i:i + 2]] = pairs.get(digits[i:i + 2], 0) + 1
    return dict(counts=counts, pairs=dict(sorted(pairs.items())), first=digits[:20], last=digits[-20:])


def _digit_string(x, k):
    """The k decimal digits of 0 <= x < 10^k, split in halves so no conversion exceeds 2000 digits."""
    if k <= 2000: return str(x).rjust(k, '0')
    h = k // 2; q, r = divmod(x, 10 ** h)
    return _digit_string(q, k - h) + _digit_string(r, h)


# ------------------------------------------------------------- exact real sets

@family('interval_q', 'mahler_z', 'value',
        'The exact set of x in [lo, hi) with frac(x (3/2)^n) in [0, 1/2) for every n < steps (Mahler\'s Z-numbers must '
        'lie in it for every number of steps): its number of intervals and total length, and the first step at which it '
        'is empty (then there is no Z-number in [lo, hi)).')
def fam_mahler_z(params, budget):
    need(set(params) == {'lo', 'hi', 'steps'}, 'Z-number fields')
    lo, hi = _rat(params['lo']), _rat(params['hi']); N = integer(params['steps'], 1, 200)
    need(0 < lo < hi <= 10 ** 6, 'interval')
    cur = [(lo, hi)]; empty_at = None; r = Q(1)
    for n in range(N):
        nxt = []
        for a, b in cur:
            k0 = int(a / r); k1 = int(b / r) + 1
            need(k1 - k0 < 100_000, 'piece bound')
            for k in range(k0, k1 + 1):
                budget.use()
                u, v = max(a, k * r), min(b, (k + Q(1, 2)) * r)
                if u < v: nxt.append((u, v))
        cur = nxt; r = r * Q(2, 3)
        need(len(cur) <= 200_000, 'interval count bound')
        if not cur: empty_at = n; break
    length = sum((b - a for a, b in cur), Q(0))
    return dict(intervals=len(cur), length=[length.numerator, length.denominator], empty_at=empty_at)


# ------------------------------------------------------------- Diophantine approximation

def _dist_interval(n, a, S=1 << 80):
    """An interval of rationals containing ||n sqrt(a)||, the distance to the nearest integer."""
    v = isqrt(a * n * n * S * S)
    lo, hi = Q(v, S), Q(v + 1, S)
    m = round(lo)
    d_lo = 0 if lo <= m <= hi else min(abs(lo - m), abs(hi - m))
    d_hi = max(abs(lo - m), abs(hi - m))
    return d_lo, d_hi


@family('approx_q', 'littlewood', 'value',
        'For x = sqrt(a) and y = sqrt(b): the n <= n_max minimizing an upper bound on n ||n x|| ||n y|| and that bound '
        '(Littlewood conjectured the lim inf is 0 for all real x, y).')
def fam_littlewood(params, budget):
    need(set(params) == {'a', 'b', 'n_max'}, 'Littlewood fields')
    a, b, N = integer(params['a'], 2, 10 ** 6), integer(params['b'], 2, 10 ** 6), integer(params['n_max'], 1, 200_000)
    need(isqrt(a) ** 2 != a and isqrt(b) ** 2 != b, 'non-squares')
    best = (None, 0)
    for n in range(1, N + 1):
        budget.use(8)
        up = n * _dist_interval(n, a)[1] * _dist_interval(n, b)[1]
        if best[0] is None or up < best[0]: best = (up, n)
    return dict(n=best[1], upper=_frac_str(best[0] + Q(1, 10 ** 15), 15))


@family('approx_q', 'lonely_runner', 'witness',
        'For every set of k distinct positive integer speeds at most s_max, the witness gives a rational time t with '
        '||t v|| >= 1/(k + 1) for every speed v (the lonely runner conjecture for these speed sets).')
def fam_lonely_runner(params, witness, budget):
    need(set(params) == {'k', 's_max'}, 'lonely runner fields')
    k, S = integer(params['k'], 1, 8), integer(params['s_max'], 1, 40)
    from itertools import combinations
    sets = list(combinations(range(1, S + 1), k))
    need(len(sets) <= 200_000 and type(witness) is dict and len(witness) == len(sets), 'one time per speed set')
    bound = Q(1, k + 1)
    for vs in sets:
        key = ','.join(map(str, vs)); need(key in witness, 'no time for ' + key)
        t = _rat(witness[key]); budget.use(k)
        for v in vs:
            f = (t * v) % 1
            need(min(f, 1 - f) >= bound, 'the time for ' + key + ' leaves speed ' + str(v) + ' too close')
    return dict(speed_sets=len(sets))


# ------------------------------------------------------------- dynamics

@family('dynamics_q', 'mandelbrot', 'value',
        'For the size x size grid c = center + (i - size/2, j - size/2) spacing: points certified in the Mandelbrot set '
        '(main cardioid or period-2 disk, exact inequalities), certified outside (an interval iterate with |z| > 2 '
        'within the iteration bound), and undecided, with the grid as characters.')
def fam_mandelbrot(params, budget):
    need(set(params) == {'center', 'spacing', 'size', 'iters'}, 'Mandelbrot fields')
    cx, cy = (_rat(v) for v in params['center']); h = _rat(params['spacing'])
    n, T = integer(params['size'], 1, 200), integer(params['iters'], 1, 2000)
    P = 64; rows = []; counts = {'in': 0, 'out': 0, 'undecided': 0}
    for j in range(n):
        row = ''
        for i in range(n):
            x = cx + (i - Q(n, 2)) * h; y = cy + (j - Q(n, 2)) * h; budget.use(4)
            q = (x - Q(1, 4)) ** 2 + y * y
            if q * (q + (x - Q(1, 4))) < y * y / 4 or (x + 1) ** 2 + y * y < Q(1, 16):
                row += '#'; counts['in'] += 1; continue
            zr, zi = I(0, 0, P), I(0, 0, P); cr, ci = I.exact(x, P), I.exact(y, P); out = False
            for _ in range(T):
                budget.use(6)
                zr, zi = zr * zr - zi * zi + cr, 2 * zr * zi + ci
                m2 = zr * zr + zi * zi
                if m2.a > (4 << P): out = True; break
                if zr.b - zr.a > (1 << (P - 8)): break  # the interval lost its precision: undecided
            if out: row += '.'; counts['out'] += 1
            else: row += '?'; counts['undecided'] += 1
        rows.append(row)
    return dict(counts=counts, grid=rows)


@family('dynamics_q', 'x2x3_orbits', 'value',
        'The orbits of the fractions a/q (0 < a < q) under x -> 2x and x -> 3x mod 1 for q prime to 6: the sizes of the '
        'minimal invariant sets, which are the finite invariant sets Furstenberg\'s conjecture allows.')
def fam_x2x3(params, budget):
    need(set(params) == {'q'}, 'orbit fields'); q = integer(params['q'], 5, 200_000)
    need(q % 2 and q % 3, 'q prime to 6')
    seen = bytearray(q); sizes = {}
    for a in range(1, q):
        if seen[a]: continue
        stack = [a]; seen[a] = 1; size = 0
        while stack:
            x = stack.pop(); size += 1; budget.use()
            for y in (2 * x % q, 3 * x % q):
                if not seen[y]: seen[y] = 1; stack.append(y)
        sizes[str(size)] = sizes.get(str(size), 0) + 1
    return dict(sorted(sizes.items(), key=lambda kv: int(kv[0])))


def _sturm_count(p, lo, hi):
    """The number of distinct real roots of a rational polynomial p (lowest degree first) in (lo, hi], by Sturm."""
    def ev(f, x):
        out = Q(0)
        for c in reversed(f): out = out * x + c
        return out
    def deriv(f): return [i * c for i, c in enumerate(f)][1:]
    def rem(f, g):
        f = list(f)
        while len(f) >= len(g) and any(f):
            c = f[-1] / g[-1]; s = len(f) - len(g)
            for i, gc in enumerate(g): f[s + i] -= c * gc
            f.pop()
            while f and f[-1] == 0: f.pop()
        return f
    seq = [list(p), deriv(p)]
    while seq[-1] and len(seq[-1]) > 1:
        r = rem(seq[-2], seq[-1])
        if not r: break
        seq.append([-c for c in r])
    def changes(x):
        vals = [ev(f, x) for f in seq if f]
        vals = [v for v in vals if v != 0]
        return sum(1 for u, v in zip(vals, vals[1:]) if (u > 0) != (v > 0))
    return changes(lo) - changes(hi)


@family('dynamics_q', 'lienard', 'value',
        'For x\' = y - eps F(x), y\' = -x with F the listed polynomial: the number of simple positive zeros u of the '
        'averaged function sum over odd k of a_k C(k+1, (k+1)/2) u^((k-1)/2) / 2^(k+1) (u = r^2); each gives a hyperbolic '
        'limit cycle near the circle of radius sqrt(u) for all small eps > 0.')
def fam_lienard(params, budget):
    need(set(params) == {'coeffs'}, 'Lienard fields'); cs = params['coeffs']
    need(type(cs) is list and 2 <= len(cs) <= 40 and all(type(c) is int for c in cs), 'integer coefficients a_0..a_n')
    p = [Q(0)] * ((len(cs) + 1) // 2 + 1)
    for k, a in enumerate(cs):
        if k % 2 == 1 and a: p[(k - 1) // 2] += Q(a * comb(k + 1, (k + 1) // 2), 2 ** (k + 1))
    while len(p) > 1 and p[-1] == 0: p.pop()
    budget.use(len(p) ** 3)
    if len(p) <= 1: return dict(simple_positive_zeros=0, degree=0)
    # squarefree part: distinct positive roots of p; simple roots are those not shared with p'
    total = _sturm_count(p, Q(0), Q(10 ** 12) + sum(abs(c) for c in p) / abs(p[-1]) * 10 ** 6)
    dp = [i * c for i, c in enumerate(p)][1:]
    g = _pgcd(p, dp)
    multiple = _sturm_count(g, Q(0), Q(10 ** 12) + sum(abs(c) for c in p) / abs(p[-1]) * 10 ** 6) if len(g) > 1 else 0
    return dict(simple_positive_zeros=total - multiple, degree=len(p) - 1)


def _pgcd(a, b):
    a, b = list(a), list(b)
    while b and any(b):
        while b and b[-1] == 0: b.pop()
        f = list(a)
        while len(f) >= len(b) and any(f):
            c = f[-1] / b[-1]; s = len(f) - len(b)
            for i, bc in enumerate(b): f[s + i] -= c * bc
            f.pop()
            while f and f[-1] == 0: f.pop()
        a, b = b, f
    return a


# ------------------------------------------------------------- spectra, lattice models, operators

def inertia_below(A, x, budget):
    """The number of eigenvalues of the rational symmetric matrix A below x: negative pivots of A - x I (Sylvester),
    or None when a zero pivot appears."""
    n = len(A); M = [[Q(A[i][j]) - (x if i == j else 0) for j in range(n)] for i in range(n)]; neg = 0
    for k in range(n):
        piv = M[k][k]
        if piv == 0: return None
        if piv < 0: neg += 1
        budget.use((n - k) ** 2)
        for i in range(k + 1, n):
            f = M[i][k] / piv
            if f:
                for j in range(k + 1, n): M[i][j] -= f * M[k][j]
    return neg


def grid_laplacian(cells):
    """The graph Laplacian (Neumann) of a set of unit cells joined across shared edges."""
    need(type(cells) is list and 1 <= len(cells) <= 400, 'cells')
    idx = {}
    for c in cells:
        need(type(c) is list and len(c) == 2 and all(type(v) is int for v in c), 'cell'); idx[tuple(c)] = len(idx)
    n = len(idx); A = [[0] * n for _ in range(n)]
    for (x, y), i in idx.items():
        for nb in ((x + 1, y), (x, y + 1)):
            j = idx.get(nb)
            if j is not None: A[i][j] = A[j][i] = -1; A[i][i] += 1; A[j][j] += 1
    return A


@family('spectrum_q', 'eigen_counts', 'value',
        'For the Neumann graph Laplacian of the listed grid domain: the number of eigenvalues below each listed '
        'threshold (exact inertia; null where a threshold is itself decisive only with pivoting).')
def fam_eigen_counts(params, budget):
    need(set(params) == {'cells', 'thresholds'}, 'eigenvalue fields')
    A = grid_laplacian(params['cells'])
    ts = params['thresholds']; need(type(ts) is list and 1 <= len(ts) <= 64, 'thresholds')
    return [inertia_below(A, _rat(t), budget) for t in ts]


def ising_counts(L, M, budget):
    """Configurations of the L x M periodic Ising model by number of unsatisfied bonds: a transfer matrix over rows
    with integer polynomial entries (index = unsatisfied bonds)."""
    states = range(1 << L)
    def row_bad(s): return sum(((s >> i) & 1) != ((s >> ((i + 1) % L)) & 1) for i in range(L)) if L > 1 else 0
    def between(s, t): return bin(s ^ t).count('1')
    total = [0] * (2 * L * M + 1)
    for start in states:
        vec = {start: [0] * 0 + [1]}
        vec = {start: _shift([1], row_bad(start))}
        for step in range(M - 1):
            nxt = {}
            for s, poly in vec.items():
                for t in states:
                    budget.use(len(poly))
                    add = _shift(poly, between(s, t) + row_bad(t))
                    cur = nxt.get(t, [])
                    nxt[t] = [(cur[i] if i < len(cur) else 0) + (add[i] if i < len(add) else 0) for i in range(max(len(cur), len(add)))]
            vec = nxt
        for s, poly in vec.items():
            closing = _shift(poly, between(s, start))
            for i, c in enumerate(closing): total[i] += c
    while total and total[-1] == 0: total.pop()
    return total


def _shift(poly, k): return [0] * k + list(poly)


@family('lattice_q', 'ising', 'value',
        'The number of spin configurations of the L x M periodic Ising model with each number of unsatisfied bonds (the '
        'partition function as an integer polynomial in x = e^(-2 beta)).')
def fam_ising(params, budget):
    need(set(params) == {'L', 'M'}, 'Ising fields')
    L, M = integer(params['L'], 1, 5), integer(params['M'], 2, 10)
    return ising_counts(L, M, budget)


@family('lattice_q', 'galerkin_2d', 'value',
        'For the 2D Euler equations truncated to wave vectors 0 < |k|^2 <= K^2: every triad k + p + q = 0 inside the '
        'truncation conserves energy (sum |w_k|^2 / |k|^2) and enstrophy (sum |w_k|^2) exactly; the number of triads, '
        'and whether each identity holds for all of them.')
def fam_galerkin(params, budget):
    need(set(params) == {'K'}, 'Galerkin fields'); K = integer(params['K'], 1, 12)
    modes = [(a, b) for a in range(-K, K + 1) for b in range(-K, K + 1) if 0 < a * a + b * b <= K * K]
    S = set(modes); triads = 0; energy = enstrophy = True
    def cross(p, q): return p[0] * q[1] - p[1] * q[0]
    def n2(p): return p[0] * p[0] + p[1] * p[1]
    for p in modes:
        for q in modes:
            k = (-p[0] - q[0], -p[1] - q[1])
            if k not in S or not (p < q < k): continue
            triads += 1; budget.use(8)
            # the interaction coefficient of the pair (a, b) on the third mode: c(a, b) = cross(a, b) (1/|b|^2 - 1/|a|^2)
            def c(a, b): return cross(a, b) * (Q(1, n2(b)) - Q(1, n2(a)))
            ck, cp, cq = c(p, q), c(q, k), c(k, p)
            if ck + cp + cq != 0: enstrophy = False
            if ck / n2(k) + cp / n2(p) + cq / n2(q) != 0: energy = False
    return dict(triads=triads, energy=energy, enstrophy=enstrophy)


@family('operator_q', 'invariant_subspace', 'witness',
        'The witness vectors span a subspace of Q^n of dimension strictly between 0 and n that the listed rational matrix '
        'maps into itself.')
def fam_invariant_subspace(params, witness, budget):
    need(set(params) == {'matrix'}, 'operator fields'); A = params['matrix']
    need(type(A) is list and 2 <= len(A) <= 40 and all(type(r) is list and len(r) == len(A) for r in A), 'square matrix')
    n = len(A); A = [[_rat(x) for x in r] for r in A]
    need(type(witness) is list and 1 <= len(witness) < n, 'between 1 and n - 1 vectors')
    V = [[_rat(x) for x in v] for v in witness]
    need(all(len(v) == n for v in V), 'vector length')
    need(_rank(V) == len(V), 'the vectors are not independent')
    for v in V:
        Av = [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]; budget.use(n * n)
        need(_rank(V + [Av]) == len(V), 'the image of a basis vector leaves the span')
    return dict(dimension=len(V), n=n)


def _rank(rows):
    M = [list(r) for r in rows]; rank = 0; cols = len(M[0]) if M else 0
    for c in range(cols):
        piv = next((i for i in range(rank, len(M)) if M[i][c] != 0), None)
        if piv is None: continue
        M[rank], M[piv] = M[piv], M[rank]
        for i in range(len(M)):
            if i != rank and M[i][c] != 0:
                f = M[i][c] / M[rank][c]; M[i] = [a - f * b for a, b in zip(M[i], M[rank])]
        rank += 1
    return rank


# ------------------------------------------------------------- the volume conjecture window

def clausen2_i(theta, P):
    """Cl2(theta) = theta - theta ln theta + sum_k c_k theta^(2k+1), c_k = |B_2k| / (2k (2k+1)!), for 0 < theta < 2 pi.
    Each term is the previous one times theta^2 c_(k+1) / c_k, so the terms stay moderate; with |B_2k| <= 4 (2k)! /
    (2 pi)^(2k) they shrink by at least (theta / 2 pi)^2 < 1/2 here, so the tail is at most twice the last term."""
    t = theta; t2 = t * t
    need(t.hi() < 5, 'theta below 5')
    c = lambda k: abs(bernoulli(2 * k)) / (2 * k * _fact(2 * k + 1))
    term = t * t2 * I.exact(c(1), t.P); out = t - t * log_i(t) + term; k = 1
    while term.abs_hi() >= 4 or k < 4:
        term = term * t2 * I.exact(c(k + 1) / c(k), t.P); out = out + term; k += 1
        need(k < 400, 'Clausen series bound')
    return out.widen(2 * term.abs_hi() + 4)


@family('knot_q', 'kashaev_41', 'value',
        'For the figure-eight knot: 2 pi ln <4_1>_N / N with the Kashaev invariant <4_1>_N = sum_(j<N) prod_(k<=j) '
        '4 sin^2(pi k / N), and the hyperbolic volume 3 Cl2(2 pi / 3), both as decimal bounds (the volume conjecture says '
        'the first tends to the second).')
def fam_kashaev(params, budget):
    need(set(params) == {'N'}, 'Kashaev fields'); N = integer(params['N'], 2, 3000)
    # the terms prod_(k<=j) 4 sin^2(pi k / N) range over hundreds of orders of magnitude: sum them in log space,
    # L_j = sum_(k<=j) ln(4 sin^2(pi k / N)) and ln sum_j e^(L_j) = L_max + ln sum_j e^(L_j - L_max)
    P = 160; pi = pi_i(P); L = [I(0, 0, P)]
    for j in range(1, N):
        budget.use(40)
        s, _ = sincos_i(pi * I.exact(Q(j, N), P))
        L.append(L[-1] + log_i(4 * s * s))
    top = max(L, key=lambda v: v.b)
    rest = I(0, 0, P)
    for v in L: rest = rest + exp_i(v - top)
    value = 2 * pi * (top + log_i(rest)) / N
    vol = 3 * clausen2_i(2 * pi / 3, P)
    return dict(value=[_dec(value.lo(), 12, True), _dec(value.hi(), 12, False)],
                volume=[_dec(vol.lo(), 12, True), _dec(vol.hi(), 12, False)])
