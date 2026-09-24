"""Operators on sequences: all-index laws, generating functions, closed forms and periods.

A law claims a(n+r) = sum c_j a(n+j) for every n >= 0. Transfers derive the law of
a transformed sequence from checked laws by characteristic-polynomial rules:
products and sums of characteristic polynomials, shifted or scaled roots,
substitution x -> x^t, powers of companion matrices and Kronecker products. The
checker in lexicon_check.py verifies each derived law against the transformed
definition with its own agreement bound, so a wrong rule is refused, not trusted.
"""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_seq_' + name, Path(__file__).with_name(name + '.py'))
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


# ------------------------------------------------------------- helpers

def charpoly_of(law):
    """Monic characteristic polynomial x^r - sum c_j x^j, low degree first."""
    c = [L.dec(x) for x in law['coefficients']]
    return [-x for x in c] + [Q(1)]


def law_from_char(sd, P):
    """The law with characteristic polynomial P for definition sd, initial terms from the definition."""
    P = L.ptrim(P); P = L.pscale(P, 1 / P[-1]); r = len(P) - 1
    return dict(coefficients=[L.enc(-P[j]) for j in range(r)], initial=[L.enc(x) for x in L.terms(sd, r)])


def law_data(sd, P):
    return dict({'def': sd}, **law_from_char(sd, P))


def order_bound_terms(sd, count):
    return L.terms(sd, count)


def transform(op_name, args, **params):
    out = dict(type='transform', op=op_name, args=args)
    if params: out['params'] = params
    return out


def companion(law):
    c = [L.dec(x) for x in law['coefficients']]; r = len(c)
    return [[Q(1) if j == i + 1 else Q(0) for j in range(r)] if i < r - 1 else list(c) for i in range(r)]


def matmul(A, B):
    return [[sum(A[i][t] * B[t][j] for t in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def matpow(A, k):
    out = [[Q(int(i == j)) for j in range(len(A))] for i in range(len(A))]
    for _ in range(k): out = matmul(out, A)
    return out


def kron(A, B):
    return [[A[i // len(B)][j // len(B)] * B[i % len(B)][j % len(B)] for j in range(len(A) * len(B))]
            for i in range(len(A) * len(B))]


def derived(rt, source, new_def, P, others=()):
    """E then S: state the rule's law for the new sequence and let the checker admit it."""
    claim = rt.transfer('law', law_data(new_def, P), source, others)
    return [claim] if rt.check(claim) else []


def checked(rt, law):
    return law['status'] == 'checked'


# ------------------------------------------------------------- proposals

@op('seq_bm_law', 'NS', ('seq',), ('law',),
    'Berlekamp-Massey on enough exact terms proposes the shortest law; the checker decides every index.')
def seq_bm_law(rt, seq):
    sd = seq['data']['def']
    for count in (8, 16, 32, 64):
        rt.budget.use(count * count)
        c = L.berlekamp_massey(L.terms(sd, count))
        if 2 * len(c) < count: break
    claim = rt.propose('law', dict({'def': sd}, coefficients=[L.enc(x) for x in c],
                                   initial=[L.enc(x) for x in L.terms(sd, len(c))]), (seq,))
    return [claim] if rt.check(claim) else [claim]


@op('seq_poly_fit', 'NS', ('seq',), ('closed',),
    'Repeated differences that vanish propose a polynomial closed form by Newton interpolation.')
def seq_poly_fit(rt, seq):
    sd = seq['data']['def']; a = L.terms(sd, 16); rows = [a]
    while rows[-1] and any(rows[-1]) and len(rows[-1]) > 2:
        rt.budget.use(len(rows[-1])); rows.append([y - x for x, y in zip(rows[-1], rows[-1][1:])])
    if any(rows[-1]) or len(rows) > 12: return []
    coefficients = []
    for i, row in enumerate(rows[:-1]):
        coefficients = L.padd(coefficients, L.pscale(falling(i), row[0] / factorial(i)))
    claim = rt.propose('closed', {'def': sd, 'form': dict(type='poly', coefficients=[L.enc(x) for x in coefficients])},
                       (seq,))
    return [claim] if rt.check(claim) else []


def falling(i):
    out = [Q(1)]
    for j in range(i): out = L.pmul(out, [Q(-j), Q(1)])
    return out


def factorial(i):
    out = 1
    for j in range(2, i + 1): out *= j
    return out


@op('seq_expsum_fit', 'NS', ('law',), ('closed',),
    'A checked law whose characteristic polynomial has distinct rational roots gives a closed exponential sum.')
def seq_expsum_fit(rt, law):
    if not checked(rt, law): return []
    P = charpoly_of(law['data']); roots = L.rational_roots(P)
    if len(roots) != len(P) - 1 or not roots: return []
    sd = law['data']['def']; a = L.terms(sd, len(roots))
    weights = L.solve_linear([[root ** n for root in roots] for n in range(len(roots))], a)
    if weights is None: return []
    claim = rt.propose('closed', {'def': sd, 'form': dict(type='expsum', terms=[[L.enc(w), L.enc(q)]
                                                                                for w, q in zip(weights, roots) if w])},
                       (law,))
    return [claim] if rt.check(claim) else []


@op('seq_gf_from_law', 'NS', ('law',), ('gf',),
    'Q(x) = 1 - sum c_j x^(r-j) and P = Q*A mod x^r turn a checked law into a generating function.')
def seq_gf_from_law(rt, law):
    if not checked(rt, law): return []
    d = law['data']; c = [L.dec(x) for x in d['coefficients']]; a = [L.dec(x) for x in d['initial']]; r = len(c)
    Qd = [Q(1)] + [-c[r - k] for k in range(1, r + 1)]
    P = L.ptrim([sum(Qd[i] * a[k - i] for i in range(k + 1)) for k in range(r)])
    claim = rt.propose('gf', {'def': d['def'], 'numerator': [L.enc(x) for x in P],
                              'denominator': [L.enc(x) for x in L.ptrim(Qd)]}, (law,))
    return [claim] if rt.check(claim) else []


@op('seq_hyper_fit', 'NS', ('seq',), ('hyper',),
    'Fit a(n+1)/a(n) = p(n)/q(n) with linear p and q; a finite claim over the available terms.')
def seq_hyper_fit(rt, seq):
    sd = seq['data']['def']
    count = min(24, len(sd['values'])) if sd['type'] == 'terms' else 24
    a = L.terms(sd, count)
    if any(x == 0 for x in a[:-1]): return []
    # a(n+1)*(q0 + q1 n) = a(n)*(p0 + p1 n), normalised by q1 = 1 or q0 = 1.
    for fixed in ('q1', 'q0'):
        rows, rhs = [], []
        for n in range(count - 1):
            if fixed == 'q1': rows.append([a[n], a[n] * n, -a[n + 1]]); rhs.append(a[n + 1] * n)
            else: rows.append([a[n], a[n] * n, -a[n + 1] * n]); rhs.append(a[n + 1])
        sol = L.solve_linear(rows, rhs)
        if sol is None: continue
        p = [sol[0], sol[1]]; q = [sol[2], Q(1)] if fixed == 'q1' else [Q(1), sol[2]]
        claim = rt.propose('hyper', {'def': sd, 'p': [L.enc(x) for x in p], 'q': [L.enc(x) for x in q],
                                     'upto': count - 1}, (seq,))
        if rt.check(claim): return [claim]
    return []


@op('seq_mod_period', 'NS', ('seq',), ('period',),
    'Find the eventual period of an integer recurrence, matrix or word count modulo a small prime.')
def seq_mod_period(rt, seq):
    sd = seq['data']['def']; out = []
    if sd['type'] not in ('lrs', 'matrix', 'words'): return []
    if sd['type'] == 'lrs' and not all(L.dec(x).denominator == 1 for x in sd['coefficients'] + sd['initial']): return []
    for m in (2, 3, 5, 7):
        a = [int(x) % m for x in L.terms(sd, 400)]; rt.budget.use(400)
        for start in range(0, 40):
            period = next((P for P in range(1, 150) if all(a[i] == a[i + P] for i in range(start, start + 200))), None)
            if period is not None: break
        if period is None: continue
        claim = rt.propose('period', {'def': sd, 'modulus': m, 'start': start, 'period': period}, (seq,))
        if rt.check(claim): out.append(claim)
    return out


@op('seq_matrix_law', 'NS', ('seq',), ('law',),
    'Cayley-Hamilton: the characteristic polynomial of the carrier matrix is a law for u*M**n*v.')
def seq_matrix_law(rt, seq):
    sd = seq['data']['def']
    if sd['type'] not in ('matrix', 'words'): return []
    M = sd['matrix'] if sd['type'] == 'matrix' else L.word_matrix(sd['patterns'])[0]
    rt.budget.use(len(M) ** 4)
    claim = rt.propose('law', law_data(sd, L.charpoly(M)), (seq,))
    return [claim] if rt.check(claim) else []


@op('seq_lincomb', 'NS', ('seq', 'seq', 'seq'), ('closed',),
    'Solve for a(n) = u*b(n) + v*c(n) on early terms; the checker proves it for every index.')
def seq_lincomb(rt, target, first, second):
    if len({target['id'], first['id'], second['id']}) < 3: return []
    a, b, c = (L.terms(o['data']['def'], 8) for o in (target, first, second))
    sol = L.solve_linear([[b[n], c[n]] for n in range(8)], a)
    if sol is None: return []
    claim = rt.propose('closed', {'def': target['data']['def'],
                                  'form': dict(type='lincomb', defs=[first['data']['def'], second['data']['def']],
                                               coefficients=[L.enc(x) for x in sol])}, (target, first, second))
    return [claim] if rt.check(claim) else []


@op('seq_order_reduce', 'NWS', ('law',), ('law', 'refutation'),
    'Divide the characteristic polynomial by a rational linear factor; keep the lower law if it checks, refute it if not.')
def seq_order_reduce(rt, law):
    if not checked(rt, law): return []
    P = charpoly_of(law['data']); sd = law['data']['def']; out = []
    for root in L.rational_roots(P):
        lower = L.pexact(P, [-root, Q(1)])
        if lower is None: continue
        claim = rt.propose('law', law_data(sd, lower), (law,))
        if rt.check(claim): return [claim]
        R = len(lower) - 1
        for i in range(R, R + 40):
            refutation = rt.refute(claim, dict(index=i))
            if refutation is not None: out += [claim, refutation]; break
        if out: return out
    return out


# ------------------------------------------------------------- refutations

def refute_at(rt, claim, limit=80):
    for i in range(limit):
        refutation = rt.refute(claim, dict(index=i))
        if refutation is not None: return [refutation]
    return []


@op('seq_law_refute', 'WS', ('law',), ('refutation',),
    'Evaluate an unchecked law against the definition term by term; the first mismatch refutes it.')
def seq_law_refute(rt, law):
    return [] if checked(rt, law) else refute_at(rt, law)


@op('seq_law_mod_refute', 'WS', ('law',), ('refutation',),
    'Scan residues modulo 1000003 to locate a mismatch cheaply; the checker confirms it exactly.')
def seq_law_mod_refute(rt, law):
    if checked(rt, law): return []
    d = law['data']; m = 1000003
    try:
        actual = [int(x) % m for x in L.terms(d['def'], 200)]
        predicted = [int(x) % m for x in L.lrs_terms([L.dec(x) for x in d['coefficients']],
                                                    [L.dec(x) for x in d['initial']], 200)]
    except (TypeError, ValueError): return []
    rt.budget.use(400)
    for i, (x, y) in enumerate(zip(actual, predicted)):
        if x != y:
            refutation = rt.refute(law, dict(index=i))
            return [refutation] if refutation is not None else []
    return []


@op('seq_gf_refute', 'WS', ('gf',), ('refutation',),
    'Expand P/Q and compare with the definition; the first mismatch refutes the generating function.')
def seq_gf_refute(rt, gf):
    return [] if gf['status'] == 'checked' else refute_at(rt, gf)


@op('seq_closed_refute', 'WS', ('closed',), ('refutation',),
    'Evaluate a closed form against the definition; the first mismatch refutes it.')
def seq_closed_refute(rt, closed):
    return [] if closed['status'] == 'checked' else refute_at(rt, closed)


@op('seq_period_refute', 'WS', ('period',), ('refutation',),
    'Find an index past the start where the claimed period fails modulo m.')
def seq_period_refute(rt, period):
    if period['status'] == 'checked': return []
    d = period['data']
    for i in range(d['start'], d['start'] + 200):
        refutation = rt.refute(period, dict(index=i))
        if refutation is not None: return [refutation]
    return []


# ------------------------------------------------------------- transfers: laws of transformed sequences

@op('seq_shift_law', 'SE', ('law',), ('law',), 'A law for a(n) is a law for a(n+s) with shifted initial terms.')
def seq_shift_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('shift', [law['data']['def']], s=1), charpoly_of(law['data']))


@op('seq_scale_law', 'SE', ('law',), ('law',), 'A law for a(n) is a law for c*a(n).')
def seq_scale_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('scale', [law['data']['def']], c=[3, 1]), charpoly_of(law['data']))


@op('seq_sum_law', 'SE', ('law', 'law'), ('law',), 'a+b satisfies the product of the two characteristic polynomials.')
def seq_sum_law(rt, first, second):
    if not (checked(rt, first) and checked(rt, second)) or first['id'] == second['id']: return []
    return derived(rt, first, transform('sum', [first['data']['def'], second['data']['def']]),
                   L.pmul(charpoly_of(first['data']), charpoly_of(second['data'])), (second,))


@op('seq_product_law', 'SE', ('law', 'law'), ('law',),
    'a*b satisfies the characteristic polynomial of the Kronecker product of the companion matrices.')
def seq_product_law(rt, first, second):
    if not (checked(rt, first) and checked(rt, second)) or first['id'] == second['id']: return []
    A, B = companion(first['data']), companion(second['data'])
    if len(A) * len(B) > 16: return []
    rt.budget.use((len(A) * len(B)) ** 4)
    return derived(rt, first, transform('product', [first['data']['def'], second['data']['def']]),
                   L.charpoly(kron(A, B)), (second,))


@op('seq_partial_sum_law', 'SE', ('law',), ('law',), 'Partial sums satisfy the characteristic polynomial times (x-1).')
def seq_partial_sum_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('partial_sum', [law['data']['def']]), L.pmul(charpoly_of(law['data']), [Q(-1), Q(1)]))


@op('seq_difference_law', 'SE', ('law',), ('law',), 'First differences satisfy the same characteristic polynomial.')
def seq_difference_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('difference', [law['data']['def']]), charpoly_of(law['data']))


@op('seq_decimate_law', 'SE', ('law',), ('law',),
    'a(t*n+j) satisfies the characteristic polynomial of the t-th power of the companion matrix.')
def seq_decimate_law(rt, law):
    if not checked(rt, law): return []
    M = companion(law['data']); rt.budget.use(len(M) ** 4)
    return derived(rt, law, transform('decimate', [law['data']['def']], t=2, j=1), L.charpoly(matpow(M, 2)))


@op('seq_binomial_law', 'SE', ('law',), ('law',), 'The binomial transform shifts every characteristic root by +1: P(x-1).')
def seq_binomial_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('binomial', [law['data']['def']]), L.pshift(charpoly_of(law['data']), -1))


@op('seq_inverse_binomial_law', 'SE', ('law',), ('law',),
    'The inverse binomial transform shifts every characteristic root by -1: P(x+1).')
def seq_inverse_binomial_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('inverse_binomial', [law['data']['def']]), L.pshift(charpoly_of(law['data']), 1))


@op('seq_interleave_law', 'SE', ('law', 'law'), ('law',),
    'Interleaving a and b satisfies P_a(x^2)*P_b(x^2).')
def seq_interleave_law(rt, first, second):
    if not (checked(rt, first) and checked(rt, second)) or first['id'] == second['id']: return []
    square = lambda P: [P[i // 2] if i % 2 == 0 else Q(0) for i in range(2 * len(P) - 1)]
    return derived(rt, first, transform('interleave', [first['data']['def'], second['data']['def']]),
                   L.pmul(square(charpoly_of(first['data'])), square(charpoly_of(second['data']))), (second,))


@op('seq_twist_law', 'SE', ('law',), ('law',), 'c^n*a(n) has every root multiplied by c: coefficients c_j*c^(r-j).')
def seq_twist_law(rt, law):
    if not checked(rt, law): return []
    P = charpoly_of(law['data']); r = len(P) - 1; c = Q(2)
    return derived(rt, law, transform('twist', [law['data']['def']], c=[2, 1]), [P[j] * c ** (r - j) for j in range(r + 1)])


@op('seq_polymul_law', 'SE', ('law',), ('law',), 'p(n)*a(n) with p of degree d satisfies P^(d+1).')
def seq_polymul_law(rt, law):
    if not checked(rt, law): return []
    return derived(rt, law, transform('polymul', [law['data']['def']], p=[[1, 1], [1, 1]]), L.ppow(charpoly_of(law['data']), 2))


@op('seq_convolution_law', 'SE', ('law', 'law'), ('law',),
    'The Cauchy product multiplies generating functions, so it satisfies P_a*P_b for every index.')
def seq_convolution_law(rt, first, second):
    if not (checked(rt, first) and checked(rt, second)) or first['id'] == second['id']: return []
    return derived(rt, first, transform('convolution', [first['data']['def'], second['data']['def']]),
                   L.pmul(charpoly_of(first['data']), charpoly_of(second['data'])), (second,))


@op('seq_reciprocal_law', 'SE', ('law',), ('law',),
    'The reciprocal series Q/P of a rational series A=P/Q has a law read from the numerator P.')
def seq_reciprocal_law(rt, law):
    if not checked(rt, law): return []
    d = law['data']; c = [L.dec(x) for x in d['coefficients']]; a = [L.dec(x) for x in d['initial']]; r = len(c)
    if not a or a[0] == 0: return []
    Qd = [Q(1)] + [-c[r - k] for k in range(1, r + 1)]
    P = L.ptrim([sum(Qd[i] * a[k - i] for i in range(k + 1)) for k in range(r)])
    # 1/A = Q/P: an all-index law of order max(deg P, deg Q + 1) with characteristic polynomial x^pad * rev(P).
    order = max(len(P) - 1, len(L.ptrim(Qd)))
    rev = list(reversed(P + [Q(0)] * (order + 1 - len(P))))
    return derived(rt, law, transform('reciprocal', [d['def']]), rev)


@op('seq_aerate_law', 'SE', ('law',), ('law',), 'Inserting t-1 zeros between terms substitutes x -> x^t in P.')
def seq_aerate_law(rt, law):
    if not checked(rt, law): return []
    P = charpoly_of(law['data']); t = 2
    return derived(rt, law, transform('aerate', [law['data']['def']], t=t),
                   [P[i // t] if i % t == 0 else Q(0) for i in range(t * (len(P) - 1) + 1)])


@op('seq_companion_carrier', 'SE', ('law',), ('law',),
    'A checked law transfers to the matrix question u*C**n*v for its companion matrix C.')
def seq_companion_carrier(rt, law):
    if not checked(rt, law): return []
    d = law['data']; c = [L.dec(x) for x in d['coefficients']]; a = [L.dec(x) for x in d['initial']]; r = len(c)
    if not r or not all(x.denominator == 1 and abs(x) <= 10 ** 6 for x in c + a): return []
    # Row vector state (a(n), ..., a(n+r-1)) advances by the transpose companion; v picks the first entry.
    M = [[int(c[j]) if i == r - 1 else int(j == i + 1) for i in range(r)] for j in range(r)]
    sd = dict(type='matrix', matrix=M, initial=[int(x) for x in a], terminal=[1] + [0] * (r - 1))
    return derived(rt, law, sd, charpoly_of(d))


# ------------------------------------------------------------- transfers of periods, generating functions and closed forms

def gf_parts(gf):
    return [L.dec(x) for x in gf['data']['numerator']], [L.dec(x) for x in gf['data']['denominator']]


def gf_claim(rt, source, sd, P, Qd, others=()):
    scale = Qd[0]
    claim = rt.transfer('gf', {'def': sd, 'numerator': [L.enc(x / scale) for x in L.ptrim(P)] or [[0, 1]],
                               'denominator': [L.enc(x / scale) for x in L.ptrim(Qd)]}, source, others)
    return [claim] if rt.check(claim) else []


def closed_claim(rt, source, sd, form):
    claim = rt.transfer('closed', {'def': sd, 'form': form}, source)
    return [claim] if rt.check(claim) else []


@op('seq_period_sum', 'SE', ('period', 'period'), ('period',),
    'Periods P1 and P2 modulo m give period lcm(P1, P2) for the sum, from the later start.')
def seq_period_sum(rt, first, second):
    a, b = first['data'], second['data']
    if first['status'] != 'checked' or second['status'] != 'checked' or a['modulus'] != b['modulus'] or first['id'] == second['id']:
        return []
    claim = rt.transfer('period', {'def': transform('sum', [a['def'], b['def']]), 'modulus': a['modulus'],
                                   'start': max(a['start'], b['start']), 'period': L.lcm(a['period'], b['period'])},
                        first, (second,))
    return [claim] if rt.check(claim) else []


@op('seq_period_product', 'SE', ('period', 'period'), ('period',),
    'Periods P1 and P2 modulo m give period lcm(P1, P2) for the termwise product.')
def seq_period_product(rt, first, second):
    a, b = first['data'], second['data']
    if first['status'] != 'checked' or second['status'] != 'checked' or a['modulus'] != b['modulus'] or first['id'] == second['id']:
        return []
    claim = rt.transfer('period', {'def': transform('product', [a['def'], b['def']]), 'modulus': a['modulus'],
                                   'start': max(a['start'], b['start']), 'period': L.lcm(a['period'], b['period'])},
                        first, (second,))
    return [claim] if rt.check(claim) else []


@op('seq_period_decimate', 'SE', ('period',), ('period',),
    'If a has period P from s, then a(2n+1) has period P/gcd(P, 2) from ceil((s-1)/2).')
def seq_period_decimate(rt, period):
    if period['status'] != 'checked': return []
    d = period['data']; P = d['period'] // (2 if d['period'] % 2 == 0 else 1)
    claim = rt.transfer('period', {'def': transform('decimate', [d['def']], t=2, j=1), 'modulus': d['modulus'],
                                   'start': max(0, -(-(d['start'] - 1) // 2)), 'period': P}, period)
    return [claim] if rt.check(claim) else []


@op('seq_gf_shift', 'SE', ('gf',), ('gf',), 'The generating function of a(n+1) is (A(x) - a(0)) / x.')
def seq_gf_shift(rt, gf):
    if gf['status'] != 'checked': return []
    P, Qd = gf_parts(gf); a0 = (P[0] if P else Q(0)) / Qd[0]
    N = L.padd(P, L.pscale(Qd, -a0))
    if N and N[0] != 0: return []
    return gf_claim(rt, gf, transform('shift', [gf['data']['def']], s=1), N[1:], Qd)


@op('seq_gf_sum', 'SE', ('gf', 'gf'), ('gf',), 'P1/Q1 + P2/Q2 = (P1 Q2 + P2 Q1) / (Q1 Q2) for the termwise sum.')
def seq_gf_sum(rt, first, second):
    if first['status'] != 'checked' or second['status'] != 'checked' or first['id'] == second['id']: return []
    (P1, Q1), (P2, Q2) = gf_parts(first), gf_parts(second)
    return gf_claim(rt, first, transform('sum', [first['data']['def'], second['data']['def']]),
                    L.padd(L.pmul(P1, Q2), L.pmul(P2, Q1)), L.pmul(Q1, Q2), (second,))


@op('seq_gf_product', 'SE', ('gf', 'gf'), ('gf',), 'The Cauchy product has generating function P1 P2 / (Q1 Q2).')
def seq_gf_product(rt, first, second):
    if first['status'] != 'checked' or second['status'] != 'checked' or first['id'] == second['id']: return []
    (P1, Q1), (P2, Q2) = gf_parts(first), gf_parts(second)
    return gf_claim(rt, first, transform('convolution', [first['data']['def'], second['data']['def']]),
                    L.pmul(P1, P2), L.pmul(Q1, Q2), (second,))


@op('seq_gf_derivative', 'SE', ('gf',), ('gf',), 'A\'(x) = (P\'Q - PQ\')/Q^2 is the generating function of (n+1) a(n+1).')
def seq_gf_derivative(rt, gf):
    if gf['status'] != 'checked': return []
    P, Qd = gf_parts(gf)
    sd = transform('polymul', [transform('shift', [gf['data']['def']], s=1)], p=[[1, 1], [1, 1]])
    return gf_claim(rt, gf, sd, L.padd(L.pmul(L.pderiv(P), Qd), L.pscale(L.pmul(P, L.pderiv(Qd)), -1)), L.pmul(Qd, Qd))


@op('seq_closed_shift', 'SE', ('closed',), ('closed',), 'A closed form f(n) of a gives f(n+1) for a(n+1).')
def seq_closed_shift(rt, closed):
    if closed['status'] != 'checked': return []
    d = closed['data']; form = d['form']; sd = transform('shift', [d['def']], s=1)
    if form['type'] == 'poly':
        return closed_claim(rt, closed, sd, dict(type='poly', coefficients=[L.enc(x) for x in
                                                                           L.pshift([L.dec(c) for c in form['coefficients']], 1)]))
    if form['type'] == 'expsum':
        return closed_claim(rt, closed, sd, dict(type='expsum', terms=[[L.enc(L.dec(c) * L.dec(q)), q] for c, q in form['terms']]))
    return []


def falling_poly(i):
    out = [Q(1)]
    for j in range(i): out = L.pmul(out, [Q(-j), Q(1)])
    return out


@op('seq_closed_partial_sum', 'SE', ('closed',), ('closed',),
    'Sum a polynomial closed form with sum_{k<=n} C(k, i) = C(n+1, i+1), or a geometric term with q != 1.')
def seq_closed_partial_sum(rt, closed):
    if closed['status'] != 'checked': return []
    d = closed['data']; form = d['form']; sd = transform('partial_sum', [d['def']])
    if form['type'] == 'poly':
        p = [L.dec(c) for c in form['coefficients']]; values = [L.peval(p, k) for k in range(len(p) + 1)]
        diffs, newton = values, []
        while diffs: newton.append(diffs[0]); diffs = [y - x for x, y in zip(diffs, diffs[1:])]
        total = []
        for i, b in enumerate(newton):
            term = L.pscale(L.pshift(falling_poly(i + 1), 1), b / factorial(i + 1))
            total = L.padd(total, term)
        return closed_claim(rt, closed, sd, dict(type='poly', coefficients=[L.enc(x) for x in total] or [[0, 1]]))
    if form['type'] == 'expsum' and all(L.dec(q) != 1 for _, q in form['terms']):
        terms, constant = [], Q(0)
        for c, q in form['terms']:
            c, q = L.dec(c), L.dec(q); terms.append([L.enc(c * q / (q - 1)), L.enc(q)]); constant -= c / (q - 1)
        if constant: terms.append([L.enc(constant), [1, 1]])
        return closed_claim(rt, closed, sd, dict(type='expsum', terms=terms))
    return []


@op('seq_closed_twist', 'SE', ('closed',), ('closed',), 'An exponential sum sum c q^n gives sum c (2q)^n for 2^n a(n).')
def seq_closed_twist(rt, closed):
    if closed['status'] != 'checked' or closed['data']['form']['type'] != 'expsum': return []
    d = closed['data']
    return closed_claim(rt, closed, transform('twist', [d['def']], c=[2, 1]),
                        dict(type='expsum', terms=[[c, L.enc(2 * L.dec(q))] for c, q in d['form']['terms']]))


@op('seq_closed_from_gf', 'NS', ('gf',), ('closed',),
    'Simple rational poles of P/Q with deg P < deg Q give an exponential sum; weights from the first terms.')
def seq_closed_from_gf(rt, gf):
    if gf['status'] != 'checked': return []
    P, Qd = gf_parts(gf); roots = L.rational_roots(Qd)
    if len(roots) != len(Qd) - 1 or len(P) >= len(Qd) or any(r == 0 for r in roots): return []
    bases = [1 / r for r in roots]; sd = gf['data']['def']; a = L.terms(sd, len(bases))
    weights = L.solve_linear([[b ** n for b in bases] for n in range(len(bases))], a)
    if weights is None: return []
    claim = rt.propose('closed', {'def': sd, 'form': dict(type='expsum', terms=[[L.enc(w), L.enc(b)]
                                                                               for w, b in zip(weights, bases) if w])}, (gf,))
    return [claim] if rt.check(claim) else []


@op('seq_hyper_refute', 'WS', ('hyper',), ('refutation',), 'Find the first index where a claimed term ratio fails.')
def seq_hyper_refute(rt, hyper):
    if hyper['status'] == 'checked': return []
    for i in range(hyper['data']['upto']):
        refutation = rt.refute(hyper, dict(index=i))
        if refutation is not None: return [refutation]
    return []


# ------------------------------------------------------------- fixtures

FIB = dict(type='lrs', coefficients=[[1, 1], [1, 1]], initial=[[0, 1], [1, 1]])
POW2 = dict(type='lrs', coefficients=[[2, 1]], initial=[[1, 1]])
MODES = dict(type='matrix', matrix=[[2, 0, 0], [0, 2, 0], [0, 0, 3]], initial=[1, 1, 1], terminal=[1, 1, 1])
WORDS = dict(type='words', patterns=['0110', '111'])
TRIANGLE = dict(type='transform', op='partial_sum', args=[dict(type='poly', coefficients=[[0, 1], [1, 1]])])
CATALAN = dict(type='terms', values=[1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796, 58786, 208012, 742900,
                                     2674440, 9694845, 35357670, 129644790, 477638700, 1767263190, 6564120420,
                                     24466267020, 91482563640, 343059613650])


def _seq(rt, sd): return rt.given('seq', {'def': sd})


def _law(rt, sd, coefficients, initial, check=True):
    obj = rt.propose('law', {'def': sd, 'coefficients': coefficients, 'initial': initial})
    if check: rt.check(obj)
    return obj


def _fib(rt): return _law(rt, FIB, [[1, 1], [1, 1]], [[0, 1], [1, 1]])


def _pow2(rt): return _law(rt, POW2, [[2, 1]], [[1, 1]])


def _modes(rt): return _law(rt, MODES, [[-6, 1], [5, 1]], [[3, 1], [7, 1]])


FIXTURES = {
    'seq_bm_law': [lambda rt: [_seq(rt, FIB)]],
    'seq_poly_fit': [lambda rt: [_seq(rt, TRIANGLE)]],
    'seq_expsum_fit': [lambda rt: [_modes(rt)]],
    'seq_gf_from_law': [lambda rt: [_fib(rt)]],
    'seq_hyper_fit': [lambda rt: [_seq(rt, CATALAN)]],
    'seq_mod_period': [lambda rt: [_seq(rt, FIB)]],
    'seq_matrix_law': [lambda rt: [_seq(rt, WORDS)]],
    'seq_lincomb': [lambda rt: [_seq(rt, MODES), _seq(rt, POW2), _seq(rt, dict(type='lrs', coefficients=[[3, 1]],
                                                                                initial=[[1, 1]]))]],
    'seq_order_reduce': [lambda rt: [_law(rt, MODES, [[6, 1], [-11, 1], [6, 1]], [[3, 1], [7, 1], [17, 1]])],
                         lambda rt: [_law(rt, dict(type='lrs', coefficients=[[-2, 1], [3, 1]], initial=[[1, 1], [3, 1]]),
                                          [[-2, 1], [3, 1]], [[1, 1], [3, 1]])]],
    'seq_law_refute': [lambda rt: [_law(rt, FIB, [[2, 1], [1, 1]], [[0, 1], [1, 1]], check=False)]],
    'seq_law_mod_refute': [lambda rt: [_law(rt, FIB, [[1, 1], [2, 1]], [[0, 1], [1, 1]], check=False)]],
    'seq_gf_refute': [lambda rt: [rt.propose('gf', {'def': FIB, 'numerator': [[0, 1], [1, 1]],
                                                    'denominator': [[1, 1], [-1, 1], [-2, 1]]})]],
    'seq_closed_refute': [lambda rt: [rt.propose('closed', {'def': POW2, 'form': dict(type='poly',
                                                                                         coefficients=[[1, 1], [1, 1]])})]],
    'seq_period_refute': [lambda rt: [rt.propose('period', {'def': FIB, 'modulus': 2, 'start': 0, 'period': 2})]],
    'seq_shift_law': [lambda rt: [_fib(rt)]],
    'seq_scale_law': [lambda rt: [_fib(rt)]],
    'seq_sum_law': [lambda rt: [_fib(rt), _pow2(rt)]],
    'seq_product_law': [lambda rt: [_fib(rt), _pow2(rt)]],
    'seq_partial_sum_law': [lambda rt: [_fib(rt)]],
    'seq_difference_law': [lambda rt: [_fib(rt)]],
    'seq_decimate_law': [lambda rt: [_fib(rt)]],
    'seq_binomial_law': [lambda rt: [_fib(rt)]],
    'seq_inverse_binomial_law': [lambda rt: [_fib(rt)]],
    'seq_interleave_law': [lambda rt: [_fib(rt), _pow2(rt)]],
    'seq_twist_law': [lambda rt: [_fib(rt)]],
    'seq_polymul_law': [lambda rt: [_fib(rt)]],
    'seq_convolution_law': [lambda rt: [_fib(rt), _pow2(rt)]],
    'seq_reciprocal_law': [lambda rt: [_law(rt, dict(type='lrs', coefficients=[[1, 1], [1, 1]], initial=[[1, 1], [1, 1]]),
                                             [[1, 1], [1, 1]], [[1, 1], [1, 1]])]],
    'seq_aerate_law': [lambda rt: [_fib(rt)]],
    'seq_companion_carrier': [lambda rt: [_fib(rt)]],
}

def _period(rt, sd, m, start, period):
    obj = rt.propose('period', {'def': sd, 'modulus': m, 'start': start, 'period': period}); rt.check(obj); return obj


def _gf(rt, sd, numerator, denominator):
    obj = rt.propose('gf', {'def': sd, 'numerator': numerator, 'denominator': denominator}); rt.check(obj); return obj


def _closed(rt, sd, form):
    obj = rt.propose('closed', {'def': sd, 'form': form}); rt.check(obj); return obj


FIXTURES.update({
    'seq_period_sum': [lambda rt: [_period(rt, FIB, 2, 0, 3), _period(rt, POW2, 2, 1, 1)]],
    'seq_period_product': [lambda rt: [_period(rt, FIB, 2, 0, 3), _period(rt, POW2, 2, 1, 1)]],
    'seq_period_decimate': [lambda rt: [_period(rt, FIB, 2, 0, 3)]],
    'seq_gf_shift': [lambda rt: [_gf(rt, FIB, [[0, 1], [1, 1]], [[1, 1], [-1, 1], [-1, 1]])]],
    'seq_gf_sum': [lambda rt: [_gf(rt, FIB, [[0, 1], [1, 1]], [[1, 1], [-1, 1], [-1, 1]]), _gf(rt, POW2, [[1, 1]], [[1, 1], [-2, 1]])]],
    'seq_gf_product': [lambda rt: [_gf(rt, FIB, [[0, 1], [1, 1]], [[1, 1], [-1, 1], [-1, 1]]), _gf(rt, POW2, [[1, 1]], [[1, 1], [-2, 1]])]],
    'seq_gf_derivative': [lambda rt: [_gf(rt, FIB, [[0, 1], [1, 1]], [[1, 1], [-1, 1], [-1, 1]])]],
    'seq_closed_shift': [lambda rt: [_closed(rt, MODES, dict(type='expsum', terms=[[[2, 1], [2, 1]], [[1, 1], [3, 1]]]))]],
    'seq_closed_partial_sum': [lambda rt: [_closed(rt, TRIANGLE, dict(type='poly', coefficients=[[0, 1], [1, 2], [1, 2]]))],
                               lambda rt: [_closed(rt, MODES, dict(type='expsum', terms=[[[2, 1], [2, 1]], [[1, 1], [3, 1]]]))]],
    'seq_closed_twist': [lambda rt: [_closed(rt, MODES, dict(type='expsum', terms=[[[2, 1], [2, 1]], [[1, 1], [3, 1]]]))]],
    'seq_closed_from_gf': [lambda rt: [_gf(rt, MODES, [[3, 1], [-8, 1]], [[1, 1], [-5, 1], [6, 1]])]],
    'seq_hyper_refute': [lambda rt: [rt.propose('hyper', {'def': CATALAN, 'p': [[2, 1], [4, 1]], 'q': [[1, 1], [1, 1]],
                                                          'upto': 20})]],
})
