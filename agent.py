"""Ember's autonomous research agent: a non-LLM, offline loop over her typed language.

A problem is stated in the language (a family of residue classes to cover, a
class map to prove descending, a claim to decide, objects to explore). Each
step the agent lists the open targets of its goal, forms candidate moves from
every operator whose signature accepts a target or an object derived from it,
ranks them by the doctrine score over measured outcomes and costs, executes the
best one under a work bound, and keeps whatever the separate checker admits.

The agent invents moves in two ways. A checked result whose derivation chains
two to four operators is promoted to a macro that replays the chain on new
targets. Pairs of operators whose output kind is the next one's input kind are
proposed as compositions from the language's type signatures and promoted when
they first produce a checked result. The ansatz operators also turn a family
found outside the base grammar into a reusable template object.

Scores schedule work and are never evidence. Saved objects are checked again
on resume. A report lists only checked results, residuals and measured costs;
an open problem stays UNKNOWN unless the checker settles it.

Every report mines its own failures: the open targets, the moves each received
and the residuals they left, with a goal-specific profile of what stayed open.
Strategy outcomes are retained across problems in a bounded library that later
problems read as discounted reports, and each goal names related problems to
try next.
"""
import hashlib
import json
from math import gcd
from pathlib import Path
import time

VERSION = 'ember.autonomous_agent.v1'
MAX_SAMPLES = 128
MAX_MACROS = 32
MAX_LOG = 64
MAX_TRIED = 6000
MAX_PER_TARGET = 1
MAX_TARGET_MOVES = 24
COMPANIONS = 4
# Operators that read the workspace: an attempt is new whenever the goal's progress has changed since.
READS_WORKSPACE = frozenset(('egypt_cover_assemble', 'egypt_finite_verify', 'collatz_cover_assemble', 'egypt_choose_lift'))
MACRO_STEPS = 4
PROPOSE_EVERY = 25
# A move that fails only for lack of work is retried once with this many times the allocation.
ESCALATION = 4
SCORE_FLOOR = 0.000001
LIBRARY_ID = 'strategy-library'
LIBRARY_ENTRIES = 256
LIBRARY_REPORTS = 2
# A class is handed to refinement only after every family grammar missed it.
FAMILY_MISSES = frozenset(('ansatz miss', 'extended ansatz miss', 'classical miss'))
# The generator whose miss each family residual records: a retired generator's miss is taken as known.
MISS_SOURCES = {'ansatz miss': 'egypt_divisor_ansatz', 'extended ansatz miss': 'egypt_ansatz_extend',
                'classical miss': 'egypt_classical_family'}
RETIRE_AFTER = 64


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def generation():
    root = Path(__file__).resolve().parent
    names = ('agent.py', 'lexicon.py', 'lexicon_check.py', 'ops_seq.py', 'ops_poly.py', 'ops_orbit.py', 'ops_egypt.py',
             'ops_arith.py', 'ops_word.py', 'ops_matrix.py', 'ops_collatz.py', 'recurrence_check.py')
    return hashlib.sha256(b''.join((root / name).read_bytes() for name in names)).hexdigest()


# ------------------------------------------------------------- doctrine scheduling

def doctrine_score(samples, context, strategy):
    """p = (1+S)/(2+S+F), m = (0.01 + sum w t)/(1+S+F), score = p / max(m, 1e-6): a policy, not a belief."""
    rows = [s for s in samples if s['context'] == context and s['strategy'] == strategy]
    S = sum(s['weight'] for s in rows if s['success']); F = sum(s['weight'] for s in rows if not s['success'])
    T = sum(s['weight'] * s['seconds'] for s in rows)
    p = (1 + S) / (2 + S + F); m = (0.01 + T) / (1 + S + F)
    return p / max(m, SCORE_FLOOR)


def weighted_reports(reports):
    """Each of R > 0 reports per route and context weighs min(0.25, 1/R)."""
    counts = {}
    for r in reports: counts[(r['context'], r['strategy'])] = counts.get((r['context'], r['strategy']), 0) + 1
    return [dict(r, weight=min(0.25, 1 / counts[(r['context'], r['strategy'])]), source='report') for r in reports]


def record_sample(samples, row):
    """Local replaces reported and repeats replace samples; at most 128 records are retained."""
    key = (row['context'], row['strategy'], row['task'])
    kept = [s for s in samples if (s['context'], s['strategy'], s['task']) != key]
    return (kept + [row])[-MAX_SAMPLES:]


def nonresidue_primes(x, powers):
    """Primes p of the modulus with x a quadratic non-residue modulo p**e (x coprime to the modulus)."""
    out = []
    for p, e in sorted(powers.items()):
        if p == 2:
            if (e == 2 and x % 4 != 1) or (e >= 3 and x % 8 != 1): out.append(2)
        elif pow(x % p, (p - 1) // 2, p) != 1: out.append(p)
    return out


# ------------------------------------------------------------- goals: problem types stated in the language

class Goal:
    persist = ()
    capped = ()

    def version(self, rt, strategy, target): return repr(self.progress(rt))

    def allowed(self, strategy, target, rt): return True

    def persisted(self, rt):
        """Checked objects worth keeping, most valuable first; the state bound may drop the tail."""
        order = ('template',) + self.persist
        return sorted((o for o in rt.objects.values() if o['kind'] == 'template' or
                       (o['status'] == 'checked' and o['kind'] in self.persist)), key=lambda o: order.index(o['kind']))

    def restore(self, rt, saved):
        """Saved objects are proposals until the checker admits them again; returns (admitted, refused)."""
        admitted = refused = 0
        for row in saved:
            obj = rt.propose(row['kind'], row['data'])
            if obj['kind'] == 'template' or rt.check(obj): admitted += 1
            else: refused += 1
        return admitted, refused

    def context(self, target): return self.kind + ':' + target['kind']

    limit_kinds = ()
    retired = frozenset()

    def retirable(self, context, strategy):
        """Whether a strategy may be retired in a context after repeated failure (a scheduling policy)."""
        return False

    def retire_scope(self, target):
        """The population a retirement applies to within a context; a new population gets a fresh chance."""
        return None

    def transfer(self, rt, rows):
        """Checked objects from records of related problems, admitted again by the checker; returns (admitted, refused)."""
        return 0, 0

    def done(self, rt): return False

    def failure_profile(self, rt): return {}

    def related(self): return []

    def schedule_key(self, rt):
        """Goal state beyond progress that can make a move newly allowed; part of a target's exhaustion signature."""
        return ()


class CoverGoal(Goal):
    """Cover every residue class of a/n = sum of `terms` unit fractions by checked polynomial families."""
    kind = 'unit_fraction_cover'
    persist = ('cover', 'finite')
    capped = ('eclass', 'en')
    limit_kinds = ('nofamily',)

    def __init__(self, p, L):
        self.p, self.L = p, L
        self.levels = [p['modulus']]
        for q in p['lifts']: self.levels.append(self.levels[-1] * q)
        self.limit = len(self.levels) + p.get('extra_lifts', 0)
        self.fam = {}; self.residual = set(); self.base_miss = set(); self.misses = {}; self.refined = set(); self.seen = 0
        self.classes = []; self.classical_miss = set(); self._ready = None; self._powers = {}
        # Incremental indexes: the step loop reads these instead of rescanning the workspace.
        self.results = []; self.covers_at = {}; self._open = {}; self.fam_count = 0

    def init(self, rt):
        p = self.p; a, terms = p['a'], p['terms']
        self.esq = [rt.given('esq', dict(a=a, terms=terms, min=p['min'], modulus=M, verify_to=p['verify_to']))
                    for M in self.levels]
        self.primes = sorted({q for M in self.levels for q in self.L.factor(M)})
        self.en = {q: rt.given('en', dict(a=a, n=q, terms=terms)) for q in self.primes}
        M0 = self.levels[0]
        for r in range(M0):
            if gcd(r, M0) == 1: rt.given('eclass', dict(a=a, terms=terms, m=M0, r=r))

    def update(self, rt):
        """Index new objects: checked family classes, residual marks, refinements and class targets."""
        keys = list(rt.objects)
        for identity in keys[self.seen:]:
            o = rt.objects[identity]
            if o['kind'] == 'residual':
                self.residual.add(o['data']['of'])
                if o['data']['note'] in FAMILY_MISSES:
                    self.misses.setdefault(o['data']['of'], set()).add(o['data']['note'])
                    if o['data']['note'] == 'classical miss': self.classical_miss.add(o['data']['of'])
                    if self.misses[o['data']['of']] >= FAMILY_MISSES: self.base_miss.add(o['data']['of'])
            elif (o['kind'] == 'esq' and len(self.levels) < self.limit and o['data']['a'] == self.p['a']
                  and o['data']['terms'] == self.p['terms'] and o['data']['modulus'] % self.levels[-1] == 0
                  and self.L.is_prime(o['data']['modulus'] // self.levels[-1])):
                # A refinement level chosen by the agent itself: the chain of levels grows by one prime.
                self.levels.append(o['data']['modulus']); self.esq.append(o)
                self.primes = sorted(set(self.primes) | set(self.L.factor(o['data']['modulus'])))
                for q in self.primes:
                    if q not in self.en: self.en[q] = rt.given('en', dict(a=self.p['a'], n=q, terms=self.p['terms']))
            elif o['kind'] == 'eclass' and o['data']['m'] in self.levels:
                # Only a refinement onto a tracked level hands the parent's obligation to its subclasses.
                self.classes.append(o)
                for parent in o['parents']: self.refined.add(parent)
            if o['kind'] == 'template' or o['kind'] in ('finite', 'cover', 'pattern', 'density', 'theorem'): self.results.append(o)
        self.seen = len(keys)
        self.fam = {}
        for identity in self.family_ids(rt):
            d = rt.objects[identity]['data']; self.fam.setdefault(d['m'], set()).add(d['r'])
        self.fam_count = sum(len(v) for v in self.fam.values())
        for o in self.results:
            if o['kind'] == 'cover' and o['status'] == 'checked': self.covers_at[o['data']['modulus']] = o

    def family_ids(self, rt):
        if not hasattr(self, '_families'): self._families = []; self._scanned = 0
        keys = list(rt.objects)
        for identity in keys[self._scanned:]:
            o = rt.objects[identity]
            if o['kind'] == 'ufam' and o['data']['a'] == self.p['a'] and len(o['data']['x']) == self.p['terms']:
                self._families.append(identity)
        self._scanned = len(keys)
        return [i for i in self._families if rt.objects[i]['status'] == 'checked']

    def families(self, rt):
        self.update(rt); return self.fam

    def covered(self, index, m, r):
        return any(m % fm == 0 and r % fm in rs for fm, rs in index.items())

    def residual_of(self, rt, target):
        """Every family generator has missed the class, or was retired in its context and is taken to miss."""
        if target['id'] in self.base_miss: return True
        found = self.misses.get(target['id'], set()); context = self.context(target)
        scope = self.retire_scope(target)
        return all(note in found or (context, MISS_SOURCES[note], scope) in self.retired for note in FAMILY_MISSES)

    def retire_scope(self, target):
        # The classes of one refinement level: lifts to a new level are a new population.
        return target['data'].get('m') if target['kind'] == 'eclass' else None

    def retirable(self, context, strategy):
        # The classical generator and wall certificates decide every class's status; they are never retired.
        return context.startswith(self.kind + ':eclass') and strategy not in ('egypt_classical_family',
                                                                              'egypt_classical_exclusion')

    def targets(self, rt):
        self.update(rt); out = []
        for q in self.primes:
            if not self.covered(self.fam, q, 0): out.append(self.en[q])
        for level, M in enumerate(self.levels):
            out += self.open_classes(M)
            out.append(self.esq[level])
            if M in self.covers_at: out.append(self.covers_at[M])
        return out

    def open_classes(self, M):
        """Open class targets of one level, recomputed only when families, classes or refinements change."""
        key = (self.fam_count, len(self.classes), len(self.refined))
        cached = self._open.get(M)
        if cached is None or cached[0] != key:
            cached = (key, [o for o in sorted((c for c in self.classes if c['data']['m'] == M), key=lambda c: c['data']['r'])
                            if o['id'] not in self.refined and not self.covered(self.fam, M, o['data']['r'])])
            self._open[M] = cached
        return cached[1]

    def version(self, rt, strategy, target):
        """What a workspace-reading move depends on: the family classes that divide its modulus."""
        self.update(rt)
        if strategy == 'egypt_cover_assemble':
            M = target['data']['modulus']
            return sum(len(rs) for m, rs in self.fam.items() if M % m == 0)
        return sum(len(rs) for rs in self.fam.values())

    def allowed(self, strategy, target, rt):
        if strategy in ('egypt_class_split', 'egypt_class_refine'):
            # A scheduling policy: refine only classes both grammars left open, and only toward the next level.
            if target['kind'] != 'eclass': return False
            m = target['data']['m']
            if m not in self.levels[:-1] or not self.residual_of(rt, target): return False
            nxt = self.levels[self.levels.index(m) + 1] // m
            least = next(q for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31) if m % q)
            return (strategy == 'egypt_class_split') == (nxt == least)
        if strategy == 'egypt_finite_verify': return target['data']['modulus'] == self.levels[-1]
        if strategy in ('egypt_cover_lift', 'egypt_cover_merge'): return False
        if strategy == 'egypt_classical_exclusion':
            # Certify a wall only where the classical generator already missed, at the finest level.
            return target['kind'] == 'eclass' and target['data']['m'] == self.levels[-1] and target['id'] in self.classical_miss
        if strategy == 'egypt_choose_lift':
            return (target['kind'] == 'esq' and target['data']['modulus'] == self.levels[-1]
                    and len(self.levels) < self.limit and self.top_ready(rt))
        return True

    def schedule_key(self, rt):
        self.update(rt); return (len(self.classical_miss), len(self.levels), len(self.retired))

    def top_ready(self, rt):
        """Every open class at the finest level has been tried by the classical generator, and a cover exists there."""
        self.update(rt); M = self.levels[-1]
        if M not in self.covers_at: return False
        key = (M, len(self.classical_miss), sum(len(v) for v in self.fam.values()), len(self.classes))
        if self._ready is None or self._ready[0] != key:
            self._ready = (key, all(c['id'] in self.classical_miss or self.covered(self.fam, M, c['data']['r'])
                                    for c in self.classes if c['data']['m'] == M and c['id'] not in self.refined))
        return self._ready[1]

    def context(self, target):
        """Classes are told apart by whether they share a factor with the modulus and, if not, by whether they are
        squares modulo every prime-power factor: a feature the agent observes, not a claim."""
        if target['kind'] != 'eclass': return self.kind + ':' + target['kind']
        m, r = target['data']['m'], target['data']['r']
        if gcd(r, m) != 1: return self.kind + ':eclass:shared'
        if m not in self._powers: self._powers[m] = self.L.factor(m)
        return self.kind + ':eclass:coprime:' + ('nonsquare' if nonresidue_primes(r, self._powers[m]) else 'square')

    def progress(self, rt):
        """A cheap signature that changes exactly when a checked family class or a result object is added."""
        self.update(rt)
        done = tuple(sorted(o['kind'] for o in self.results if o['kind'] == 'template' or o['status'] == 'checked'))
        return self.fam_count, done

    def persisted(self, rt):
        """Templates, the finest checked cover (its families rebuild coverage), the latest finite range, and every
        claim about that cover in compact form (the cover replaced by its digest), then the certified walls."""
        covers = [o for o in rt.objects.values() if o['kind'] == 'cover' and o['status'] == 'checked']
        finite = [o for o in rt.objects.values() if o['kind'] == 'finite' and o['status'] == 'checked']
        best = max(covers, key=lambda o: (o['data']['modulus'], len(o['data']['entries'])), default=None)
        families = [rt.objects[i] for i in self.family_ids(rt)]
        claims = []
        if best is not None:
            inside = {self.L.digest(e['family']) for e in best['data']['entries']}
            families = [o for o in families if self.L.digest(o['data']) not in inside
                        and not self.covered_by(best['data'], o['data'])]
            ref = self.L.digest(best['data'])
            for o in rt.objects.values():
                if o['kind'] in ('pattern', 'density') and o['status'] == 'checked' and o['data']['cover'] == best['data']:
                    body = {k: v for k, v in o['data'].items() if k != 'cover'}
                    claims.append(dict(kind=o['kind'], data=dict(body, cover_ref=ref)))
        if finite:
            # The theorem about the saved range is kept with the range replaced by its digest.
            ref = self.L.digest(finite[-1]['data'])
            claims += [dict(kind='theorem', data=dict({k: v for k, v in o['data'].items() if k != 'finite'}, finite_ref=ref))
                       for o in rt.objects.values() if o['kind'] == 'theorem' and o['status'] == 'checked'
                       and o['data']['finite'] == finite[-1]['data']]
        walls = [o for o in rt.objects.values() if o['kind'] == 'nofamily' and o['status'] == 'checked']
        return ([self.tree(rt)] + [o for o in rt.objects.values() if o['kind'] == 'template'] + ([best] if best else [])
                + families + finite[-1:] + claims + walls)

    def tree(self, rt):
        """The refinement tree as bookkeeping, not a claim: every level (the agent's own included), the classes that
        were refined, and the family grammars each class has already missed."""
        self.update(rt); notes = sorted(FAMILY_MISSES)
        refined = sorted([rt.objects[i]['data']['m'], rt.objects[i]['data']['r']] for i in self.refined
                         if rt.objects[i]['kind'] == 'eclass')
        misses = sorted([rt.objects[i]['data']['m'], rt.objects[i]['data']['r'],
                         sum(1 << notes.index(n) for n in found)] for i, found in self.misses.items())
        return dict(kind='cover_tree', data=dict(a=self.p['a'], terms=self.p['terms'], levels=self.levels,
                                                 refined=refined, misses=misses))

    def rebuild(self, rt, tree):
        """Recreate the saved refinement tree so that remembered moves stay consistent with the workspace."""
        p = self.p; notes = sorted(FAMILY_MISSES)
        if (tree.get('a'), tree.get('terms')) != (p['a'], p['terms']) or tree.get('levels', [])[:len(self.levels)] != self.levels:
            return
        for M in tree['levels'][len(self.levels):]:
            rt.given('esq', dict(a=p['a'], terms=p['terms'], min=p['min'], modulus=M, verify_to=p['verify_to']))
            self.update(rt)
        for m, r in tree.get('refined', []):
            if m not in self.levels or m == self.levels[-1]: continue
            nxt = self.levels[self.levels.index(m) + 1]
            parent = rt.given('eclass', dict(a=p['a'], terms=p['terms'], m=m, r=r))
            for j in range(nxt // m):
                rt.propose('eclass', dict(a=p['a'], terms=p['terms'], m=nxt, r=r + m * j), (parent,))
        for m, r, mask in tree.get('misses', []):
            cls = rt.given('eclass', dict(a=p['a'], terms=p['terms'], m=m, r=r))
            for k, note in enumerate(notes):
                if mask >> k & 1: rt.residual(cls, ['restored from the saved refinement tree'], note)
        self.update(rt)

    def covered_by(self, cover, family):
        return any(family['m'] % e['family']['m'] == 0 and family['r'] % e['family']['m'] == e['family']['r']
                   for e in cover['entries'])

    def restore(self, rt, saved):
        for row in saved:
            if row['kind'] == 'cover_tree': self.rebuild(rt, row['data'])
        saved = [row for row in saved if row['kind'] != 'cover_tree']
        covers = {self.L.digest(row['data']): row['data'] for row in saved if row['kind'] == 'cover'}
        ranges = {self.L.digest(row['data']): row['data'] for row in saved if row['kind'] == 'finite'}
        expanded = []
        for row in saved:
            data = row['data']
            if 'cover_ref' in data:
                # A compact claim is rechecked against the saved cover it names; without that cover it is dropped.
                if data['cover_ref'] not in covers: continue
                data = dict({k: v for k, v in data.items() if k != 'cover_ref'}, cover=covers[data['cover_ref']])
            if 'finite_ref' in data:
                if data['finite_ref'] not in ranges: continue
                data = dict({k: v for k, v in data.items() if k != 'finite_ref'}, finite=ranges[data['finite_ref']])
            expanded.append(dict(kind=row['kind'], data=data))
        saved = expanded
        admitted, refused = Goal.restore(self, rt, saved)
        for row in saved:
            if row['kind'] != 'cover': continue
            cover = rt.propose('cover', row['data'])
            if cover['status'] != 'checked': continue
            for entry in row['data']['entries']:
                # The families were checked inside the cover check; restating them keeps coverage bookkeeping exact.
                family = rt.propose('ufam', entry['family'])
                if rt.check(family): admitted += 1
        return admitted, refused

    def transfer(self, rt, rows):
        """Families, covers, walls and templates are claims about the equation a/n = 1/x + 1/y + 1/z itself, whatever
        the refinement budget of the problem that found them: they carry over to a problem with the same a and terms.
        Each is a proposal until the checker admits it again; level-specific claims (ranges, patterns) do not carry."""
        a, terms = self.p['a'], self.p['terms']
        def same(row):
            d = row['data']
            if row['kind'] == 'ufam': return d.get('a') == a and len(d.get('x', ())) == terms
            if row['kind'] in ('cover', 'nofamily'): return d.get('a') == a and d.get('terms') == terms
            return row['kind'] == 'template' and d.get('a') == a
        admitted = refused = 0
        for row in rows:
            if row['kind'] not in ('ufam', 'cover', 'nofamily', 'template') or not same(row): continue
            obj = rt.propose(row['kind'], row['data'])
            if obj['kind'] == 'template' or rt.check(obj): admitted += 1
            else: refused += 1
            if row['kind'] == 'cover' and obj['status'] == 'checked':
                for entry in row['data']['entries']:
                    if rt.check(rt.propose('ufam', entry['family'])): admitted += 1
        return admitted, refused

    def level_uncovered(self):
        """Uncovered residues per level. A residue is covered by a family class dividing the modulus, or when every
        refinement at the next level is covered; computed by lifting only the uncovered residues."""
        levels = self.levels
        per = [[r for r in range(levels[0]) if not self.covered(self.fam, levels[0], r)]]
        for i in range(1, len(levels)):
            M, prev = levels[i], levels[i - 1]
            per.append([x + prev * j for x in per[-1] for j in range(M // prev) if not self.covered(self.fam, M, x + prev * j)])
        out = {levels[-1]: per[-1]}
        for i in range(len(levels) - 2, -1, -1):
            keep = {y % levels[i] for y in out[levels[i + 1]]}
            out[levels[i]] = [x for x in per[i] if x in keep]
        return out

    def pattern_status(self, rt, M, rule='uncovered_coprime_are_squares'):
        """A pattern conjecture for this level's cover: checked, refuted (with a witness residue) or not attempted."""
        for o in rt.objects.values():
            if o['kind'] == 'pattern' and o['status'] == 'checked' and o['data']['cover']['modulus'] == M \
                    and o['data']['rule'] == rule:
                return dict(status='checked', primes=o['data']['primes']) if 'primes' in o['data'] else dict(status='checked')
        for o in rt.objects.values():
            if o['kind'] == 'refutation' and o['status'] == 'checked' and o['data']['claim']['kind'] == 'pattern' \
                    and o['data']['claim']['data']['cover']['modulus'] == M and o['data']['claim']['data']['rule'] == rule:
                return dict(status='refuted', residue=o['data']['witness']['residue'])
        return dict(status='not attempted')

    def local_images(self, rt, M):
        """The checked local-image pattern of this level: allowed residues of open classes per prime power."""
        for o in rt.objects.values():
            if o['kind'] == 'pattern' and o['status'] == 'checked' and o['data']['cover']['modulus'] == M \
                    and o['data']['rule'] == 'uncovered_coprime_local_images':
                return o['data']['images']
        return None

    def walls(self, rt, M):
        return sum(1 for o in rt.objects.values() if o['kind'] == 'nofamily' and o['status'] == 'checked'
                   and o['data']['m'] == M)

    def summary(self, rt):
        self.update(rt); index = self.fam; levels = []; uncovered_at = self.level_uncovered()
        for i, M in enumerate(self.levels):
            uncovered = uncovered_at[M]; powers = self.L.factor(M)
            coprime = [r for r in uncovered if gcd(r, M) == 1]
            nonsquares = [r for r in coprime if nonresidue_primes(r, powers)]
            levels.append(dict(modulus=M, chosen_by='agent' if i >= len(self.p['lifts']) + 1 else 'problem',
                               covered=M - len(uncovered), uncovered=len(uncovered),
                               uncovered_coprime=coprime[:64], uncovered_coprime_count=len(coprime),
                               uncovered_coprime_squares=len(coprime) - len(nonsquares),
                               uncovered_coprime_nonsquares=nonsquares[:64],
                               uncovered_coprime_nonsquare_count=len(nonsquares),
                               square_pattern=self.pattern_status(rt, M),
                               signature_pattern=self.pattern_status(rt, M, 'uncovered_coprime_square_outside'),
                               local_images=self.local_images(rt, M),
                               certified_walls=self.walls(rt, M)))
        return dict(levels=levels, families=sum(len(v) for v in index.values()))

    def failure_profile(self, rt):
        """What stayed open at the finest level: the primes at which each open coprime class is a non-residue."""
        self.update(rt); M = self.levels[-1]; powers = self.L.factor(M); histogram = {}
        coprime = [r for r in self.level_uncovered()[M] if gcd(r, M) == 1]
        for r in coprime:
            key = ','.join(str(p) for p in nonresidue_primes(r, powers)) or 'square'
            histogram[key] = histogram.get(key, 0) + 1
        return dict(modulus=M, open_coprime=len(coprime), nonresidue_signatures=histogram,
                    certified_walls=self.walls(rt, M), open_examples=coprime[:16],
                    refinement_budget_left=self.limit - len(self.levels))

    def related(self):
        """Closest related problems: the next numerators with the same statement (Sierpinski's 5/n for a = 4)."""
        return [dict(self.p, a=a) for a in (self.p['a'] + 1, self.p['a'] + 2) if a <= 16]


class DescentGoal(Goal):
    """Certify descent T^j(n) < n on every residue class modulo d^depth of a class map."""
    kind = 'descent_cover'
    persist = ('descent', 'cfinite', 'cycle')
    capped = ('cclass',)

    def __init__(self, p, L):
        self.p, self.L = p, L; self.top = p['map']['d'] ** p['depth']
        self.index_ = {}; self.residual = set(); self.classes = []; self.refined = set(); self.seen = 0
        self.results = []

    def init(self, rt):
        d = self.p['map']['d']
        self.root = rt.given('cproblem', dict(map=self.p['map'], depth=self.p['depth'], verify_to=self.p['verify_to']))
        for r in range(d): rt.given('cclass', dict(map=self.p['map'], modulus=d, residue=r))

    def update(self, rt):
        keys = list(rt.objects)
        for identity in keys[self.seen:]:
            o = rt.objects[identity]
            if o['kind'] == 'residual': self.residual.add(o['data']['of'])
            elif o['kind'] == 'cclass' and o['data']['modulus'] <= self.top:
                self.classes.append(o)
                for parent in o['parents']: self.refined.add(parent)
            elif o['kind'] in ('descent', 'dcover', 'cfinite', 'cycle'): self.results.append(o)
        self.seen = len(keys)
        self.index_ = {}
        for o in self.results:
            if o['kind'] == 'descent' and o['status'] == 'checked':
                self.index_.setdefault(o['data']['modulus'], set()).add(o['data']['residue'])

    def descents(self, rt):
        self.update(rt); return self.index_

    def covered(self, index, M, r):
        return any(M % fm == 0 and r % fm in rs for fm, rs in index.items())

    def targets(self, rt):
        index = self.descents(rt)
        out = [o for o in sorted(self.classes, key=lambda o: (o['data']['modulus'], o['data']['residue']))
               if o['id'] not in self.refined and not self.covered(index, o['data']['modulus'], o['data']['residue'])]
        return out + [self.root] + [o for o in self.results if o['kind'] == 'dcover' and o['status'] == 'checked'][-1:]

    def allowed(self, strategy, target, rt):
        if strategy == 'collatz_split':
            return target['kind'] == 'cclass' and target['data']['modulus'] < self.top and target['id'] in self.residual
        return True

    def progress(self, rt):
        index = self.descents(rt)
        return (sum(len(v) for v in index.values()),
                tuple(sorted(o['kind'] for o in self.results if o['status'] == 'checked' and o['kind'] != 'descent')))

    def persisted(self, rt):
        rows = [[o['data']['modulus'], o['data']['residue'], o['data']['steps'], o['data']['bound']]
                for o in rt.objects.values() if o['kind'] == 'descent' and o['status'] == 'checked']
        rest = [o for o in rt.objects.values() if o['status'] == 'checked' and o['kind'] in ('cfinite', 'cycle')]
        self.update(rt)
        tree = dict(map=self.p['map'],
                    refined=sorted([rt.objects[i]['data']['modulus'], rt.objects[i]['data']['residue']] for i in self.refined
                                   if rt.objects[i]['kind'] == 'cclass'),
                    residual=sorted([rt.objects[i]['data']['modulus'], rt.objects[i]['data']['residue']] for i in self.residual
                                    if i in rt.objects and rt.objects[i]['kind'] == 'cclass'))
        return [dict(kind='descent_tree', data=tree), dict(kind='descent_rows', data=dict(map=self.p['map'], rows=rows))] + rest

    def restore(self, rt, saved):
        admitted = refused = 0; plain = []; d = self.p['map']['d']
        for row in saved:
            if row['kind'] == 'descent_tree' and row['data'].get('map') == self.p['map']:
                # Bookkeeping, not claims: recreate refined classes and the residuals that justified refinement.
                for M, r in row['data'].get('refined', []):
                    parent = rt.given('cclass', dict(map=self.p['map'], modulus=M, residue=r))
                    for i in range(d):
                        rt.propose('cclass', dict(map=self.p['map'], modulus=M * d, residue=r + M * i), (parent,))
                for M, r in row['data'].get('residual', []):
                    rt.residual(rt.given('cclass', dict(map=self.p['map'], modulus=M, residue=r)),
                                ['restored from the saved refinement tree'], 'refine the class')
                continue
        for row in saved:
            if row['kind'] == 'descent_tree': continue
            if row['kind'] != 'descent_rows': plain.append(row); continue
            for M, r, steps, bound in row['data']['rows']:
                obj = rt.propose('descent', dict(map=row['data']['map'], modulus=M, residue=r, steps=steps, bound=bound))
                if rt.check(obj): admitted += 1
                else: refused += 1
        a, b = Goal.restore(self, rt, plain)
        return admitted + a, refused + b

    def summary(self, rt):
        index = self.descents(rt); d = self.p['map']['d']; rows = []
        M = d
        while M <= self.top:
            rows.append(dict(modulus=M, open=sum(1 for r in range(M) if not self.covered(index, M, r)) if M <= 1 << 20 else None))
            M *= d
        return dict(levels=rows, descents=sum(len(v) for v in index.values()))

    def failure_profile(self, rt):
        """Open classes at the finest modulus reached, by how many of their first steps are odd."""
        index = self.descents(rt); d = self.p['map']['d']; M = self.top
        if M > 1 << 20 or d != 2: return {}
        histogram = {}
        for r in range(M):
            if self.covered(index, M, r): continue
            odd, x = 0, r + M
            for _ in range(self.p['depth']):
                i = x % d; odd += i; x = (self.p['map']['a'][i] * x + self.p['map']['b'][i]) // d
            histogram[str(odd)] = histogram.get(str(odd), 0) + 1
        return dict(modulus=M, odd_steps_of_open_classes=histogram)

    def related(self):
        m = self.p['map']
        if m['d'] != 2: return []
        return [dict(self.p, map=dict(m, a=[m['a'][0], m['a'][1] + 2])), dict(self.p, map=dict(m, b=[m['b'][0], -m['b'][1]]))]


class DecideGoal(Goal):
    """Decide one claim: the checker admits it, or a checked refutation refutes it."""
    kind = 'decide'

    def __init__(self, p, L): self.p = p

    def init(self, rt):
        self.claim = rt.propose(self.p['kind'], self.p['data'])

    def targets(self, rt): return [self.claim] if self.claim['status'] not in ('checked', 'refuted') else []

    def done(self, rt): return self.claim['status'] in ('checked', 'refuted')

    def progress(self, rt): return self.claim['status']

    def summary(self, rt): return dict(claim_status=self.claim['status'], claim_kind=self.claim['kind'])


class ExploreGoal(Goal):
    """Find checked facts of the requested kinds about each given object."""
    kind = 'explore'

    def __init__(self, p, L): self.p = p

    def init(self, rt):
        self.roots = [rt.given(o['kind'], o['data']) for o in self.p['objects']]

    def found(self, rt, root):
        kinds = set()
        for o in rt.objects.values():
            if o['status'] == 'checked' and o['question'] == root['question']: kinds.add(o['kind'])
        return kinds

    def targets(self, rt):
        return [r for r in self.roots if not set(self.p['goals']) <= self.found(rt, r)]

    def done(self, rt): return not self.targets(rt)

    def progress(self, rt): return tuple(tuple(sorted(self.found(rt, r))) for r in self.roots)

    def summary(self, rt):
        return dict(found=[dict(kind=r['kind'], checked_kinds=sorted(self.found(rt, r))) for r in self.roots])


GOALS = dict(unit_fraction_cover=CoverGoal, descent_cover=DescentGoal, decide=DecideGoal, explore=ExploreGoal)


def bind(task, host, L):
    allowed = {'query', 'problem', 'moves', 'move_work', 'reports', 'name'}
    if type(task) is not dict or task.get('query') != 'autonomous_research' or set(task) - allowed:
        raise host.Refused('autonomous research task fields')
    p = task.get('problem'); moves = task.get('moves', 200); per = task.get('move_work', 2_000_000)
    reports = task.get('reports', [])
    if type(moves) is not int or not 1 <= moves <= 200_000: raise host.Refused('moves per call 1..200000')
    if type(per) is not int or not 1 <= per <= 100_000_000: raise host.Refused('move work bound')
    if type(reports) is not list or len(reports) > 128: raise host.Refused('at most 128 reported samples')
    for r in reports:
        if type(r) is not dict or set(r) != {'context', 'strategy', 'task', 'success', 'seconds'} \
                or type(r['success']) is not bool or type(r['seconds']) not in (int, float) or r['seconds'] < 0:
            raise host.Refused('reported sample shape')
    if type(p) is not dict or p.get('type') not in GOALS: raise host.Refused('problem type')
    kind = p['type']
    if kind == 'unit_fraction_cover':
        need = {'type', 'a', 'terms', 'min', 'modulus', 'lifts', 'verify_to'}
        if not need <= set(p) <= need | {'extra_lifts'}: raise host.Refused('unit fraction cover fields')
        if type(p.get('extra_lifts', 0)) is not int or not 0 <= p.get('extra_lifts', 0) <= 4:
            raise host.Refused('at most four refinement primes chosen by the agent')
        if type(p['a']) is not int or not 1 <= p['a'] <= 16 or p['terms'] != 3: raise host.Refused('numerator 1..16 and three terms')
        if type(p['min']) is not int or not 2 <= p['min'] <= 1000: raise host.Refused('minimum n')
        if type(p['modulus']) is not int or not 1 <= p['modulus'] <= 100_000: raise host.Refused('cover modulus')
        if type(p['lifts']) is not list or len(p['lifts']) > 3 or not all(type(q) is int and L.is_prime(q) for q in p['lifts']):
            raise host.Refused('at most three prime lifts')
        top = p['modulus']
        for q in p['lifts']: top *= q
        if top > 1_000_000: raise host.Refused('lifted modulus at most 10^6')
        if type(p['verify_to']) is not int or not p['min'] < p['verify_to'] <= 2_000_000: raise host.Refused('verify_to bound')
    elif kind == 'descent_cover':
        if set(p) != {'type', 'map', 'depth', 'verify_to'}: raise host.Refused('descent cover fields')
        if type(p['depth']) is not int or not 1 <= p['depth'] <= 20: raise host.Refused('descent depth 1..20')
        if type(p['verify_to']) is not int or not 3 <= p['verify_to'] <= 2_000_000: raise host.Refused('verify_to bound')
    elif kind == 'decide':
        if set(p) != {'type', 'kind', 'data'} or type(p['data']) is not dict: raise host.Refused('decide fields')
    else:
        if set(p) != {'type', 'objects', 'goals'} or type(p['objects']) is not list or not 1 <= len(p['objects']) <= 8:
            raise host.Refused('explore fields')
        if type(p['goals']) is not list or not p['goals']: raise host.Refused('explore goals')
    return p, moves, per, weighted_reports(reports), digest(dict(query='autonomous_research', problem=p))


# ------------------------------------------------------------- the agent

class Agent:
    def __init__(self, host, L, checker, registry, goal, rt, per, samples, macros, tried, unseen):
        self.host, self.L, self.checker, self.registry, self.goal, self.rt = host, L, checker, registry, goal, rt
        self.per, self.samples, self.macros, self.tried, self.unseen = per, samples, macros, tried, unseen
        self.produced_by = {}; self.log = []; self.events = {d: 0 for d in 'NWSE'}; self.moves = 0
        self.seen_contexts = {(s['context'], s['task']) for s in samples}
        self.attempts = {}; self.by_kind = {}; self.children = {}; self.indexed = 0; self.rederivable = set()
        self.target_moves = {}; self.exhausted = {}; self.outcomes = {}; self.escalated = {}; self.memo = {}
        self.checkable = set(checker.CHECKS) | {'invariant', 'semi'}
        # Strategies retired per context and level after RETIRE_AFTER failures without a success in this run.
        self.retired = {}; goal.retired = self.retired; self.retire_tally = {}

    def index(self):
        """Incrementally index new workspace objects by kind and by parent."""
        keys = list(self.rt.objects)
        for identity in keys[self.indexed:]:
            o = self.rt.objects[identity]
            self.by_kind.setdefault(o['kind'], []).append(identity)
            for parent in o['parents']: self.children.setdefault(parent, []).append(identity)
        self.indexed = len(keys)

    # -- move table: operators, the verify move, and invented or proposed macros
    def strategies(self):
        table = {k: v for k, v in self.registry.items() if not k.startswith('_')}
        table['verify'] = dict(name='verify', dirs='S', consumes=('*',), produces=('*',), fn=None)
        for m in self.macros:
            table[m['name']] = dict(name=m['name'], dirs=m['dirs'], consumes=tuple(m['consumes']),
                                    produces=tuple(m['produces']), fn=None, steps=m['steps'])
        by_kind = {}
        for name, spec in table.items():
            for slot, kind in enumerate(spec['consumes']): by_kind.setdefault(kind, []).append((name, slot))
        return table, by_kind

    def descendants(self, target, limit=8):
        out = [target]; queue = [target['id']]; seen = {target['id']}
        while queue and len(out) < limit:
            for child in self.children.get(queue.pop(0), []):
                if child in seen: continue
                seen.add(child); o = self.rt.objects[child]
                if o['status'] in ('checked', 'candidate') and o['kind'] != 'residual':
                    out.append(o); queue.append(child)
                    if len(out) >= limit: break
        return out

    def companions(self, kind, exclude):
        out = []
        for identity in reversed(self.by_kind.get(kind, [])):
            o = self.rt.objects[identity]
            if identity not in exclude and o['status'] in ('checked', 'given'): out.append(o)
            if len(out) >= COMPANIONS: break
        return out

    def allowed(self, name, target, table):
        """A macro obeys the goal's policy at every one of its steps; a strategy retired in the target's context
        is not tried again there in this run."""
        if self.retired and (self.goal.context(target), name, self.goal.retire_scope(target)) in self.retired:
            return False
        steps = table[name].get('steps') or [name]
        return all(self.goal.allowed(step, target, self.rt) for step in steps)

    def candidates(self, target, table, by_kind):
        focus = self.descendants(target); out = []; version = None
        for f in focus:
            if f['status'] == 'candidate' and f['kind'] in self.checkable and self.goal.allowed('verify', target, self.rt):
                out.append(('verify', [f]))
            for name, slot in by_kind.get(f['kind'], []):
                if name == 'verify' or not self.allowed(name, target, table): continue
                if self.attempts.get((target['id'], name), 0) >= MAX_PER_TARGET: continue
                kinds = table[name]['consumes']; args = [None] * len(kinds); args[slot] = f; ok = True
                for j, other in enumerate(kinds):
                    if j == slot: continue
                    pool = self.companions(other, {f['id']} | {a['id'] for a in args if a})
                    if not pool: ok = False; break
                    args[j] = pool[0]
                if ok: out.append((name, args))
        fresh = []
        for name, args in out:
            parts = [name] + [a['id'] for a in args]
            if name in READS_WORKSPACE:
                parts.append(repr(self.goal.version(self.rt, name, target)))
            key = digest(parts)[:20]  # scheduling memory only; a collision can at worst skip one move
            if key not in self.tried: fresh.append((name, args, key))
        return fresh

    def run_op(self, name, args, budget):
        spec = self.registry.get(name)
        self.rt.budget = budget; before = set(self.rt.objects); self.rt.events = []
        if name == 'verify':
            ok = self.rt.check(args[0]); out = [args[0]] if ok else []
        elif spec is not None:
            out = self.apply(name, spec, args)
        else:
            out = self.run_macro(name, args, budget)
        for event, identity in self.rt.events: self.events[event] += 1
        for o in out:
            if o['id'] not in before: self.produced_by[o['id']] = (name, [a['id'] for a in args])
        return out

    def apply(self, name, spec, args):
        """One operator application. An operator that reads only its arguments is not recomputed on the same
        arguments within a run: a macro replaying a step already taken reuses its outputs."""
        if name in READS_WORKSPACE: return spec['fn'](self.rt, *args)
        key = (name,) + tuple(a['id'] for a in args)
        if key in self.memo: return [self.rt.objects[i] for i in self.memo[key] if i in self.rt.objects]
        out = spec['fn'](self.rt, *args)
        self.memo[key] = [o['id'] for o in out]
        return out

    def run_macro(self, name, args, budget):
        macro = next(m for m in self.macros if m['name'] == name); out = []; current = args
        for i, step in enumerate(macro['steps']):
            spec = self.registry[step]; before = set(self.rt.objects); self.rt.events = []
            produced = self.apply(step, spec, current)
            for o in produced:
                if o['id'] not in before: self.produced_by[o['id']] = (step, [a['id'] for a in current])
            out += produced
            if i + 1 == len(macro['steps']): break
            nxt = self.registry[macro['steps'][i + 1]]['consumes']
            head = [o for o in produced if o['kind'] == nxt[0] and o['status'] in ('checked', 'candidate', 'given')]
            if not head: break
            current = [head[0]]
            for other in nxt[1:]:
                pool = self.companions(other, {head[0]['id']})
                if not pool: return out
                current.append(pool[0])
        return out

    def invent(self, output):
        """Promote the derivation chain of a checked output to a macro move."""
        chain = []; o = output
        while o['id'] in self.produced_by and len(chain) < MACRO_STEPS:
            name, arg_ids = self.produced_by[o['id']]
            if name in self.registry: chain.insert(0, name)
            else: break
            first = self.rt.objects.get(arg_ids[0]) if arg_ids else None
            if first is None or first['id'] not in self.produced_by: break
            o = first
        if len(chain) < 2 or len(self.macros) >= MAX_MACROS: return None
        name = 'macro:' + '>'.join(chain)
        if any(m['name'] == name for m in self.macros): return None
        dirs = ''.join(d for d in 'NWSE' if any(d in self.registry[s]['dirs'] for s in chain))
        macro = dict(name=name, steps=chain, dirs=dirs, consumes=list(self.registry[chain[0]]['consumes']),
                     produces=list(self.registry[chain[-1]]['produces']), origin='derivation', status='invented',
                     invented_at=self.moves, uses=0, successes=0, source_output=output['kind'])
        self.macros.append(macro)
        return macro

    def propose_compositions(self):
        """Type-directed compositions A then B where B consumes what A produces and both have succeeded."""
        good = {s['strategy'] for s in self.samples if s['success'] and s['strategy'] in self.registry}
        for a in sorted(good):
            for b in sorted(good):
                if a == b or len(self.macros) >= MAX_MACROS: continue
                A, B = self.registry[a], self.registry[b]
                if B['consumes'][0] not in A['produces']: continue
                name = 'macro:' + a + '>' + b
                if any(m['name'] == name for m in self.macros): continue
                self.macros.append(dict(name=name, steps=[a, b],
                                        dirs=''.join(d for d in 'NWSE' if d in A['dirs'] or d in B['dirs']),
                                        consumes=list(A['consumes']), produces=list(B['produces']), origin='types',
                                        status='proposed', invented_at=self.moves, uses=0, successes=0, source_output=None))
                return

    def step(self, allocation, remaining=None):
        self.index(); table, by_kind = self.strategies(); progress = repr(self.goal.progress(self.rt))
        key_extra = self.goal.schedule_key(self.rt)
        for target in self.goal.targets(self.rt):
            if target['kind'] in self.goal.capped and self.target_moves.get(target['id'], 0) >= MAX_TARGET_MOVES: continue
            # A target with no fresh move stays exhausted until the move table or its derived objects change.
            signature = (len(table), len(self.children.get(target['id'], [])), progress, key_extra)
            if self.exhausted.get(target['id']) == signature: continue
            fresh = self.candidates(target, table, by_kind)
            if not fresh:
                self.exhausted[target['id']] = signature; continue
            context = self.goal.context(target)
            fresh.sort(key=lambda c: -doctrine_score(self.samples, context, c[0]))
            if (context, target['id']) not in self.seen_contexts:
                self.seen_contexts.add((context, target['id'])); self.unseen += 1
                if self.unseen % 5 == 0: fresh.reverse()
            name, args, key = fresh[0]
            if key in self.escalated:
                allocation = min(allocation * ESCALATION, max(allocation, (remaining or allocation) // 2))
            return self.execute(target, context, name, args, key, allocation)
        return None

    def execute(self, target, context, name, args, key, allocation):
        host = self.host; budget = host.Budget(allocation); parent = self.rt.budget
        before = self.goal.progress(self.rt); began = time.perf_counter_ns(); reason = None; out = []
        existing = set(self.rt.objects) if self.goal.limit_kinds else None
        try: out = self.run_op(name, args, budget)
        except (host.Exhausted, RuntimeError, self.checker.Limit) as exc: reason = 'limit: ' + str(exc)[:120]
        except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
            reason = 'operator error: ' + type(exc).__name__ + ': ' + str(exc)[:120]
        self.rt.budget = parent
        parent.use(budget.work)
        seconds = (time.perf_counter_ns() - began) / 1e9
        # Progress, or a newly checked certificate of a limit (a wall): a certified limitation is a result.
        success = self.goal.progress(self.rt) != before or (existing is not None and any(
            o['id'] not in existing and o['kind'] in self.goal.limit_kinds and o['status'] == 'checked' for o in out))
        self.moves += 1
        if reason and reason.startswith('limit') and key not in self.escalated:
            # Out of resources, not out of ideas: the same move gets one retry with a larger allocation.
            self.escalated[key] = allocation
            self.attempts[(target['id'], name)] = self.attempts.get((target['id'], name), 0) - 1
            self.target_moves[target['id']] = self.target_moves.get(target['id'], 0) - 1
        else: self.tried.add(key)
        if name in READS_WORKSPACE or 'cover' in [a['kind'] for a in args]: self.rederivable.add(key)
        self.attempts[(target['id'], name)] = self.attempts.get((target['id'], name), 0) + 1
        self.target_moves[target['id']] = self.target_moves.get(target['id'], 0) + 1
        self.samples = record_sample(self.samples, dict(context=context, strategy=name, task=target['id'], success=success,
                                                        seconds=round(seconds, 6), weight=1, source='local'))
        tally = self.outcomes.setdefault((context, name), [0, 0, 0.0])
        tally[0 if success else 1] += 1; tally[2] += seconds
        scope = self.goal.retire_scope(target); count = self.retire_tally.setdefault((context, name, scope), [0, 0])
        count[0 if success else 1] += 1
        if not count[0] and count[1] >= RETIRE_AFTER and self.goal.retirable(context, name) \
                and (context, name, scope) not in self.retired:
            self.retired[(context, name, scope)] = dict(failures=count[1], at_move=self.moves)
        for m in self.macros:
            if m['name'] == name:
                m['uses'] += 1; m['successes'] += int(success)
                if success and m['status'] == 'proposed': m['status'] = 'promoted'
        invented = None
        if success:
            for o in out:
                if o['status'] == 'checked': invented = self.invent(o) or invented
        if self.moves % PROPOSE_EVERY == 0: self.propose_compositions()
        row = dict(move=self.moves, target=target['kind'], strategy=name, success=success, work=budget.work,
                   outputs=[(o['kind'], o['status']) for o in out][:6])
        if reason: row['reason'] = reason
        if invented: row['invented'] = invented['name']
        self.log = (self.log + [row])[-MAX_LOG:]
        return row


# ------------------------------------------------------------- strategy retention and failure mining

def load_library(state):
    """Strategy outcomes kept from earlier problems, as discounted reports (at most one unit per route and context)."""
    row = next((o for o in state['observations'] if o.get('task_id') == LIBRARY_ID), None)
    entries = [e for e in (row or {}).get('entries', []) if type(e) is dict and type(e.get('context')) is str
               and type(e.get('strategy')) is str and all(type(e.get(k)) in (int, float) and e[k] >= 0
                                                           for k in ('successes', 'failures', 'seconds'))]
    reports = []
    for e in entries:
        uses = e['successes'] + e['failures']
        if not uses: continue
        seconds = e['seconds'] / uses
        for success, count in ((True, e['successes']), (False, e['failures'])):
            reports += [dict(context=e['context'], strategy=e['strategy'], task='library', success=success,
                             seconds=seconds)] * min(int(count), LIBRARY_REPORTS)
    return entries, weighted_reports(reports)


def merge_library(entries, outcomes):
    table = {(e['context'], e['strategy']): dict(e) for e in entries}
    for (context, strategy), (wins, misses, seconds) in outcomes.items():
        row = table.setdefault((context, strategy), dict(context=context, strategy=strategy, successes=0, failures=0,
                                                         seconds=0.0))
        row['successes'] += wins; row['failures'] += misses; row['seconds'] = round(row['seconds'] + seconds, 6)
    return sorted(table.values(), key=lambda e: (-(e['successes'] + e['failures']), e['context'], e['strategy']))[:LIBRARY_ENTRIES]


def target_brief(target):
    d = target['data']
    if target['kind'] == 'eclass': return dict(kind='eclass', m=d['m'], r=d['r'])
    if target['kind'] == 'cclass': return dict(kind='cclass', modulus=d['modulus'], residue=d['residue'])
    if target['kind'] == 'esq': return dict(kind='esq', modulus=d['modulus'])
    return dict(kind=target['kind'])


def mine_failures(agent, goal, rt):
    """Why the open targets stayed open: the moves each received and the residual notes they left."""
    if agent is None: return {}
    notes = {}
    for o in rt.objects.values():
        if o['kind'] == 'residual': notes.setdefault(o['data']['of'], set()).add(o['data']['note'])
    tried = {}
    for (target, name) in agent.attempts: tried.setdefault(target, set()).add(name)
    groups = {}; examples = []; open_targets = goal.targets(rt)
    for t in open_targets:
        key = t['kind'] + ': ' + (', '.join(sorted(notes.get(t['id'], ()))) or 'no residual')
        groups[key] = groups.get(key, 0) + 1
        if len(examples) < 8 and t['kind'] in goal.capped:
            examples.append(dict(target_brief(t), moves=sorted(tried.get(t['id'], ())), residuals=sorted(notes.get(t['id'], ())),
                                 exhausted=t['id'] in agent.exhausted,
                                 capped=agent.target_moves.get(t['id'], 0) >= MAX_TARGET_MOVES))
    return dict(open_targets=len(open_targets), by_outcome=groups, examples=examples, profile=goal.failure_profile(rt))


# ------------------------------------------------------------- state

def compact(obj):
    return obj if set(obj) == {'kind', 'data'} else dict(kind=obj['kind'], data=obj['data'])


def save(host, state, state_path, record, library=None):
    """Write the record within the state bound. Scheduling memory is trimmed before any evidence; evidence is
    dropped from the least valuable end only as a last resort, and the number dropped is recorded and returned."""
    if state_path is None: return 0
    ids = {record['task_id']} | ({library['task_id']} if library else set())
    others = [o for o in state['observations'] if o['task_id'] not in ids]
    state['observations'] = (others + ([library] if library else []) + [record])[-128:]
    record['dropped_objects'] = 0
    size = lambda: len(host.canonical(state).encode()) + 1
    if size() > host.STATE_LIMIT:
        record['tried'] = record['tried'][-500:]; record['rederivable'] = record['rederivable'][-500:]
        record['log'] = record['log'][-8:]; record['samples'] = record['samples'][-200:]
    dropped = 0
    while size() > host.STATE_LIMIT and record['objects']:
        excess = size() - host.STATE_LIMIT
        while excess > 0 and record['objects']:
            excess -= len(host.canonical(record['objects'].pop()).encode()) + 1; dropped += 1
        record['dropped_objects'] = dropped
    target = Path(state_path); target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(host.canonical(state) + '\n', encoding='utf-8', newline='\n'); temp.replace(target)
    return dropped


def run(task, state_path, limit, host):
    started = time.perf_counter_ns(); budget = host.Budget(limit)
    L = host.local_module('lexicon'); checker = host.local_module('lexicon_check')
    problem, moves, per, reports, identity = bind(task, host, L)
    registry, _ = L.load_ops(); gen = generation()
    state = host.read_state(state_path)
    old = next((o for o in state['observations'] if o.get('task_id') == identity and o.get('kind') == 'autonomous_research'), None)
    rt = L.Runtime(checker, budget)
    goal = GOALS[problem['type']](problem, L); goal.init(rt)
    library, retained = load_library(state)
    samples, macros, tried, unseen, replayed, invalid = retained + list(reports), [], set(), 0, 0, 0
    carried = (0, 0)
    agent = None
    try:
        if old is not None:
            if old.get('generation') == gen:
                samples = [s for s in old.get('samples', []) if type(s) is dict] + samples
                tried = set(x for x in old.get('tried', []) if type(x) is str)
                # Moves that read the workspace or summarize a cover are re-derivable after a resume.
                tried -= set(old.get('rederivable', []))
                unseen = old.get('unseen', 0) if type(old.get('unseen')) is int else 0
            for m in old.get('macros', []):
                if type(m) is dict and all(s in registry for s in m.get('steps', [])) and m.get('steps'): macros.append(m)
            saved = [o for o in old.get('objects', []) if type(o) is dict and type(o.get('data')) is dict]
            replayed, invalid = goal.restore(rt, saved)
            if invalid:
                # Refused evidence invalidates the scheduling memory built on it; the search is redone.
                tried = set()
        else:
            # A new problem starts from what related problems already proved about the same equation.
            rows = [o for rec in state['observations'] if rec.get('kind') == 'autonomous_research'
                    for o in rec.get('objects', []) if type(o) is dict and type(o.get('data')) is dict]
            carried = goal.transfer(rt, rows)
        agent = Agent(host, L, checker, registry, goal, rt, per, samples[-MAX_SAMPLES:], macros, tried, unseen)
        status = 'UNKNOWN'; reason = 'move allowance used'
        for _ in range(moves):
            if goal.done(rt): break
            remaining = limit - budget.work
            if remaining <= 0: reason = 'work budget exhausted'; break
            row = agent.step(max(1, min(per, remaining // 2)), remaining)
            if row is None: reason = 'no untried move for any open target'; break
    except host.Exhausted as exc:
        reason = str(exc)
    if goal.done(rt): status, reason = 'CHECKED_RESEARCH', 'goal settled by checked results'
    record = dict(task_id=identity, kind='autonomous_research', generation=gen, problem=problem,
                  objects=[compact(o) for o in goal.persisted(rt)], macros=agent.macros if agent else macros,
                  samples=[s for s in (agent.samples if agent else samples) if s.get('source') == 'local'],
                  tried=sorted(agent.tried if agent else tried)[-MAX_TRIED:], unseen=agent.unseen if agent else unseen,
                  rederivable=sorted(agent.rederivable)[-MAX_TRIED:] if agent else [],
                  log=agent.log if agent else [])
    entries = merge_library(library, agent.outcomes if agent else {})
    dropped = save(host, state, state_path, record, dict(task_id=LIBRARY_ID, kind='strategy_library', entries=entries))
    checked = [o for o in rt.objects.values() if o['status'] == 'checked']
    by_kind = {}
    for o in checked: by_kind[o['kind']] = by_kind.get(o['kind'], 0) + 1
    ranking = []
    if agent:
        contexts = sorted({s['context'] for s in agent.samples})
        for c in contexts:
            strategies = sorted({s['strategy'] for s in agent.samples if s['context'] == c},
                                key=lambda s: -doctrine_score(agent.samples, c, s))
            ranking.append(dict(context=c, order=[dict(strategy=s, score=round(doctrine_score(agent.samples, c, s), 3))
                                                  for s in strategies[:6]]))
    return dict(status=status, reason=reason, task_id=identity, problem=problem, generation=gen,
                moves_executed=agent.moves if agent else 0, work=budget.work,
                elapsed_ns=time.perf_counter_ns() - started, replayed_objects=replayed, invalidated_objects=invalid,
                dropped_objects=dropped, carried_objects=dict(admitted=carried[0], refused=carried[1]),
                goal=goal.summary(rt), checked_objects=by_kind,
                results=[result_row(o) for o in checked if o['kind'] in ('cover', 'finite', 'pattern', 'density', 'theorem',
                                                                           'dcover', 'cfinite', 'cycle', 'exclusion')][-12:],
                refutations=sum(1 for o in checked if o['kind'] == 'refutation'),
                invented_moves=[dict(name=m['name'], origin=m['origin'], status=m['status'], dirs=m['dirs'],
                                     uses=m['uses'], successes=m['successes'], invented_at=m['invented_at'])
                                for m in (agent.macros if agent else macros)],
                templates=[o['data'] for o in rt.objects.values() if o['kind'] == 'template'][:16],
                directions_observed=agent.events if agent else {}, scheduler=ranking, log=agent.log[-24:] if agent else [],
                retired_strategies=[dict(context=c, strategy=s, scope=w, **info) for (c, s, w), info in agent.retired.items()]
                if agent else [],
                failures=mine_failures(agent, goal, rt), related_problems=goal.related(),
                strategy_library=dict(entries=len(entries), reports_loaded=len(retained)),
                limits='Operators search bounded grammars; the checker admits every reported claim in its stated scope. '
                       'UNKNOWN leaves the problem open. Scores order moves and are not beliefs.')


def result_row(o):
    d = o['data']; ev = o.get('evidence', {})
    row = dict(kind=o['kind'], scope=ev.get('scope'))
    if o['kind'] == 'cover': row.update(modulus=d['modulus'], covered=ev.get('covered'), bound=d['bound'], families=len(d['entries']))
    if o['kind'] == 'finite': row.update(lo=d['lo'], hi=d['hi'], via_cover=ev.get('via_cover'), via_witness=ev.get('via_witness'),
                                        via_divisor=ev.get('via_divisor'))
    if o['kind'] == 'density': row.update(modulus=d['cover']['modulus'], fraction=d['fraction'])
    if o['kind'] == 'pattern': row.update(modulus=d['cover']['modulus'], rule=d['rule'])
    if o['kind'] == 'theorem': row.update(modulus=ev.get('modulus'), open_residues=ev.get('open_residues'),
                                          open_coprime=ev.get('open_coprime'), lo=d['lo'], range_hi=ev.get('range_hi'))
    if o['kind'] == 'dcover': row.update(modulus=d['modulus'], covered=ev.get('covered'))
    if o['kind'] == 'cfinite': row.update(lo=d['lo'], hi=d['hi'])
    if o['kind'] == 'cycle': row.update(start=d['start'], length=d['length'])
    return row
