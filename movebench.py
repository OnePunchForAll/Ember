"""Execute every operator of Ember's typed language and compare declared with observed directions.

For each operator the bench builds its fixtures in a fresh runtime, runs the
operator, and records the events that produced the objects it returned: N for a
new candidate, W for a checked refutation-type object or a residual, S for a
checker admission, E for a claim about another question derived from a checked
claim. An operator passes when its declared directions equal the union observed
over its fixtures, every returned checked object is admitted again by a fresh
checker call, its argument and output kinds match its signature, and nothing
raised. The per-direction counts therefore count only executed, observed moves.
"""
import importlib.util
from pathlib import Path
import time

FIXTURE_WORK = 20_000_000


def _load(name):
    spec = importlib.util.spec_from_file_location('ember_movebench_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class Budget:
    def __init__(self, limit): self.limit = limit; self.work = 0

    def use(self, amount=1):
        self.work += amount
        if self.work > self.limit: raise RuntimeError('move bench fixture work bound')


def run(names=None):
    lexicon = _load('lexicon'); checker = _load('lexicon_check')
    registry, fixtures = lexicon.load_ops()
    rows = []; started = time.perf_counter_ns()
    for name, spec in registry.items():
        if name.startswith('_') or (names and name not in names): continue
        observed, problems, outputs, work = set(), [], 0, 0
        cases = fixtures.get(name, [])
        if not cases: problems.append('no fixture')
        for build in cases:
            rt = lexicon.Runtime(checker, Budget(FIXTURE_WORK))
            try:
                args = build(rt)
                if [a['kind'] for a in args] != list(spec['consumes']):
                    problems.append('fixture kinds ' + ','.join(a['kind'] for a in args)); continue
                rt.events = []
                out = spec['fn'](rt, *args)
            except Exception as exc:  # the bench reports failures instead of stopping
                problems.append(type(exc).__name__ + ': ' + str(exc)[:160]); continue
            work += rt.budget.work; outputs += len(out)
            returned = {o['id'] for o in out}
            observed |= {event for event, identity in rt.events if identity in returned}
            for o in out:
                if o['kind'] not in spec['produces']: problems.append('unexpected output kind ' + o['kind'])
                if o['status'] == 'checked':
                    try: checker.check(o['kind'], o['data'], Budget(FIXTURE_WORK))
                    except checker.Invalid as exc: problems.append('fresh recheck failed: ' + str(exc)[:120])
        declared = set(spec['dirs'])
        if observed != declared:
            problems.append('declared ' + spec['dirs'] + ' but observed ' + ''.join(d for d in 'NWSE' if d in observed))
        rows.append(dict(name=name, module=spec['module'], entry=spec['entry'], dirs=spec['dirs'],
                         observed=''.join(d for d in 'NWSE' if d in observed), fixtures=len(cases), outputs=outputs,
                         work=work, ok=not problems, problems=problems, summary=spec['summary']))
    counts = {d: sum(d in row['dirs'] for row in rows if row['ok']) for d in 'NWSE'}
    return dict(status='MOVE_BENCH', ok=all(row['ok'] for row in rows), operators=len(rows),
                passed=sum(row['ok'] for row in rows), counts=counts, rows=rows,
                elapsed_ns=time.perf_counter_ns() - started,
                limits='Directions are observed on fixtures, not proved for every input; a passing operator can still '
                       'miss on other inputs, and only the checker admits a claim.')
