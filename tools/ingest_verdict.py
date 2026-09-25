"""Record an independent verdict in her instance state: the one bit that goes back, with the counts behind it.

    python -I -B -X utf8 tools/ingest_verdict.py <state.json> <verdict.json> [--seconds N] [--note TEXT]

The entry goes into the rounds ledger record ('problem-rounds', which her calls carry forward), never into a new
record: a state at its record bound would otherwise evict a research record for bookkeeping. The entry names the
verdict's digest and the state's own digest at the time, so a stale entry is recognizable. She never reads the
counts; the ledger keeps them so that what came back, and when, is inspectable beside her rounds."""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
LEDGER_ID = 'problem-rounds'
MAX_VERDICTS = 64


def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(x): return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path); parser.add_argument('verdict', type=Path)
    parser.add_argument('--seconds', type=int); parser.add_argument('--note', default='')
    args = parser.parse_args(argv[1:])
    import ember
    state = ember.read_state(args.state)
    v = json.loads(args.verdict.read_text(encoding='utf-8'))
    for key in ('bit', 'counts', 'walls', 'self_test', 'version'):
        if key not in v: raise SystemExit('not a verdict report: missing ' + key)
    ledger = next((o for o in state['observations'] if o.get('task_id') == LEDGER_ID), None)
    if ledger is None: raise SystemExit('the state has no rounds ledger to record the verdict in')
    calls = sum(len(rounds) for rounds in ledger.get('entries', {}).values()) if type(ledger.get('entries')) is dict else None
    entry = dict(bit=v['bit'], counts=v['counts'], walls=v['walls'], self_test=bool(v['self_test'].get('ok')),
                 self_test_cases=len(v['self_test'].get('checks', {})), verdict_version=v['version'],
                 verdict_digest=hashlib.sha256(args.verdict.read_bytes()).hexdigest(),
                 state_digest=digest([o for o in state['observations'] if o.get('task_id') != LEDGER_ID]),
                 rounds_recorded=calls, seconds=args.seconds, note=args.note)
    entries = [e for e in ledger.get('verdicts', []) if e.get('verdict_digest') != entry['verdict_digest']]
    ledger['verdicts'] = (entries + [entry])[-MAX_VERDICTS:]
    ember.retain(state, args.state, ledger)
    print(json.dumps(dict(status='VERDICT_RECORDED', bit=entry['bit'], counts=entry['counts'], verdicts_kept=len(ledger['verdicts']),
                          verdict_digest=entry['verdict_digest'][:16], state=str(args.state))))
    return 0


if __name__ == '__main__': sys.exit(main(sys.argv))
