# Campaigns

This ledger records Ember's research campaigns: the problem she was given, what
she did with it, how every claim was checked, what she failed at and why, the
instruments added so she could do better, and what is still open. It is the
single record the reports draw on; a round's receipts are the code revision,
the agent fingerprint, the task statement and the verdict.

## The loop

1. **Only the problem is supplied.** Claude writes the problem as a task in
   Ember's typed language. The task carries no answer and no hint.
2. **Ember works alone.** `autonomous_research` chooses her own moves, offline
   and without a language model.
3. **Three-valued check.** Her own checker admits every claim she reports.
   Independently, `tools/verdict.py` first tests itself on known-true and
   known-false claims, then recomputes every saved claim with code that shares
   nothing with hers. Each claim is VERIFIED, REFUTED (with the failing witness)
   or UNRESOLVED. One bit goes back to her: "verified", or "no, keep thinking".
4. **Failures are mined.** Her report says which targets stayed open, which
   moves each received and which residuals they left, with a profile of what
   stayed open.
5. **Instruments, not answers.** When she failed because of her own
   limitations, Claude builds the general capability she lacked and adds it to
   her. It changes her options; it never contains the answer for the target.
   The new capability passes the move bench and the package checks, and she
   runs again.
6. **Strategies are retained.** Measured outcomes of her moves carry over to
   later problems as discounted reports. Each problem names its closest related
   problems, and those are offered to her next.
7. **Limits count.** A certified limitation, reported honestly, is a result.

## Standing directives

These are the director's standing instructions for how Ember is developed.

- Upgrade, repair and evolve additively. Keep one stable implementation.
- When she hits a wall, build the instrument she needs, then the next one. Do
  not stop at reporting a failure.
- Run her end to end on problems chosen for her, with her own choice of tools.
  Check her claims and never supply the answer.
- Mine her failures, find which ones came from her own limitations, and build
  instruments that change the options she can choose from.
- Keep strategies across problems, and offer her the closest related problems.
- Aim her at closed, intermediate and open problems. Aim her at refutation as
  well as proof.
- Close the authorship gap. She should state and prove her own lemmas and
  build the proof chain herself, not only its head.
- Give her tools for variance and invariance, equality and inequality,
  symmetry, transformation, abstraction and recursion. The aim is exactness,
  creativity and skill.
- Phrases must be earned by evidence. A discovered limitation, honestly
  reported, is welcome.

## Campaign 1: which residue classes do identities reach? (Erdős–Straus)

**Problem supplied.** 4/n = 1/x + 1/y + 1/z for every n >= 2 (open).
Cover residue classes by checked polynomial families, starting at modulus 840
with refinement primes 11, 3 and 3, and check every n below 100,000.

### Round 1 (commit ae5918a, agent fingerprint 6ef2b7fe)

- **Result.** Modulo 840 she left exactly Mordell's six square classes open.
  At 9,240, 27,720 and 83,160 she left 34, 96 and 284 coprime classes open. Of
  these, 4, 6 and 14 were not squares, and her claim "the open classes are
  exactly the squares" was refuted at each of those levels. Every n below
  100,000 was checked.
- **Verdict.** `tools/verdict.py` on the saved state: self-test passed; cover
  (227 families, 82,876 residues) VERIFIED; finite range VERIFIED. Bit:
  verified.
- **Failure mining.**
  - All 14 open non-square classes at 83,160 are quadratic non-residues modulo
    11 only. They are squares modulo 8, 27, 5 and 7, and they lift the square
    classes 1, 121 and 361 mod 840.
  - Widening her divisor grammar to s < 40 and c < 1,200 found no family for
    the four such classes at 9,240.
  - No fixed-parameter family of the two classical types with modulus dividing
    83,160 reaches any of the 14. Type II was enumerated completely; Type I was
    searched with parameters up to 300.
  - Refining them by 13, 17, 19 or 23 lets classical families reach about 40%
    of the lifts. Refining by 2, 3, 5, 7 or 11 reaches almost none.
  - She had also covered 10 classes at 83,160 that no classical fixed-parameter
    family reaches, with cubic and quartic families of her own. An example is
    x = (n + 11)/4 on 2041 mod 27,720.
  - Her limitations: she had no generator for the classical types, could not
    certify a wall, had only one pattern to conjecture, and refined only by the
    primes she was given.
- **Instruments added (additive).**
  - `egypt_classical_family`: the two classical fixed-parameter types, for any
    numerator. Type II is complete over its moduli; Type I is searched with
    u <= v <= 120 and w <= 120. Each family is stated on the coarsest class its
    parameters need.
  - `egypt_classical_exclusion` and the `nofamily` claim: a checked limitative
    certificate that no classical fixed-parameter family reaches a class.
  - `egypt_signature_pattern`: finds the least set of primes outside which
    every open class is a local square, and claims it.
  - `egypt_choose_lift` and `extra_lifts`: she chooses her own refinement prime
    by measured yield.
  - Failure mining in every report, a cross-problem strategy library, related
    problems, and `tools/verdict.py`.
  - `egypt_reduction_theorem` and the `theorem` claim, for the authorship
    directive. From a checked range and the cover inside it, she states the
    whole theorem: every n >= 2 whose residue is covered has a representation.
    The checker verifies the chain: each family holds from its threshold, the
    range covers everything below the cover bound, and the two meet.

### Round 2 attempts that exposed further limitations

Each of these runs was stopped or finished early. The cause of each was mined
from her own report or log, and the fix was added before the next run. None of
them changed what counts as checked.

- **First launch (stopped).** On a small test her refinement move never became
  eligible. A target whose moves were all disallowed was cached as exhausted,
  and the cache key ignored the classical misses that make the move allowed.
  The exhaustion key now includes goal state beyond progress.
- **Small test.** A cached readiness value was computed before her top-level
  cover existed and never refreshed. The cover test now runs outside the cache.
- **Run 2a (fingerprint 6aae13b4, 3,084 moves, 168 s).** Her coverage matched
  round 1 exactly: 6, 34, 96 and 284 open classes. The finest cover used 28
  families instead of 227. She certified all 284 open classes at 83,160 as
  walls, and her signature pattern was admitted at 9,240, 27,720 and 83,160
  with the single exceptional prime 11. Her refinement move then failed at its
  work bound (5,000,001 units, move 3,074), and a failed move was never
  retried. Fixes: the yield test samples at most 6 classes and 24 lifts per
  prime; a move that fails only for lack of work is retried once with four
  times the allocation.
- **Run 2b (fingerprint e4a06622, stopped after 35 CPU minutes).** She chose
  her prime, but at the new level every step recomputed the open classes
  against every family modulus, about 0.3 s per move. Her moves themselves
  took at most 0.11 s. Fix: incremental indexes for open classes, covers and
  progress. On three examples, repeated runs of the old and new code give the
  same goals and checked results. Move order differs between any two runs,
  because the doctrine score uses measured time.
- **Run 2c (fingerprint d13cd619, stopped after 10.5 CPU minutes).** A sampling
  profile of the live process showed 58% of the time in her extended divisor
  grammar, mostly re-run inside her own invented macros. A macro that begins
  with a step she had already taken on the same class repeated the whole scan.
  Fix: within a run, an operator that reads only its arguments is not
  recomputed on the same arguments; a macro reuses the earlier outputs. Moves
  that read the wider workspace are excluded. Goals and checked results on the
  examples are unchanged.
- **Run 2d (fingerprint 4edee77e, stopped during its second call).** The first
  call used its 20,000 moves in 651 s. She had chosen the prime 19 herself
  (modulus 1,580,040) and covered 2,138 of the 5,112 coprime lifts. Resuming
  exposed a durability defect. Her refinement tree was not saved: the refined
  classes, the misses that justify each refinement, and the level she had
  chosen. The moves that built them were remembered as tried, so a resumed run
  could not rebuild them. Fix: the tree is saved as bookkeeping (not as claims)
  and rebuilt on resume, for the descent goal as well. A call may now run up to
  200,000 moves, so a round fits in one call.

### Round 2 (fingerprint 76fd3cba, one call: 43,918 moves, 1,783 s)

The run resumed the 2d state, whose refinement tree was rebuilt. The
fingerprint names the working tree before the compact encoding below; that
tree was not committed separately.

- **Result.**
  - Coverage at 840, 9,240, 27,720 and 83,160 was the same as in round 1: 6,
    34, 96 and 284 open coprime classes.
  - She certified all 284 open classes at 83,160 as walls: no classical
    fixed-parameter family reaches any of them.
  - Her signature pattern was admitted at 9,240, 27,720 and 83,160, with the
    single exceptional prime 11.
  - She chose the refinement prime 19 herself, by measured yield (modulus
    1,580,040). There she covered every coprime class except 2,619 (2,430
    squares and 189 non-squares), and certified all 2,619 as walls.
  - She stated her reduction theorem at 83,160 and the checker admitted it:
    every n >= 2 outside 284 residue classes mod 83,160 has a representation.
  - The open fraction of residues fell from 284/83,160 (0.34%) to
    2,619/1,580,040 (0.17%).
- **Verdict.** Self-test passed. 3,526 claims VERIFIED, none refuted or
  unresolved. Bit: verified.
- **Failure mining.**
  - Her cover at 1,580,040 could not be stated. Written as expression trees,
    its 658 families took 316,437 bytes, above the 256 KiB bound on one object.
    Her patterns, density and theorem at her own level were therefore never
    attempted, and the level shows as "not attempted".
  - Her state file had room for this round. A larger round would have lost
    evidence silently: the state bound dropped checked objects before
    trimming scheduling memory, and reported nothing.
- **Instruments added (additive).**
  - A compact encoding of families as coefficient lists. The same cover takes
    135,621 bytes. The checker and the independent verdict accept both
    encodings. On three examples, runs give the same goals and checked
    results as before; only move order differs.
  - Saving within the state bound now trims scheduling memory (tried moves,
    log, samples) before any evidence. Evidence is dropped from the least
    valuable end only as a last resort, and the number dropped is recorded in
    the state and the report.

## Campaign 2: Sierpiński's 5/n (the related problem she offered)

**Problem supplied.** 5/n = 1/x + 1/y + 1/z for every n >= 2 (open;
Sierpiński, 1956). The statement is the one her Campaign 1 report offered as
its closest related problem: numerator 5, modulus 840, refinement primes 11, 3
and 3, one refinement prime of her own, and a checked range below 100,000. Her
state held only the strategy library from Campaign 1: 43 entries, read as 115
discounted reports. None of her Campaign 1 claims carried over.

### Round 1 (fingerprint 2e24a579, 2,219 moves, 37 s)

- **Result.**
  - Open coprime classes: 2 at 840 (1 and 421), 10 at 9,240, 10 at 27,720 and
    29 at 83,160.
  - She chose the refinement prime 13 herself (modulus 1,081,080). There she
    left 29 open coprime classes (15 squares and 14 non-squares), and she
    certified every one of them as a wall.
  - Her local-image pattern at 1,081,080 was admitted. Every open class is
    1 mod 5, 7 and 13, lies in {1, 10, 19} mod 27 (so 1 mod 9), in {1, 5}
    mod 8 (so 1 mod 4), and in {1, 3, 4, 5, 6, 9, 10} mod 11. Together, each
    open class is 1 mod 16,380.
  - Her square pattern was refuted at every level. The square 121 mod 840,
    for example, is covered. The numerator-4 obstruction does not carry over
    to 5/n, so her signature move, which presumes it, was not attempted.
  - Her theorem was admitted at 27,720: every n >= 2 outside 11 residue
    classes mod 27,720 has a representation.
- **Comparison.** She did better than the classical types alone. A reference
  computation (not shown to her) used only Type I and Type II families with
  parameters up to 120. It leaves 9 coprime classes open at 840 and 366 at
  83,160; she left 2 and 29. Secondary sources say the case is settled except
  possibly for n = 1 (mod 278,460) (reported from Guy, *Unsolved Problems in
  Number Theory*, D11). No primary source could be opened from this
  environment. Her classes are consistent with that statement: 278,460 is
  16,380 × 17, and she never refined by 17.
- **Verdict.** Self-test passed. 64 claims VERIFIED (her cover at 1,081,080,
  the range, density, pattern and 60 walls). Bit: verified.
- **Failure mining.**
  - Her theorem stopped at 27,720, far coarser than her cover. The theorem
    check asked that a single bound for the whole cover (the largest family
    threshold, 1,076,041 at 1,081,080) lie inside the checked range. Every
    class at her finest level is actually safe: the least threshold among the
    families reaching a class is at most its first member past the range. The
    obstacle was a coarse representation of the chain, not missing evidence.
  - Her saved state kept only the newest range. The one theorem she had
    proved was about an older range, so it was not saved.
  - Her refinement budget was spent (`refinement_budget_left: 0`). She never
    refined by a second prime of her own.
