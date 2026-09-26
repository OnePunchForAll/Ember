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
from types import GeneratorType

VERSION = 'ember.autonomous_agent.v1'
MAX_SAMPLES = 128
MAX_MACROS = 32
MAX_LOG = 64
MAX_TRIED = 6000
MAX_PER_TARGET = 1
MAX_TARGET_MOVES = 24
COMPANIONS = 4
# Operators that read the workspace: an attempt is new whenever the goal's progress has changed since.
READS_WORKSPACE = frozenset(('egypt_cover_assemble', 'egypt_finite_verify', 'collatz_cover_assemble', 'egypt_choose_lift',
                             'egypt_classical_sweep', 'egypt_wall_sweep', 'egypt_range_chunk', 'egypt_range_union',
                             'egypt_theorem_range', 'egypt_theorem_multiples', 'egypt_divisor_families',
                             'egypt_theorem_families', 'egypt_range_square', 'egypt_residual_profile', 'egypt_residual_falsify',
                             'egypt_shape_search'))
# Moves tried once per state of what they read, not once per target and call: each chunk, union or extension is new.
REPEATABLE = frozenset(('egypt_range_chunk', 'egypt_range_union', 'egypt_theorem_range', 'egypt_theorem_multiples',
                        'egypt_divisor_families', 'egypt_theorem_families', 'egypt_range_square', 'egypt_residual_profile',
                        'egypt_residual_falsify', 'egypt_shape_search'))
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
REFUSE_AFTER = 8  # claims of one strategy refused in a context and scope with none admitted before it is retired with the reason
REFUSE_BOUND = 2  # refusals at a bound of the language (a reason naming an instrument) that retire a strategy there at once
REFUSAL_FLOOR = 8  # a round that refused at least this many claims and admitted fewer waits for an instrument in her scan
NEVER_RETIRED = ('egypt_classical_family', 'egypt_classical_exclusion', 'egypt_classical_sweep', 'egypt_wall_sweep', 'verify')
# A refusal reason names the bound or instrument that would lift it: a fixed table read by the diagnosis, not a claim
# about why the round failed. Order matters where one reason contains another.
INSTRUMENTS = (('family shapes bound', 'MAX_DFAM_SHAPES in lexicon_check: the shapes a proof\'s family part may name'),
               ('family shape', 'MAX_DFAM_H in lexicon_check: the h a divisor family may have'),
               ('finite range bound', 'MAX_RANGE in lexicon_check: a longer range needs range_extend chunks'),
               ('closure residue bound', 'CLOSURE_RESIDUES in lexicon_check: a closure by family moduli'),
               ('premise identities', 'MAX_PREMISES in lexicon_check: the premises a derivation may name'),
               ('sieve lift bound', 'SIEVE_LIFTS in lexicon_check'), ('term count bound', 'MAX_TERMS in lexicon_check'),
               ('bit bound', 'MAX_BITS in lexicon_check'), ('object exceeds', 'MAX_OBJECT_BYTES in lexicon'))


def instrument_for(reason):
    return next((name for key, name in INSTRUMENTS if key in reason), None)


def refusal_rows(rt, limit=16):
    """The claims the checker refused this call, by move, kind and reason, most refused first, each with the first
    refused identity and the instrument its reason names (None when the table names none)."""
    rows = sorted(rt.refusals.items(), key=lambda kv: (-kv[1][0], kv[0]))[:limit]
    return [dict(strategy=k[0], kind=k[1], reason=k[2], count=v[0], first=v[1], instrument=instrument_for(k[2])) for k, v in rows]


def bound_refusals(rt):
    """The refusals whose reason names a bound of the language: their count and the most frequent such reason."""
    rows = [(v[0], k[2]) for k, v in rt.refusals.items() if instrument_for(k[2])]
    return sum(c for c, _ in rows), (max(rows)[1] if rows else None)


def diagnosis(agent, goal, rt, gained, refused, reason):
    """For a round that ran out of moves, gained nothing, refused more claims than it admitted, or had a claim refused
    at a bound of the language: what was exhausted, what was refused and why, the residual's size, and the instrument
    each refusal reason names. Read from her own run; it names a bound, not a cause. `blocked` is 'instrument' when a
    bound refused her claims, 'refused' when the checker refused more than it admitted, 'exhausted' when the round
    gained nothing without refusals, and 'none' when the round ran out of moves after gaining."""
    if agent is None: return None
    at_bound, bound = bound_refusals(rt)
    if gained and refused <= gained and reason != EXHAUSTED and not at_bound: return None
    kinds = {}
    for tid in agent.exhausted:
        o = rt.objects.get(tid); k = o['kind'] if o else 'gone'; kinds[k] = kinds.get(k, 0) + 1
    rows = refusal_rows(rt, 8)
    residual = sum(len(o['data']['items']) if type(o['data'].get('items')) in (list, dict) else 1
                   for o in rt.objects.values() if o['kind'] == 'residual')
    return dict(gained=gained, refused=refused, at_bound=at_bound, bound=bound, exhausted=kinds, residual_items=residual,
                reasons=[dict(reason=r['reason'], count=r['count'], strategy=r['strategy'], instrument=r['instrument']) for r in rows],
                instruments=sorted({r['instrument'] for r in rows if r['instrument']}),
                blocked='instrument' if at_bound else 'refused' if refused > gained and refused >= REFUSAL_FLOOR
                else 'exhausted' if not gained else 'none')
PRIOR_PROBES = 8  # a strategy her library has seen fail in a context gets this many tries per level before retiring
# Moves that prepare a whole level: tried once per workspace state rather than once per target.
LEVEL_STEPS = ('egypt_classical_obstruction', 'egypt_classical_sweep', 'egypt_wall_sweep')
MAX_ROUNDS = 32  # rounds remembered per problem: what each call obtained and cost, for her choice among problems
LEDGER_ID = 'problem-rounds'  # one record keeping every problem's rounds, so her choice survives evicted evidence
MAX_RECORDS = 128  # records one instance state holds (the host's bound); the oldest are evicted first
ARCHIVE_ENTRIES = 1024  # evicted records whose evidence file her ledger still names, oldest dropped first
EXHAUSTED = 'no untried move for any open target'
# Anytime moves: an operator that breathes (yields) runs in slices of at most SLICE_WORK; at a breath past the slice
# it waits with its own budget and place, and each step chooses again between the waiting moves and the best fresh
# one. At most MAX_SUSPENDED moves wait: with the table full she resumes one rather than starting another, so every
# search she starts is run to its end within the call unless its target closes or it reaches its work bound, which
# is ESCALATION times its allocation over all its slices (the bound an escalated plain move has).
SLICE_WORK = 4_000_000
MAX_SUSPENDED = 8
# Her choice among problems: a round is a success to the degree g / (g + GAIN_HALF) of its g new checked results, and
# a failure for the rest; only her last RECENT_ROUNDS rounds on a problem count.
GAIN_HALF = 64
RECENT_ROUNDS = 4
MAX_WIDEN_LEVELS = 4  # a settled window is restated with larger bounds up to this many times, by her own proposal


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def generation():
    root = Path(__file__).resolve().parent
    names = ('agent.py', 'lexicon.py', 'lexicon_check.py', 'ops_seq.py', 'ops_poly.py', 'ops_orbit.py', 'ops_egypt.py',
             'ops_arith.py', 'ops_word.py', 'ops_matrix.py', 'ops_collatz.py', 'recurrence_check.py', 'ops_wnum.py',
             'ops_wdisc.py', 'window_check.py', 'window_real.py', 'window_discrete.py')
    return hashlib.sha256(b''.join((root / name).read_bytes() for name in names)).hexdigest()


# The object kinds a problem starts from, by type; a window's own objects name theirs.
PROBLEM_KINDS = {'unit_fraction_cover': ('esq', 'eclass', 'en', 'ufam', 'cover'), 'descent_cover': ('cproblem', 'cclass', 'descent')}
CORE_FILES = ('agent.py', 'lexicon.py', 'lexicon_check.py')
WINDOW_FILES = ('window_check.py', 'window_real.py', 'window_discrete.py')


def relevant_generation(problem, registry):
    """The fingerprint of what a round on this problem can depend on: the core (this scheduler, the runtime, the
    checker) and the operator modules whose moves can apply, found by closure over the language's signatures from the
    problem's own kinds; a window's question kinds bring the window tools. A change of her code elsewhere leaves the
    problem's rounds valid, so only what the change can touch is checked again."""
    kinds = set(PROBLEM_KINDS.get(problem.get('type')) or [o.get('kind') for o in problem.get('objects', []) if type(o) is dict])
    modules = set(); grown = True
    while grown:
        grown = False
        for spec in registry.values():
            if type(spec) is not dict or 'consumes' not in spec: continue
            if set(spec['consumes']) & kinds:
                new = set(spec['produces']) - kinds
                if spec['module'] not in modules or new: modules.add(spec['module']); kinds |= new; grown = True
    files = list(CORE_FILES) + sorted(m if m.endswith('.py') else m + '.py' for m in modules)
    if any(str(k).endswith('_q') or k in ('value', 'witness', 'proof') for k in kinds): files += list(WINDOW_FILES)
    root = Path(__file__).resolve().parent
    return hashlib.sha256(b''.join((root / name).read_bytes() for name in files if (root / name).exists())).hexdigest()


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


def saved_cover(cover, best, heads=()):
    """The saved cover object whose data a claim carries, among the covers persisted with it, or None."""
    for head in ([best] if best is not None else []) + list(heads):
        if head is not None and head['data'] == cover: return head
    return None


def forget_first(records):
    """What to forget first when the record bound is reached: records of settled problems (their evidence is on file
    and their problem waits for new instruments), then the oldest of the rest in their order; an open problem's record
    stays as long as it can."""
    settled = [o for o in records if o.get('status') == 'CHECKED_RESEARCH']
    return settled + [o for o in records if o.get('status') != 'CHECKED_RESEARCH']


def compact_proof(L, obj, best, heads=()):
    """A saved derivation whose proof carries a saved cover names it by digest; it is expanded again on resume."""
    d = obj['data']; proof = d.get('proof')
    head = saved_cover(proof.get('cover'), best, heads) if type(proof) is dict else None
    if head is None: return obj
    return dict(kind=obj['kind'], data=dict(d, proof=dict({k: v for k, v in proof.items() if k != 'cover'},
                                                          cover_ref=L.digest(head['data']))))


def latest_residual_claims(derived):
    """Derived claims to save: every one, except that of the residual predicates only the widest claim of each
    predicate is kept (an earlier claim of the same predicate over fewer proofs is implied by it); breaks are kept."""
    widest = {}
    for o in derived:
        d = o['data']
        if d['rule'] == 'residual_predicate':
            key = json.dumps(d['statement']['predicate'], sort_keys=True); best = widest.get(key)
            if best is None or (d['statement']['hi'], len(d['premises'])) > (best['data']['statement']['hi'], len(best['data']['premises'])):
                widest[key] = o
    return [o for o in derived if o['data']['rule'] != 'residual_predicate' or widest[json.dumps(o['data']['statement']['predicate'], sort_keys=True)] is o]


def compact_range(L, obj, best, heads=()):
    """A saved range whose cover is a saved cover names it by digest; it is expanded again on resume."""
    d = obj['data']; head = saved_cover(d.get('cover'), best, heads)
    if head is None: return obj
    return dict(kind=obj['kind'], data=dict({k: v for k, v in d.items() if k != 'cover'}, cover_ref=L.digest(head['data'])))


def gaps(values):
    """Sorted integers as their first value and the gaps between neighbours."""
    values = sorted(values)
    return values[:1] + [b - a for a, b in zip(values, values[1:])]


def ungaps(encoded):
    out = []
    for step in encoded: out.append(step if not out else out[-1] + step)
    return out


def lean_family(L, d):
    """A classical family saved by its parameters only; parameters are recovered for families found without them."""
    if 'p' not in d and 'x' in d and len(d['x']) == 3 and all(e and type(e[0]) is list for e in d['x']):
        named = L.classical_params_of(d['a'], d['m'], d['r'], d['x'])
        if named: d = dict(d, p=named)
    return {k: v for k, v in d.items() if k != 'x'} if 'p' in d else d


def full_family(L, d, shapes=None):
    """A family in working form: parameters are kept, and the denominators rebuilt when they were left out, from the
    named classical parameters or from the family's identity in its shape table."""
    if 's' in d: return L.unshape(d, shapes)
    return dict(d, x=L.classical_x(d['a'], d['m'], d['r'], d['p'])) if 'x' not in d and 'p' in d else d


BATCH_FAMILIES = 512  # families per saved batch, so the state bound can keep some batches when not all fit


def family_batches(L, a, terms, families):
    """Families saved in the compact form: batches with one shape table each, classical families by parameters."""
    out = []
    for i in range(0, len(families), BATCH_FAMILIES):
        shapes, members = L.shape_table([lean_family(L, d) for d in families[i:i + BATCH_FAMILIES]])
        out.append(dict(kind='ufam', data=dict(a=a, terms=terms, shapes=shapes, members=members)))
    return out


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

    def capped_key(self, rt, target, retired_in):
        """Goal state that can give a capped target a new move, or None to fall back on global progress. retired_in
        counts retirements per (context, scope)."""
        return None

    def capped_global(self, rt):
        """The part of capped_key shared by every target (retirements aside, which the agent counts itself)."""
        return ()

    def library_context(self, context, problems):
        """A saved library context in the goal's current naming; problems are the saved problem statements of this
        goal type in the state, or empty when some record has none."""
        return context

    def transfer(self, rt, rows):
        """Checked objects from records of related problems, admitted again by the checker; returns (admitted, refused)."""
        return 0, 0

    def done(self, rt): return False

    def outcome(self, rt):
        """How checked results settled the problem ('proved', 'refuted' or 'found'), or None while it is open."""
        return None

    def settled(self, rt, target):
        """The checked claim that rules out the goal's remaining strategies on an open target, or None."""
        return None

    def failure_profile(self, rt): return {}

    def related(self): return []

    def schedule_key(self, rt):
        """Goal state beyond progress that can make a move newly allowed; part of a target's exhaustion signature."""
        return ()

    def attempting(self, strategy, target, rt):
        """Told before each move is executed; a goal may keep what it needs to schedule its own steps."""

    def carry_report(self):
        """Saved claims whose admission the goal deferred until its own claims could settle them."""
        return {}

    def carries(self, record):
        """Whether transfer carries the checked claims of this saved record into the goal's own work."""
        return False


class CoverGoal(Goal):
    """Cover every residue class of a/n = sum of `terms` unit fractions by checked polynomial families."""
    kind = 'unit_fraction_cover'
    persist = ('cover', 'finite')
    capped = ('eclass', 'en')
    limit_kinds = ('nofamily', 'obstruction')

    def outcome(self, rt):
        """'proved' once a checked theorem leaves no residue open from the problem's least n: every n >= min is then
        represented, below the checked range's end by the range and above it by a family. Covers never refute."""
        self.update(rt)
        for o in self.theorems:
            d = o['data']
            if o['status'] == 'checked' and d['a'] == self.p['a'] and d['terms'] == self.p['terms'] \
                    and d['lo'] <= self.p['min'] and o.get('evidence', {}).get('open_residues') == 0:
                return 'proved'
        return None

    def done(self, rt): return self.outcome(rt) is not None

    def __init__(self, p, L):
        self.p, self.L = p, L
        self.levels = [p['modulus']]
        for q in p['lifts']: self.levels.append(self.levels[-1] * q)
        self.limit = len(self.levels) + p.get('extra_lifts', 0)
        self.fam = {}; self.residual = set(); self.base_miss = set(); self.misses = {}; self.refined = set(); self.seen = 0
        self.classes = []; self.classical_miss = set(); self._ready = None; self._powers = {}; self._contexts = {}
        # Incremental indexes: the step loop reads these instead of rescanning the workspace.
        self.results = []; self.covers_at = {}; self._open = {}; self.fam_count = 0; self.theorems = []
        self.fam = {}; self.fam_log = []; self._fam_known = set(); self.lemmas = []
        # Walls by modulus, lemma attempts and refutations: what a level already knows about its classes.
        self.walled = {}; self._wall_pending = []; self.lemma_tried = set(); self.lemma_refuted = set(); self._prep = None
        # The workspace state at which each level step was last tried: a tried step no longer holds the level back.
        self.swept = {}; self._sweeps = 0
        # Carried walls by modulus, admitted once her lemma at their level is settled (the lemma implies the square ones).
        self.deferred = {}; self.carried_later = dict(admitted=0, refused=0, implied_by_lemma=0); self._lemma_at = {}

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
        for identity in rt.order[self.seen:]:
            o = rt.objects.get(identity)
            if o is None: continue
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
            if o['kind'] == 'template' or o['kind'] in ('finite', 'cover', 'pattern', 'density', 'theorem', 'obstruction', 'derived'):
                self.results.append(o)
                if o['kind'] == 'theorem': self.theorems.append(o)
                if o['kind'] == 'obstruction': self.lemmas.append(o); self.lemma_tried.add(o['data']['m'])
            if o['kind'] == 'nofamily' and o['data'].get('a') == self.p['a']: self._wall_pending.append(o)
            if o['kind'] == 'refutation' and o['data']['claim']['kind'] == 'obstruction': self._wall_pending.append(o)
        self.seen = len(rt.order)
        waiting = []
        for o in self._wall_pending:
            if o['status'] != 'checked': waiting.append(o); continue
            if o['kind'] == 'refutation': self.lemma_refuted.add(o['data']['claim']['data']['m']); continue
            d = o['data']; self.walled.setdefault(d['m'], set()).update(d['rs'] if 'rs' in d else [d['r']])
        self._wall_pending = waiting
        # Family classes only accumulate; the log keeps their order of discovery for incremental updates.
        for identity in self.fresh_family_ids(rt):
            if identity in self._fam_known: continue
            self._fam_known.add(identity); d = rt.objects[identity]['data']; rs = self.fam.setdefault(d['m'], set())
            if d['r'] not in rs: rs.add(d['r']); self.fam_log.append((d['m'], d['r']))
        self.fam_count = len(self.fam_log)
        for o in self.results:
            if o['kind'] == 'cover' and o['status'] == 'checked': self.covers_at[o['data']['modulus']] = o

    def fresh_family_ids(self, rt):
        """Checked family objects of this equation not returned before, in creation order. A family seen before it was
        checked waits until it is checked, refuted or refused (the checker never admits a refused claim later)."""
        if not hasattr(self, '_checked'): self._checked = []; self._waiting = []; self._scanned = 0
        fresh = []
        for position in range(self._scanned, len(rt.order)):
            identity = rt.order[position]; o = rt.objects.get(identity)
            if o is None or o['kind'] != 'ufam' or o['data']['a'] != self.p['a'] or len(o['data']['x']) != self.p['terms']:
                continue
            (fresh if o['status'] == 'checked' else self._waiting).append((position, identity))
        self._scanned = len(rt.order); waiting = []
        for position, identity in self._waiting:
            o = rt.objects.get(identity)
            if o is None or o['status'] == 'refuted' or o.get('rejections'): continue
            (fresh if o['status'] == 'checked' else waiting).append((position, identity))
        self._waiting = waiting
        fresh.sort(); self._checked += fresh
        return [identity for _, identity in fresh]

    def family_ids(self, rt):
        """Every checked family object of this equation, in the order they were found checked."""
        self.update(rt); return [identity for _, identity in self._checked]

    def families(self, rt):
        self.update(rt); return self.fam

    def covered(self, index, m, r):
        return any(m % fm == 0 and r % fm in rs for fm, rs in index.items())

    def residual_of(self, rt, target):
        """Every family generator has missed the class, or was retired in its context and is taken to miss."""
        if target['id'] in self.base_miss: return True
        found = self.misses.get(target['id'], set()); context = self.context(target)
        if self.obstructed(rt, target): found = found | {'classical miss'}
        scope = self.retire_scope(target)
        return all(note in found or (context, MISS_SOURCES[note], scope) in self.retired for note in FAMILY_MISSES)

    def retire_scope(self, target):
        # The classes of one refinement level: lifts to a new level are a new population.
        return target['data'].get('m') if target['kind'] == 'eclass' else None

    def capped_global(self, rt):
        return len(self.levels), len(self.lemmas), len(self.lemma_refuted)

    def capped_key(self, rt, target, retired_in):
        # A class gains a move only through its own derived objects, a new level, a lemma, or, above the finest level
        # where it can release a refinement, a retirement in its own context and level; a family found elsewhere does
        # not change what the class can try.
        coarse = target['kind'] != 'eclass' or target['data']['m'] != self.levels[-1]
        return (len(self.levels), len(self.lemmas), len(self.lemma_refuted),
                retired_in.get((self.context(target), self.retire_scope(target)), 0) if coarse else 0)

    def library_context(self, context, problems):
        # Contexts saved before the numerator was part of their name are read as this numerator only when every saved
        # record of this goal type has it: 4/n and 5/n classes answer the same strategies differently.
        legacy = self.kind + ':eclass:'
        if context.startswith(legacy) and problems and all(p.get('a') == self.p['a'] for p in problems):
            return self.kind + ':a' + str(self.p['a']) + ':eclass:' + context[len(legacy):]
        return context

    def retirable(self, context, strategy):
        # The classical generator and wall certificates decide every class's status; they are never retired.
        return ':eclass' in context and context.startswith(self.kind) and strategy not in NEVER_RETIRED

    def targets(self, rt):
        self.update(rt); out = []
        if self.deferred: self.settle_deferred(rt)
        # The finest level is prepared before its classes: her lemma, then the classical sweep, then the walls.
        if self.preparing(rt): out.append(self.esq[-1])
        for q in self.primes:
            if not self.covered(self.fam, q, 0): out.append(self.en[q])
        for level, M in enumerate(self.levels):
            out += self.open_classes(M)
            out.append(self.esq[level])
            if M in self.covers_at: out.append(self.covers_at[M])
        return out

    def search_spoke(self, rt):
        """Whether the shape search has run this call: a general family or its note admitted since the carried set."""
        if not getattr(self, '_spoke', False):
            self._spoke = any(o['id'] not in rt.carried and (o['kind'] == 'gfam' or (o['kind'] == 'residual'
                              and str(o['data'].get('note', '')).startswith('shape search'))) for o in rt.objects.values())
        return self._spoke

    def lemma_at(self, m):
        """Her checked lemma at a multiple of m, if any: it speaks for every coprime square class modulo m."""
        key = (m, len(self.lemmas))
        if key not in self._lemma_at:
            if len(self._lemma_at) > 4096: self._lemma_at.clear()
            self._lemma_at[key] = any(o['status'] == 'checked' and o['data']['m'] % m == 0 and o['data']['a'] == self.p['a']
                                      for o in self.lemmas)
        return self._lemma_at[key]

    def implied_wall(self, d):
        """A wall that her checked lemma implies: a coprime class that is a square modulo every prime-power factor of m,
        with the lemma checked at a multiple of m. A classical family reaching it would have a modulus dividing m and
        would reach a coprime square class at the lemma's level, which the lemma excludes."""
        m, r = d['m'], d['r']
        if d.get('a') != self.p['a'] or d.get('terms') != self.p['terms'] or gcd(r, m) != 1 or not self.lemma_at(m):
            return False
        if m not in self._powers: self._powers[m] = self.L.factor(m)
        return not nonresidue_primes(r, self._powers[m])

    def settle_deferred(self, rt):
        """Admit carried walls once she has reached their level and her lemma there is settled: the walls it implies
        are not checked again, the others are proposed and checked. Walls at a level she has not reached keep waiting
        and are saved as they were carried."""
        for m in list(self.deferred):
            if m not in self.levels or not (self.p['terms'] != 3 or self.lemma_at(m) or self.lemma_settled(m)
                                            or ('egypt_classical_obstruction', m) in self.swept):
                continue
            for d in self.deferred.pop(m):
                if self.implied_wall(d): self.carried_later['implied_by_lemma'] += 1; continue
                self.carried_later['admitted' if rt.check(rt.propose('nofamily', d)) else 'refused'] += 1

    def carry_report(self):
        return dict(self.carried_later, waiting=sum(len(v) for v in self.deferred.values()))

    def carries(self, record):
        p = record.get('problem')
        return (type(p) is dict and p.get('type') == self.kind and p.get('a') == self.p['a']
                and p.get('terms') == self.p['terms'])

    def lemma_settled(self, M):
        """Her lemma was stated at this level, or refuted at a divisor (a refutation there holds here too)."""
        return M in self.lemma_tried or any(M % m == 0 for m in self.lemma_refuted)

    def level_needs(self, rt, M):
        """(classes still without a classical outcome, missed classes still without a wall) at level M."""
        # A new family only closes work, so it does not refresh the count; every sweep attempt does, so a count a
        # family made stale costs at most one sweep that finds nothing to do.
        key = (M, len(self.classical_miss), len(self.classes), len(self.refined), len(self.lemmas),
               sum(len(v) for v in self.walled.values()), self._sweeps)
        if self._prep is None or self._prep[0] != key:
            opened = self.open_classes(M); walled = self.walled.get(M, set())
            sweep = sum(1 for c in opened if c['id'] not in self.classical_miss and not self.obstructed(rt, c))
            walls = sum(1 for c in opened if c['id'] in self.classical_miss and c['data']['r'] not in walled
                        and not self.obstructed(rt, c))
            self._prep = (key, (sweep, walls))
        return self._prep[1]

    def level_step_wanted(self, rt, strategy, M):
        """Whether a level step has work left at level M: the lemma until stated or tried, then the classical sweep while
        classes lack a classical outcome, then the wall batch for the classes the generator missed."""
        if strategy == 'egypt_classical_obstruction': return not self.lemma_settled(M)
        if not (self.lemma_settled(M) or ('egypt_classical_obstruction', M) in self.swept): return False
        sweep, walls = self.level_needs(rt, M)
        return bool(sweep) if strategy == 'egypt_classical_sweep' else (not sweep and bool(walls))

    def step_state(self, rt, strategy, target):
        return True if strategy == 'egypt_classical_obstruction' else self.version(rt, strategy, target)

    def attempting(self, strategy, target, rt):
        if strategy in LEVEL_STEPS and target['kind'] == 'esq':
            self.swept[(strategy, target['data']['modulus'])] = self.step_state(rt, strategy, target); self._sweeps += 1

    def preparing(self, rt):
        """The finest level is prepared before its other questions, while a level step has work it has not yet tried
        in the current workspace state."""
        if self.p['terms'] != 3: return False
        M = self.levels[-1]; esq = self.esq[-1]
        return any(self.level_step_wanted(rt, name, M) and self.swept.get((name, M)) != self.step_state(rt, name, esq)
                   for name in LEVEL_STEPS)

    def open_classes(self, M):
        """Open class targets of one level, sorted by residue, kept incrementally with a map from residue to class: a
        class that is open stays open until a family found since the last call reaches it or it is refined, and new
        classes are tested against every family."""
        cached = self._open.get(M)
        if cached is None:
            opened = [o for o in sorted((c for c in self.classes if c['data']['m'] == M), key=lambda c: c['data']['r'])
                      if o['id'] not in self.refined and not self.covered(self.fam, M, o['data']['r'])]
            self._open[M] = (len(self.fam_log), len(self.classes), len(self.refined), opened,
                             {o['data']['r']: o for o in opened})
            return opened
        fams, classes, refined, opened, at = cached
        if (fams, classes, refined) == (len(self.fam_log), len(self.classes), len(self.refined)): return opened
        fresh = {}
        for m, r in self.fam_log[fams:]:
            if M % m == 0: fresh.setdefault(m, set()).add(r)
        gone = set()
        for m, rs in fresh.items():
            # A new family class reaches its lifts r + m*j modulo M: look those up when they are fewer than the list.
            if (M // m) * len(rs) < len(at):
                for r in rs:
                    for x in range(r, M, m):
                        o = at.pop(x, None)
                        if o is not None: gone.add(o['id'])
            else:
                for o in opened:
                    if o['data']['r'] % m in rs and at.pop(o['data']['r'], None) is not None: gone.add(o['id'])
        if refined != len(self.refined):
            for o in opened:
                if o['id'] in self.refined and at.pop(o['data']['r'], None) is not None: gone.add(o['id'])
        if gone: opened = [o for o in opened if o['id'] not in gone]
        if classes != len(self.classes):
            added = [c for c in self.classes[classes:] if c['data']['m'] == M and c['id'] not in self.refined
                     and not self.covered(self.fam, M, c['data']['r']) and c['data']['r'] not in at]
            if added:
                opened = sorted(opened + added, key=lambda c: c['data']['r'])
                for c in added: at[c['data']['r']] = c
        self._open[M] = (len(self.fam_log), len(self.classes), len(self.refined), opened, at)
        return opened

    def version(self, rt, strategy, target):
        """What a workspace-reading move depends on: the family classes that divide its modulus."""
        self.update(rt)
        if strategy == 'egypt_cover_assemble':
            M = target['data']['modulus']
            return sum(len(rs) for m, rs in self.fam.items() if M % m == 0)
        if strategy in ('egypt_classical_sweep', 'egypt_wall_sweep'):
            return (self.fam_count, len(self.classical_miss), len(self.classes), len(self.lemmas),
                    sum(len(v) for v in self.walled.values()))
        if strategy in ('egypt_residual_profile', 'egypt_shape_search'): return ('carried',)  # read what the call carried in: once per call
        if strategy == 'egypt_residual_falsify':
            # Runs again only when a chunk proof or a residual claim was added, not on every derived object.
            return (sum(1 for o in self.results if o['kind'] == 'derived' and o['status'] == 'checked'
                        and o['data']['rule'] in ('range_extend', 'residual_predicate', 'residual_break')),)
        if strategy in ('egypt_range_chunk', 'egypt_range_union', 'egypt_theorem_range', 'egypt_theorem_multiples',
                        'egypt_divisor_families', 'egypt_theorem_families', 'egypt_range_square'):
            # The range moves depend on the admitted ranges, derivations, theorems and covers.
            return tuple(sum(1 for o in self.results if o['kind'] == k and o['status'] == 'checked')
                         for k in ('finite', 'derived', 'theorem', 'cover', 'dfam', 'gfam'))
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
        if strategy in LEVEL_STEPS:
            if target['kind'] != 'esq' or target['data']['modulus'] != self.levels[-1]: return False
            return self.level_step_wanted(rt, strategy, self.levels[-1])
        if target['kind'] == 'esq' and target['data']['modulus'] == self.levels[-1] and self.preparing(rt):
            return False  # the level's other questions wait until it is prepared
        if strategy == 'egypt_classical_family' and target['kind'] == 'eclass':
            # Known already: the sweep missed it, or her lemma rules out every classical family for it.
            if target['id'] in self.classical_miss or self.obstructed(rt, target): return False
        if strategy in ('egypt_range_chunk', 'egypt_finite_verify') and target['data'].get('terms') == 3 \
                and getattr(self, 'gated', False) and not self.search_spoke(rt):
            # Shapes before ranges: a range move waits until her shape search has run this call (it states general
            # families or a note), so a chunk uses every family she can find. The preregistered rounds of the shape
            # search found the chunk running first on ten problems of eleven, and the families unused.
            return False
        if strategy == 'egypt_finite_verify': return target['data']['modulus'] == self.levels[-1]
        if strategy in ('egypt_cover_lift', 'egypt_cover_merge'): return False
        if strategy == 'egypt_classical_exclusion':
            # Certify a wall only where the classical generator already missed, at the finest level, and not for a
            # square class once her obstruction lemma covers the level: the lemma already excludes it.
            return (target['kind'] == 'eclass' and target['data']['m'] == self.levels[-1]
                    and target['id'] in self.classical_miss and not self.obstructed(rt, target)
                    and target['data']['r'] not in self.walled.get(target['data']['m'], ()))
        if strategy == 'egypt_choose_lift':
            return (target['kind'] == 'esq' and target['data']['modulus'] == self.levels[-1]
                    and len(self.levels) < self.limit and self.top_ready(rt))
        return True

    def schedule_key(self, rt):
        self.update(rt)
        return (len(self.classical_miss), len(self.levels), len(self.retired), sum(len(v) for v in self.walled.values()),
                len(self.lemma_tried), len(self.lemma_refuted), len(self.swept))

    def top_ready(self, rt):
        """Every open class at the finest level has been tried by the classical generator, and a cover exists there."""
        self.update(rt); M = self.levels[-1]
        if M not in self.covers_at: return False
        key = (M, len(self.classical_miss), sum(len(v) for v in self.fam.values()), len(self.classes), len(self.lemmas))
        if self._ready is None or self._ready[0] != key:
            self._ready = (key, all(c['id'] in self.classical_miss or self.obstructed(rt, c) or self.covered(self.fam, M, c['data']['r'])
                                    for c in self.classes if c['data']['m'] == M and c['id'] not in self.refined))
        return self._ready[1]

    def context(self, target):
        """Classes are told apart by whether they share a factor with the modulus and, if not, by whether they are
        squares modulo every prime-power factor: a feature the agent observes, not a claim."""
        if target['kind'] != 'eclass': return self.kind + ':' + target['kind']
        known = self._contexts.get(target['id'])
        if known is None:
            m, r = target['data']['m'], target['data']['r']
            if m not in self._powers: self._powers[m] = self.L.factor(m)
            known = self.kind + ':a' + str(self.p['a']) + ':eclass:' + (
                'shared' if gcd(r, m) != 1 else 'coprime:nonsquare' if nonresidue_primes(r, self._powers[m]) else 'coprime:square')
            self._contexts[target['id']] = known
        return known

    def progress(self, rt):
        """A cheap signature that changes exactly when a checked family class or a result object is added."""
        self.update(rt)
        done = tuple(sorted(o['kind'] for o in self.results if o['kind'] == 'template' or o['status'] == 'checked'))
        return self.fam_count, done

    def persisted(self, rt):
        """Her theorem's chain first: the cover her latest checked range uses, the range and every claim about that
        cover in compact form (the cover replaced by its digest); then the finest checked cover and its claims when it
        is another cover; her lemmas, templates, walls and refinement tree; and the families outside both covers."""
        covers = [o for o in rt.objects.values() if o['kind'] == 'cover' and o['status'] == 'checked']
        # The base ranges start at the problem's least n (one per cover they were verified with); later chunks extend
        # them through derivations.
        finite = sorted((o for o in rt.objects.values() if o['kind'] == 'finite' and o['status'] == 'checked'),
                        key=lambda o: (o['data']['lo'] != self.p['min'], o['data']['lo'], -o['data']['hi']))
        bases = [o for o in finite if o['data']['lo'] == self.p['min']]
        chunks = [o for o in finite if bases and o['data']['lo'] >= bases[0]['data']['hi']]; finite = bases[:1]
        best = max(covers, key=lambda o: (o['data']['modulus'], len(o['data']['entries'])), default=None)
        chain = next((o for o in covers if finite and o['data'] == finite[-1]['data']['cover']), None) or best
        heads = [chain] + ([best] if best is not None and best is not chain else []) if chain is not None else []
        families = [rt.objects[i] for i in self.family_ids(rt)]
        claims = {id(o): [] for o in heads}
        for head in heads:
            inside = {self.L.digest(full_family(self.L, e['family'], head['data'].get('shapes'))) for e in head['data']['entries']}
            families = [o for o in families if self.L.digest(o['data']) not in inside
                        and not self.covered_by(head['data'], o['data'])]
            ref = self.L.digest(head['data'])
            for o in rt.objects.values():
                if o['kind'] in ('pattern', 'density') and o['status'] == 'checked' and o['data']['cover'] == head['data']:
                    body = {k: v for k, v in o['data'].items() if k != 'cover'}
                    claims[id(head)].append(dict(kind=o['kind'], data=dict(body, cover_ref=ref)))
        chained = []
        for base in bases:
            # Each base range is kept, its cover by digest when that cover is saved, and every theorem about it with the
            # range replaced by its digest.
            ref = self.L.digest(base['data'])
            chained += [compact_range(self.L, base, chain, heads)] + [
                dict(kind='theorem', data=dict({k: v for k, v in o['data'].items() if k != 'finite'}, finite_ref=ref))
                for o in rt.objects.values() if o['kind'] == 'theorem' and o['status'] == 'checked'
                and o['data']['finite'] == base['data']]
        claims_first = ([chain] + chained + claims[id(chain)] if chain is not None else chained)
        claims_first += [row for head in heads[1:] for row in [head] + claims[id(head)]]
        # Range chunks past the base range and the derivations built on them (the chunk's cover is named by digest).
        # Divisor families stand alone; the chunk proofs that use them name their shapes and are checked exactly.
        claims_first += [dict(kind=k, data=o['data']) for k in ('dfam', 'gfam') for o in rt.objects.values() if o['kind'] == k and o['status'] == 'checked']
        claims_first += [compact_range(self.L, o, chain, heads) for o in chunks]
        claims_first += [compact_proof(self.L, o, chain, heads) for o in latest_residual_claims(
            [o for o in rt.objects.values() if o['kind'] == 'derived' and o['status'] == 'checked'])]
        lemmas = [o for o in rt.objects.values() if (o['kind'] == 'obstruction' and o['status'] == 'checked') or
                  (o['kind'] == 'refutation' and o['status'] == 'checked' and o['data']['claim']['kind'] == 'obstruction')]
        batches = {}
        self.update(rt)
        for o in rt.objects.values():
            if o['kind'] == 'nofamily' and o['status'] == 'checked':
                d = o['data']; rows = batches.setdefault((d['a'], d['terms'], d['m'], d['bound']), [])
                rows.extend(r for r in (d['rs'] if 'rs' in d else [d['r']])
                            if not self.implied_wall(dict(a=d['a'], terms=d['terms'], m=d['m'], r=r)))
        # Carried walls still waiting for a lemma are saved as they were carried; the next call admits them again.
        for m, waiting in self.deferred.items():
            for d in waiting: batches.setdefault((d['a'], d['terms'], d['m'], d['bound']), []).append(d['r'])
        # Walls are saved one batch per modulus, and classical families by their parameters: shorter certificates for
        # the same claims, expanded again when she resumes.
        walls = [dict(kind='nofamily', data=dict(a=a, terms=terms, m=m, bound=bound, rs=sorted(set(rs))))
                 for (a, terms, m, bound), rs in sorted(batches.items())]
        families = family_batches(self.L, self.p['a'], self.p['terms'], [o['data'] for o in families])
        # Most valuable first, since the state bound trims from the end: her theorem's chain (the cover, the range and
        # the claims that name them), her lemmas, templates and walls, then the refinement tree (bookkeeping for a
        # resume), and last the families outside the cover, which her generators find again.
        return (claims_first + lemmas + [o for o in rt.objects.values() if o['kind'] == 'template'] + walls
                + [self.tree(rt)] + families)

    def tree(self, rt):
        """The refinement tree as bookkeeping, not a claim: every level (the agent's own included), the classes that
        were refined, and the family grammars each class has already missed. Residues are grouped by modulus (and by
        the set of missed grammars) and stored as gaps between sorted residues: [m, [r0, r1 - r0, ...]]."""
        self.update(rt); notes = sorted(FAMILY_MISSES); refined = {}; misses = {}
        for i in self.refined:
            d = rt.objects[i]['data']
            if rt.objects[i]['kind'] == 'eclass': refined.setdefault(d['m'], []).append(d['r'])
        for i, found in self.misses.items():
            d = rt.objects[i]['data']
            misses.setdefault((d['m'], sum(1 << notes.index(n) for n in found)), []).append(d['r'])
        return dict(kind='cover_tree', data=dict(a=self.p['a'], terms=self.p['terms'], levels=self.levels, form='gaps',
                                                 refined=[[m, gaps(rs)] for m, rs in sorted(refined.items())],
                                                 misses=[[m, mask, gaps(rs)] for (m, mask), rs in sorted(misses.items())]))

    def rebuild(self, rt, tree):
        """Recreate the saved refinement tree so that remembered moves stay consistent with the workspace."""
        p = self.p; notes = sorted(FAMILY_MISSES)
        if (tree.get('a'), tree.get('terms')) != (p['a'], p['terms']) or tree.get('levels', [])[:len(self.levels)] != self.levels:
            return
        for M in tree['levels'][len(self.levels):]:
            rt.given('esq', dict(a=p['a'], terms=p['terms'], min=p['min'], modulus=M, verify_to=p['verify_to']))
            self.update(rt)
        refined, misses = tree.get('refined', []), tree.get('misses', [])
        if tree.get('form') == 'gaps':
            refined = [(m, r) for m, rs in refined for r in ungaps(rs)]
            misses = [(m, r, mask) for m, mask, rs in misses for r in ungaps(rs)]
        for m, r in refined:
            if m not in self.levels or m == self.levels[-1]: continue
            nxt = self.levels[self.levels.index(m) + 1]
            parent = rt.given('eclass', dict(a=p['a'], terms=p['terms'], m=m, r=r))
            for j in range(nxt // m):
                rt.propose('eclass', dict(a=p['a'], terms=p['terms'], m=nxt, r=r + m * j), (parent,))
        for m, r, mask in misses:
            cls = rt.given('eclass', dict(a=p['a'], terms=p['terms'], m=m, r=r))
            for k, note in enumerate(notes):
                # The restored miss records the attempt of the generator whose miss it is.
                if mask >> k & 1: rt.residual(cls, ['restored from the saved refinement tree'], note, by=MISS_SOURCES.get(note))
        self.update(rt)

    def covered_by(self, cover, family):
        return any(family['m'] % e['family']['m'] == 0 and family['r'] % e['family']['m'] == e['family']['r']
                   for e in cover['entries'])

    def expand(self, rows):
        """Saved rows in the working form: a wall batch becomes one wall per residue, and a family saved by its
        parameters regains its denominators (the checker then admits both again)."""
        out = []
        for row in rows:
            d = row['data']
            if row['kind'] == 'nofamily' and 'rs' in d:
                out += [dict(kind='nofamily', data=dict({k: v for k, v in d.items() if k != 'rs'}, r=r)) for r in d['rs']]
            elif row['kind'] == 'ufam' and 'members' in d:
                out += [dict(kind='ufam', data=full_family(self.L, f, d['shapes'])) for f in d['members']]
            elif row['kind'] == 'ufam': out.append(dict(kind='ufam', data=full_family(self.L, d)))
            elif row['kind'] == 'cover':
                out.append(dict(kind='cover', data=d))
            else: out.append(row)
        return out

    def restore(self, rt, saved):
        for row in saved:
            if row['kind'] == 'cover_tree': self.rebuild(rt, row['data'])
        saved = self.expand([row for row in saved if row['kind'] != 'cover_tree'])
        covers = {self.L.digest(row['data']): row['data'] for row in saved if row['kind'] == 'cover'}
        with_covers = []
        for row in saved:
            data = row['data']
            if 'cover_ref' in data:
                # A compact claim is rechecked against the saved cover it names; without that cover it is dropped.
                if data['cover_ref'] not in covers: continue
                data = dict({k: v for k, v in data.items() if k != 'cover_ref'}, cover=covers[data['cover_ref']])
            if row['kind'] == 'derived' and type(data.get('proof')) is dict and 'cover_ref' in data['proof']:
                if data['proof']['cover_ref'] not in covers: continue
                data = dict(data, proof=dict({k: v for k, v in data['proof'].items() if k != 'cover_ref'},
                                             cover=covers[data['proof']['cover_ref']]))
            with_covers.append(dict(kind=row['kind'], data=data))
        ranges = {self.L.digest(row['data']): row['data'] for row in with_covers if row['kind'] == 'finite'}
        expanded = []
        for row in with_covers:
            data = row['data']
            if 'finite_ref' in data:
                if data['finite_ref'] not in ranges: continue
                data = dict({k: v for k, v in data.items() if k != 'finite_ref'}, finite=ranges[data['finite_ref']])
            expanded.append(dict(kind=row['kind'], data=data))
        saved = expanded
        walls = [row for row in saved if row['kind'] == 'nofamily']
        derived = [row for row in saved if row['kind'] == 'derived']
        admitted, refused = Goal.restore(self, rt, [row for row in saved if row['kind'] not in ('nofamily', 'derived')])
        # A derivation is admitted once every premise it names is admitted again; one whose premise is gone is refused.
        pending = derived
        while pending:
            rest = []
            for row in pending:
                if all(rt.admitted(i) is not None for i in row['data'].get('premises', [])):
                    if rt.check(rt.propose('derived', row['data'])): admitted += 1
                    else: refused += 1
                else: rest.append(row)
            if len(rest) == len(pending): refused += len(rest); break
            pending = rest
        # Walls come after her lemmas: a wall a restored lemma implies is not checked again.
        self.update(rt); kept = []
        for row in walls:
            if self.implied_wall(row['data']): self.carried_later['implied_by_lemma'] += 1
            else: kept.append(row)
        more, less = Goal.restore(self, rt, kept); admitted += more; refused += less
        for row in saved:
            if row['kind'] != 'cover': continue
            cover = rt.propose('cover', row['data'])
            if cover['status'] != 'checked': continue
            for entry in row['data']['entries']:
                # The families were checked inside the cover check; restating them keeps coverage bookkeeping exact.
                family = rt.propose('ufam', full_family(self.L, entry['family'], row['data'].get('shapes')))
                if rt.check(family): admitted += 1
        return admitted, refused

    def transfer(self, rt, rows):
        """Families, covers, walls and templates are claims about the equation a/n = 1/x + 1/y + 1/z itself, whatever
        the refinement budget of the problem that found them: they carry over to a problem with the same a and terms.
        Each is a proposal until the checker admits it again; level-specific claims (ranges, patterns) do not carry."""
        a, terms = self.p['a'], self.p['terms']
        def same(row):
            d = row['data']
            if row['kind'] == 'ufam': return d.get('a') == a and (len(d['x']) if 'x' in d else 3) == terms
            if row['kind'] in ('cover', 'nofamily', 'obstruction'): return d.get('a') == a and d.get('terms') == terms
            return row['kind'] == 'template' and d.get('a') == a
        admitted = refused = 0
        for row in self.expand([r for r in rows if r['kind'] in ('ufam', 'cover', 'nofamily', 'obstruction', 'template')]):
            if not same(row): continue
            if row['kind'] == 'nofamily':
                # Walls wait for her lemma at their level, which implies the square ones (see settle_deferred).
                self.deferred.setdefault(row['data']['m'], []).append(row['data']); continue
            obj = rt.propose(row['kind'], row['data'])
            if obj['kind'] == 'template' or rt.check(obj): admitted += 1
            else: refused += 1
            if row['kind'] == 'cover' and obj['status'] == 'checked':
                for entry in row['data']['entries']:
                    if rt.check(rt.propose('ufam', full_family(self.L, entry['family'], row['data'].get('shapes')))):
                        admitted += 1
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

    def obstructed(self, rt, target):
        """A square class at this level whose walls her checked obstruction lemma at a finer or equal level implies."""
        if not self.lemmas: return False
        m, r = target['data']['m'], target['data']['r']
        if gcd(r, m) != 1 or 'coprime:square' not in self.context(target): return False
        return self.lemma_at(m)

    def obstruction(self, rt, M):
        for o in self.results:
            if o['kind'] == 'obstruction' and o['data']['m'] == M:
                if o['status'] == 'checked': return dict(status='checked', reached=o['evidence']['reached'])
        for o in rt.objects.values():
            if o['kind'] == 'refutation' and o['status'] == 'checked' and o['data']['claim']['kind'] == 'obstruction' \
                    and o['data']['claim']['data']['m'] == M:
                w = o['data']['witness']
                return dict(status='refuted', modulus=w['modulus'], residue=w['residue'], params=w['params'])
        return dict(status='not attempted')

    def walls(self, rt, M):
        self.update(rt); return len(self.walled.get(M, ()))

    def settled(self, rt, target):
        if target['kind'] != 'eclass': return None
        if self.obstructed(rt, target): return 'obstruction lemma'
        if target['data']['r'] in self.walled.get(target['data']['m'], ()): return 'wall'
        return None

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
                               certified_walls=self.walls(rt, M), obstruction=self.obstruction(rt, M)))
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
        self.results = []; self.pending = []; self.desc_log = []; self.dcovers = []; self._open = None; self.others = []

    def init(self, rt):
        d = self.p['map']['d']
        self.root = rt.given('cproblem', dict(map=self.p['map'], depth=self.p['depth'], verify_to=self.p['verify_to']))
        for r in range(d): rt.given('cclass', dict(map=self.p['map'], modulus=d, residue=r))

    def update(self, rt):
        """Index new objects incrementally; results not yet checked are revisited until they are."""
        for identity in rt.order[self.seen:]:
            o = rt.objects.get(identity)
            if o is None: continue
            if o['kind'] == 'residual': self.residual.add(o['data']['of'])
            elif o['kind'] == 'cclass' and o['data']['modulus'] <= self.top:
                self.classes.append(o)
                for parent in o['parents']: self.refined.add(parent)
            elif o['kind'] in ('descent', 'dcover', 'cfinite', 'cycle'): self.results.append(o); self.pending.append(o)
        self.seen = len(rt.order)
        waiting = []
        for o in self.pending:
            if o['status'] != 'checked': waiting.append(o); continue
            if o['kind'] == 'descent':
                rs = self.index_.setdefault(o['data']['modulus'], set())
                if o['data']['residue'] not in rs:
                    rs.add(o['data']['residue']); self.desc_log.append((o['data']['modulus'], o['data']['residue']))
            else:
                self.others.append(o)
                if o['kind'] == 'dcover': self.dcovers.append(o)
        self.pending = waiting

    def descents(self, rt):
        self.update(rt); return self.index_

    def covered(self, index, M, r):
        return any(M % fm == 0 and r % fm in rs for fm, rs in index.items())

    def targets(self, rt):
        """Open classes sorted by modulus and residue, kept incrementally: an open class leaves the list when a descent
        found since the last call reaches it or it is refined; new classes are tested against every descent."""
        index = self.descents(rt); key = lambda o: (o['data']['modulus'], o['data']['residue'])
        n_desc, n_cls, n_ref, opened = self._open or (0, 0, 0, [])
        if (n_desc, n_cls, n_ref) != (len(self.desc_log), len(self.classes), len(self.refined)):
            fresh = {}
            for fm, r in self.desc_log[n_desc:]: fresh.setdefault(fm, set()).add(r)
            if fresh:
                opened = [o for o in opened if not any(o['data']['modulus'] % fm == 0 and o['data']['residue'] % fm in rs
                                                       for fm, rs in fresh.items())]
            if n_ref != len(self.refined): opened = [o for o in opened if o['id'] not in self.refined]
            added = [o for o in self.classes[n_cls:] if o['id'] not in self.refined
                     and not self.covered(index, o['data']['modulus'], o['data']['residue'])]
            if added: opened = sorted(opened + added, key=key)
            self._open = (len(self.desc_log), len(self.classes), len(self.refined), opened)
        return opened + [self.root] + self.dcovers[-1:]

    def allowed(self, strategy, target, rt):
        if strategy == 'collatz_split':
            return target['kind'] == 'cclass' and target['data']['modulus'] < self.top and target['id'] in self.residual
        if strategy == 'collatz_affine_descent':
            # The move is deterministic on a class, so a residual it left there (in this run or restored from the saved
            # tree) is its outcome: it is not tried again, whatever part of the tried-move memory a resume kept.
            return target['id'] not in self.residual
        return True

    def capped_key(self, rt, target, retired_in):
        return (len(self.retired),)

    def outcome(self, rt):
        """'refuted' by a checked cycle avoiding 1: its least member m >= 2 never falls below m. 'proved' by a checked
        descent cover reaching every class of its modulus together with a checked range from 2 to the cover's bound:
        every n >= 2 then falls below itself, below the bound by the range and from it by the cover."""
        self.update(rt)
        mine = [o for o in self.others if o['data']['map'] == self.p['map']]
        if any(o['kind'] == 'cycle' for o in mine): return 'refuted'
        reach = max([o['data']['hi'] for o in mine if o['kind'] == 'cfinite' and o['data']['lo'] <= 2], default=0)
        for o in mine:
            if o['kind'] == 'dcover' and o.get('evidence', {}).get('covered') == o['data']['modulus'] \
                    and reach >= o['data']['bound']:
                return 'proved'
        return None

    def done(self, rt): return self.outcome(rt) is not None

    def progress(self, rt):
        self.descents(rt)
        return len(self.desc_log), tuple(sorted(o['kind'] for o in self.others))

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
                                ['restored from the saved refinement tree'], 'refine the class', by='collatz_affine_descent')
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

    def outcome(self, rt): return dict(checked='proved', refuted='refuted').get(self.claim['status'])

    def progress(self, rt): return self.claim['status']

    def summary(self, rt): return dict(claim_status=self.claim['status'], claim_kind=self.claim['kind'])


class ExploreGoal(Goal):
    """Find checked facts of the requested kinds about each given object. The goal 'window' asks, for each window
    object, for the answer kind its family gives (a value, a witness or a proof)."""
    kind = 'explore'
    persist = ('value', 'witness', 'proof')

    def __init__(self, p, L): self.p = p

    def init(self, rt):
        self.roots = [rt.given(o['kind'], o['data']) for o in self.p['objects']]
        self.wanted = []
        for r in self.roots:
            goals = set(self.p['goals'])
            if 'window' in goals: goals = (goals - {'window'}) | {rt.checker.window_kind(r['kind'], r['data']['family'])}
            self.wanted.append(goals)

    def found(self, rt, root):
        kinds = set()
        for o in rt.objects.values():
            if o['status'] == 'checked' and o['question'] == root['question']: kinds.add(o['kind'])
        return kinds

    def targets(self, rt):
        return [r for r, goals in zip(self.roots, self.wanted) if not goals <= self.found(rt, r)]

    def done(self, rt): return not self.targets(rt)

    def outcome(self, rt): return 'found' if self.done(rt) else None

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
        if type(p['a']) is not int or not 1 <= p['a'] <= 64 or p['terms'] != 3: raise host.Refused('numerator 1..64 and three terms')
        if type(p['min']) is not int or not 2 <= p['min'] <= 100_000: raise host.Refused('minimum n')
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
        if 'window' in p['goals']:
            checker = host.local_module('lexicon_check')
            for o in p['objects']:
                if type(o) is not dict or set(o) != {'kind', 'data'} or type(o['data']) is not dict \
                        or checker.window_kind(o['kind'], o['data'].get('family')) is None:
                    raise host.Refused('a window goal takes window objects of known families')
                try: checker.question(o['kind'], o['data'])
                except checker.Invalid as exc: raise host.Refused('window object: ' + str(exc))
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
        self.retired = {}; goal.retired = self.retired; self.retire_tally = {}; self.priors = set(); self.retired_in = {}
        goal.gated = 'egypt_shape_search' in registry  # range moves wait for her shape search where it exists
        # Refusal accounting per (context, strategy, scope): [claims refused, claims admitted] in this run.
        self.refused_by = {}
        self.pooled = set(); self.quiet = set(); self.quiet_key = None
        # Anytime moves waiting at a breath, by move key; and (object, move) pairs whose residual records an attempt.
        self.suspended = {}; self.attempted_by = set(); self.switches = 0; self.resumes = 0; self.slices = 0; self.settled = 0; self.settled_objects = 0
        self.abandoned = 0; self.last_key = None

    def index(self):
        """Incrementally index new workspace objects by kind and by parent."""
        for identity in self.rt.order[self.indexed:]:
            o = self.rt.objects.get(identity)
            if o is None: continue
            self.by_kind.setdefault(o['kind'], []).append(identity)
            if o['kind'] == 'residual' and 'by' in o['data']: self.attempted_by.add((o['data']['of'], o['data']['by']))
            for parent in o['parents']:
                self.children.setdefault(parent, []).append(identity); self.quiet.discard(parent)
        self.indexed = len(self.rt.order)

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

    def companion_kinds(self, table):
        """Kinds a multi-argument move takes as a companion that have had a usable object. Only a kind joining this set
        can give a capped target a new move, so the set only grows; each kind is looked for from its oldest object."""
        kinds = {k for spec in table.values() if len(spec['consumes']) > 1 for k in spec['consumes']}
        for k in kinds - self.pooled:
            if any(self.rt.objects[i]['status'] in ('checked', 'given') for i in self.by_kind.get(k, ())): self.pooled.add(k)
        return tuple(sorted(kinds & self.pooled))

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
        # Whether a strategy is allowed depends on the target and the goal state, not on the focus object: ask once.
        permitted = {}
        def allowed(name):
            if name not in permitted:
                permitted[name] = self.goal.allowed('verify', target, self.rt) if name == 'verify' else self.allowed(name, target, table)
            return permitted[name]
        for f in focus:
            if f['status'] == 'candidate' and f['kind'] in self.checkable and allowed('verify'):
                out.append(('verify', [f]))
            for name, slot in by_kind.get(f['kind'], []):
                if name == 'verify' or not allowed(name): continue
                if name not in LEVEL_STEPS and name not in REPEATABLE \
                        and self.attempts.get((target['id'], name), 0) >= MAX_PER_TARGET: continue
                # A deterministic one-argument move that left a residual on this object has been attempted, whatever
                # the tried-move memory kept: the residual is the record.
                if len(table[name]['consumes']) == 1 and name not in READS_WORKSPACE and (f['id'], name) in self.attempted_by:
                    continue
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
            if key not in self.tried and key not in self.suspended: fresh.append((name, args, key))
        return fresh

    def run_op(self, name, args, budget):
        """Start a move: the verify move, an operator (a list, or an anytime move's generator) or a macro. Events and
        provenance are recorded by execute, per slice and at completion."""
        spec = self.registry.get(name)
        self.rt.budget = budget; self.rt.events = []
        if name == 'verify':
            ok = self.rt.check(args[0]); return [args[0]] if ok else []
        if spec is not None: return self.apply(name, spec, args)
        return self.run_macro(name, args, budget)

    def apply(self, name, spec, args):
        """One operator application: a list of objects, or an anytime move's generator (see finish). An operator that
        reads only its arguments is not recomputed on the same arguments within a run: a macro replaying a step
        already taken reuses its outputs."""
        if name in READS_WORKSPACE: return spec['fn'](self.rt, *args)
        key = (name,) + tuple(a['id'] for a in args)
        if key in self.memo: return [self.rt.objects[i] for i in self.memo[key] if i in self.rt.objects]
        return spec['fn'](self.rt, *args)

    def finish(self, name, args, out):
        """Record a completed application's outputs for reuse on the same arguments."""
        if name not in READS_WORKSPACE and name in self.registry:
            self.memo[(name,) + tuple(a['id'] for a in args)] = [o['id'] for o in out]
        return out

    def run_macro(self, name, args, budget):
        macro = next(m for m in self.macros if m['name'] == name); out = []; current = args
        for i, step in enumerate(macro['steps']):
            # A step obeys the goal's policy for the object it acts on, not only for the macro's first target: a
            # restricted move (a refinement, say) must not reach a derived class the policy would refuse.
            if i and not self.goal.allowed(step, current[0], self.rt): break
            spec = self.registry[step]; before = set(self.rt.objects); self.rt.events = []
            produced = self.finish(step, current, self.L.drive(self.apply(step, spec, current)))  # a macro runs its steps whole
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
        """One scheduling decision: the best fresh move of the first open target with one, or a suspended anytime
        move, whichever scores higher (a suspended move's doctrine score is divided by 1 + its idle slices). So she
        can leave a long search at any breath for a better move and come back to it, and a search that keeps
        producing keeps its place."""
        self.index(); table, by_kind = self.strategies(); progress = repr(self.goal.progress(self.rt))
        key_extra = self.goal.schedule_key(self.rt); pools = None
        # Quiet targets are capped targets found exhausted since the goal-wide part of their signature last changed and
        # with no new derived object since: their signature is unchanged, so they are skipped without recomputing it.
        quiet_key = (len(table), self.goal.capped_global(self.rt), self.companion_kinds(table), len(self.retired))
        if quiet_key != self.quiet_key: self.quiet.clear(); self.quiet_key = quiet_key
        targets = self.goal.targets(self.rt); fresh_choice = None
        for target in targets:
            if target['id'] in self.quiet: continue
            if target['kind'] in self.goal.capped and self.target_moves.get(target['id'], 0) >= MAX_TARGET_MOVES: continue
            # A target with no fresh move stays exhausted until the move table or its derived objects change. A class
            # target is not reopened by progress elsewhere, only by what can change its own moves.
            capped_key = self.goal.capped_key(self.rt, target, self.retired_in) if target['kind'] in self.goal.capped else None
            if capped_key is not None:
                if pools is None: pools = self.companion_kinds(table)
                signature = (len(table), len(self.children.get(target['id'], [])), capped_key, pools)
            else:
                signature = (len(table), len(self.children.get(target['id'], [])), progress, key_extra)
            if self.exhausted.get(target['id']) == signature:
                if capped_key is not None: self.quiet.add(target['id'])
                continue
            fresh = self.candidates(target, table, by_kind)
            if not fresh:
                self.exhausted[target['id']] = signature
                if capped_key is not None: self.quiet.add(target['id'])
                continue
            context = self.goal.context(target)
            fresh.sort(key=lambda c: -doctrine_score(self.samples, context, c[0]))
            if (context, target['id']) not in self.seen_contexts:
                self.seen_contexts.add((context, target['id'])); self.unseen += 1
                if self.unseen % 5 == 0: fresh.reverse()
            name, args, key = fresh[0]
            fresh_choice = (target, context, name, args, key, doctrine_score(self.samples, context, name)); break
        open_ids = {t['id'] for t in targets}
        for rec in list(self.suspended.values()):
            if rec['target']['id'] not in open_ids: self.drop(rec, 'target closed')
        waiting = max(self.suspended.values(), key=lambda r: doctrine_score(self.samples, r['context'], r['name']) / (1 + r['idle']),
                      default=None)
        if waiting is not None:
            score = doctrine_score(self.samples, waiting['context'], waiting['name']) / (1 + waiting['idle'])
            if fresh_choice is None or score >= fresh_choice[5] or len(self.suspended) >= MAX_SUSPENDED:
                if self.last_key != waiting['key']: self.switches += 1
                return self.execute(waiting['target'], waiting['context'], waiting['name'], waiting['args'], waiting['key'],
                                    allocation, resume=waiting)
        if fresh_choice is None: return None
        target, context, name, args, key, _ = fresh_choice
        if key in self.escalated:
            allocation = min(allocation * ESCALATION, max(allocation, (remaining or allocation) // 2))
        return self.execute(target, context, name, args, key, allocation)

    def settle(self, gen, budget, allowance):
        """Ask a waiting move to finish with what it has: 'checkpoint' at its breath, and this much work to state it
        (a base range or a chunk states the part verified so far; a sweep the classes swept). A move that ignores the
        signal runs on until the allowance is spent."""
        budget.limit = budget.work + allowance
        try:
            gen.send('checkpoint')
            while True: gen.send('checkpoint')
        except StopIteration as done: return done.value or []

    def top_refusal(self, name):
        """The reason the checker gave most often to a move's claims this call, or None."""
        rows = [(v[0], k[2]) for k, v in self.rt.refusals.items() if k[0] == name]
        return max(rows)[1] if rows else None

    def note_refusals(self, context, name, scope, refused, admitted, at_bound=0):
        """Refusal accounting per strategy, context and scope. A strategy whose claims the checker refused REFUSE_AFTER
        times here with none admitted, or REFUSE_BOUND times at a bound of the language, is retired with the reason,
        whatever its context (a scheduling policy: what it proposes cannot be admitted as stated, so it stops spending
        until the code or the state changes); a strategy retired for failing keeps its refusal reason too. Returns the
        retirement made here, or None."""
        if not refused and not admitted: return None
        key = (context, name, scope); tally = self.refused_by.setdefault(key, [0, 0, 0])
        tally[0] += refused; tally[1] += admitted; tally[2] += at_bound
        if key in self.retired:
            if tally[0] and 'reason' not in self.retired[key]: self.retired[key].update(refused=tally[0], reason=self.top_refusal(name))
            return None
        if (tally[0] >= REFUSE_AFTER or tally[2] >= REFUSE_BOUND) and not tally[1] and name not in NEVER_RETIRED:
            self.retired[key] = dict(failures=self.retire_tally.get(key, [0, 0])[1], refused=tally[0], at_bound=tally[2],
                                     reason=self.top_refusal(name), at_move=self.moves, prior=(context, name) in self.priors)
            self.retired_in[(context, scope)] = self.retired_in.get((context, scope), 0) + 1
            return self.retired[key]
        return None

    def breathe(self, gen, budget, stop_at):
        """Advance an anytime move until it returns its objects, or until a breath finds the slice used (None)."""
        while True:
            try: next(gen)
            except StopIteration as done: return done.value or []
            if budget.work >= stop_at: return None

    def suspend(self, rec):
        """Keep a move waiting at its breath (step starts no fresh move while MAX_SUSPENDED wait, so the table is
        bounded without abandoning any search)."""
        self.suspended[rec['key']] = rec

    def drop(self, rec, why):
        """End a suspended move without its result: its generator is closed; an abandoned move counts as tried and as
        a failure of its strategy, a move whose target closed leaves no sample."""
        rec['gen'].close(); self.suspended.pop(rec['key'], None)
        if why == 'abandoned':
            self.tried.add(rec['key']); self.abandoned += 1
            self.samples = record_sample(self.samples, dict(context=rec['context'], strategy=rec['name'], task=rec['target']['id'],
                                                            success=False, seconds=round(rec['seconds'], 6), weight=1, source='local'))
        self.log = (self.log + [dict(move=self.moves, target=rec['target']['kind'], strategy=rec['name'], success=False,
                                     work=rec['budget'].work, outputs=[], dropped=why, slices=rec['slices'])])[-MAX_LOG:]

    def close(self):
        """End of the call: each move still waiting is asked to finish with what it has (a checkpoint at its next breath,
        with a quarter of its allocation to state it), and what it states is admitted like any other result; the rest
        of its search starts over if it is chosen in a later call."""
        waiting = len(self.suspended)
        for rec in list(self.suspended.values()):
            self.execute(rec['target'], rec['context'], rec['name'], rec['args'], rec['key'], rec['allocation'], resume=rec, settle=True)
        for rec in list(self.suspended.values()): rec['gen'].close()
        self.suspended.clear()
        return waiting

    def execute(self, target, context, name, args, key, allocation, resume=None, settle=False):
        """Run a move for one slice. A plain move runs to its end or its work bound. An anytime move runs until it
        breathes with its slice used, and then waits with its own budget for a later step (resume); its outcome is
        recorded when it ends. The move being run is named to the runtime, so a residual it leaves records it."""
        host = self.host; parent = self.rt.budget
        if resume is None:
            budget = host.Budget(allocation); gen = None; began_work = 0; slices = 0; seconds_before = 0.0
            progressed = False; objects_before = set(self.rt.objects)
            existing = objects_before if self.goal.limit_kinds else None
            self.goal.attempting(name, target, self.rt)
        else:
            budget = resume['budget']; budget.limit = budget.work + allocation; gen = resume['gen']; began_work = budget.work
            slices = resume['slices']; seconds_before = resume['seconds']; progressed = resume['progressed']
            existing = resume['existing']; objects_before = resume['objects_before']; self.resumes += 1
        before = self.goal.progress(self.rt); began = time.perf_counter_ns(); reason = None; out = None
        self.rt.budget = budget; self.rt.current_move = name; self.rt.events = []
        refusals_before = sum(r[0] for r in self.rt.refusals.values()); refused_earlier = resume['refused'] if resume else 0
        bound_before = bound_refusals(self.rt)[0]; bound_earlier = resume['at_bound'] if resume else 0
        try:
            if gen is None:
                out = self.run_op(name, args, budget)
                if isinstance(out, GeneratorType): gen, out = out, None
            # The slice ends at the first breath past half the move's work bound (or SLICE_WORK), so a breath comes
            # before the bound even when the bound is small.
            if gen is not None and settle:
                out = self.settle(gen, budget, max(allocation // 4, 1)); gen = None; self.settled += 1; self.settled_objects += len(out)
            elif gen is not None: out = self.breathe(gen, budget, began_work + min(max(allocation // 2, 1), SLICE_WORK))
        except (host.Exhausted, RuntimeError, self.checker.Limit) as exc: reason = 'limit: ' + str(exc)[:120]; gen = None
        except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
            reason = 'operator error: ' + type(exc).__name__ + ': ' + str(exc)[:120]; gen = None
        self.rt.budget = parent; self.rt.current_move = None
        for event, identity in self.rt.events: self.events[event] += 1
        parent.use(budget.work - began_work)
        seconds = seconds_before + (time.perf_counter_ns() - began) / 1e9
        self.moves += 1; self.last_key = key; slice_progress = self.goal.progress(self.rt) != before
        progressed = progressed or slice_progress
        if out is None and reason is None and gen is not None and budget.work >= allocation * ESCALATION:
            # The move has had the work an escalated move gets, over all its slices: it ends at its bound, keeping
            # what it can state at its next breath.
            try: out = self.settle(gen, budget, max(allocation // 4, 1)); self.settled += 1; self.settled_objects += len(out)
            except (host.Exhausted, RuntimeError, self.checker.Limit, ValueError, KeyError, TypeError, IndexError, ZeroDivisionError): out = None
            gen = None
            if not out: out = None; reason = 'limit: anytime move work bound'; self.escalated.setdefault(key, allocation)
        if out is None and reason is None and gen is not None:
            # Waiting at a breath with the slice used: the move keeps its budget and its place.
            self.slices += 1
            self.suspend(dict(gen=gen, budget=budget, target=target, context=context, name=name, args=args, key=key, allocation=allocation,
                              slices=slices + 1, idle=0 if slice_progress else (resume['idle'] + 1 if resume else 1),
                              seconds=seconds, progressed=progressed, existing=existing, objects_before=objects_before,
                              refused=refused_earlier + sum(r[0] for r in self.rt.refusals.values()) - refusals_before,
                              at_bound=bound_earlier + bound_refusals(self.rt)[0] - bound_before))
            row = dict(move=self.moves, target=target['kind'], strategy=name, success=slice_progress, work=budget.work - began_work,
                       outputs=[], waiting=True, slices=slices + 1)
            self.log = (self.log + [row])[-MAX_LOG:]
            return row
        out = self.finish(name, args, out or []); self.suspended.pop(key, None)
        for o in out:
            if o['id'] not in objects_before: self.produced_by[o['id']] = (name, [a['id'] for a in args])
        # Progress, or a newly checked certificate of a limit (a wall): a certified limitation is a result.
        success = progressed or (existing is not None and any(
            o['id'] not in existing and o['kind'] in self.goal.limit_kinds and o['status'] == 'checked' for o in out))
        if resume is None:
            self.attempts[(target['id'], name)] = self.attempts.get((target['id'], name), 0) + 1
            self.target_moves[target['id']] = self.target_moves.get(target['id'], 0) + 1
        if reason and reason.startswith('limit') and key not in self.escalated:
            # Out of resources, not out of ideas: the same move gets one retry with a larger allocation.
            self.escalated[key] = allocation
            self.attempts[(target['id'], name)] = self.attempts.get((target['id'], name), 0) - 1
            self.target_moves[target['id']] = self.target_moves.get(target['id'], 0) - 1
        else: self.tried.add(key)
        if name in READS_WORKSPACE or 'cover' in [a['kind'] for a in args]: self.rederivable.add(key)
        self.samples = record_sample(self.samples, dict(context=context, strategy=name, task=target['id'], success=success,
                                                        seconds=round(seconds, 6), weight=1, source='local'))
        tally = self.outcomes.setdefault((context, name), [0, 0, 0.0])
        tally[0 if success else 1] += 1; tally[2] += seconds
        scope = self.goal.retire_scope(target); count = self.retire_tally.get((context, name, scope))
        if count is None:
            # Experience: a strategy her library has only seen fail in this context starts close to retirement.
            count = self.retire_tally[(context, name, scope)] = [0, RETIRE_AFTER - PRIOR_PROBES if (context, name) in self.priors else 0]
        count[0 if success else 1] += 1
        if not count[0] and count[1] >= RETIRE_AFTER and self.goal.retirable(context, name) \
                and (context, name, scope) not in self.retired:
            self.retired[(context, name, scope)] = dict(failures=count[1], at_move=self.moves, prior=(context, name) in self.priors)
            self.retired_in[(context, scope)] = self.retired_in.get((context, scope), 0) + 1
        self.note_refusals(context, name, scope, refused_earlier + sum(r[0] for r in self.rt.refusals.values()) - refusals_before,
                           sum(1 for o in out if o['status'] == 'checked' and o['id'] not in objects_before),
                           bound_earlier + bound_refusals(self.rt)[0] - bound_before)
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
        if slices: row['slices'] = slices + 1
        if reason: row['reason'] = reason
        if invented: row['invented'] = invented['name']
        self.log = (self.log + [row])[-MAX_LOG:]
        return row


# ------------------------------------------------------------- strategy retention and failure mining

def load_ledger(state):
    """Every problem's rounds by task id: what each call obtained and cost. Kept apart from the per-problem records,
    whose evidence the state bound may drop, so her choice among problems keeps its memory."""
    row = next((o for o in state['observations'] if o.get('task_id') == LEDGER_ID), None)
    entries = (row or {}).get('entries')
    if type(entries) is not dict: return {}
    return {k: [r for r in v if type(r) is dict][-MAX_ROUNDS:] for k, v in entries.items()
            if type(k) is str and type(v) is list}


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


def experience_priors(goal, library, state, problem):
    """(context, strategy) pairs her library has seen only fail, at least RETIRE_AFTER times, in the current context
    naming: a scheduling prior that shortens the probes before retirement, not a claim that the strategy cannot work."""
    records = [rec for rec in state['observations'] if rec.get('kind') == 'autonomous_research']
    problems = [] if any(type(rec.get('problem')) is not dict for rec in records) else \
        [rec['problem'] for rec in records if rec['problem'].get('type') == problem['type']]
    tally = {}
    for e in library:
        row = tally.setdefault((goal.library_context(e['context'], problems), e['strategy']), [0, 0])
        row[0] += e['successes']; row[1] += e['failures']
    return {key for key, (wins, misses) in tally.items() if wins == 0 and misses >= RETIRE_AFTER}


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
                                 settled_by=goal.settled(rt, t), exhausted=t['id'] in agent.exhausted,
                                 capped=agent.target_moves.get(t['id'], 0) >= MAX_TARGET_MOVES))
    return dict(open_targets=len(open_targets), by_outcome=groups, examples=examples, profile=goal.failure_profile(rt))


# ------------------------------------------------------------- state

def compact(obj):
    return obj if set(obj) == {'kind', 'data'} else dict(kind=obj['kind'], data=obj['data'])


SPILL_SUFFIX = '.evidence'  # a directory beside the state file: evidence the state bounds cannot hold, one file per record


def spill_dir(state_path): return Path(state_path).with_name(Path(state_path).name + SPILL_SUFFIX)


def spill(host, state_path, record):
    """Move a record's evidence into its own file beside the state, bounded like a state (the least valuable end is
    dropped only if one record's evidence alone exceeds it). The file is named by its content's digest, so a state
    written earlier never names a file that was overwritten; the record keeps the file's name, digest and count, so a
    resume or the verdict can load it back. Returns the number of objects dropped."""
    rows = record.get('objects', [])
    if not rows: return 0
    body = dict(task_id=record['task_id'], objects=list(rows)); dropped = 0
    while len(host.canonical(body).encode()) + 1 > host.STATE_LIMIT and body['objects']:
        body['objects'].pop(); dropped += 1
    folder = spill_dir(state_path); folder.mkdir(parents=True, exist_ok=True)
    text = host.canonical(body); key = hashlib.sha256(text.encode()).hexdigest(); name = key[:32] + '.json'
    temp = folder / (name + '.tmp'); temp.write_text(text + '\n', encoding='utf-8', newline='\n'); temp.replace(folder / name)
    record['spilled'] = dict(file=name, objects=len(body['objects']), digest=key)
    record['objects'] = []
    return dropped


def evidence(host, state_path, record):
    """A record's saved evidence: its inline objects, or its spilled file when the file's digest matches the record.
    A missing or altered file gives no evidence, and the problem's search is simply done again."""
    rows = [o for o in record.get('objects', []) if type(o) is dict and type(o.get('data')) is dict]
    ref = record.get('spilled')
    if rows or type(ref) is not dict or state_path is None: return rows
    name = ref.get('file')
    if type(name) is not str or Path(name).name != name or not name.endswith('.json'): return rows
    path = spill_dir(state_path) / name
    if not path.is_file() or path.stat().st_size > host.STATE_LIMIT + 1: return rows
    raw = path.read_bytes()
    if hashlib.sha256(raw.rstrip(b'\n')).hexdigest() != ref.get('digest'): return rows
    body = host.load_json(path, host.STATE_LIMIT + 1)
    if type(body) is not dict or body.get('task_id') != record['task_id'] or type(body.get('objects')) is not list: return rows
    return [o for o in body['objects'] if type(o) is dict and type(o.get('data')) is dict]


def load_archive(state):
    """Records the record bound evicted whose evidence stays on file, oldest first: [{task_id, file, objects,
    digest}], kept in her ledger, which is never evicted."""
    row = next((o for o in state['observations'] if o.get('task_id') == LEDGER_ID), None)
    shelf = (row or {}).get('archive')
    if type(shelf) is not list: return []
    return [dict(task_id=e['task_id'], file=e['file'], objects=e['objects'], digest=e['digest']) for e in shelf
            if type(e) is dict and type(e.get('task_id')) is str and type(e.get('file')) is str
            and type(e.get('objects')) is int and type(e.get('digest')) is str][-ARCHIVE_ENTRIES:]


def save(host, state, state_path, record, library=None, carried=(), ledger=None):
    """Write the record within the state bound, moving what is worth least first: this record's scheduling memory,
    then the scheduling memory of other records (it serves only a resume of their problem), then the evidence of
    records whose claims this run carried over and checked again (carried: their task ids; that evidence now lives in
    this record, so it is dropped, and a record left with none is removed), then the evidence of the largest other
    records, which is spilled to its own file beside the state (see spill), and last this record's own evidence, also
    spilled. Only evidence beyond one file's bound is dropped; the number this record dropped is recorded and
    returned. When the record bound evicts her oldest records, their evidence stays on file and the ledger keeps
    where (see load_archive); files no longer named by the state are removed once it is written."""
    if state_path is None: return 0
    ids = {record['task_id']} | ({library['task_id']} if library else set()) | ({ledger['task_id']} if ledger else set())
    others = forget_first([o for o in state['observations'] if o['task_id'] not in ids])
    rows = others + ([library] if library else []) + ([ledger] if ledger else []) + [record]
    state['observations'] = rows[-MAX_RECORDS:]
    if ledger is not None:
        shelf = ledger.setdefault('archive', [])
        for o in rows[:-MAX_RECORDS]:
            if o.get('kind') != 'autonomous_research': continue
            if o.get('objects'): spill(host, state_path, o)
            ref = o.get('spilled')
            if type(ref) is dict and type(ref.get('file')) is str and type(ref.get('objects')) is int \
                    and type(ref.get('digest')) is str:
                shelf[:] = [e for e in shelf if e['task_id'] != o['task_id']] + [
                    dict(task_id=o['task_id'], file=ref['file'], objects=ref['objects'], digest=ref['digest'])]
        del shelf[:-ARCHIVE_ENTRIES]
    record['dropped_objects'] = 0
    # The canonical state's exact length, from each record's cached length: only a record that changed is serialized
    # again (a whole-state serialization per step made a save at the bound cost a minute).
    base = len(host.canonical(dict(state, observations=[])).encode()) + 1; weights = {}
    def size():
        rows = state['observations']
        for o in rows:
            if id(o) not in weights: weights[id(o)] = len(host.canonical(o).encode())
        return base + sum(weights[id(o)] for o in rows) + max(0, len(rows) - 1)
    def changed(o): weights.pop(id(o), None)
    if size() > host.STATE_LIMIT:
        record['tried'] = record['tried'][-500:]; record['rederivable'] = record['rederivable'][-500:]
        record['log'] = record['log'][-8:]; record['samples'] = record['samples'][-200:]; changed(record)
    older = [o for o in state['observations'] if o is not record and o.get('kind') == 'autonomous_research']
    for o in older:
        if size() <= host.STATE_LIMIT: break
        if any(o.get(key) for key in ('tried', 'rederivable', 'log', 'samples')):
            for key in ('tried', 'rederivable', 'log', 'samples'):
                if key in o: o[key] = []
            changed(o)
    def trim(row):
        # Drop from the least valuable end until the state fits, then put back, most valuable first, every dropped
        # object that still fits: one large object must not take the smaller ones behind it along.
        current = size(); before = len(row['objects'])
        if current <= host.STATE_LIMIT: return 0
        gone = []
        while current > host.STATE_LIMIT and row['objects']:
            o = row['objects'].pop(); gone.append(o); current -= len(host.canonical(o).encode()) + 1
        for o in reversed(gone):
            extra = len(host.canonical(o).encode()) + 1
            if current + extra <= host.STATE_LIMIT: row['objects'].append(o); current += extra
        changed(row)
        while size() > host.STATE_LIMIT and row['objects']: row['objects'].pop(); changed(row)  # separators
        return before - len(row['objects'])
    for o in older:
        if o['task_id'] not in carried: continue
        if size() <= host.STATE_LIMIT: break
        o['dropped_objects'] = o.get('dropped_objects', 0) + trim(o); changed(o)
        if not o['objects'] and not o.get('spilled'): state['observations'].remove(o)
    for o in sorted(older, key=lambda o: -len(host.canonical(o.get('objects', [])))):
        if size() <= host.STATE_LIMIT: break
        if o in state['observations'] and o.get('objects'):
            o['dropped_objects'] = o.get('dropped_objects', 0) + spill(host, state_path, o); changed(o)
    dropped = 0
    if size() > host.STATE_LIMIT: dropped = spill(host, state_path, record); changed(record)
    dropped += trim(record); record['dropped_objects'] = dropped; changed(record)
    while size() > host.STATE_LIMIT and record['objects']:  # the count itself can add a digit
        record['objects'].pop(); dropped += 1; record['dropped_objects'] = dropped; changed(record)
    target = Path(state_path); target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(host.canonical(state) + '\n', encoding='utf-8', newline='\n'); temp.replace(target)
    folder = spill_dir(state_path)
    if folder.is_dir():
        # Only after the state is written: a file the state no longer names (superseded or dropped) is removed.
        keep = {o['spilled'].get('file') for o in state['observations'] if type(o.get('spilled')) is dict}
        keep |= {e['file'] for e in load_archive(state)}
        for f in folder.iterdir():
            if f.is_file() and f.name not in keep and f.name.endswith(('.json', '.json.tmp')): f.unlink()
    return dropped


def run(task, state_path, limit, host):
    started = time.perf_counter_ns(); budget = host.Budget(limit)
    L = host.local_module('lexicon'); checker = host.local_module('lexicon_check')
    problem, moves, per, reports, identity = bind(task, host, L)
    registry, _ = L.load_ops(); gen = generation(); rel = relevant_generation(problem, registry)
    state = host.read_state(state_path)
    old = next((o for o in state['observations'] if o.get('task_id') == identity and o.get('kind') == 'autonomous_research'), None)
    archive = load_archive(state)
    shelved = next((e for e in archive if e['task_id'] == identity), None) if old is None else None
    rt = L.Runtime(checker, budget)
    goal = GOALS[problem['type']](problem, L); goal.init(rt)
    library, retained = load_library(state)
    samples, macros, tried, unseen, replayed, invalid = retained + list(reports), [], set(), 0, 0, 0
    carried = (0, 0)
    agent = None; baseline = 0; status = 'UNKNOWN'; reason = 'move allowance used'
    try:
        if old is not None:
            # The record's scheduling memory is reused when nothing a round on this problem can depend on has changed
            # (older records name only the whole fingerprint).
            if old.get('relevant', old.get('generation')) == (rel if 'relevant' in old else gen):
                samples = [s for s in old.get('samples', []) if type(s) is dict] + samples
                tried = set(x for x in old.get('tried', []) if type(x) is str)
                # Moves that read the workspace or summarize a cover are re-derivable after a resume.
                tried -= set(old.get('rederivable', []))
                unseen = old.get('unseen', 0) if type(old.get('unseen')) is int else 0
            for m in old.get('macros', []):
                if type(m) is dict and all(s in registry for s in m.get('steps', [])) and m.get('steps'): macros.append(m)
            saved = evidence(host, state_path, old)
            replayed, invalid = goal.restore(rt, saved)
            if invalid:
                # Refused evidence invalidates the scheduling memory built on it; the search is redone.
                tried = set()
        elif shelved is not None:
            # The record bound evicted this problem's record; its evidence stayed on file and is admitted again.
            replayed, invalid = goal.restore(rt, evidence(host, state_path, dict(task_id=identity, spilled=shelved)))
        else:
            # A new problem starts from what related problems already proved about the same equation.
            rows = [o for rec in state['observations'] if rec.get('kind') == 'autonomous_research'
                    and type(rec.get('problem')) is dict and rec['problem'].get('type') == problem['type']
                    for o in evidence(host, state_path, rec)]
            carried = goal.transfer(rt, rows)
        # Checked results replayed or carried over are not this round's; what the round adds is counted from here.
        baseline = sum(1 for o in rt.objects.values() if o['status'] == 'checked')
        rt.carried = frozenset(o['id'] for o in rt.objects.values() if o['status'] == 'checked')
        agent = Agent(host, L, checker, registry, goal, rt, per, samples[-MAX_SAMPLES:], macros, tried, unseen)
        agent.priors = experience_priors(goal, library, state, problem)
        for _ in range(moves):
            if goal.done(rt): break
            remaining = limit - budget.work
            if remaining <= 0: reason = 'work budget exhausted'; break
            row = agent.step(max(1, min(per, remaining // 2)), remaining)
            if row is None: reason = EXHAUSTED; break
    except host.Exhausted as exc:
        reason = str(exc)
    waiting = agent.close() if agent else 0
    settled = None
    if goal.done(rt): status, reason, settled = 'CHECKED_RESEARCH', 'goal settled by checked results', goal.outcome(rt)
    gained = max(0, sum(1 for o in rt.objects.values() if o['status'] == 'checked') - baseline) if agent else 0
    # Refusal accounting: what the checker refused this call (carried claims included), and the reason given most.
    refused = sum(r[0] for r in rt.refusals.values())
    refusal = max(((v[0], k[2]) for k, v in rt.refusals.items()), default=(0, None))[1]
    at_bound, bound = bound_refusals(rt)
    ledger = load_ledger(state)
    rounds = (ledger.get(identity) or [r for r in (old or {}).get('rounds', []) if type(r) is dict])[-(MAX_ROUNDS - 1):]
    rounds.append(dict(generation=gen[:16], relevant=rel[:16], status=status, reason=reason, settled=settled, new_checked=gained,
                       moves=agent.moves if agent else 0, seconds=round((time.perf_counter_ns() - started) / 1e9, 3),
                       refused=refused, refusal=refusal, at_bound=at_bound, bound=bound))
    record = dict(task_id=identity, kind='autonomous_research', generation=gen, relevant=rel, problem=problem, status=status,
                  reason=reason, settled=settled, rounds=rounds,
                  objects=[compact(o) for o in goal.persisted(rt)], macros=agent.macros if agent else macros,
                  samples=[s for s in (agent.samples if agent else samples) if s.get('source') == 'local'],
                  tried=sorted(agent.tried if agent else tried)[-MAX_TRIED:], unseen=agent.unseen if agent else unseen,
                  rederivable=sorted(agent.rederivable)[-MAX_TRIED:] if agent else [],
                  log=agent.log if agent else [])
    entries = merge_library(library, agent.outcomes if agent else {})
    carried_ids = {rec['task_id'] for rec in state['observations']
                   if rec.get('kind') == 'autonomous_research' and rec is not old and goal.carries(rec)}
    ledger[identity] = rounds
    dropped = save(host, state, state_path, record, dict(task_id=LIBRARY_ID, kind='strategy_library', entries=entries),
                   carried_ids, dict(task_id=LEDGER_ID, kind='problem_rounds', entries=ledger,
                                     archive=[e for e in archive if e['task_id'] != identity],
                                     # verdicts recorded by tools/ingest_verdict.py ride along: the bit that came back
                                     verdicts=next((o.get('verdicts', []) for o in state['observations'] if o.get('task_id') == LEDGER_ID), [])))
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
    return dict(status=status, reason=reason, settled=settled, task_id=identity, problem=problem, generation=gen,
                new_checked=gained, rounds=len(rounds), moves_executed=agent.moves if agent else 0, work=budget.work,
                anytime=dict(slices=agent.slices, resumes=agent.resumes, switches=agent.switches, abandoned=agent.abandoned,
                             waiting_at_end=waiting, settled=agent.settled, settled_objects=agent.settled_objects) if agent else {},
                elapsed_ns=time.perf_counter_ns() - started, replayed_objects=replayed, invalidated_objects=invalid,
                dropped_objects=dropped, carried_objects=dict(admitted=carried[0], refused=carried[1]),
                carried_later=goal.carry_report(),
                goal=goal.summary(rt), checked_objects=by_kind,
                results=visible_results(checked),
                refutations=sum(1 for o in checked if o['kind'] == 'refutation'),
                invented_moves=[dict(name=m['name'], origin=m['origin'], status=m['status'], dirs=m['dirs'],
                                     uses=m['uses'], successes=m['successes'], invented_at=m['invented_at'])
                                for m in (agent.macros if agent else macros)],
                templates=[o['data'] for o in rt.objects.values() if o['kind'] == 'template'][:16],
                directions_observed=agent.events if agent else {}, scheduler=ranking, log=agent.log[-24:] if agent else [],
                retired_strategies=[dict(context=c, strategy=s, scope=w, **info) for (c, s, w), info in agent.retired.items()]
                if agent else [],
                failures=mine_failures(agent, goal, rt), related_problems=goal.related(),
                refused=refused, refusals=refusal_rows(rt), diagnosis=diagnosis(agent, goal, rt, gained, refused, reason),
                strategy_library=dict(entries=len(entries), reports_loaded=len(retained)),
                limits='Operators search bounded grammars; the checker admits every reported claim in its stated scope. '
                       'UNKNOWN leaves the problem open. Scores order moves and are not beliefs.')


# ------------------------------------------------------------- the open-problem library

PROBLEMS = 'problems.json'
PROBLEMS_SCHEMA = 'ember.problems.v1'
UNTRIED = 'not attempted yet'
# Ties among equal scores: open problems, then windows (finite exact views onto catalog problems), then closed ones.
STATUS_TIERS = dict(open=0, window=1, closed=2)
CHOICE_RULE = ('an untried problem scores p = 1/2 over m = 0.01; a tried one, the doctrine score over her last four '
               'rounds on it (a round with g new checked results is a success of weight g / (g + 64) and a failure of '
               'the remaining weight, its seconds its cost); a widening she proposed inherits the rounds of the window '
               'it widens until it has its own; ties go to open problems, then windows, then closed problems, then to '
               'the problem type her strategy library has the most successes with, then to the id')


def round_samples(rounds, name):
    """Doctrine samples from her rounds on a problem: the last RECENT_ROUNDS rounds, each a success to the degree
    g / (g + GAIN_HALF) of its g new checked results and a failure for the rest, at the round's seconds."""
    out = []
    for i, r in enumerate(rounds[-RECENT_ROUNDS:]):
        g = r.get('new_checked') if type(r.get('new_checked')) is int and r['new_checked'] >= 0 else 0
        seconds = r['seconds'] if type(r.get('seconds')) in (int, float) and r['seconds'] >= 0 else 0.0
        w = g / (g + GAIN_HALF)
        if w: out.append(dict(context='problem', strategy=name, task=str(i), success=True, weight=w, seconds=seconds))
        if w < 1: out.append(dict(context='problem', strategy=name, task=str(i), success=False, weight=1 - w, seconds=seconds))
    return out


def proposed_windows(problems, ledger, widen, valid):
    """Her own next problems: a settled window restated with larger bounds, up to MAX_WIDEN_LEVELS levels. A
    widening is offered only while the window below it is settled, so her frontier grows one step per settled step;
    the ledger keeps a widening's rounds under its own task, like any problem's."""
    out = []
    if widen is None: return out
    for e in problems:
        if e['status'] != 'window': continue
        parent = e
        for level in range(2, MAX_WIDEN_LEVELS + 1):
            key = digest(dict(query='autonomous_research', problem=parent['task']))
            rounds = ledger.get(key, [])
            if not rounds or rounds[-1].get('status') != 'CHECKED_RESEARCH': break
            objects = []
            for o in parent['task']['objects']:
                if type(o.get('data')) is not dict or type(o['data'].get('params')) is not dict: objects = None; break
                p = widen(o['kind'], o['data'].get('family'), o['data']['params'])
                if p is None: objects = None; break
                objects.append(dict(kind=o['kind'], data=dict(family=o['data']['family'], params=p)))
            if objects is None: break
            task = dict(type='explore', objects=objects, goals=list(parent['task']['goals']))
            if not valid(task): break
            child = dict(id=e['id'] + '@' + str(level), title=(e.get('title') or e['id']) + ', widened ' + str(level - 1) + 'x',
                         status='window', window_of=e.get('window_of'), task=task, proposed_by='ember', level=level,
                         parent=parent['id'], parent_key=key)
            out.append(child); parent = child
    return out


def load_problems(host, L):
    """The packaged problem library: problems stated as tasks in her language, and a catalog of open problems she cannot
    state yet, each naming what her language lacks. Only ids, statuses and tasks steer her choice; the prose is for
    people and may be wrong without changing what she does."""
    data = host.load_json(Path(__file__).resolve().parent / PROBLEMS)
    if type(data) is not dict or data.get('schema') != PROBLEMS_SCHEMA: raise host.Refused('problem library schema')
    problems, catalog, needs = data.get('problems'), data.get('catalog'), data.get('needs')
    resolved = data.get('resolved', [])
    if type(problems) is not list or type(catalog) is not list or type(needs) is not dict or type(resolved) is not list:
        raise host.Refused('problem library shape')
    seen = set()
    for e in problems + catalog + resolved:
        if type(e) is not dict or type(e.get('id')) is not str or not e['id'] or e['id'] in seen:
            raise host.Refused('problem library ids')
        seen.add(e['id'])
    viewed = {e['id'] for e in catalog + resolved}
    for e in problems:
        if e.get('status') not in STATUS_TIERS: raise host.Refused('problem status of ' + e['id'])
        if (e['status'] == 'window') != ('window_of' in e) or ('window_of' in e and e['window_of'] not in viewed):
            raise host.Refused('a window names the catalog problem it views: ' + e['id'])
        try:
            bind(dict(query='autonomous_research', problem=e.get('task')), host, L)
        except host.Refused as exc:
            raise host.Refused('library task ' + e['id'] + ': ' + str(exc))
    for e in catalog:
        if type(e.get('needs')) is not list or not e['needs'] or not all(n in needs for n in e['needs']):
            raise host.Refused('catalog needs of ' + e['id'])
    return problems, catalog, needs


def choose(problems, state, gen, registry=None):
    """Her ranking of the stated problems, read from her own records only. A problem settled at this generation, or
    left with no untried move, waits for new instruments. The rest are ranked by CHOICE_RULE: every problem gets a first
    round, and after that the ones where her rounds keep producing checked results cheaply come first. A scheduling
    policy over her experience, not a belief about which problem is easier or which answer is true."""
    records = {rec['task_id']: rec for rec in state['observations'] if rec.get('kind') == 'autonomous_research'}
    ledger = load_ledger(state)
    affinity = {}
    for e in load_library(state)[0]:
        kind = e['context'].split(':')[0]; affinity[kind] = affinity.get(kind, 0) + e['successes']
    rows = []
    for e in problems:
        key = digest(dict(query='autonomous_research', problem=e['task'])); rec = records.get(key)
        rounds = ledger.get(key) or [r for r in (rec or {}).get('rounds', []) if type(r) is dict]
        inherited = not rounds and e.get('parent_key') in ledger
        history = ledger[e['parent_key']] if inherited else rounds
        samples = round_samples(history, e['id'])
        score = doctrine_score(samples, 'problem', e['id'])
        rel = relevant_generation(e['task'], registry)[:16] if registry else None
        # Rounds at the code a round on this problem can depend on; older rounds are compared by the whole fingerprint.
        here = [r for r in rounds if (r.get('relevant') == rel if 'relevant' in r and rel else r.get('generation') == gen[:16])]
        last = here[-1] if here else {}
        recent = history[-RECENT_ROUNDS:]
        if last.get('status') == 'CHECKED_RESEARCH':
            eligible, why = False, 'settled at this generation (' + str(last.get('settled')) + ')'
        elif last.get('bound') and (last.get('reason') == EXHAUSTED or last.get('refused', 0) > last.get('new_checked', 0)):
            # Her own diagnosis: a bound of the language refused the round's claims and the round then ran out of moves
            # (or admitted fewer than it refused), so the problem waits for the instrument the reason names; a change
            # of the code a round can depend on makes it eligible again.
            eligible, why = False, ('last round had ' + str(last.get('at_bound')) + ' claims refused at a bound (' + str(last['bound']) +
                                    ': ' + str(instrument_for(last['bound'])) + '); waits for that instrument')
        elif type(last.get('refused')) is int and last['refused'] >= REFUSAL_FLOOR and last['refused'] > last.get('new_checked', 0):
            # The checker refused more of the round's claims than it admitted: the problem waits like one out of moves.
            eligible, why = False, ('last round refused ' + str(last['refused']) + ' claims and admitted ' + str(last.get('new_checked', 0)) +
                                    ' (' + str(last.get('refusal')) + '); waits for an instrument')
        elif last.get('reason') == EXHAUSTED:
            eligible, why = False, ('no untried move left at this generation; waits for new instruments' +
                                    (' (' + str(last['refused']) + ' claims refused: ' + str(last.get('refusal')) + ')' if last.get('refused') else ''))
        elif inherited:
            eligible, why = True, ('her own widening of ' + e['parent'] + ', ranked by its rounds: gains ' +
                                   ', '.join(str(r.get('new_checked', 0)) for r in recent) + ' in ' +
                                   str(round(sum(x['seconds'] for x in samples))) + ' s')
        elif not rounds:
            eligible, why = True, UNTRIED if rec is None and key not in ledger else 'attempted before rounds were recorded'
        else:
            eligible, why = True, ('last ' + str(len(recent)) + ' of ' + str(len(rounds)) + ' rounds gained ' +
                                   ', '.join(str(r.get('new_checked', 0)) for r in recent) + ' checked results in ' +
                                   str(round(sum(x['seconds'] for x in samples))) + ' s')
        rows.append(dict(id=e['id'], status=e['status'], type=e['task']['type'], eligible=eligible, why=why,
                         score=round(score, 6), rounds=len(rounds),
                         **({'proposed_by': e['proposed_by'], 'level': e['level'], 'parent': e['parent']} if 'proposed_by' in e else {}),
                         order=(not eligible, -score, STATUS_TIERS[e['status']], -affinity.get(e['task']['type'], 0),
                                e['id'])))
    rows.sort(key=lambda r: r['order'])
    for r in rows: del r['order']
    return rows


def scan(task, state_path, limit, host):
    """Scan the problem library, choose one stated problem by her own records, and run a round on it."""
    L = host.local_module('lexicon')
    if type(task) is not dict or task.get('query') != 'open_problems' or set(task) - {'query', 'moves', 'move_work', 'run'}:
        raise host.Refused('open problem scan fields')
    moves = task.get('moves', 200); per = task.get('move_work', 2_000_000); go = task.get('run', True)
    if type(moves) is not int or not 1 <= moves <= 200_000: raise host.Refused('moves per call 1..200000')
    if type(per) is not int or not 1 <= per <= 100_000_000: raise host.Refused('move work bound')
    if type(go) is not bool: raise host.Refused('run is true or false')
    problems, catalog, needs = load_problems(host, L)
    gen = generation(); state = host.read_state(state_path)
    def valid(problem):
        try: bind(dict(query='autonomous_research', problem=problem), host, L); return True
        except host.Refused: return False
    proposed = proposed_windows(problems, load_ledger(state), L.load_ops()[0].get('_widen'), valid)
    ranking = choose(problems + proposed, state, gen, L.load_ops()[0])
    tally = {}; windowed = {e['window_of'] for e in problems if e['status'] == 'window'}
    for e in catalog:
        for n in e['needs']: tally.setdefault(n, []).append(e['id'])
    report = dict(query='open_problems', rule=CHOICE_RULE, ranking=ranking,
                  library=dict(stated=len(problems), open=sum(1 for e in problems if e['status'] == 'open'),
                               closed=sum(1 for e in problems if e['status'] == 'closed'),
                               windows=sum(1 for e in problems if e['status'] == 'window'), catalog=len(catalog),
                               proposed=len(proposed)),
                  backlog=[dict(need=n, problems=len(ids), windowed=sum(1 for i in ids if i in windowed), examples=ids[:4])
                           for n, ids in sorted(tally.items(), key=lambda kv: (-len(kv[1]), kv[0]))])
    pick = next((r for r in ranking if r['eligible']), None)
    if pick is None:
        return dict(report, status='UNKNOWN', generation=gen,
                    reason='every stated problem is settled or has no untried move at this generation; the backlog '
                           'names what her language lacks for the rest')
    entry = next(e for e in problems + proposed if e['id'] == pick['id'])
    report['choice'] = dict(id=entry['id'], title=entry.get('title'), status=entry['status'], why=pick['why'],
                            score=pick['score'])
    if entry['status'] == 'window': report['choice']['window_of'] = entry['window_of']
    if 'proposed_by' in entry:
        report['choice'].update(proposed_by=entry['proposed_by'], level=entry['level'], parent=entry['parent'],
                                task=entry['task'])
    if not go: return dict(report, status='SCANNED', generation=gen, reason='choice made; the round was not run')
    result = run(dict(query='autonomous_research', problem=entry['task'], moves=moves, move_work=per, name=entry['id']),
                 state_path, limit, host)
    return dict(result, **report)


RESULT_KINDS = ('cover', 'finite', 'pattern', 'density', 'theorem', 'derived', 'dfam', 'gfam', 'dcover', 'cfinite', 'cycle', 'exclusion',
                'value', 'witness', 'proof')


def visible_results(checked):
    """The last twelve result rows, with the range chain summarized: the base range, the widest admitted union and
    the widest theorem extension stand for the chunks and derivations behind them (all of which are counted)."""
    rows = [o for o in checked if o['kind'] in RESULT_KINDS]
    unions = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] == 'range_union']
    extensions = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] == 'theorem_range']
    closures = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] == 'theorem_multiples']
    dfams = [o for o in rows if o['kind'] == 'dfam']  # one row stands for the family list; the count is in checked_objects
    gfams = [o for o in rows if o['kind'] == 'gfam']  # and one for her own general families
    composed = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] == 'theorem_families']
    squares = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] == 'composite_range']
    residual = [o for o in rows if o['kind'] == 'derived' and o['data']['rule'] in ('residual_predicate', 'residual_break')]
    keep = {id(o) for o in (max(unions, key=lambda o: o['data']['statement']['hi'], default=None),
                            max(extensions, key=lambda o: ('closure' in o['data']['statement'], o['data']['statement']['range_hi']), default=None),
                            min(closures, key=lambda o: (o['data']['statement']['open_residues'], -o['data']['statement']['closed_at']), default=None),
                            max(composed, key=lambda o: (len(o['data']['statement']['families']), o['data']['statement']['range_hi']), default=None),
                            max(squares, key=lambda o: o['data']['statement']['reach'], default=None),
                            # one row stands for the residual predicates: the widest, most selective one; the breaks are counted
                            min(residual, key=lambda o: (o['data']['rule'] != 'residual_predicate', -o['data']['statement']['hi'],
                                                         o['data']['statement'].get('sample', {}).get('satisfied', 0)), default=None)) if o is not None}
    base_lo = min((o['data']['lo'] for o in rows if o['kind'] == 'finite'), default=None)
    shown = [o for o in rows if not (o['kind'] == 'finite' and o['data']['lo'] != base_lo)
             and not (o['kind'] == 'derived' and id(o) not in keep) and not (o['kind'] == 'dfam' and o is not dfams[0])
             and not (o['kind'] == 'gfam' and o is not gfams[0])]
    # The range chain's rows are kept whatever the cut; the other rows fill the rest from the newest.
    chain = [o for o in shown if o['kind'] in ('finite', 'theorem', 'derived')]
    others = [o for o in shown if o['kind'] not in ('finite', 'theorem', 'derived')]
    return [result_row(o) for o in others[max(0, len(others) - max(0, 12 - len(chain))):] + chain]


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
    if o['kind'] == 'dfam': row.update(shape=d['shape'], h=d['h'], form=ev.get('form'))
    if o['kind'] == 'gfam': row.update(params=[d['i'], d['j'], d['h1'], d['h2']], form=ev.get('form'), instances=ev.get('instances'))
    if o['kind'] == 'derived':
        row.update(rule=d['rule'], premises=len(d['premises']), **{k: v for k, v in d['statement'].items() if k != 'kind'},
                   statement=d['statement']['kind'])
        if d['rule'] == 'range_extend': row.update(via_cover=ev.get('via_cover'), via_witness=ev.get('via_witness'), via_divisor=ev.get('via_divisor'), via_family=ev.get('via_family'))
    if o['kind'] == 'cycle': row.update(start=d['start'], length=d['length'])
    if o['kind'] in ('value', 'witness', 'proof'):
        # a window's answer: the value itself, or the checker's summary of a witness or proof, cut for the report
        answer = d['value'] if o['kind'] == 'value' else ev.get('summary')
        text = json.dumps(answer, sort_keys=True, separators=(',', ':'))
        row.update(tool=d['q'], family=d['family'], params=d['params'],
                   answer=answer if len(text) <= 600 else text[:600] + '...')
    return row
