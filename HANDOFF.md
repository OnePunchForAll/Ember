# Handoff: synthesize the Ember campaign, check her progress, then push her further

You are a coding agent working on this repository on its owner's desktop. This
file is your opening brief. Everything it cites is committed on the branch you
are on; nothing here asks you to trust this text over the files.

## 1. What Ember is, in one paragraph

Ember is an offline, non-LLM research agent written in Python with no
dependencies (`ember.py` and the modules beside it). She holds a typed
language of claims (227 operators, 384 catalogued moves), a checker that
admits a claim only by exact recomputation (`lexicon_check.py`,
`window_check.py`, `window_discrete.py`, `window_real.py`), an autonomous
agent that chooses her own moves and problems (`agent.py`), a library of 156
stated problems (25 open, 5 closed, 126 windows) she scans in her own loop
(`problems.json`, campaign mode in `ember.py`), and an independent verdict
tool that recomputes every saved claim in its own code and hands her back one
bit (`tools/verdict.py`, `tools/verdict_windows.py`). The doctrine she is built
under: nobody supplies her answers or hints; instruments are built when she
hits a wall; every attempt is bound to its original task; evidence, not
confidence, determines what is reported; limitations are recorded as
precisely as results. Read `README.md` (about 1,900 lines) for the machine,
`CAMPAIGNS.md` (about 2,550 lines) for the ledger of every campaign, contest,
instrument, run and verdict, `RESEARCH.md` for the status of her reasoning
abilities, `RESEARCH_INQUIRY.md` for the research question that was asked of a
research session, and `RESEARCH_RESULTS.md` for what came back (source-reported,
with its provenance).

## 2. Where the campaign stands (commit 81057f2 and after)

Read the last five entries of `CAMPAIGNS.md` first; the rest of this section
is their summary, and the ledger wins over this summary.

- Her scans: 2,056 calls of her own loop on one instance state across nine
  fingerprints. Verdicts on her state after calls 646, 1,269, 1,484, 1,709
  and 1,946 found every claim VERIFIED except 27 UNRESOLVED window values that
  have no independent rule; none refuted. The last verdict: 113,350 VERIFIED
  (102,976 of them walls), 0 REFUTED, 27 UNRESOLVED, 61 self-test cases, 6,192 s.
- Her theorems reduce Erdős–Straus at 4/n, Sierpiński's 5/n and Schinzel's
  numerators 6 to 19 and 21 to finitely many open residue classes each,
  closed under multiples, with verified ranges near four million, and she
  names her own divisor families (the `gfam` space) and pushes her ranges with
  them (witnesses per number fell 62 to 90 percent on eleven problems). She
  cannot settle any of these by covers: her own checked lemma is Schinzel's
  theorem (residue-class identities never reach the square classes).
- This session installed, from the research brief: certified exception sets
  (`exceptions` claims: every n up to 2a^2 + 1 with no three-term
  representation, each certified by a complete divisor-method search the
  verdict repeats; her window `window-schinzel-beyond-bounds` settles in five
  seconds with eight sets; the sets for every numerator 4 to 64 were checked
  in a scratch run and all verified), and four exact-certificate search kinds
  at the frontier with their families and verdict rules: van der Waerden
  colorings (`waerden_coloring`, `waerden_search`), the no-three-in-line grid
  to n = 64 (`nothree_search`, symmetric backtracking rot4 and rct4),
  coverings with a least modulus (`min_modulus_covering`,
  `covering_lcm_search`), circulant Ramsey graphs checked through vertex 0
  (`circulant_ramsey`, `circulant_search`). Seven open problems state the
  records one past their frontier (`no-three-in-line-61`,
  `van-der-waerden-7-3`, `-8-3`, `-10-3`, `-11-3`, `ramsey-3-16`,
  `covering-modulus-8`). The searches resume across her calls: their state is
  saved in a residual, persisted in her record, restored on the root it
  names, and a round that saves a state is "resuming", not exhausted.
- Calibrations the searches reproduce (all independently verified): W(2, 3),
  W(3, 3), W(4, 3); the grids 14, 16, 17, 18, 20, 24, 25; the least lcms 12
  (least modulus 2) and 120 (least modulus 3), and her values 360, 2,520,
  10,080 for least moduli 4, 5, 6; circulant graphs for R(3, 5), R(3, 6),
  R(3, 9). What they do not reproduce: W(5, 3) > 169 and the records at 7 to
  11 colors; the grids 13, 15, 21 (rct4) and 30 upward; the proved least lcm
  10,080 for least modulus 7 and anything for least modulus 8 below 78,000;
  circulant graphs for R(3, 7), R(3, 8), R(3, 10) and R(3, 16). No record was
  set. The margins are in the entry "Exact certificates at the frontier".
- Her seventh scan (calls 1,710 to 1,946) ran with all of this; its resumed
  frontier rounds repeated their first rounds because the saved state did
  not reach her record; fixed in commit 641d913 (fingerprint 2a420a28) with a
  package check that reads the saved state back from the state file. Her
  eighth scan at that fix was stopped at call 110 of its re-check wave when
  the campaign was handed over; no verdict was run on its final state.
- The package builds and verifies with 681 checks:
  `python -I -B -X utf8 tools/build_public_package.py --verify --output OUT/ember.zip --receipt OUT/receipt.json`
  (about two minutes). `ember.py --move-bench` runs every operator's fixtures;
  `ember.py --pyramid` prints the move catalog.

## 3. Her committed state and how to check her progress

`runs/scan13/lib.state.json` (with its `.evidence/` directory) is her state
after call 2,056; `runs/scan12/lib.verdict.json` the last verdict;
`runs/README.md` the commands. Do these, in order, before anything else:

1. Build and verify the package on your machine (the command above). Compare
   the receipt's `passed` with 681. A failing check names a case; do not
   silence it.
2. Run the verdict on her committed state:
   `python -I -B -X utf8 tools/verdict.py runs/scan13/lib.state.json > lib.verdict.json`
   (about 100 minutes; exit code 3 means the bit "no, keep thinking", which
   is expected: no open problem is settled). Compare its counts with the
   seventh scan's verdict (VERIFIED should be slightly above 113,350, REFUTED
   0, UNRESOLVED 27). Any REFUTED claim is a finding: record it in
   CAMPAIGNS.md with the claim and the verdict's reason before touching code.
3. Ingest the verdict into a working copy of her state
   (`tools/ingest_verdict.py`) and run her loop from it for one wall cap
   (runs/README.md). Watch two things: the frontier problems' rounds should
   resume (each round's saved state advances: candidates tried, restarts,
   steps; the round reason is "a search saved its state to resume"), and the
   theorem rounds should keep adding chunks with claims refused only at the
   language's bounds. Then run the verdict on the result and write the ledger
   entry in the form of the existing ones (what she chose, what each kind of
   round reached, the verdict's numbers, scope, open obligations).

## 4. Synthesis you owe the owner

Write one document, `SYNTHESIS.md`, that a mathematician who has never seen
this repository can read in an hour: what Ember is; what she has proved or
certified, each with its scope and where the verdict says so; what she has
not (no open problem settled, no record set), with the measured margins; the
instruments built in order and the wall each answered, taken from the ledger
headings (six instruments, two contests and their transfers, the third round,
refusal accounting, residual mining, her own shapes, exception sets, the
frontier searches); what the research brief asked and what it changed; and
the open obligations ranked by what a certificate from her would mean. Keep
the distinction the ledger keeps everywhere: proposed, implemented, locally
checked, source-reported. Cite ledger entries and commits, not memory. Do not
restate the brief's claims as facts; they carry [P] [V] [R] [U] markers for a
reason. Numbers go in tables; prose says what they mean.

## 5. Then push her further, in this order

Each item is an instrument she lacks, named by a failure in the ledger. Build
it as her code (no external solver at run time; she is offline and
dependency-free), with the family or claim kind, the checker's exact rule,
the verdict's own rule, an operator with fixtures, a package check with a
true and a false case, a problem or window in `problems.json` if new, a README
paragraph, a ledger entry with preregistered expectations before the run and
the measurement after, then her loop, then the verdict. In that order; the
ledger records the order.

1. **Coverings, least modulus 8 at lcm 10,080.** Since the least lcm for
   least modulus 7 is 10,080 (arXiv 2607.19029, proved), the least for 8 is
   at least 10,080; a covering of Z_10080 with distinct moduli all at least 8
   would settle it exactly. Her greedy-plus-completion search does not even
   reproduce the modulus-7 covering at 10,080 (ledger), and an offline
   CaDiCaL run on the SAT encoding (not hers) returned nothing in two hours.
   Build her an exact cover over all 65 divisors of 10,080 that are at least
   8: branch on the least uncovered residue, classes covering most first, a
   capacity bound (each modulus covers exactly L/m residues), CRT-structured
   ordering (moduli grouped by their 2-part), and resumable state; calibrate
   on least modulus 3 (120), 4 (her 360), 5 (2,520) and 6 (10,080), and
   report honestly if 7 at 10,080 stays out of reach, which bounds what 8
   means.
2. **Van der Waerden ends.** Komkov's records came from SAT extension of
   power-residue colorings. Her backtracking extension has a node limit that
   the Rabung prefixes do not reach. Build a unit-propagation extension over
   progressions (her CDCL solver in `ops_wdisc.py` already logs RUP proofs;
   encode "extend this prefix by e elements" as a CNF and solve it with her
   own solver), calibrate on W(4, 3) > 75 and W(5, 3) > 169 (not reproduced
   now), then let her run at 7 to 11 colors.
3. **The grid.** Her symmetric backtracking reproduces every even n to 24 and
   the odd 17 and 25, and stops in the thirties; Flammenkamp's classes rot2,
   dia1, dia2, ort1, ort2 are not implemented, and the line blocking is not
   incremental. Add the classes and a slope-set representation (the brief's
   `check_nothree` in RESEARCH_RESULTS.md is O(n^2) per point), calibrate on
   47 and 52, and only then spend her calls on 61.
4. **Circulants.** Add the multiplier symmetry (one representative per orbit
   of the connection set under Z_n^*), incremental scoring, and an exact
   independence check with a coloring bound in the verdict's own code (it has
   one; keep it independent). Calibrate on R(3, 8) at 27 and R(3, 10) at 39,
   which she does not reproduce.
5. **Exception sets into the theorem problems.** A stated theorem problem's
   least n should be checked against her certified set for that numerator,
   and a cover asked from the least n above the largest certified exception;
   today the minima come from an earlier search (confirmed by the complete
   search at each minimum, ledger entry on exception sets).
6. **The 27 UNRESOLVED window values.** Give the verdict an independent rule
   for each (the families are listed in the verdict's output under
   UNRESOLVED); until then every scan carries them.

## 6. Rules that do not bend

- Never give her an answer, a witness or a hint; build instruments. A result
  is hers only if her own moves produced it and the verdict verified it.
- Never edit a fingerprinted file (`agent.py`, `lexicon.py`,
  `lexicon_check.py`, `ops_*.py`, `recurrence_check.py`, `window_*.py`) while
  her scan runs; the fingerprint is computed per call.
- Build and verify the package before every code commit; the manifest
  (`PUBLIC_MANIFEST.json`) is written by the build and committed with the
  code. Do not edit public sources while a build runs.
- The ledger is append-only in substance: an error in an earlier entry gets an
  erratum in a later one, not a rewrite. Entry headings carry the commits and
  fingerprint they describe; code commits first, ledger commits after.
- Report proposed, implemented, locally checked and source-reported work as
  different things; a finite benchmark is not general superiority; a saved
  search state is not evidence about a record.
- No model identifiers in anything committed; write the owner as they/them;
  end your commit messages with the attribution lines your own session
  requires, not the ones in this repository's history.
- Keep her offline, dependency-free and non-LLM at run time. Tools you use to
  decide what to build (a SAT solver, a paper) are yours, not hers, and go in
  the ledger as such.

## 7. Files touched most in this campaign, for orientation

`agent.py` (goals, choice, persistence, RESUMABLE_SEARCHES, RESUMING),
`ops_egypt.py` (unit fraction operators, exception scan at the end),
`ops_wdisc.py` (window searches; the four resumable frontier searches near
the end), `lexicon_check.py` (claim checks; `three_term_search`,
`check_exceptions`), `window_discrete.py` and `window_check.py` (window
families), `tools/verdict.py` and `tools/verdict_windows.py` (the independent
rules), `tools/build_public_package.py` (681 checks; the frontier and
exception blocks are inside the `sieve_code` string and consumed by named
`check(...)` calls), `problems.json` (the library), `RESEARCH_RESULTS.md`
(the brief, with its provenance header).
