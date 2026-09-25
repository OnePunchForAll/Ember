"""Search operators for Ember's discrete and algebraic windows: colorings, paths, graceful labelings, cycle covers,
Ramsey colorings, sunflower-free families, prime progressions, Sidon sets, Hadamard matrices, projective planes,
orthogonal Latin squares, a CDCL SAT solver that logs RUP proofs, circuits, geometric configurations, Kakeya sets,
Andrews-Curtis moves, inscribed squares, plane automorphism inverses, matrix multiplication schemes found by flips,
and rational points. Every search is her own code; the checker verifies what it finds.
"""
from fractions import Fraction as Q
import importlib.util
from itertools import combinations, permutations, product
from math import gcd, isqrt
from pathlib import Path
import random


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_wdisc_' + name, Path(__file__).with_name(name + '.py'))
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


def _mr(n):
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


# ------------------------------------------------------------- graphs

def graph(spec):
    """(n, adjacency sets), her own reading of a graph specification."""
    if 'edges' in spec:
        n = spec['n']; adj = [set() for _ in range(n)]
        for u, v in spec['edges']: adj[u].add(v); adj[v].add(u)
        return n, adj
    name = spec['named']
    if name == 'petersen': return graph(dict(named='gp', n=5, k=2))
    if name == 'gp':
        m, k = spec['n'], spec['k']
        return graph(dict(n=2 * m, edges=[[i, (i + 1) % m] for i in range(m)] + [[i, i + m] for i in range(m)] +
                          [[m + i, m + (i + k) % m] for i in range(m)]))
    if name == 'cycle': return graph(dict(n=spec['n'], edges=[[i, (i + 1) % spec['n']] for i in range(spec['n'])]))
    if name == 'complete': return graph(dict(n=spec['n'], edges=[list(e) for e in combinations(range(spec['n']), 2)]))
    if name == 'paley':
        q = spec['q']; sq = {x * x % q for x in range(1, q)}
        return graph(dict(n=q, edges=[[i, j] for i, j in combinations(range(q), 2) if (j - i) % q in sq]))
    if name == 'hypercube':
        d = spec['d']
        return graph(dict(n=1 << d, edges=[[v, v ^ (1 << b)] for v in range(1 << d) for b in range(d) if v < v ^ (1 << b)]))
    if name == 'cayley':
        gens = [tuple(g) for g in spec['perms']]; ident = tuple(range(len(gens[0]))); idx = {ident: 0}; order = [ident]
        for g in order:
            for s in gens:
                h = tuple(s[x] for x in g)
                if h not in idx: idx[h] = len(order); order.append(h)
        edges = {(min(idx[g], idx[tuple(s[x] for x in g)]), max(idx[g], idx[tuple(s[x] for x in g)]))
                 for g in order for s in gens if idx[g] != idx[tuple(s[x] for x in g)]}
        return graph(dict(n=len(order), edges=[list(e) for e in sorted(edges)]))
    raise KeyError(name)


def color_with(n, adj, k, rt):
    colors = [-1] * n
    def pick():
        best, key = -1, None
        for v in range(n):
            if colors[v] < 0:
                kk = (len({colors[u] for u in adj[v] if colors[u] >= 0}), len(adj[v]))
                if key is None or kk > key: best, key = v, kk
        return best
    def go():
        rt.budget.use()
        v = pick()
        if v < 0: return True
        used = {colors[u] for u in adj[v]}
        top = max(colors) + 1
        for c in range(min(k, top + 1)):
            if c in used: continue
            colors[v] = c
            if go(): return True
        colors[v] = -1
        return False
    return colors if go() else None


def ham_path(n, adj, rt):
    order = sorted(range(n), key=lambda v: len(adj[v]))
    for start in order:
        path = [start]; seen = {start}
        def go():
            rt.budget.use()
            if len(path) == n: return True
            v = path[-1]
            for u in sorted(adj[v] - seen, key=lambda u: len(adj[u] - seen)):
                path.append(u); seen.add(u)
                if go(): return True
                path.pop(); seen.discard(u)
            return False
        if go(): return path
    return None


def free_trees(n):
    """Every tree on n vertices up to isomorphism, keyed by the same center-rooted code the checker uses."""
    out = {}
    L_ = list(range(n)) if n > 1 else [0]
    while L_ is not None:
        edges = []; stack = []
        for i, lev in enumerate(L_):
            while stack and L_[stack[-1]] >= lev: stack.pop()
            if stack: edges.append((stack[-1], i))
            stack.append(i)
        code = tree_code(n, edges)
        if code not in out: out[code] = edges
        if n <= 2 or not any(x > 1 for x in L_): break
        p = max(i for i in range(len(L_)) if L_[i] > 1)
        q = max(i for i in range(p) if L_[i] == L_[p] - 1)
        s = L_[:p]
        for i in range(p, len(L_)): s.append(s[i - (p - q)])
        L_ = s
    return out


def tree_code(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges: adj[u].append(v); adj[v].append(u)
    if n == 1: return '()'
    deg = [len(a) for a in adj]; leaves = [v for v in range(n) if deg[v] <= 1]; left = n
    while left > 2:
        nxt = []
        for v in leaves:
            left -= 1
            for u in adj[v]:
                deg[u] -= 1
                if deg[u] == 1: nxt.append(u)
        leaves = nxt
    def enc(v, parent): return '(' + ''.join(sorted(enc(u, v) for u in adj[v] if u != parent)) + ')'
    return min(enc(c, -1) for c in leaves)


def graceful(n, edges, rt):
    adj = [[] for _ in range(n)]
    for u, v in edges: adj[u].append(v); adj[v].append(u)
    order = []; seen = set(); start = max(range(n), key=lambda v: len(adj[v])); queue = [start]
    while queue:
        v = queue.pop(0)
        if v in seen: continue
        seen.add(v); order.append(v); queue += [u for u in adj[v] if u not in seen]
    lab = [-1] * n; used = set(); diffs = set()
    def go(i):
        rt.budget.use()
        if i == n: return True
        v = order[i]; nbrs = [lab[u] for u in adj[v] if lab[u] >= 0]
        for x in range(n):
            if x in used: continue
            ds = [abs(x - y) for y in nbrs]
            if any(d in diffs or d == 0 for d in ds) or len(set(ds)) != len(ds): continue
            lab[v] = x; used.add(x); diffs.update(ds)
            if go(i + 1): return True
            lab[v] = -1; used.discard(x); diffs.difference_update(ds)
        return False
    return lab if go(0) else None


def cycles_of(n, adj, rt, max_len=None):
    out = []; max_len = max_len or n
    for s in range(n):
        stack = [(s, [s])]
        while stack:
            v, path = stack.pop(); rt.budget.use()
            for u in adj[v]:
                if u == s and len(path) >= 3 and path[1] < path[-1]: out.append(list(path))
                elif u > s and u not in path and len(path) < max_len: stack.append((u, path + [u]))
    return out


def double_cover(n, adj, rt):
    cyc = cycles_of(n, adj, rt)
    def edges_of(c): return [(min(c[i], c[(i + 1) % len(c)]), max(c[i], c[(i + 1) % len(c)])) for i in range(len(c))]
    E = sorted({(u, v) for u in range(n) for v in adj[u] if u < v}); need = {e: 2 for e in E}
    by_edge = {e: [] for e in E}
    for i, c in enumerate(cyc):
        for e in edges_of(c): by_edge[e].append(i)
    chosen = []
    def go():
        rt.budget.use()
        open_e = [e for e in E if need[e] > 0]
        if not open_e: return True
        e = min(open_e, key=lambda e: len(by_edge[e]))
        for i in by_edge[e]:
            es = edges_of(cyc[i])
            if all(need[f] > 0 for f in es):
                for f in es: need[f] -= 1
                chosen.append(cyc[i])
                if go(): return True
                chosen.pop()
                for f in es: need[f] += 1
        return False
    return chosen if go() else None


def total_color(n, adj, rt):
    D = max(len(a) for a in adj); k = D + 2
    E = sorted({(u, v) for u in range(n) for v in adj[u] if u < v})
    items = [('v', v) for v in range(n)] + [('e', e) for e in E]
    vc = [-1] * n; ec = {}
    def ok(item, c):
        if item[0] == 'v':
            v = item[1]
            return all(vc[u] != c for u in adj[v]) and all(ec.get((min(v, u), max(v, u))) != c for u in adj[v])
        u, v = item[1]
        return c != vc[u] and c != vc[v] and all(ec.get((min(x, w), max(x, w))) != c for x in (u, v) for w in adj[x]
                                                   if (min(x, w), max(x, w)) != (u, v))
    def go(i):
        rt.budget.use()
        if i == len(items): return True
        it = items[i]
        for c in range(k):
            if ok(it, c):
                if it[0] == 'v': vc[it[1]] = c
                else: ec[it[1]] = c
                if go(i + 1): return True
                if it[0] == 'v': vc[it[1]] = -1
                else: ec.pop(it[1], None)
        return False
    if not go(0): return None
    return dict(vertices=vc, edges={str(u) + '-' + str(v): c for (u, v), c in ec.items()})


def has_clique(n, adj, s, rt):
    def go(R, P):
        rt.budget.use()
        if len(R) >= s: return True
        if len(R) + len(P) < s: return False
        for v in sorted(P):
            if go(R | {v}, P & adj[v]): return True
            P = P - {v}
        return False
    return go(set(), set(range(n)))


def ramsey_search(params, rt):
    """Induced subgraphs of Paley graphs first, then circulant graphs on n vertices: every symmetric set of distances
    when there are at most 2^16 of them, else a random sample."""
    n, s, t = params['n'], params['s'], params['t']
    found = _paley_ramsey(n, s, t, rt)
    if found is not None: return found
    half = list(range(1, n // 2 + 1)); rng = random.Random(n * 100 + s * 10 + t)
    sets = (product((0, 1), repeat=len(half)) if len(half) <= 16 else
            (tuple(rng.randrange(2) for _ in half) for _ in range(20_000)))
    for bits in sets:
        dist = {d for d, b in zip(half, bits) if b}; dist |= {n - d for d in dist}
        adj = [{(v + d) % n for d in dist} for v in range(n)]
        comp = [set(range(n)) - adj[v] - {v} for v in range(n)]
        if not has_clique(n, adj, s, rt) and not has_clique(n, comp, t, rt):
            return [[u, v] for u in range(n) for v in adj[u] if u < v]
    return None


def _paley_ramsey(n, s, t, rt):
    for q in range(n, 4 * n + 10):
        if q % 4 != 1 or not _mr(q): continue
        qn, qadj = graph(dict(named='paley', q=q))
        adj = [qadj[v] & set(range(n)) for v in range(n)]
        comp = [set(range(n)) - adj[v] - {v} for v in range(n)]
        if not has_clique(n, adj, s, rt) and not has_clique(n, comp, t, rt):
            return [[u, v] for u in range(n) for v in adj[u] if u < v]
    return None


def graph_search(params, rt, family):
    if family == 'coloring':
        n, adj = graph(params['graph']); c = color_with(n, adj, params['k'], rt); return c
    if family == 'ham_path':
        n, adj = graph(params['graph']); return ham_path(n, adj, rt)
    if family == 'graceful_trees':
        out = {}
        for code in free_trees(params['n']):
            # the claim names vertices in preorder of the code; read the tree back from its code
            edges = []; stack = []; count = 0
            for ch in code:
                if ch == '(':
                    if stack: edges.append((stack[-1], count))
                    stack.append(count); count += 1
                else: stack.pop()
            lab = graceful(params['n'], edges, rt)
            if lab is None: return None
            out[code] = lab
        return out
    if family == 'cycle_double_cover':
        n, adj = graph(params['graph']); return double_cover(n, adj, rt)
    if family == 'total_coloring':
        n, adj = graph(params['graph']); return total_color(n, adj, rt)
    if family == 'ramsey_coloring': return ramsey_search(params, rt)
    return None


# ------------------------------------------------------------- set systems, additive sets

def sunflower_free(params, rt):
    w, k, size = params['w'], params['k'], params['size']
    rng = random.Random(size * 1000 + w * 10 + k)
    for ground in range(w + 1, 4 * w + 8):
        pool = [frozenset(c) for c in combinations(range(ground), w)]
        for attempt in range(40):
            rng.shuffle(pool); fam = []
            for s in pool:
                rt.budget.use(len(fam))
                if all(not _sunflower(list(g) + [s]) for g in combinations(fam, k - 1)): fam.append(s)
                if len(fam) == size: return [sorted(x) for x in fam]
    return None


def _sunflower(sets):
    core = frozenset.intersection(*sets)
    return all((a & b) == core for a, b in combinations(sets, 2))


def prime_ap(params, rt):
    k = params['k']; prim = 1
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        if p <= k: prim *= p
    for mult in range(1, 200000):
        d = prim * mult
        for a in range(3, 20000, 2):
            rt.budget.use(k)
            if all(_mr(a + i * d) for i in range(k)): return [a, d]
    return None


def sidon_set(params, rt):
    n, size = params['n'], params['size']
    best = []
    def go(x, S, diffs):
        rt.budget.use()
        if len(S) == size: best.extend(S); return True
        if len(S) + (n - x + 1) < size: return False
        for y in range(x, n + 1):
            nd = {y - s for s in S}
            if len(nd) == len(S) and not nd & diffs:
                if go(y + 1, S + [y], diffs | nd): return True
        return False
    return best if go(1, [], set()) else None


# ------------------------------------------------------------- designs: finite fields, Hadamard, planes, MOLS

class GF:
    """GF(p^k) with elements 0..q-1 read as coefficient vectors base p, reduced by a monic irreducible polynomial."""
    def __init__(self, q):
        f = {}; x = q; d = 2
        while d * d <= x:
            while x % d == 0: f[d] = f.get(d, 0) + 1; x //= d
            d += 1
        if x > 1: f[x] = f.get(x, 0) + 1
        assert len(f) == 1
        self.p, self.k = next(iter(f.items())); self.q = q
        self.mod = self._irreducible() if self.k > 1 else None
        self.mul_table = [[self._mul(a, b) for b in range(q)] for a in range(q)]
    def _digits(self, a): return [(a // self.p ** i) % self.p for i in range(self.k)]
    def _num(self, ds): return sum(d * self.p ** i for i, d in enumerate(ds))
    def add(self, a, b): return self._num([(x + y) % self.p for x, y in zip(self._digits(a), self._digits(b))])
    def neg(self, a): return self._num([(-x) % self.p for x in self._digits(a)])
    def _mul(self, a, b):
        if self.k == 1: return a * b % self.p
        x, y = self._digits(a), self._digits(b); prod = [0] * (2 * self.k - 1)
        for i, u in enumerate(x):
            for j, v in enumerate(y): prod[i + j] = (prod[i + j] + u * v) % self.p
        for i in range(len(prod) - 1, self.k - 1, -1):
            c = prod[i]
            if c:
                for j, m in enumerate(self.mod): prod[i - self.k + j] = (prod[i - self.k + j] - c * m) % self.p
        return self._num(prod[:self.k])
    def mul(self, a, b): return self.mul_table[a][b]
    def _irreducible(self):
        p, k = self.p, self.k
        for tail in product(range(p), repeat=k):
            poly = list(tail) + [1]
            if tail[0] == 0: continue
            if all(sum(c * pow(x, i, p) for i, c in enumerate(poly)) % p for x in range(p)) and self._no_factor(poly):
                return poly
    def _no_factor(self, poly):
        p, k = self.p, self.k
        for d in range(2, k // 2 + 1):
            for tail in product(range(p), repeat=d):
                g = list(tail) + [1]; r = list(poly)
                for i in range(len(r) - 1, d - 1, -1):
                    c = r[i]
                    for j in range(d + 1): r[i - d + j] = (r[i - d + j] - c * g[j]) % p
                if not any(r[:d]): return False
        return True
    def chi(self, a):
        if a == 0: return 0
        r = 1; e = (self.q - 1) // 2; b = a
        while e:
            if e & 1: r = self.mul(r, b)
            b = self.mul(b, b); e >>= 1
        return 1 if r == 1 else -1


def _prime_power(q):
    if q < 2: return False
    f = set(); x = q; d = 2
    while d * d <= x:
        while x % d == 0: f.add(d); x //= d
        d += 1
    if x > 1: f.add(x)
    return len(f) == 1


def hadamard(n, rt, memo=None):
    memo = {} if memo is None else memo
    if n in memo: return memo[n]
    out = None
    if n == 1: out = [[1]]
    elif n == 2: out = [[1, 1], [1, -1]]
    elif n % 4 == 0:
        if _prime_power(n - 1) and (n - 1) % 4 == 3:
            F = GF(n - 1); q = n - 1
            S = [[0] * n for _ in range(n)]
            for j in range(1, n): S[0][j] = 1; S[j][0] = -1
            for i in range(q):
                for j in range(q): S[i + 1][j + 1] = F.chi(F.add(j, F.neg(i)))
            out = [[S[i][j] + (1 if i == j else 0) for j in range(n)] for i in range(n)]
        elif n % 2 == 0 and _prime_power(n // 2 - 1) and (n // 2 - 1) % 4 == 1:
            q = n // 2 - 1; F = GF(q); m = q + 1
            C = [[0] * m for _ in range(m)]
            for j in range(1, m): C[0][j] = C[j][0] = 1
            for i in range(q):
                for j in range(q): C[i + 1][j + 1] = F.chi(F.add(j, F.neg(i)))
            out = [[0] * n for _ in range(n)]
            for i in range(m):
                for j in range(m):
                    if i == j: blk = [[1, -1], [-1, -1]]
                    else: c = C[i][j]; blk = [[c, c], [c, -c]]
                    for a in range(2):
                        for b in range(2): out[2 * i + a][2 * j + b] = blk[a][b]
        else:
            for a in range(2, n):
                if n % a == 0 and a % 2 == 0 or a in (2,) and n % a == 0:
                    b = n // a
                    if b < 1 or (b > 2 and b % 4) or (a > 2 and a % 4): continue
                    A, B = hadamard(a, rt, memo), hadamard(b, rt, memo)
                    if A and B:
                        out = [[A[i // b][j // b] * B[i % b][j % b] for j in range(n)] for i in range(n)]; break
    rt.budget.use(n * n)
    memo[n] = out
    return out


def projective_plane(q):
    F = GF(q); pts = []
    for x in range(q):
        for y in range(q): pts.append((x, y, 1))
    for x in range(q): pts.append((x, 1, 0))
    pts.append((1, 0, 0))
    lines = pts
    def dot(a, b):
        s = 0
        for u, v in zip(a, b): s = F.add(s, F.mul(u, v))
        return s
    return [[i for i, p in enumerate(pts) if dot(p, l) == 0] for l in lines]


def mols(n, k, rt):
    if _prime_power(n) and k <= n - 1:
        F = GF(n)
        return [[[F.add(F.mul(a, i), j) for j in range(n)] for i in range(n)] for a in range(1, k + 1)]
    if n == 10 and k == 2: return mols_search(n, rt)
    return None


def mols_search(n, rt, seed=10):
    """A pair of orthogonal Latin squares: a random Latin square, its transversals, and n disjoint ones."""
    rng = random.Random(seed)
    for attempt in range(20):
        L_ = _random_latin(n, rng, rt)
        if L_ is None: continue
        trans = []
        def go(i, used_cols, used_syms, perm):
            rt.budget.use()
            if len(trans) > 4000: return
            if i == n: trans.append(tuple(perm)); return
            for j in range(n):
                s = L_[i][j]
                if not used_cols >> j & 1 and not used_syms >> s & 1:
                    perm.append(j); go(i + 1, used_cols | 1 << j, used_syms | 1 << s, perm); perm.pop()
        go(0, 0, 0, [])
        # n disjoint transversals: each cell (i, j) covered once; a transversal is a set of cells (i, perm[i])
        cells = [frozenset((i, t[i]) for i in range(n)) for t in trans]
        by_cell = {}
        for idx, c in enumerate(cells):
            for cell in c: by_cell.setdefault(cell, []).append(idx)
        chosen = []; covered = set()
        def cover():
            rt.budget.use()
            if len(chosen) == n: return True
            free = [(0, j) for j in range(n) if (0, j) not in covered]
            cell = min(((i, j) for i in range(n) for j in range(n) if (i, j) not in covered),
                       key=lambda c: len(by_cell.get(c, ())))
            for idx in by_cell.get(cell, ()):
                if not cells[idx] & covered:
                    chosen.append(idx); covered.update(cells[idx])
                    if cover(): return True
                    chosen.pop(); covered.difference_update(cells[idx])
            return False
        if cover():
            M = [[0] * n for _ in range(n)]
            for sym, idx in enumerate(chosen):
                for i, j in cells[idx]: M[i][j] = sym
            return [L_, M]
    return None


def _random_latin(n, rng, rt):
    for attempt in range(200):
        sq = [[-1] * n for _ in range(n)]
        rows = [set() for _ in range(n)]; cols = [set() for _ in range(n)]
        def go(k):
            rt.budget.use()
            if k == n * n: return True
            i, j = divmod(k, n)
            opts = [s for s in range(n) if s not in rows[i] and s not in cols[j]]; rng.shuffle(opts)
            for s in opts:
                sq[i][j] = s; rows[i].add(s); cols[j].add(s)
                if go(k + 1): return True
                rows[i].discard(s); cols[j].discard(s)
            sq[i][j] = -1
            return False
        if go(0): return sq
    return None


def design_search(params, rt, family):
    if family == 'hadamard':
        H = hadamard(params['n'], rt)
        return None if H is None else [''.join('+' if x > 0 else '-' for x in row) for row in H]
    if family == 'projective_plane':
        q = params['q']
        return projective_plane(q) if _prime_power(q) else None
    if family == 'mols': return mols(params['n'], params['k'], rt)
    return None


# ------------------------------------------------------------- SAT: CDCL with a RUP proof log

def cdcl(V, clauses, rt, max_conflicts=200_000):
    """('sat', model string) or ('unsat', learned clauses ending with []) or None when the conflict budget ends.
    Every learned clause is a first-UIP clause, implied by unit propagation from the clauses before it."""
    db = []; watches = {}
    val = [None] * (V + 1); level = [0] * (V + 1); reason = [None] * (V + 1); trail = []; lims = []
    activity = [0.0] * (V + 1); inc = 1.0; proof = []
    def add_clause(c):
        db.append(c)
        for lit in c[:2]: watches.setdefault(lit, []).append(len(db) - 1)
    def value(lit):
        v = val[abs(lit)]
        return None if v is None else v == (lit > 0)
    def assign(lit, why):
        val[abs(lit)] = lit > 0; level[abs(lit)] = len(lims); reason[abs(lit)] = why; trail.append(lit)
    units = []
    for c in clauses:
        c = list(dict.fromkeys(c))
        if not c: proof.append([]); return ('unsat', proof)
        if len(c) == 1: units.append(c[0])
        else: add_clause(c)
    for lit in units:
        if value(lit) is False: proof.append([]); return ('unsat', proof)
        if value(lit) is None: assign(lit, None)
    qhead = [0]
    def propagate():
        while qhead[0] < len(trail):
            lit = trail[qhead[0]]; qhead[0] += 1; neg = -lit; rt.budget.use()
            ws = watches.get(neg, []); i = 0
            while i < len(ws):
                ci = ws[i]; c = db[ci]
                if c[0] == neg: c[0], c[1] = c[1], c[0]
                if value(c[0]) is True: i += 1; continue
                moved = False
                for k in range(2, len(c)):
                    if value(c[k]) is not False:
                        c[1], c[k] = c[k], c[1]; watches.setdefault(c[1], []).append(ci); ws[i] = ws[-1]; ws.pop()
                        moved = True; break
                if moved: continue
                if value(c[0]) is False: return ci
                assign(c[0], ci); i += 1
        return None
    def analyze(ci):
        seen = set(); learnt = []; counter = 0; p = None; idx = len(trail) - 1; c = db[ci]; cur = len(lims)
        while True:
            for q in (c if p is None else c[1:]):
                v = abs(q)
                if v not in seen and level[v] > 0:
                    seen.add(v); activity[v] += inc
                    if level[v] >= cur: counter += 1
                    else: learnt.append(q)
            while abs(trail[idx]) not in seen: idx -= 1
            p = trail[idx]; idx -= 1; counter -= 1
            if counter == 0: break
            c = db[reason[abs(p)]]
            if c[0] != p: c = [p] + [x for x in c if x != p]
        learnt = [-p] + learnt
        back = max((level[abs(q)] for q in learnt[1:]), default=0)
        if len(learnt) > 1:
            j = max(range(1, len(learnt)), key=lambda k: level[abs(learnt[k])]); learnt[1], learnt[j] = learnt[j], learnt[1]
        return learnt, back
    def backjump(lv):
        while len(lims) > lv:
            start = lims.pop()
            while len(trail) > start:
                lit = trail.pop(); val[abs(lit)] = None; reason[abs(lit)] = None
        qhead[0] = min(qhead[0], len(trail))
    conflicts = 0; restart = 100
    while True:
        ci = propagate()
        if ci is not None:
            conflicts += 1
            if not lims: proof.append([]); return ('unsat', proof)
            learnt, back = analyze(ci); proof.append(list(learnt)); inc *= 1.05
            backjump(back)
            if len(learnt) == 1: assign(learnt[0], None)
            else: add_clause(learnt); assign(learnt[0], len(db) - 1)
            if conflicts > max_conflicts: return None
            if conflicts % restart == 0: backjump(0); restart = int(restart * 1.5)
            continue
        free = [v for v in range(1, V + 1) if val[v] is None]
        if not free: return ('sat', ''.join('1' if val[v] else '0' for v in range(1, V + 1)))
        v = max(free, key=lambda v: activity[v]); lims.append(len(trail)); assign(-v, None)


def cnf(encoder, args):
    """Her own CNF encodings (the checker encodes the same questions independently)."""
    if encoder == 'php':
        n = args['n']; P, H = n + 1, n; v = lambda p, h: p * H + h + 1
        return P * H, [[v(p, h) for h in range(H)] for p in range(P)] + \
            [[-v(p, h), -v(q, h)] for h in range(H) for p, q in combinations(range(P), 2)]
    if encoder == 'ramsey':
        n, s, t = args['n'], args['s'], args['t']
        idx = {e: i + 1 for i, e in enumerate(combinations(range(n), 2))}
        return len(idx), [[-idx[e] for e in combinations(S, 2)] for S in combinations(range(n), s)] + \
            [[idx[e] for e in combinations(S, 2)] for S in combinations(range(n), t)]
    if encoder == 'schur':
        n, k = args['n'], args['k']; v = lambda i, c: (i - 1) * k + c + 1
        return n * k, [[v(i, c) for c in range(k)] for i in range(1, n + 1)] + \
            [[-v(i, c), -v(j, c), -v(i + j, c)] for c in range(k) for i in range(1, n + 1) for j in range(i, n + 1 - i)]
    if encoder == 'waerden':
        n, Lk = args['n'], args['k']; cls = []
        for a in range(1, n + 1):
            for d in range(1, n):
                if a + (Lk - 1) * d > n: break
                t = [a + i * d for i in range(Lk)]; cls += [t, [-x for x in t]]
        return n, cls
    raise KeyError(encoder)


# ------------------------------------------------------------- circuits

def circuit_search(n, table, max_size, rt):
    """A shortest circuit (binary gates) for the n-input truth table, by breadth-first search over the sets of
    computed functions, keeping one construction per set."""
    size = 1 << n; mask = (1 << size) - 1
    ins = [sum(1 << r for r in range(size) if r >> (n - 1 - i) & 1) for i in range(n)]
    def gate(op, a, b):
        return (((op >> 0 & 1) * (~a & ~b)) | ((op >> 1 & 1) * (~a & b)) | ((op >> 2 & 1) * (a & ~b))
                | ((op >> 3 & 1) * (a & b))) & mask
    if table in ins: return []
    frontier = {frozenset(ins): []}
    for s in range(1, max_size + 1):
        nxt = {}
        for wires, gates in frontier.items():
            order = ins + [None] * len(gates)
            vals = list(ins)
            for g in gates: vals.append(gate(g[0], vals[g[1]], vals[g[2]]))
            for i in range(len(vals)):
                for j in range(i, len(vals)):
                    for op_ in range(16):
                        rt.budget.use()
                        t = gate(op_, vals[i], vals[j])
                        if t in wires: continue
                        g2 = gates + [[op_, i, j]]
                        if t == table: return g2
                        if s < max_size:
                            key = wires | {t}
                            if key not in nxt: nxt[key] = g2
        frontier = nxt
        if len(frontier) > 200_000: return None
    return None


# ------------------------------------------------------------- geometry

PYTH = [(Q(3, 5), Q(4, 5)), (Q(5, 13), Q(12, 13)), (Q(8, 17), Q(15, 17)), (Q(7, 25), Q(24, 25)), (Q(20, 29), Q(21, 29)),
        (Q(12, 37), Q(35, 37)), (Q(9, 41), Q(40, 41)), (Q(28, 53), Q(45, 53))]


def unit_points(n, rt):
    """Subset sums of rational unit vectors: each vector added to a point gives a unit distance."""
    vecs = [(Q(1), Q(0))] + [v for a, b in PYTH for v in ((a, b), (b, a), (-a, b))]
    m = max(1, (n - 1).bit_length()); vecs = vecs[:m]
    pts = []
    for mask in range(1 << m):
        pts.append((sum((v[0] for i, v in enumerate(vecs) if mask >> i & 1), Q(0)),
                    sum((v[1] for i, v in enumerate(vecs) if mask >> i & 1), Q(0))))
    return pts[:n]


def area2(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def no_three(n, rt):
    pts = []
    def ok(p): return all(area2(a, b, p) != 0 for a, b in combinations(pts, 2))
    def go(row):
        rt.budget.use()
        if row == n: return True
        for x, y in combinations(range(n), 2):
            a, b = (x, row), (y, row)
            if ok(a):
                pts.append(a)
                if ok(b):
                    pts.append(b)
                    if go(row + 1): return True
                    pts.pop()
                pts.pop()
        return False
    return [list(p) for p in pts] if go(0) else None


def convex_position(pts):
    k = len(pts)
    for i in range(k):
        for j in range(k):
            if i == j: continue
            side = [area2(pts[i], pts[j], pts[m]) for m in range(k) if m not in (i, j)]
            if all(s > 0 for s in side) or all(s < 0 for s in side): break
        else: return False
    return True


def convex_free(n, k, rt, seed=1):
    rng = random.Random(seed * 100 + n * 10 + k)
    for attempt in range(400):
        pts = [(rng.randrange(1000), rng.randrange(1000)) for _ in range(n)]
        for rounds in range(300):
            rt.budget.use(n)
            if any(area2(a, b, c) == 0 for a, b, c in combinations(pts, 3)):
                pts[rng.randrange(n)] = (rng.randrange(1000), rng.randrange(1000)); continue
            bad = [S for S in combinations(range(n), k) if convex_position([pts[i] for i in S])]
            if not bad: return [list(p) for p in pts]
            i = rng.choice(rng.choice(bad)); pts[i] = (rng.randrange(1000), rng.randrange(1000))
    return None


def kissing(dim, count):
    if dim == 8 and count <= 240:
        vs = []
        for i, j in combinations(range(8), 2):
            for s, t in product((2, -2), repeat=2):
                v = [0] * 8; v[i], v[j] = s, t; vs.append(v)
        for signs in product((1, -1), repeat=8):
            if signs.count(-1) % 2 == 0: vs.append(list(signs))
        return vs[:count]
    vs = []
    for i, j in combinations(range(dim), 2):
        for s, t in product((1, -1), repeat=2):
            v = [0] * dim; v[i], v[j] = s, t; vs.append(v)
    return vs[:count] if len(vs) >= count else None


def rational_distance_set(n, rt, box=60):
    pts = [(x, y) for x in range(box) for y in range(box)]
    def good(a, b):
        d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2; r = isqrt(d); return r * r == d
    chosen = [(0, 0)]
    def concyclic(a, b, c, d):
        rows = [[p[0] - d[0], p[1] - d[1], (p[0] - d[0]) ** 2 + (p[1] - d[1]) ** 2] for p in (a, b, c)]
        return (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1]) - rows[0][1] * (rows[1][0] * rows[2][2] -
                rows[1][2] * rows[2][0]) + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])) == 0
    def go(start):
        rt.budget.use()
        if len(chosen) == n: return True
        for i in range(start, len(pts)):
            p = pts[i]
            if p in chosen or not all(good(p, q) for q in chosen): continue
            if any(area2(a, b, p) == 0 for a, b in combinations(chosen, 2)): continue
            if any(concyclic(a, b, c, p) for a, b, c in combinations(chosen, 3)): continue
            chosen.append(p)
            if go(i + 1): return True
            chosen.pop()
        return False
    return [list(p) for p in chosen] if go(0) else None


def moser_spindle():
    """Two rhombi of unit equilateral triangles at the origin, the second turned by theta with cos = 5/6 and sin =
    sqrt(11)/6 so that the far tips are at distance 1: coordinates in Q(sqrt 3, sqrt 11), as [1, sqrt3, sqrt11,
    sqrt33] coefficients."""
    h = Q(1, 2)
    def pt(x, y): return [x, y]
    O = pt([0, 0, 0, 0], [0, 0, 0, 0]); M1 = pt([0, h, 0, 0], [h, 0, 0, 0]); M2 = pt([0, h, 0, 0], [-h, 0, 0, 0])
    T1 = pt([0, 1, 0, 0], [0, 0, 0, 0])
    c, s = Q(5, 6), Q(1, 6)  # cos theta = 5/6, sin theta = sqrt(11)/6
    def rot(p):
        (x0, x1, x2, x3), (y0, y1, y2, y3) = p
        # x' = c x - s sqrt11 y, y' = s sqrt11 x + c y; sqrt11 * sqrt3 = sqrt33, sqrt11 * sqrt11 = 11
        def times_sqrt11(v): a, b, cc, d = v; return [11 * cc, 11 * d, a, b]
        xs, ys = times_sqrt11([x0, x1, x2, x3]), times_sqrt11([y0, y1, y2, y3])
        return [[c * a - s * b for a, b in zip([x0, x1, x2, x3], ys)], [s * a + c * b for a, b in zip(xs, [y0, y1, y2, y3])]]
    pts = [O, M1, M2, T1, rot(M1), rot(M2), rot(T1)]
    enc = [[[[q.numerator, q.denominator] for q in coord] for coord in p] for p in pts]
    edges = [[0, 1], [0, 2], [1, 2], [1, 3], [2, 3], [0, 4], [0, 5], [4, 5], [4, 6], [5, 6], [3, 6]]
    return dict(points=enc, edges=edges)


def illuminate(vs):
    V = [(Q(x) if type(x) is int else Q(*x), Q(y) if type(y) is int else Q(*y)) for x, y in vs]
    n = len(V)
    def unit(v):
        m = (float(v[0]) ** 2 + float(v[1]) ** 2) ** 0.5
        return (Q(float(v[0]) / m).limit_denominator(1000), Q(float(v[1]) / m).limit_denominator(1000))
    # directions from the polygon itself: each vertex's cone bisector, and for each edge b c the sum of the unit edges
    # leaving it backwards at b and forwards at c (inside both cones when the corners are not too sharp)
    cand = []
    for i in range(n):
        a, b, c = V[i - 1], V[i], V[(i + 1) % n]; d = V[(i + 2) % n]
        u1, u2 = unit((a[0] - b[0], a[1] - b[1])), unit((c[0] - b[0], c[1] - b[1]))
        cand.append((u1[0] + u2[0], u1[1] + u2[1]))
        w1, w2 = unit((a[0] - b[0], a[1] - b[1])), unit((d[0] - c[0], d[1] - c[1]))
        cand.append((w1[0] + w2[0], w1[1] + w2[1]))
    cand = [c for c in cand if c != (0, 0)]
    cand += [(1, 1), (-1, 1), (-1, -1), (1, -1), (1, 0), (0, 1), (-1, 0), (0, -1), (2, 1), (-1, 2), (-2, -1), (1, -2)]
    def lit(d, i):
        a, b, c = V[i - 1], V[i], V[(i + 1) % n]
        n1 = (-(b[1] - a[1]), b[0] - a[0]); n2 = (-(c[1] - b[1]), c[0] - b[0])
        return d[0] * n1[0] + d[1] * n1[1] > 0 and d[0] * n2[0] + d[1] * n2[1] > 0
    for k in range(1, 5):
        for D in combinations(cand, k):
            if all(any(lit(d, i) for d in D) for i in range(n)):
                return [[[x.numerator, x.denominator] if type(x) is Q else x for x in d] for d in D]
    return None


def borsuk_parts(points, rt):
    P = [tuple(Q(x) if type(x) is int else Q(*x) for x in p) for p in points]; d = len(P[0])
    def d2(a, b): return sum((x - y) ** 2 for x, y in zip(a, b))
    D = max(d2(a, b) for a, b in combinations(P, 2))
    adj = [set() for _ in P]
    for i, j in combinations(range(len(P)), 2):
        if d2(P[i], P[j]) == D: adj[i].add(j); adj[j].add(i)
    return color_with(len(P), adj, d + 1, rt)


def kakeya(q, n, rt):
    pts = list(product(range(q), repeat=n)); S = set()
    dirs = [d for d in product(range(q), repeat=n) if any(d) and d[next(i for i in range(n) if d[i])] == 1]
    for d in dirs:
        best, gain = None, None
        for b in pts:
            rt.budget.use()
            line = [tuple((b[i] + t * d[i]) % q for i in range(n)) for t in range(q)]
            new = sum(1 for x in line if x not in S)
            if gain is None or new < gain: best, gain = line, new
        S.update(best)
    return [list(p) for p in sorted(S)]


# ------------------------------------------------------------- groups, knots, algebra, curves

def ac_search(rels, rt, limit=200_000, maxlen=30):
    """Best-first search over Andrews-Curtis moves, shortest total relator length first."""
    import heapq
    def red(w):
        out = []
        for x in w:
            if out and out[-1] == -x: out.pop()
            else: out.append(x)
        return out
    def cyc(w):
        w = red(w)
        while len(w) >= 2 and w[0] == -w[-1]: w = w[1:-1]
        return w
    def trivial(r): return all(len(cyc(x)) == 1 for x in r) and sorted(abs(cyc(x)[0]) for x in r) == [1, 2]
    start = (tuple(red(rels[0])), tuple(red(rels[1])))
    seen = {start: None}; heap = [(len(start[0]) + len(start[1]), 0, start)]; tick = 0
    while heap:
        _, _, st = heapq.heappop(heap); rt.budget.use()
        if trivial([list(st[0]), list(st[1])]):
            path = []
            while seen[st] is not None: prev, mv = seen[st]; path.append(mv); st = prev
            return path[::-1]
        for i in (0, 1):
            r, o = list(st[i]), list(st[1 - i])
            moves = [(['inv', i], red([-x for x in reversed(r)])), (['mul', i], red(r + o)),
                     (['mulinv', i], red(r + [-x for x in reversed(o)]))]
            moves += [(['conj', i, g], red([g] + r + [-g])) for g in (1, -1, 2, -2)]
            for mv, nr in moves:
                if len(nr) > maxlen: continue
                ns = (tuple(nr), st[1]) if i == 0 else (st[0], tuple(nr))
                if ns not in seen:
                    seen[ns] = (st, mv); tick += 1; heapq.heappush(heap, (len(ns[0]) + len(ns[1]), tick, ns))
                    if len(seen) > limit: return None
    return None


def square_search(vs):
    P = [(Q(x) if type(x) is int else Q(*x), Q(y) if type(y) is int else Q(*y)) for x, y in vs]
    E = list(zip(P, P[1:] + P[:1]))
    # corners A = a0 + s (a1 - a0) on edge i and B = b0 + t (b1 - b0) on edge j; with R the quarter turn, C = B + R(B - A)
    # and D = A + R(B - A) must lie on edges k and l: two linear equations in s, t
    for i, j, k, l in product(range(len(E)), repeat=4):
        for sgn in (1, -1):
            (a0, a1), (b0, b1), (c0, c1), (d0, d1) = E[i], E[j], E[k], E[l]
            def R(v): return (-sgn * v[1], sgn * v[0])
            # A(s) = a0 + s u, B(t) = b0 + t w
            u = (a1[0] - a0[0], a1[1] - a0[1]); w = (b1[0] - b0[0], b1[1] - b0[1])
            # C(s, t) = B + R(B - A) = b0 + t w + R(b0 - a0) + t R(w) - s R(u); on line c0 + x (c1 - c0): cross = 0
            def affine_point(base, ts, ss):
                return base, ts, ss
            Cb = (b0[0] + R((b0[0] - a0[0], b0[1] - a0[1]))[0], b0[1] + R((b0[0] - a0[0], b0[1] - a0[1]))[1])
            Ct = (w[0] + R(w)[0], w[1] + R(w)[1]); Cs = (-R(u)[0], -R(u)[1])
            Db = (a0[0] + R((b0[0] - a0[0], b0[1] - a0[1]))[0], a0[1] + R((b0[0] - a0[0], b0[1] - a0[1]))[1])
            Dt = R(w); Ds = (u[0] - R(u)[0], u[1] - R(u)[1])
            ec = (c1[0] - c0[0], c1[1] - c0[1]); ed = (d1[0] - d0[0], d1[1] - d0[1])
            def cross(a, b): return a[0] * b[1] - a[1] * b[0]
            # cross(point - c0, ec) = 0: linear in s, t
            e1 = (cross(Cs, ec), cross(Ct, ec), -cross((Cb[0] - c0[0], Cb[1] - c0[1]), ec))
            e2 = (cross(Ds, ed), cross(Dt, ed), -cross((Db[0] - d0[0], Db[1] - d0[1]), ed))
            det = e1[0] * e2[1] - e1[1] * e2[0]
            if det == 0: continue
            s = (e1[2] * e2[1] - e1[1] * e2[2]) / det; t = (e1[0] * e2[2] - e1[2] * e2[0]) / det
            if not (0 <= s <= 1 and 0 <= t <= 1): continue
            A = (a0[0] + s * u[0], a0[1] + s * u[1]); B = (b0[0] + t * w[0], b0[1] + t * w[1])
            if A == B: continue
            C = (B[0] + R((B[0] - A[0], B[1] - A[1]))[0], B[1] + R((B[0] - A[0], B[1] - A[1]))[1])
            D = (A[0] + R((B[0] - A[0], B[1] - A[1]))[0], A[1] + R((B[0] - A[0], B[1] - A[1]))[1])
            def on(x, e0, e1_):
                return cross((x[0] - e0[0], x[1] - e0[1]), (e1_[0] - e0[0], e1_[1] - e0[1])) == 0 and \
                    min(e0[0], e1_[0]) <= x[0] <= max(e0[0], e1_[0]) and min(e0[1], e1_[1]) <= x[1] <= max(e0[1], e1_[1])
            if on(C, c0, c1) and on(D, d0, d1):
                return [[[x.numerator, x.denominator] for x in p] for p in (A, B, C, D)]
    return None


def _pm(p):
    """{(i, j): Fraction} from [[coefficient, [i, j]], ...]."""
    out = {}
    for c, e in p:
        q = Q(c) if type(c) is int else Q(*c); out[tuple(e)] = out.get(tuple(e), Q(0)) + q
    return {k: v for k, v in out.items() if v}


def _mul(a, b):
    out = {}
    for k1, v1 in a.items():
        for k2, v2 in b.items():
            k = (k1[0] + k2[0], k1[1] + k2[1]); out[k] = out.get(k, Q(0)) + v1 * v2
    return {k: v for k, v in out.items() if v}


def _add(a, b, c=Q(1)):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, Q(0)) + c * v
        if not out[k]: del out[k]
    return out


def _pow(a, e):
    out = {(0, 0): Q(1)}
    for _ in range(e): out = _mul(out, a)
    return out


def _deg(p): return max((i + j for i, j in p), default=-1)


def _top(p):
    d = _deg(p); return {k: v for k, v in p.items() if sum(k) == d}


def plane_inverse(F, rt):
    """Invert a polynomial automorphism of the plane by degree reduction (Jung-van der Kulk): subtract c g^k from the
    higher-degree component while its top form is c times a power of the other's, down to an affine map."""
    f, g = _pm(F[0]), _pm(F[1]); steps = []
    for _ in range(64):
        rt.budget.use(len(f) + len(g))
        df, dg = _deg(f), _deg(g)
        if df <= 1 and dg <= 1: break
        swap = dg > df
        hi, lo = (g, f) if swap else (f, g)
        dh, dl = _deg(hi), _deg(lo)
        if dl < 1 or dh % dl: return None
        k = dh // dl; tl = _top(lo); th = _top(hi); pk = _pow(tl, k)
        key = next(iter(pk)); c = th.get(key, Q(0)) / pk[key]
        if c == 0 or _add(th, pk, -c): return None
        hi = _add(hi, _pow(lo, k), -c)
        steps.append((1 if swap else 0, c, k))
        if swap: g = hi
        else: f = hi
    # affine map (f, g) = M (x, y) + v; the inverse is M^-1 ((x, y) - v)
    a, b, e = f.get((1, 0), Q(0)), f.get((0, 1), Q(0)), f.get((0, 0), Q(0))
    c_, d, h = g.get((1, 0), Q(0)), g.get((0, 1), Q(0)), g.get((0, 0), Q(0))
    det = a * d - b * c_
    if det == 0 or _deg(f) > 1 or _deg(g) > 1: return None
    # W starts as the identity; each reduction step T (component i minus c times the other to the k) composes on it
    X, Y = {(1, 0): Q(1)}, {(0, 1): Q(1)}; W = [X, Y]
    for comp, c, k in steps:
        if comp == 0: W = [_add(W[0], _pow(W[1], k), -c), W[1]]
        else: W = [W[0], _add(W[1], _pow(W[0], k), -c)]
    U = [_add(W[0], {(0, 0): e}, -1) if e else W[0], _add(W[1], {(0, 0): h}, -1) if h else W[1]]
    G = [_add({k: v * d / det for k, v in U[0].items()}, U[1], -b / det),
         _add({k: v * (-c_) / det for k, v in U[0].items()}, U[1], a / det)]
    return [[[[v.numerator, v.denominator], list(k)] for k, v in sorted(p.items())] for p in G]


def tensor_flip(n, m, p, rank, rt, seeds=40, steps=100_000):
    """Flip-graph search over GF(2) (Kauers and Moosbauer): from the standard scheme, random flips
    a (x) b (x) c + a (x) b' (x) c' -> a (x) (b + b') (x) c + a (x) b' (x) (c' + c), with reductions whenever terms sharing
    a factor have dependent second factors, until the scheme has at most the target rank; then a sign for every
    coefficient by backtracking, so that the scheme holds over the integers. Factors are bit masks over GF(2)."""
    sizes = (n * m, m * p, p * n)
    def standard():
        return [[1 << (i * m + j), 1 << (j * p + k), 1 << (k * n + i)] for i in range(n) for j in range(m) for k in range(p)]
    def reduce(terms):
        changed = True
        while changed:
            changed = False
            terms[:] = [t for t in terms if t[0] and t[1] and t[2]]
            rt.budget.use(len(terms))
            for f in range(3):
                groups = {}
                for i, t in enumerate(terms): groups.setdefault(t[f], []).append(i)
                for g in groups.values():
                    if len(g) < 2: continue
                    for o1 in [x for x in range(3) if x != f]:
                        o2 = 3 - f - o1
                        for i, k in combinations(g, 2):
                            if terms[i][o1] == terms[k][o1]:
                                terms[i][o2] ^= terms[k][o2]; del terms[k]; changed = True; break
                        if not changed and len(g) >= 3:
                            for k in g:
                                for i, j in combinations([x for x in g if x != k], 2):
                                    if terms[k][o1] == terms[i][o1] ^ terms[j][o1]:
                                        terms[i][o2] ^= terms[k][o2]; terms[j][o2] ^= terms[k][o2]; del terms[k]
                                        changed = True; break
                                if changed: break
                        if changed: break
                    if changed: break
                if changed: break
    def walk(seed):
        rng = random.Random(seed * 7919 + n * 100 + m * 10 + p); terms = standard(); reduce(terms)
        for _ in range(steps):
            if len(terms) <= rank: return terms
            rt.budget.use(4)
            f = rng.randrange(3); groups = {}
            for i, t in enumerate(terms): groups.setdefault(t[f], []).append(i)
            pairs = [g for g in groups.values() if len(g) >= 2]
            if not pairs: continue
            g = rng.choice(pairs); x, y = rng.sample(g, 2)
            o1, o2 = [i for i in range(3) if i != f]
            if rng.random() < 0.5: o1, o2 = o2, o1
            terms[x][o1] ^= terms[y][o1]; terms[y][o2] ^= terms[x][o2]
            reduce(terms)
        return terms if len(terms) <= rank else None
    def lift(terms):
        cells = [(t, f, i) for t, term in enumerate(terms) for f in range(3) for i in range(sizes[f]) if term[f] >> i & 1]
        index = {c: k for k, c in enumerate(cells)}; cons = []
        for a in range(sizes[0]):
            for b in range(sizes[1]):
                for c in range(sizes[2]):
                    want = int(a // m == c % n and a % m == b // p and b % p == c // n)
                    ts = [t for t, term in enumerate(terms) if term[0] >> a & 1 and term[1] >> b & 1 and term[2] >> c & 1]
                    if not ts:
                        if want: return None
                        continue
                    cons.append(([(index[(t, 0, a)], index[(t, 1, b)], index[(t, 2, c)]) for t in ts], want))
        sign = [0] * len(cells); watch = [[] for _ in cells]; tries = [0]
        for ci, (prods, _) in enumerate(cons):
            for pr in prods:
                for v in pr: watch[v].append(ci)
        order = sorted(range(len(cells)), key=lambda v: -len(watch[v]))
        def ok(ci):
            prods, want = cons[ci]; total = free = 0
            for pr in prods:
                if sign[pr[0]] and sign[pr[1]] and sign[pr[2]]: total += sign[pr[0]] * sign[pr[1]] * sign[pr[2]]
                else: free += 1
            return abs(want - total) <= free and (want - total - free) % 2 == 0
        def go(k):
            tries[0] += 1; rt.budget.use()
            if tries[0] > 2_000_000: return False
            if k == len(order): return True
            v = order[k]
            for sg in (1, -1):
                sign[v] = sg
                if all(ok(ci) for ci in watch[v]) and go(k + 1): return True
            sign[v] = 0
            return False
        if not go(0): return None
        return [[[sign[index[(t, f, i)]] if term[f] >> i & 1 else 0 for i in range(sizes[f])] for f in range(3)]
                for t, term in enumerate(terms)]
    for seed in range(seeds):
        found = walk(seed)
        if found is None: continue
        lifted = lift(found)
        if lifted is not None: return lifted
    return None


def rational_points(a, b, rt, D=12, U=400):
    out = []
    for d in range(1, D + 1):
        for u in range(-U, U + 1):
            if gcd(u, d) != 1: continue
            rt.budget.use()
            rhs = u ** 3 + a * u * d ** 4 + b * d ** 6
            if rhs < 0: continue
            v = isqrt(rhs)
            if v * v == rhs:
                out.append([[u, d * d], [v, d ** 3]])
                if v: out.append([[u, d * d], [-v, d ** 3]])
            if len(out) >= 40: return out
    return out or None


# ------------------------------------------------------------- dispatch

def run_search(rt, root, kind, fn):
    d = root['data']
    try: found = fn(d['family'], d['params'], rt)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, IndexError, AssertionError): return []
    if found is None: return []
    claim = rt.propose(kind, {'q': root['kind'], 'family': d['family'], 'params': d['params'], kind: found}, (root,))
    return [claim] if rt.check(claim) else []


@op('graph_search', 'NS', ('graph_q',), ('witness',),
    'Find a coloring, Hamiltonian path, graceful labelings of every small tree, a cycle double cover, a total coloring '
    'or a Ramsey coloring (Paley graphs).')
def graph_search_op(rt, root): return run_search(rt, root, 'witness', lambda f, p, rt: graph_search(p, rt, f))


@op('setsys_search', 'NS', ('setsys_q',), ('witness',), 'Find a sunflower-free family of sets by randomized greedy search.')
def setsys_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: sunflower_free(p, rt) if f == 'sunflower_free' else None)


@op('additive_search', 'NS', ('additive_q',), ('witness',),
    'Find k primes in arithmetic progression, or a Sidon set of a given size in 1..n.')
def additive_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: prime_ap(p, rt) if f == 'prime_ap' else
                      sidon_set(p, rt) if f == 'sidon_set' else None)


@op('design_search', 'NS', ('design_q',), ('witness',),
    'Construct a Hadamard matrix (Sylvester, Paley I and II, Kronecker), a projective plane over a finite field, or '
    'mutually orthogonal Latin squares (field constructions; order 10 by transversal search).')
def design_search_op(rt, root): return run_search(rt, root, 'witness', lambda f, p, rt: design_search(p, rt, f))


@op('sat_search', 'NS', ('sat_q',), ('witness',), 'Solve a finite question\'s CNF encoding with CDCL and give a model.')
def sat_search(rt, root):
    def fn(f, p, rt):
        if f != 'sat': return None
        V, cl = cnf(p['encoder'], p['args']); r = cdcl(V, cl, rt)
        return r[1] if r and r[0] == 'sat' else None
    return run_search(rt, root, 'witness', fn)


@op('sat_prove', 'NS', ('sat_q',), ('proof',),
    'Refute a finite question\'s CNF encoding with CDCL, logging each learned clause: a RUP proof ending in the empty '
    'clause.')
def sat_prove(rt, root):
    def fn(f, p, rt):
        if f != 'unsat': return None
        V, cl = cnf(p['encoder'], p['args']); r = cdcl(V, cl, rt)
        return r[1] if r and r[0] == 'unsat' else None
    return run_search(rt, root, 'proof', fn)


@op('circuit_search', 'NS', ('circuit_q',), ('witness',), 'Find a smallest circuit of binary gates for a truth table.')
def circuit_search_op(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: circuit_search(p['n'], p['table'], p['size'], rt)
                      if f == 'circuit' else None)


def config_search(f, p, rt):
    if f == 'unit_distances': return [[[x.numerator, x.denominator] for x in pt] for pt in unit_points(p['n'], rt)]
    if f == 'no_three_in_line': return no_three(p['n'], rt)
    if f == 'convex_free': return convex_free(p['n'], p['k'], rt)
    if f == 'kissing': return kissing(p['dim'], p['count'])
    if f == 'rational_distances': return rational_distance_set(p['n'], rt)
    if f == 'unit_distance_graph': return moser_spindle() if (p['a'], p['b'], p['colors']) == (3, 11, 4) else None
    if f == 'illumination': return illuminate(p['vertices'])
    if f == 'borsuk': return borsuk_parts(p['points'], rt)
    if f == 'heilbronn': return heilbronn(p['n'], p['area'], rt)
    if f == 'sphere_energy': return sphere_points(p['n'], p['energy'], rt)
    return None


def sphere_points(n, energy, rt, seed=5):
    """n points on the unit sphere by projected gradient descent in floating point, then moved to exact rational points
    of the sphere by inverse stereographic projection of rational approximations; the energy is bounded exactly."""
    import math
    target = Q(energy) if type(energy) is int else Q(*energy); rng = random.Random(seed * 17 + n)
    def rational(p):
        x, y, z = p; s = 1 if z <= 0 else -1  # project from the pole farther away
        u = Q(x / (1 - s * z)).limit_denominator(10 ** 7); v = Q(y / (1 - s * z)).limit_denominator(10 ** 7)
        r = u * u + v * v
        return (2 * u / (1 + r), 2 * v / (1 + r), s * (r - 1) / (1 + r))
    def bound(P):
        units = 0
        for i in range(n):
            for j in range(i + 1, n):
                d2 = sum((a - b) ** 2 for a, b in zip(P[i], P[j])); a, b = d2.numerator, d2.denominator
                units += -(-(isqrt(a * b * 10 ** 30) + 1) // a)
        return Q(units, 10 ** 15)
    for attempt in range(8):
        pts = []
        for _ in range(n):
            v = [rng.gauss(0, 1) for _ in range(3)]; m = math.sqrt(sum(c * c for c in v)); pts.append([c / m for c in v])
        step = 0.05
        for it in range(4000):
            rt.budget.use(n * n)
            force = [[0.0, 0.0, 0.0] for _ in range(n)]
            for i in range(n):
                for j in range(i + 1, n):
                    d = [pts[i][k] - pts[j][k] for k in range(3)]; r2 = d[0] ** 2 + d[1] ** 2 + d[2] ** 2
                    f = 1 / (r2 * math.sqrt(r2))
                    for k in range(3): force[i][k] += f * d[k]; force[j][k] -= f * d[k]
            for i in range(n):
                q = [pts[i][k] + step * force[i][k] / n for k in range(3)]; m = math.sqrt(sum(c * c for c in q))
                pts[i] = [c / m for c in q]
            if it % 1000 == 999: step /= 2
        P = [rational(p) for p in pts]
        if len(set(P)) == n and bound(P) <= target:
            return [[[c.numerator, c.denominator] for c in p] for p in P]
    return None


def heilbronn(n, area, rt, seed=3):
    """Hill climbing on a grid of the unit square: move a point of a smallest triangle to a random nearby grid point and
    keep the move when the smallest area does not drop; restart from random points when stuck."""
    target = Q(area) if type(area) is int else Q(*area); rng = random.Random(seed * 31 + n)
    grid = 120
    def smallest(pts):
        rt.budget.use(n ** 3 // 6 + 1)
        return min((abs(area2(a, b, c)), (i, j, k)) for (i, a), (j, b), (k, c) in combinations(enumerate(pts), 3))
    for attempt in range(40):
        pts = [(rng.randrange(grid + 1), rng.randrange(grid + 1)) for _ in range(n)]
        best = smallest(pts); stall = 0
        while stall < 600:
            if Q(best[0], 2 * grid * grid) >= target:
                return [[[x, grid], [y, grid]] for x, y in pts]
            i = rng.choice(best[1]); step = rng.choice((1, 2, 4, 8, 16))
            x, y = pts[i]; cand = (min(grid, max(0, x + rng.randint(-step, step))), min(grid, max(0, y + rng.randint(-step, step))))
            if cand in pts: stall += 1; continue
            trial = pts[:i] + [cand] + pts[i + 1:]; now = smallest(trial)
            if now[0] >= best[0]:
                stall = 0 if now[0] > best[0] else stall + 1; pts, best = trial, now
            else: stall += 1
    return None


@op('config_search', 'NS', ('config_q',), ('witness',),
    'Construct or search a geometric configuration: unit distances, a Heilbronn set, no three in line, a convex-free '
    'set, a kissing arrangement, a rational distance set, the Moser spindle, illuminating directions, a Borsuk '
    'partition or low-energy points on the sphere.')
def config_search_op(rt, root): return run_search(rt, root, 'witness', config_search)


@op('kakeya_search', 'NS', ('kakeya_q',), ('witness',),
    'Build a Kakeya set over F_q: for each direction, the line overlapping the set most.')
def kakeya_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: kakeya(p['q'], p['n'], rt) if f == 'kakeya_set' else None)


@op('group_search', 'NS', ('group_q',), ('witness',),
    'Search Andrews-Curtis moves breadth first for a trivialization of a balanced presentation.')
def group_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: ac_search(p['relators'], rt) if f == 'ac_trivial' else None)


@op('knot_search', 'NS', ('knot_q',), ('witness',),
    'Find a square inscribed in a polygon: corners on edges by exact linear algebra.')
def knot_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: square_search(p['vertices']) if f == 'inscribed_square' else None)


@op('algebra_search', 'NS', ('algebra_q',), ('witness',),
    'Invert a plane polynomial automorphism by degree reduction, or search a matrix multiplication scheme by flips.')
def algebra_search(rt, root):
    def fn(f, p, rt):
        if f == 'polynomial_inverse': return plane_inverse(p['F'], rt)
        if f == 'tensor': return tensor_flip(p['n'], p['m'], p['p'], p['rank'], rt)
        return None
    return run_search(rt, root, 'witness', fn)


@op('variety_search', 'NS', ('variety_q',), ('witness',), 'Find rational points of small height on an elliptic curve.')
def variety_search(rt, root):
    return run_search(rt, root, 'witness', lambda f, p, rt: rational_points(p['a'], p['b'], rt)
                      if f == 'rational_points' else None)


def _w(rt, tool, family, params): return rt.given(tool, dict(family=family, params=params))


FIXTURES = {
    'graph_search': [lambda rt: [_w(rt, 'graph_q', 'coloring', dict(graph=dict(named='petersen'), k=3))],
                     lambda rt: [_w(rt, 'graph_q', 'graceful_trees', dict(n=6))]],
    'setsys_search': [lambda rt: [_w(rt, 'setsys_q', 'sunflower_free', dict(w=2, k=3, size=5))]],
    'additive_search': [lambda rt: [_w(rt, 'additive_q', 'prime_ap', dict(k=5))]],
    'design_search': [lambda rt: [_w(rt, 'design_q', 'hadamard', dict(n=12))]],
    'sat_search': [lambda rt: [_w(rt, 'sat_q', 'sat', dict(encoder='schur', args=dict(n=4, k=2)))]],
    'sat_prove': [lambda rt: [_w(rt, 'sat_q', 'unsat', dict(encoder='php', args=dict(n=3)))]],
    'circuit_search': [lambda rt: [_w(rt, 'circuit_q', 'circuit', dict(n=2, table=6, size=2))]],
    'config_search': [lambda rt: [_w(rt, 'config_q', 'kissing', dict(dim=4, count=24))]],
    'kakeya_search': [lambda rt: [_w(rt, 'kakeya_q', 'kakeya_set', dict(q=3, n=2))]],
    'group_search': [lambda rt: [_w(rt, 'group_q', 'ac_trivial', dict(relators=[[1, 2, -1], [2, 2, 1]]))]],
    'knot_search': [lambda rt: [_w(rt, 'knot_q', 'inscribed_square', dict(vertices=[[0, 0], [4, 0], [4, 3], [0, 3]]))]],
    'algebra_search': [lambda rt: [_w(rt, 'algebra_q', 'polynomial_inverse',
                                      dict(F=[[[1, [1, 0]], [1, [0, 2]]], [[1, [0, 1]]]]))]],
    'variety_search': [lambda rt: [_w(rt, 'variety_q', 'rational_points', dict(a=-2, b=1))]],
}
