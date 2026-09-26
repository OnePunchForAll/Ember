# Her committed state

`scan13/lib.state.json` is Ember's instance state after call 2,056 of her
library scans (the eighth scan, stopped at call 110 of that scan), at
fingerprint 2a420a28 (commit 641d913): 128 problem records with their checked
claims, the saved states of her frontier searches, her strategy library and
her verdict memory. `scan13/lib.state.json.evidence/` holds the evidence the
24 MiB state bound could not keep, one file per record, named by digest.
`scan13/s.calls.txt` and `scan13/s.log.txt` are that scan's call and round
logs; `scan13/scan.json` is the task her loop runs (`open_problems`, 10,000
moves a call, 50,000,000 work units a move). `scan12/lib.verdict.json` is the
independent verdict on her state after call 1,946 (113,350 VERIFIED, 0
REFUTED, 27 UNRESOLVED), with that scan's logs; it is ingested into the
state above.

To continue her loop, copy the state and its evidence directory out of the
repository (her loop rewrites the state and spills evidence beside it) and
run, from the repository root:

```text
python -I -B -X utf8 ember.py runs/scan13/scan.json --state WORK/lib.state.json --work 4000000000 --calls 320 --out WORK --seconds 6300
python -I -B -X utf8 tools/verdict.py WORK/lib.state.json > WORK/lib.verdict.json
python -I -B -X utf8 tools/ingest_verdict.py WORK/lib.state.json WORK/lib.verdict.json --seconds SECONDS --note "which scan, which calls, which fingerprint"
```

The first obligation is the verdict on `scan13/lib.state.json` itself, which
was not run (CAMPAIGNS.md, the last entry). A change to any file her
fingerprint covers makes every settled problem eligible again, so a scan at
a new fingerprint begins with a re-check wave of about two hundred calls.
