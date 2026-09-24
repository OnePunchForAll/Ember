"""Operators on binary words avoiding a set of patterns.

Complementing letters or reversing every pattern preserves the number of
avoiding words of each length, so a checked law transfers to the image pattern
set. The Goulden-Jackson cluster method gives the generating function
1/(1 - 2x - sum_w C_w(x)) from the overlap system of the patterns, independently
of the prefix automaton that the checker uses.
"""
from fractions import Fraction as Q
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_ops_word_' + name, Path(__file__).with_name(name + '.py'))
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


def word_law(law):
    return law['status'] == 'checked' and law['data']['def']['type'] == 'words'


def image_law(rt, law, patterns):
    d = law['data']
    claim = rt.transfer('law', dict(d, **{'def': dict(type='words', patterns=patterns)}), law)
    return [claim] if rt.check(claim) else []


@op('word_complement_law', 'SE', ('law',), ('law',),
    'Swapping 0 and 1 in every pattern is a length-preserving bijection of avoiding words.')
def word_complement_law(rt, law):
    if not word_law(law): return []
    patterns = [w.translate(str.maketrans('01', '10')) for w in law['data']['def']['patterns']]
    return image_law(rt, law, patterns) if patterns != law['data']['def']['patterns'] else []


@op('word_reverse_law', 'SE', ('law',), ('law',),
    'Reversing words is a length-preserving bijection between avoiders of P and of reversed P.')
def word_reverse_law(rt, law):
    if not word_law(law): return []
    patterns = [w[::-1] for w in law['data']['def']['patterns']]
    return image_law(rt, law, patterns) if patterns != law['data']['def']['patterns'] else []


@op('word_automaton_carrier', 'SE', ('law',), ('law',),
    'Transfer a checked word law to the transition-count question of the producer\'s prefix automaton.')
def word_automaton_carrier(rt, law):
    if not word_law(law): return []
    M, u, v = L.word_matrix(law['data']['def']['patterns'])
    claim = rt.transfer('law', dict(law['data'], **{'def': dict(type='matrix', matrix=M, initial=u, terminal=v)}), law)
    return [claim] if rt.check(claim) else []


def overlaps(u, w):
    """Nonempty strings that are proper suffixes of u and proper prefixes of w."""
    return [u[len(u) - k:] for k in range(1, min(len(u), len(w))) if u[len(u) - k:] == w[:k]]


def det(A):
    if len(A) == 1: return A[0][0]
    total = []
    for j in range(len(A)):
        minor = [row[:j] + row[j + 1:] for row in A[1:]]
        term = L.pmul(A[0][j], det(minor))
        total = L.padd(total, term if j % 2 == 0 else L.pscale(term, -1))
    return total


@op('word_cluster_gf', 'NS', ('seq',), ('gf',),
    'Goulden-Jackson: solve C_w + sum_u K_wu C_u = -x^|w| by Cramer\'s rule and form 1/(1 - 2x - sum C_w).')
def word_cluster_gf(rt, seq):
    sd = seq['data']['def']
    if sd['type'] != 'words' or len(sd['patterns']) > 3: return []
    B = sd['patterns']
    if any(a != b and a in b for a in B for b in B): return []
    n = len(B)
    A = [[[Q(int(i == j))] for j in range(n)] for i in range(n)]
    for i, w in enumerate(B):
        for j, u in enumerate(B):
            for s in overlaps(u, w):
                term = [Q(0)] * (len(w) - len(s)) + [Q(1)]
                A[i][j] = L.padd(A[i][j], term)
    b = [L.pscale([Q(0)] * len(w) + [Q(1)], -1) for w in B]
    D = det(A); rt.budget.use(8 ** n)
    total = []
    for i in range(n):
        Ai = [[b[r] if c == i else A[r][c] for c in range(n)] for r in range(n)]
        total = L.padd(total, det(Ai))
    # f = 1 / (1 - 2x - total/D) = D / (D*(1 - 2x) - total)
    denominator = L.padd(L.pmul(D, [Q(1), Q(-2)]), L.pscale(total, -1))
    numerator = D
    if not denominator or denominator[0] == 0: return []
    scale = denominator[0]
    claim = rt.propose('gf', {'def': sd, 'numerator': [L.enc(x / scale) for x in L.ptrim(numerator)],
                              'denominator': [L.enc(x / scale) for x in L.ptrim(denominator)]}, (seq,))
    return [claim] if rt.check(claim) else []


def _law(rt, patterns, coefficients, initial):
    obj = rt.propose('law', {'def': dict(type='words', patterns=patterns), 'coefficients': coefficients, 'initial': initial})
    rt.check(obj); return obj


def _words_law(rt, patterns):
    sd = dict(type='words', patterns=patterns); M = L.word_matrix(patterns)[0]
    P = L.charpoly(M); r = len(P) - 1
    return _law(rt, patterns, [L.enc(-P[j]) for j in range(r)], [L.enc(x) for x in L.terms(sd, r)])


FIXTURES = {
    'word_complement_law': [lambda rt: [_words_law(rt, ['0110', '111'])]],
    'word_reverse_law': [lambda rt: [_words_law(rt, ['0010', '11'])]],
    'word_automaton_carrier': [lambda rt: [_words_law(rt, ['0110', '111'])]],
    'word_cluster_gf': [lambda rt: [rt.given('seq', {'def': dict(type='words', patterns=['0110', '111'])})]],
}
