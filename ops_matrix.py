"""Operators on transition counts u*M**h*v over the integers.

Transposition, unimodular similarity, powers, direct sums, Kronecker products,
scaling and horizon shifts carry a checked count to another count question with
a known value. Krylov minimal polynomials and rational eigenpairs are proposed
and admitted by exact recomputation.
"""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_matrix_' + name, Path(__file__).with_name(name + '.py'))
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


def matmul(A, B):
    return [[sum(A[i][t] * B[t][j] for t in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def count_data(M, u, v, h, value):
    return dict(matrix=M, initial=u, terminal=v, horizon=h, value=L.enc(value))


def claimed(rt, kind, data, parents=(), source=None):
    obj = rt.transfer(kind, data, source, parents) if source is not None else rt.propose(kind, data, parents)
    return [obj] if rt.check(obj) else []


def fits(M):
    return all(abs(x) <= 10 ** 6 for row in M for x in row) and len(M) <= 64


@op('matrix_transpose_count', 'SE', ('countval',), ('countval',), 'u*M**h*v equals v*(M^T)**h*u.')
def matrix_transpose_count(rt, c):
    if c['status'] != 'checked': return []
    d = c['data']; M = [list(r) for r in zip(*d['matrix'])]
    return claimed(rt, 'countval', count_data(M, d['terminal'], d['initial'], d['horizon'], L.dec(d['value'])), source=c)


@op('matrix_similarity_count', 'SE', ('countval',), ('countval',),
    'For unimodular P, (uP)(P^-1 M P)**h(P^-1 v) equals u*M**h*v; here P adds the first row to the second.')
def matrix_similarity_count(rt, c):
    if c['status'] != 'checked' or len(c['data']['matrix']) < 2: return []
    d = c['data']; n = len(d['matrix'])
    P = [[int(i == j) + int(i == 0 and j == 1) for j in range(n)] for i in range(n)]
    Pi = [[int(i == j) - int(i == 0 and j == 1) for j in range(n)] for i in range(n)]
    M = matmul(matmul(Pi, d['matrix']), P)
    u = [sum(d['initial'][t] * P[t][j] for t in range(n)) for j in range(n)]
    v = [sum(Pi[i][t] * d['terminal'][t] for t in range(n)) for i in range(n)]
    if not fits(M): return []
    return claimed(rt, 'countval', count_data(M, u, v, d['horizon'], L.dec(d['value'])), source=c)


@op('matrix_power_count', 'SE', ('countval',), ('countval',), 'At an even horizon 2h, M counts equal M^2 counts at h.')
def matrix_power_count(rt, c):
    d = c['data']
    if c['status'] != 'checked' or d['horizon'] % 2: return []
    M = matmul(d['matrix'], d['matrix'])
    if not fits(M): return []
    return claimed(rt, 'countval', count_data(M, d['initial'], d['terminal'], d['horizon'] // 2, L.dec(d['value'])), source=c)


def block(A, B):
    n, m = len(A), len(B)
    return [list(A[i]) + [0] * m for i in range(n)] + [[0] * n + list(B[i]) for i in range(m)]


@op('matrix_direct_sum_count', 'SE', ('countval', 'countval'), ('countval',),
    'Counts of two systems at one horizon add for the block-diagonal system.')
def matrix_direct_sum_count(rt, a, b):
    x, y = a['data'], b['data']
    if a['status'] != 'checked' or b['status'] != 'checked' or x['horizon'] != y['horizon'] or a['id'] == b['id']: return []
    return claimed(rt, 'countval', count_data(block(x['matrix'], y['matrix']), x['initial'] + y['initial'],
                                              x['terminal'] + y['terminal'], x['horizon'],
                                              L.dec(x['value']) + L.dec(y['value'])), (b,), a)


@op('matrix_kronecker_count', 'SE', ('countval', 'countval'), ('countval',),
    'Counts of two systems at one horizon multiply for the Kronecker product system.')
def matrix_kronecker_count(rt, a, b):
    x, y = a['data'], b['data']
    if a['status'] != 'checked' or b['status'] != 'checked' or x['horizon'] != y['horizon'] or a['id'] == b['id']: return []
    A, B = x['matrix'], y['matrix']; n, m = len(A), len(B)
    if n * m > 64: return []
    K = [[A[i // m][j // m] * B[i % m][j % m] for j in range(n * m)] for i in range(n * m)]
    u = [p * q for p in x['initial'] for q in y['initial']]; v = [p * q for p in x['terminal'] for q in y['terminal']]
    if not fits(K): return []
    return claimed(rt, 'countval', count_data(K, u, v, x['horizon'], L.dec(x['value']) * L.dec(y['value'])), (b,), a)


@op('matrix_scale_count', 'SE', ('countval',), ('countval',), 'Scaling M by c scales the count by c^h.')
def matrix_scale_count(rt, c):
    if c['status'] != 'checked': return []
    d = c['data']; M = [[2 * x for x in row] for row in d['matrix']]
    if not fits(M): return []
    return claimed(rt, 'countval', count_data(M, d['initial'], d['terminal'], d['horizon'],
                                              L.dec(d['value']) * 2 ** d['horizon']), source=c)


@op('matrix_horizon_shift', 'SE', ('countval',), ('countval',), 'u*M**h*v equals (u*M)*M**(h-1)*v.')
def matrix_horizon_shift(rt, c):
    d = c['data']
    if c['status'] != 'checked' or d['horizon'] < 1: return []
    n = len(d['matrix']); u = [sum(d['initial'][t] * d['matrix'][t][j] for t in range(n)) for j in range(n)]
    if any(abs(x) > 10 ** 6 for x in u): return []
    return claimed(rt, 'countval', count_data(d['matrix'], u, d['terminal'], d['horizon'] - 1, L.dec(d['value'])), source=c)


@op('matrix_count_eval', 'NS', ('count',), ('countval',), 'Iterate u*M**h*v exactly and state the value.')
def matrix_count_eval(rt, q):
    d = q['data']; row = [Q(x) for x in d['initial']]
    for _ in range(d['horizon']):
        rt.budget.use(len(row) ** 2)
        row = [sum(row[i] * d['matrix'][i][j] for i in range(len(row))) for j in range(len(row))]
    value = sum(x * y for x, y in zip(row, d['terminal']))
    return claimed(rt, 'countval', count_data(d['matrix'], d['initial'], d['terminal'], d['horizon'], value), (q,))


@op('matrix_krylov_law', 'NS', ('count',), ('law',),
    'The first dependency among v, Mv, M^2 v gives the minimal polynomial of v, a law for u*M**h*v.')
def matrix_krylov_law(rt, q):
    d = q['data']; M = d['matrix']; n = len(M)
    vectors = [[Q(x) for x in d['terminal']]]
    for k in range(1, n + 1):
        rt.budget.use(n * n)
        prev = vectors[-1]; vectors.append([sum(M[i][j] * prev[j] for j in range(n)) for i in range(n)])
        sol = L.solve_linear([[vectors[t][i] for t in range(k)] for i in range(n)], vectors[k])
        if sol is not None: break
    else: return []
    sd = dict(type='matrix', matrix=M, initial=d['initial'], terminal=d['terminal'])
    law = dict({'def': sd}, coefficients=[L.enc(x) for x in sol], initial=[L.enc(x) for x in L.terms(sd, len(sol))])
    return claimed(rt, 'law', law, (q,))


@op('matrix_rational_eigen', 'NS', ('count',), ('eigen',),
    'Rational roots of the characteristic polynomial and their kernel vectors give eigenpairs.')
def matrix_rational_eigen(rt, q):
    M = q['data']['matrix']; n = len(M); out = []
    rt.budget.use(n ** 4)
    for lam in L.rational_roots(L.charpoly(M))[:4]:
        basis = L.nullspace([[Q(M[i][j]) - (lam if i == j else 0) for j in range(n)] for i in range(n)], n)
        if basis: out += claimed(rt, 'eigen', dict(matrix=M, value=L.enc(lam), vector=[L.enc(x) for x in basis[0]]), (q,))
    return out


@op('matrix_count_refute', 'WS', ('countval',), ('refutation',), 'Recompute a claimed count; a different value refutes it.')
def matrix_count_refute(rt, c):
    if c['status'] == 'checked': return []
    refutation = rt.refute(c, {})
    return [refutation] if refutation is not None else []


@op('matrix_eigen_refute', 'WS', ('eigen',), ('refutation',), 'Multiply out M v; if it is not lambda v the eigenpair is refuted.')
def matrix_eigen_refute(rt, eig):
    if eig['status'] == 'checked': return []
    refutation = rt.refute(eig, {})
    return [refutation] if refutation is not None else []


FIB_M = [[1, 1], [1, 0]]


def _count(rt, M, u, v, h, value, check=True):
    obj = rt.propose('countval', count_data(M, u, v, h, value))
    if check: rt.check(obj)
    return obj


FIXTURES = {
    'matrix_transpose_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55)]],
    'matrix_similarity_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55)]],
    'matrix_power_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55)]],
    'matrix_direct_sum_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55), _count(rt, [[2]], [1], [1], 10, 1024)]],
    'matrix_kronecker_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55), _count(rt, [[2]], [1], [1], 10, 1024)]],
    'matrix_scale_count': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55)]],
    'matrix_horizon_shift': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 55)]],
    'matrix_count_eval': [lambda rt: [rt.given('count', dict(matrix=FIB_M, initial=[1, 0], terminal=[0, 1], horizon=20))]],
    'matrix_krylov_law': [lambda rt: [rt.given('count', dict(matrix=[[2, 0, 0], [0, 2, 0], [0, 0, 3]], initial=[1, 1, 1],
                                                             terminal=[1, 1, 1], horizon=5))]],
    'matrix_rational_eigen': [lambda rt: [rt.given('count', dict(matrix=[[2, 1], [0, 3]], initial=[1, 0], terminal=[0, 1],
                                                                 horizon=3))]],
    'matrix_count_refute': [lambda rt: [_count(rt, FIB_M, [1, 0], [0, 1], 10, 56, check=False)]],
    'matrix_eigen_refute': [lambda rt: [rt.propose('eigen', dict(matrix=[[2, 1], [0, 3]], value=[2, 1], vector=[[1, 1], [1, 1]]))]],
}
