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
- Keep a library of open problems: stated in her language where it can
  state them, and otherwise catalogued with what her language lacks. She
  scans it and chooses which problem to work on herself.
- Build the tools her language needs to at least see every catalogued
  problem: a finite exact window on each, checked like any other claim. A
  window settles nothing about its problem.

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

### Round 3 (commit 71309f8, fingerprint 2e24a579, one call: 37,852 moves, 1,518 s)

The run resumed the round-2 state. Because the fingerprint had changed, her
scheduling memory was cleared, and each of the 3,642 saved claims was
admitted again by the checker. None was refused.

- **Result.**
  - With the compact encoding she assembled her cover at 1,580,040: 658
    families, 2,619 open coprime classes (2,430 squares and 189
    non-squares).
  - Her signature pattern was admitted there with the exceptional primes
    {11, 19}. The open non-squares are non-residues at 11 only (91), at 19
    only (83), or at both (15).
  - Her local-image pattern was admitted. So was the exact covered fraction,
    58,423/58,520 of all residues.
  - She certified 2,620 walls at 1,580,040. One is on a covered class:
    5569 mod 1,580,040. No classical fixed-parameter family reaches that
    class, but a family of her own grammar does: x = (n + 95)/4, with the
    remainder 95/(n x) split into a cubic y and a quadratic z. The classical
    Type II split is quadratic in both.
- **Verdict.** Self-test passed. 2,909 claims VERIFIED. Bit: verified.
- **Failure mining.**
  - Her theorem at 1,580,040 was refused. The theorem check asked the whole
    cover's bound (1,577,041) to lie inside the checked range (100,000). The
    saved state kept no theorem at all: the one she had was about an older
    range.
  - Her refinement budget was spent.
  - Of her move time in rounds 1 to 3, 391 s went to wall certificates
    (0.135 s each). The checker tried all 871,200 Type I parameter triples
    per class. Most of the rest went to strategies that never once
    succeeded on a square class: the extended ansatz and its macros took
    about 565 s.

### Instruments added after round 3 (commit f996f32, fingerprint f37fad1c)

- **A theorem checked class by class.** For each covered residue, the check
  looks at the families that reach it. The least threshold among them must
  be at most the first member of the residue at or past the checked range.
  Members below the range are covered by the range, and members from that
  first one on by a family. This is exact, and every theorem the old
  single-bound rule admitted is still admitted. Campaign 2 round 2 tested
  it first, at fingerprint 66138c77 (a working tree between the two
  commits).
- **Sieve certificates.** A cover may carry its chain of levels. Coverage,
  patterns, density and the theorem are then decided by lifting, from one
  level to the next, only the classes no family reaches. This is sound for
  any chain: a family that reaches a class reaches every lift of it. The
  theorem check descends into a class only while its threshold test fails,
  which is exact because thresholds can only fall at finer levels. For the
  square patterns, the open units are counted against the number of squares
  of units, a product over prime powers. On her 1,081,080 cover for 5/n, the
  sieve gave the same 29 open residues as enumeration, with 3% of the work.
  Refinement is now bounded by the number of classes to lift (60,000), not
  by the size of the modulus, and wall certificates are admitted up to
  moduli of 10^12. The independent verdict decides sieved claims with its
  own sieve, and it counts squares of units by brute force on each prime
  power.
- **A pruned wall search.** A (u, v) pair whose a u v does not divide
  (u + v) m cannot divide for any w, so it is skipped. On 24 test classes
  the results were identical to the unpruned search. One wall at 1,580,040
  now costs 0.013 s.
- **Learned retirement.** Her classes are now told apart by one observed
  feature: whether a class is a square modulo every prime-power factor of
  its modulus. A strategy that fails 64 times without one success in a
  context is retired there for the rest of the run, and the report lists
  every retirement. The classical generator and the wall certificates are
  never retired, because they decide each class's status. For refinement,
  a retired generator's miss counts as known. A certified wall now counts
  as a result for scheduling. Nothing about squares is assumed. For 5/n,
  square classes are coverable, so there the rule has nothing to retire.
- **A warm start across problem statements.** A problem with a new
  statement, such as a larger refinement budget, gets a new identity.
  Before this change it started from nothing. It now imports the checked
  families, covers, walls and templates that other records hold for the
  same numerator and number of terms, and the checker admits each of them
  again. Ranges, patterns and theorems belong to their own levels and do
  not carry over. On the small example with two primes of her own, 12
  objects carried over. She chose 5 and then 7, reached 840 with exactly
  Mordell's six square classes open, and used 97 moves instead of 108.
- A problem statement may now allow up to four refinement primes of her own.

### Round 4 (commit f996f32, fingerprint f37fad1c, one call: 6,880 moves, 147 s)

The run resumed the round-3 state with the instruments above. Each of the
3,639 saved claims was admitted again, and none was refused.

- **Result.** She stated her theorem at her own level, and the checker
  admitted it: every n >= 2 outside 2,619 residue classes mod 1,580,040 has
  a representation 4/n = 1/x + 1/y + 1/z. Every other count matched
  round 3.
- **Retirement.** Twelve strategies retired in the square context near move
  1,030 after 64 failures each, the extended ansatz and its macros among
  them. The round took 147 s against round 3's 1,518 s, with the pruned
  wall search contributing to the gain.
- **Verdict.** Self-test passed. 2,910 claims VERIFIED, the theorem
  included. Bit: verified.
- **Failure mining.**
  - Twelve strategies also retired in the non-square context near move
    3,450. By then every open non-square class was one of the 189 hardest
    walls. In a deeper run, the rule would withhold those strategies from
    the new non-square classes of the next level, and her own grammar is
    sometimes the only way into those. Fixed: retirement now applies to one
    refinement level.
  - Her walls are correct as stated, but the Type I part of her classical
    generator stopped at u, v, w <= 120. A complete enumeration exists
    because the set is finite at a fixed modulus. It reaches 26 of the 2,619
    open classes at 1,580,040, for example 32881 with (u, v, w) =
    (38, 297, 1), stated on 32881 mod 45,144. Fixed: the generator, the
    checker and the verdict enumerate Type I completely (commit fcf1925,
    fingerprint 4873ff1e), and new walls are complete claims.

### Round 5, first attempt (fingerprint f37fad1c, stopped after 20 CPU minutes)

The problem statement changed so that she may choose up to three refinement
primes herself. It is a new problem, so her checked families and walls
carried over by the warm start.

- **Failure mining.** A live profile showed that 22% of the time went to
  recomputing her square/non-square context on every candidate move, and
  15% to walls. The run also predated the complete classical enumeration.
  It was stopped and restarted at the current fingerprint rather than left
  to finish with instruments already superseded.

### Round 5, second attempt (fingerprint 5d9d835b, stopped after about 22 CPU minutes)

- **Failure mining.** Her first call ended at its work allowance, which my
  runner treated as final; it now resumes on either resource limit. A live
  profile of the resumed call then showed 55% of the time recomputing a
  level's whole open-class list after every new family, which is quadratic
  at deep levels. It was stopped for the instruments below.

### Round 5, third attempt (commit 9498159, fingerprint 0bf025cf, stopped after 52 CPU minutes)

- **Failure mining.** Two live profiles showed about 70% of the time in
  scheduling, not in her moves (9%). The new `obstructed` test scanned
  every result object on every call. `candidates` also asked the goal's
  policy once per pair of focus object and strategy, although the answer
  depends only on the target and the strategy.
- **Instruments.** Her lemmas are kept in a list of their own, at most one
  per level. The policy is asked once per strategy in each call. On the
  examples and a depth-16 Collatz run the results are the same; only the
  scope sentence of the new sieved descent cover differs.

### Round 5 (commit e11f640, fingerprint 832b6e55, one call: 47,904 moves, 4,852 s)

The statement lets her choose up to three refinement primes. It is a new
problem, so round 4's checked families, covers and walls carried over by the
warm start (3,635 admitted again, none refused).

- **Result.** She chose 19, then 13. Her theorem: every n >= 2 outside 15,055
  residue classes mod 20,540,520 has a representation 4/n = 1/x + 1/y + 1/z.
  Of those classes 14,580 are coprime squares and 475 non-squares. Her lemma
  holds at 20,540,520 (68,734 reached classes, none a square). Her third
  prime went unused: every candidate would have lifted more than her bound of
  60,000 classes.
- **A defect in saving.** The report holds these results, but the state file
  does not. All 175 objects of the new record were dropped to keep the state
  under 1 MiB, because the round-4 record took 866 kB in an older and longer
  format. The verdict on that state covers only round 4's claims (2,910
  VERIFIED, bit verified), so the theorem at 20,540,520 has no independent
  verdict. Fixed below.
- **Failure mining.** 873 of the 4,852 s went to her moves; the rest was
  scheduling. Of the move time, 422 s were per-class classical searches
  (17,328 misses) and walls (17,202) on square classes her checked lemma
  already settles, and 50 s the extended ansatz on square classes (0 of
  292). The productive work was the extended ansatz on non-square classes:
  338 families directly and about 440 through its macros. The instruments
  in the section on her round-5 profile answer these lines.

### Round 5 rerun (commit c6a9673, fingerprint 6b6c3a09, one call: 6,582 moves, 370 s)

The same statement, from the same round-4 state, with the upgraded code.

- **Result.** Counting every lift exactly, she chose 13, then 17, then 2
  (raising 2^3 to 2^4). Her theorem at her finest level: every n >= 2
  outside 26,262 residue classes mod 36,756,720 has a representation, an open
  fraction of 7.14 × 10^-4 against 7.33 × 10^-4 in the first run. Of the
  open classes 25,920 are coprime squares and 342 non-squares. Her lemma
  holds at every level she chose, with 162,099 reached classes at
  36,756,720, none a square. The walls her lemma implies were not checked
  again (270 carried ones). The 2,620 walls carried from level 1,580,040,
  which she did not choose this time, were saved as carried and checked again
  by the verdict.
- **Speed.** 370 s against 4,852 s, and 6,582 moves against 47,904. Sixty-five
  strategies retired on her library's prior after 8 tries each.
- **Saving.** Nothing of her record was dropped. The superseded round-4
  record was trimmed to fit instead; its evidence stays in the round-4
  receipts.
- **Verdict.** Self-test passed. 6,048 claims VERIFIED, among them the
  theorem, the four lemmas and 5,424 walls; none REFUTED or UNRESOLVED. Bit:
  verified.
- **What this establishes.** A checked reduction of 4/n to 26,262 residue
  classes mod 36,756,720, with every smaller n checked below 100,000. The
  square classes are the known obstruction to polynomial identities; the
  342 non-squares are limits of her grammars at this depth. The conjecture
  stays open.

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

### Round 2 (fingerprint 66138c77, 501 moves, 22 s)

The run resumed her 5/n state under the class-by-class theorem check alone.

- **Result.** She stated and proved her theorem at her finest level: every
  n >= 2 outside 29 residue classes mod 1,081,080 has a representation
  5/n = 1/x + 1/y + 1/z. Before this, her theorem was at 27,720 with 11
  open classes. The open fraction fell from 11/27,720 (0.040%) to
  29/1,081,080 (0.0027%).
- **Verdict.** Self-test passed. 65 claims VERIFIED, the theorem included.
  Bit: verified.


### Round 3, first attempt (fingerprint f37fad1c, stopped after 11 CPU minutes)

The problem statement changed so that she may choose up to three refinement
primes herself. Her state carried the checked 5/n families and walls from
rounds 1 and 2, through the warm start.

- **Failure mining.** A live sampling profile put 94% of the time in
  `egypt_family_fit`. At her deeper levels it factors numbers near 10^16
  (n times x) by trial division up to 10^8. That work was not charged to the
  move's allocation, so the move's work bound could never stop it.
- **Instrument.** Factorization now removes primes below 1,000 by trial
  division, splits what remains with Pollard's rho (Brent's variant), and
  certifies primes by Miller-Rabin with thirteen prime bases, which is exact
  below 3.3 x 10^24. Divisor lists are generated from the factorization. On
  3,000 random inputs and the edge cases, the results equal trial division.
  Products near 10^25 factor in milliseconds. The same profile of Campaign 1
  round 5 found 22% of its time recomputing her square/non-square context
  for every candidate move; the context is now kept per class.

### Round 3, second attempt (fingerprint eeb4510f, stopped after 3 CPU minutes)

- **Failure mining.** Factoring was no longer the bottleneck. The process
  had grown to 2 GB, though, because the checker kept up to 16 complete
  Type I parameter lists of about 1.5 million triples each, and the
  generator kept up to 64 class indexes. At deeper levels that would have
  exhausted memory. A complete wall also scanned every triple, about 0.2 s
  per class at moduli near 2 x 10^7.
- **Instrument.** The checker, the generator and the verdict each keep only
  the classes the Type I families reach, as an index built once per modulus
  for a few moduli, and never the parameter lists. A wall is now a few
  hundred lookups. Three moduli near 2 x 10^7 take 10 s with a peak of
  110 MB, and the three implementations agree on every sampled class.

### Round 3 (fingerprint 5d9d835b, five calls: 28,329 moves, 853 s)

After the two stopped attempts she ran on the fixed code, with my runner
resuming her whenever a call ended at its work allowance.

- **Result.**
  - She chose the primes 13, 19 and 29 herself.
  - She stated and proved her theorem at 20,540,520: every n >= 2 outside
    131 residue classes mod 20,540,520 has a representation
    5/n = 1/x + 1/y + 1/z. The theorem rests on a sieved cover of 549
    families, which covers 20,540,389 of the residues. The open fraction
    fell from 29/1,081,080 to 131/20,540,520 (0.00064%).
  - At her third level, 595,675,080, 1,624 coprime classes stayed open
    (206 squares and 1,418 non-squares), with 1,744 walls certified. She
    found 1,557 families in all.
- **Verdict.** Self-test passed. 3,150 claims VERIFIED, both theorems
  included. Bit: verified.
- **Failure mining.**
  - Her cover at 595,675,080 could not be stated: it exceeded 256 KiB.
    Most of her families there come from her own divisor grammar, with
    denominators of degree 1, 2 and 4 in k, at about 290 bytes each.
  - Her state file reached 1,037,587 bytes of its 1 MiB bound. Walls took
    one object each, and the saved range carried a second copy of the
    cover.
  - Each complete wall was charged the full Type I enumeration
    (8.7 million units at 595,675,080), although the class index had been
    built once. Every wall therefore failed its first allocation and
    succeeded only on the retry.

### Round 4 (commit 9498159, fingerprint 0bf025cf, one call: 5,353 moves, 92 s)

The run resumed her round-3 state with the instruments built after it (see
the last section). Each of the 3,700 saved claims was admitted again, and none was refused.

- **Result.**
  - With the larger bound on one claim she assembled her cover at
    595,675,080: 1,491 families, covering 595,673,456 residues.
  - She stated and proved her theorem there: every n >= 2 outside 1,624
    residue classes mod 595,675,080 has a representation
    5/n = 1/x + 1/y + 1/z. The open fraction is 2.7 in a million.
  - She stated the obstruction lemma for 5/n, and her checker refuted it
    with her own witness: Type II (1, 1, 1) reaches the square class
    4 mod 5. For 5/n, square classes are reachable.
  - At that level, strategies that had failed 64 times without a success in
    the non-square context were retired, the extended ansatz and its
    macros among them.
- **Verdict.** Self-test passed. 2,142 claims VERIFIED (2,132 walls,
  her theorem at 595,675,080 on a sieved cover, and her round-2 theorem).
  Bit: verified.
- **Failure mining.** Her refutation of the lemma was not saved, because
  refutations were not persisted, so the verdict could not recheck it.
  Fixed: checked refutations of her lemmas are saved, and the verdict
  verifies them with its own code. A reached-class witness must name a
  genuine classical family with a modulus dividing m that reaches a coprime
  square class.

### Round 5, first attempt (commit c6a9673, fingerprint 6b6c3a09, stopped after 57 minutes)

The statement lets her choose up to four refinement primes, one more than
round 4, so it is a new problem: her checked claims carried over by the warm
start and her refinement tree started fresh.

- **Failure mining.** A profile of a parallel copy showed 42% of the time in
  her prime choice and 36% in her checker. Each exact count built the whole
  classical table for M·p, eleven times per level, and a table near 10^10
  takes about 35 s. Her lemma is refuted for 5/n, so every carried wall was
  checked again at once. That included the walls at 595,675,080, a level her
  better choice no longer visits. It was stopped for the two instruments
  described with the prime choice and the carried walls: new primes first,
  and carried walls that wait until she reaches their level.

### Round 5, second attempt (commit 2372847, fingerprint 25ef49d0, stopped after 14 minutes)

- **Failure mining.** Her prime choice fell to 19% of a parallel profile. Her
  checker's Type I index then took 54%. Near 10^10 the index is charged
  millions of work units when it is built, more than one move's allocation.
  The charge came before the index was kept, so the failed move discarded
  the finished index, and its retry built it again (about 40 s each time).
  Fixed: both checker indexes are kept first and then charged, and the least
  recently used one leaves first.

### Round 5, third attempt (commit ce4a67d, fingerprint d1e35696, one call: 19,665 moves, 715 s)

- **Result.** She chose 13, 19, 23 and then 17, ending at 8,031,343,320 with
  821 open classes (114 coprime squares and 707 non-squares), an open
  fraction of 1.02 × 10^-7. Her theorem stands one level up: every n >= 2
  outside 492 residue classes mod 472,431,960 has a representation 5/n =
  1/x + 1/y + 1/z (1.04 × 10^-6 of residues open, against 2.73 × 10^-6 in
  round 4).
- **Two limits.** A cover at 8,031,343,320 needs more families than the
  4,096 entries her checker admits in one cover claim. So her finest level
  carries walls and open classes but no theorem. A cover there would also
  approach the 1 MiB bound on one claim and on her whole state. Her prime
  choice does not yet account for the size of the certificate the next
  level needs; that is an open obligation.
- **A defect in saving.** The theorem did not reach her state file. Her range
  had been checked with an earlier cover than the largest one, so the range
  was saved with its own 400 kB copy of that cover. Trimming from the end
  removed the theorem before it removed that copy, which then freed far more
  than needed. Fixed: the cover her latest range uses comes first, and the
  range and theorem name it by digest.

### Round 5 (commit 02d6910, fingerprint fa4ddeb0, one call: 20,683 moves, 701 s)

The same statement as the third attempt, from the same round-4 state.

- **Result.** The same choices and counts: primes 13, 19, 23 and 17, her
  theorem that every n >= 2 outside 492 residue classes mod 472,431,960 has
  a representation, and 821 open classes at 8,031,343,320 with no cover
  there. At 472,431,960 her checked pattern says every open class is 1 mod
  5, 7 and 13, 1 mod 9, and 1 mod 4.
- **Saving.** Her state now holds her theorem's cover, range and theorem, her
  refutation of the lemma, her templates, walls and refinement tree, and
  166 kB of her families: 1,048,374 of 1,048,576 bytes. The finest cover
  (about 500 kB) and 3,556 families did not fit and were dropped.
- **Verdict.** Self-test passed. 9,482 claims VERIFIED, among them the
  theorem, the refutation (Type II (1, 1, 1) reaches the square class 4 mod
  5), 598 families and 8,873 walls; none REFUTED or UNRESOLVED. Bit:
  verified. The verdict took 560 s, most of it on walls at large moduli.
- **What this establishes.** A checked reduction of 5/n to 492 residue
  classes mod 472,431,960, with every smaller n checked below 100,000.
  Secondary sources say the case is settled except possibly for n ≡ 1
  (mod 278,460); her open classes are consistent with that statement. The
  problem stays open here.

### Round 6, resume attempt (commit bb040bf, fingerprint f20d30b7, one call: 2,474 moves, 152 s)

The round-5 statement, resumed from her round-5 state, with the compact
format and the 8 MiB bound.

- **Result.** She replayed 11,453 saved objects and for the first time
  assembled a cover at 8,031,343,320 (2,883 families). Her theorem moved
  there, but with 3,999 open classes rather than 821. The round-5 save had
  dropped 3,556 families, and she did not find them again.
- **Failure mining.** At 8,031,343,320 her divisor ansatz and its extension
  were retired in the non-square context after 64 misses each (moves 701
  and 702). Of the open classes there, 2,231 carry only a classical miss:
  the ansatz never ran on them. Retirement counts the misses of the current
  run only, so the successes the lossy save removed did not count. Not
  fixed: her saves in these campaigns no longer drop anything (below), and
  the round was rerun from the round-4 state. Open obligation: a resume
  after a lossy save should not retire a generator on a level whose
  earlier successes were lost. This state was not given to the verdict.

### Round 6 (commit bb040bf, fingerprint f20d30b7, one call: 21,029 moves, 738 s)

The round-5 statement, from the round-4 state as in round 5, with the
compact format and the larger bounds.

- **Result.** The same choices as round 5: primes 13, 19, 23 and 17, and
  821 open classes at 8,031,343,320 (114 coprime squares and 707
  non-squares). This time the cover there fits (6,061 families), and her
  theorem moved down one level: every n >= 2 outside 821 residue classes
  mod 8,031,343,320 has a representation 5/n = 1/x + 1/y + 1/z. That is an
  open fraction of 1.02 × 10^-7, against 1.04 × 10^-6 in round 5.
- **Saving.** 1,661,284 of 8,388,608 bytes, and nothing dropped. Her record
  holds the finest cover in the compact form (392,806 bytes), her range,
  theorem and refutation, 126 templates, walls in 8 batches, her refinement
  tree, and the 942 families outside the cover in 2 batches.
- **Verdict.** Self-test passed (22 cases). 11,903 claims VERIFIED across
  the three records in the state, among them the theorem at
  8,031,343,320, its cover, the refutation, the 942 families and 10,945
  walls; none REFUTED or UNRESOLVED. Bit: verified. The verdict took 635 s.
- **What this establishes.** A checked reduction of 5/n to 821 residue
  classes mod 8,031,343,320, with every n in [2, 100,000) checked
  directly. The problem stays open here.

## Campaign 3: the Collatz stopping-time sieve to 2^18 (a closed check)

**Problem supplied.** The map T(n) = n/2 or (3n+1)/2: certify descent class
by class modulo 2^18, and check every n below 10^6. The open counts at each
level are known. She was given only the map, the depth and the range. Her
counts are compared with an independent parity simulation that she never
sees: 1, 1, 2, 3, 4, 8, 13, 19, 38, 64, 128, 226, 367, 734, 1,295, 2,114,
4,228 and 7,495 for k = 1 to 18.

### First attempt (fingerprint 5d9d835b, stopped after 32 CPU minutes)

- **Failure mining.** A live profile showed 51% of the time rebuilding the
  open-class list and 22% rebuilding the descent index on every step. At
  depth 18 both are quadratic. It was stopped for the instruments below.

### Round 1 (commit 9498159, fingerprint 0bf025cf, one call: 32,117 moves, 343 s)

- **Result.** Her open counts agreed with the independent simulation at 16
  of the 18 levels. At k = 16 and k = 17 she left 6 classes open that the
  simulation certifies: 2,120 against 2,114, and 4,234 against 4,228. At
  k = 18 the two agreed again, at 7,495.
- **Verdict.** Self-test passed. 3,503 claims VERIFIED (3,502 descents and
  the range below 10^6). Bit: verified. Every claim she made was right; the
  discrepancy is in what she missed.
- **Failure mining.**
  - The six classes (4799, 7711, 10559, 11431, 15423 and 15743 mod 2^16)
    first contract at step 16, the depth of their own level. Each was
    refined without any failed descent attempt of its own. An invented
    macro (split, then split) checked the refinement policy only against
    its first target, so its second step split a derived class that the
    policy would have refused. Her descent move certifies these classes at
    once when it is applied to them. She certified them only two levels
    later.
  - Her descent cover at 2^18 was not stated. It listed every covered
    residue lifted to the finest modulus, about 255,000 rows, which is past
    both the row limit and the bound on one claim.
- **Instruments.**
  - A macro's steps obey the goal's policy for the object each step acts
    on. The macro stops at the first step the policy refuses.
  - A sieved descent cover. Rows stay at their own moduli, and coverage at
    the cover modulus is counted by lifting, along the powers of 2, only
    the classes no row reaches. The lifted form is still accepted.
  - With both, a depth-18 run in the development copy (fingerprint
    457fb52e) took 155 s. It matched the independent counts at all 18
    levels, and her sieved descent cover at 2^18 covered exactly
    254,649 = 262,144 - 7,495 classes. The committed rerun is recorded
    below once it has run.

### Round 2 (commit 0474b45, fingerprint 832b6e55, one call: 25,985 moves, 172 s)

The run started fresh, with only her strategy library.

- **Result.** Her open counts equal the independent simulation at all 18
  levels, ending with 7,495 open classes mod 2^18. Her sieved descent cover
  at 2^18 covers exactly 254,649 = 262,144 - 7,495 classes. Every n below
  10^6 falls below itself. She needed 1,752 descents, against 3,502 in
  round 1: each class is now certified at its own level instead of being
  refined first.
- **Verdict.** Self-test passed. 1,753 claims VERIFIED (the descents and the
  range). Bit: verified.
- **What this establishes.** Her machinery reproduces a known computation
  exactly, after a defect that the closed check exposed was fixed. It says
  nothing about the classes that survive, and the conjecture stays open.

## Instruments built after Campaign 1 round 5, Campaign 2 round 3 and the first Collatz attempt (commit 9498159, fingerprint 0bf025cf)

- **A lemma instead of 2,430 walls (authorship).** The `obstruction` claim
  says that no classical fixed-parameter family, of either type and with any
  parameters and a class modulus dividing m, reaches a coprime square class
  mod m. The checker enumerates every reached class completely and requires
  each coprime one to be a local non-residue. A refutation names the
  parameters and a reached square class. For 4/n the lemma holds at 840,
  83,160, 1,580,040 and 20,540,520 (68,734 reached classes, none a square).
  For 5/n it is refuted: Type II (1, 1, 1) reaches the square class 4 mod 5.
  When the lemma is checked at her finest level, square classes need no
  individual walls. A family that reached one would also reach its square
  lifts.
- **Incremental bookkeeping.** An open class leaves her list only when a
  family (or a descent) found since the last step reaches it. New classes
  are tested against everything, and the runtime keeps objects in creation
  order so that only new ones are read. The results were compared with the
  full recomputation on every call of three runs: 5,146 calls, no
  difference. At Collatz depth 14 the run was 3.3 times faster, with the
  same open counts at every level.
- **Honest work accounting.** The complete Type I enumeration is charged
  when it is computed, and each later wall its lookups: 8.7 million units
  for the first wall at 595,675,080, about 25 thousand for the next.
- **Shorter certificates.** A classical family may name its parameters
  (type, u, v, e or w). The checker and the verdict each rebuild the
  denominators with their own formulas, so covers and saved states keep only
  the parameters. For older families her producer recovers the parameters
  from the denominators and uses them only when the rebuild is exact
  (224 of 224 in a test, none wrong). Walls are saved one batch per modulus,
  and a saved range names its cover by digest. Every one of these is
  expanded and admitted again on resume. Her 5/n state fell from 1,037,587
  to 726,964 bytes with nothing lost.
- **A larger bound on one claim.** One claim may now take 1 MiB instead of
  256 KiB. The 1 MiB bound on her whole state file is unchanged.
- **A readable verdict.** The verdict lists every claim other than a
  verified wall, and summarizes the walls. Before this, it listed only the
  first 512 claims.

## Instruments built from her round-5 profile (the upgrade for faster, smarter rounds)

Her round 5 on the committed code took 4,852 s. Only 873 s of it went to her
moves; the rest was scheduling and bookkeeping. Of the move time, 422 s went to
per-class classical searches (17,328 misses) and walls (17,202) on square
classes that her checked lemma already settles. Each instrument below answers
one line of that profile, or a defect that her runs exposed.

- **Her lemma first, then whole-level moves.** Her finest level is prepared
  before its classes: the obstruction lemma, then `egypt_classical_sweep`,
  which runs the classical generator over every class still without a
  classical outcome in one move, then `egypt_wall_sweep`, one batch wall claim
  for the classes it missed. Square classes a checked lemma settles are left
  out of both. The checker admits the batch only after checking every listed
  class as its own wall. Both new operators pass the move bench with declared
  directions NWS equal to those observed.
- **Level steps tried once per workspace state.** The first fresh run of the
  new flow stopped early, without choosing her refinement prime. Each target
  could try each operator once, so the sweeps could not run again as classes
  reached the finest level. The level then waited for preparation that could
  never finish, and her other finest-level moves were blocked. Now each level
  step runs once per workspace state, and a step already tried in the current
  state no longer holds the level back.
- **Rescans only on change.** A class with no fresh move is looked at again
  only when something that can give it one changes: its own derived objects, a
  new level, a lemma, the kinds available as companions, or (above the finest
  level) a retirement in its own context and level. Such a class is skipped
  with one set lookup until then. Companion kinds, lemma lookups, level counts,
  the checked-family index and the open-class lists are all kept
  incrementally. Checking for a companion walked every class object backwards
  on every step; that walk alone had taken about a quarter of a profile.
- **Experience priors.** A strategy her library has seen fail at least 64 times
  with no success in a context gets 8 tries per level there before it retires
  (it had 64). That is a scheduling prior, not evidence, and one success at a
  level keeps it there. Contexts saved before the numerator was part of their
  name are read as the current numerator only when every saved record has it:
  4/n and 5/n classes answer the same strategies differently, and contexts now
  carry the numerator.
- **Her prime chosen on exact counts.** She chose each refinement prime from 6
  open classes and at most 24 of their lifts. On round 4's cover that sample
  scores 13 and 17 alike (5 of 24). Exact counts separate them: lifting by 13
  leaves 16,868 classes open mod 20,540,520, lifting by 17 leaves 23,759 mod
  26,860,680, and primes already dividing the modulus reach almost nothing.
  She now counts every coprime lift a classical family reaches and takes the
  prime that leaves the smallest fraction of residues open. A family class q
  that divides M·p but not M reaches exactly the lifts of x whose residue mod
  p^(v_p(M)+1) is its own, for its entries congruent to x mod q/p, so the
  count needs one lookup per table modulus for each open class, not one per
  lift. On 2,619 classes and eight primes it equals a direct search over every
  lift, at 3 to 19 times less work. A package check compares the two. Each
  count still needs the whole classical table for M·p, about 35 s near
  10^10, so she counts new primes first and primes of M only when no new prime
  reaches a lift: a prime already in M gets no lift divisible by it, and its
  measured yields were far lower (74 of 5,238 lifts for 2 at 1,580,040). The
  table cache is bounded by entries as well as count.
- **Carried walls wait for her lemma.** Walls carried from a related problem
  are admitted once she reaches their level and her lemma there is settled;
  walls at levels she does not reach are saved as they were carried, and the
  verdict checks them. A wall on a class
  that is a coprime square modulo every prime-power factor of m follows from a
  checked lemma at a multiple of m: a family reaching it would have a modulus
  dividing m and would reach a coprime square class at the lemma's level.
  Those walls are not checked again, and a saved state keeps the lemma instead
  of them. Re-admitting round 4's 2,904 walls had taken 78% of the first
  profile of the new flow.
- **A Type II index in the checker.** For a fixed numerator and modulus, the
  classes the Type II families reach are enumerated once into an index,
  charged when it is built. Each wall then costs one lookup per divisor. On
  9,720 residues across five numerators and eight moduli, the indexed and
  unindexed enumerations agree exactly. Divisor lists are kept for reuse.
- **The state bound keeps her results.** Her round-5 record lost all 175 of
  its objects to the 1 MiB bound, while the round-4 record, in an older and
  longer format, kept 866 kB. The bound now trims this record's scheduling
  memory first, then other records' scheduling memory, then the evidence of
  records whose claims this run carried over and checked again, and this
  record's own evidence last. Within a record her theorem's chain comes first,
  then her lemmas, templates and walls, then the refinement tree, and last the
  families outside her cover, which her generators find again. The tree stores
  residues grouped by modulus as gaps between sorted values.
- **Reports.** Each failure example names the checked claim that settles it
  (`settled_by`: the obstruction lemma or a wall). The verdict reports a claim
  whose cover or range reference matches nothing saved as UNRESOLVED, with
  that reason.

Matched comparisons: each started from a fresh state, on the same machine, while
the other code tree ran at the same time.

| Task | Committed code | Upgraded code |
|---|---|---|
| Round-4 statement (4/n, one prime of her own) | 11,481 moves, 299 s; prime 19; theorem at 1,580,040 with 2,593 classes open (1.64 × 10^-3 of residues) | 3,437 moves, 74 s; prime 13; theorem at 1,081,080 with 1,674 open (1.55 × 10^-3) |
| Campaign 2 round-4 statement (5/n, three primes of her own) | 19,634 moves, 585 s; primes 13, 19, 29; theorem at 595,675,080 with 1,215 open (2.04 × 10^-6). A second run: 19,168 moves, 565 s, and no theorem, because its last range check failed | 10,586 moves, 251 s; primes 13, 19, 23; theorem at 472,431,960 with 492 open (1.04 × 10^-6) |
| Campaign 3 round-2 statement (Collatz to 2^18, closed) | 25,980 moves, 156 s | 25,939 moves, 113 s; in both, all 18 levels equal the independent counts |

Before her prime choice changed, the upgraded code reached the same open
classes as the committed code at every level of both 4/n and 5/n. It took
107 s against 299 s on 4/n, and 392 s against 565 s on 5/n. The new choice
then gave her smaller open fractions as well. Her move order still depends on
measured seconds, so two runs of the same code can differ.

## The compact proof format and a larger state (commits c5fdbb2 and the one after it)

Her Campaign 2 round 5 stopped at two size limits. A cover at her finest
level, 8,031,343,320, needed more than the 4,096 families her checker admits
in one claim. And her largest cover, about 500 kB, did not fit into the 1 MiB
state beside the cover her theorem uses. First the certificates were made
shorter, then the bounds were raised.

- **An identity written once.** A family on the class n = m·k + r is an
  identity in n placed on a class: x(k) = X(m·k + r), with X(n) =
  x((n − r)/m). Her round-5 covers held 1,910 and 2,185 families written out
  in full (about 250 bytes each), but only 111 and 130 distinct identities.
  A cover may now carry a shape table: each identity once, as its
  denominators in n. An entry names its class, threshold and identity (about
  45 bytes), and classical families keep their parameters. Her covers are
  assembled in this form. The checker rebuilds each entry with its own
  arithmetic and checks it as if it were written out; the verdict does the
  same with its own code, and three self-test cases cover it. Written-out
  covers are still admitted.
- **Family batches.** The families outside her covers are saved as batch
  claims of at most 512 families, each with one shape table. On resume, and
  in the verdict, a batch becomes one claim per family.
- **Measured on her saved round-5 claims.** The round trip is exact.
  Covers: 500,666 → 123,449 bytes (5/n) and 498,278 → 139,089 bytes
  (4/n). The 598 saved 5/n families: 151,820 → 35,897 bytes. The checker
  admits both forms with the same coverage (472,431,468 and 36,730,458
  residues) and refuses a forged identity. Two package checks guard the
  format.
- **Larger bounds.** A task file stays bounded to 1 MiB. An instance state
  may now take 8 MiB instead of 1 MiB, one claim 4 MiB instead of 1 MiB,
  and one cover 65,536 families instead of 4,096 (about 2.9 MB in the
  compact form). The state-bound package check now sizes its test records
  to the host's bound.
- **First use.** Campaign 2 round 6 ran with both. Her cover at
  8,031,343,320 (6,061 families) takes 392,806 bytes, her state 1.66 MB,
  and her theorem now stands at that level.

## The open-problem library: her first 24 scans (commit 2709dd2, fingerprint 0979c09b)

The library gave her 16 stated problems. Twenty-four `open_problems` calls on one
instance state (24 calls, 3,355 s in all, the longest 645 s), each choosing by her
own records:

- **Calls 1-16: a first round on every problem.** Untried problems tie at the
  top score, so she took them in order: the eleven open ones first, then the
  five closed ones. The open rounds ended by move allowance or with no untried
  move and settled nothing. The four calibrations settled in their first round:
  3/n proved (17 moves), the halving map proved (4 moves), and the 3n - 1 and
  5n + 1 maps refuted by checked cycles (101 and 236 moves). The Collatz sieve
  to 2^18 ran out of its move allowance, as its size predicts.
- **Calls 17-24: her ranking at work.** With every problem tried, the doctrine
  score over her own rounds ordered them. Every round so far had gained new
  checked results, so the score favoured the problems whose rounds were
  shortest: she returned to the Collatz sieve and the Collatz conjecture, then
  to Schinzel's 9/n (one round of 105 s, score 0.0127, just above Collatz at
  0.0124 after three rounds of 258 s in all) and 6/n. No open problem was
  settled.
- **Verdict.** The independent verdict on her final state after the 24 scans
  (7,986,276 bytes) returned the bit "verified": 75,755 saved claims VERIFIED
  (65,751 of them walls), none refuted, none unresolved, in 893 s.
- **What the scans exposed.** After 16 problems her state held 7,986,276 bytes
  of its 8 MiB bound, and the 128-record bound would have evicted the records of
  the oldest problems, and with them her memory of having tried them. Her rounds
  now live in one ledger record per state that neither bound evicts (see the
  next section). A resume after a save that dropped evidence also retired some
  of her generators; that remains open.

## The 30 window tools (fingerprint 4ca544c6)

The catalog named 30 kinds of mathematics her language lacked (`needs`). The
request was to build the tools she needs "in order to at least see them".

- **What was built.** Twenty-nine window question kinds, one per kind of view,
  and wider statement bounds for unit-fraction problems (numerators up to 64,
  least n up to 100,000). A window names a family and its parameters; its answer
  is a value the checker recomputes, a witness it verifies or a proof it replays.
  120 families: 81 value, 37 witness, 2 proof (`window_check.py`,
  `window_real.py` with rigorous interval arithmetic, `window_discrete.py`).
  47 operators propose answers (`ops_wnum.py`, `ops_wdisc.py`): a compute move
  per tool, search moves with her own code, a widen move and a refute move. The
  move bench passes all 212 operators; the pyramid audit binds 369 moves in 34
  modules.
- **The windows.** 125 catalog problems have one. Each ran as an explore task
  with the goal `window` on a fresh state: all 125 settled, in 182 s altogether
  (median 0.5 s, 119 under 5 s, the longest 23 s for the pebbling numbers of
  P3 x P3), with 199 moves in all and at most 5 per window.
- **Agreement with published values** (every such comparison made): twin prime
  pairs below 10^3..10^6: 35, 205, 1224, 8169 (OEIS A007508); Sophie Germain
  primes: 37, 190, 1171, 7746 (A092816); prime quadruplets: 5, 12, 38, 166
  (A050258); n with n^2 + 1 prime below 10^3..10^5: 112, 841, 6656 (A083844);
  the 22 maximal prime gaps below 10^7, ending with 154 after 4,652,353
  (A002386, A005250); Mersenne exponents below 3000; F_0 to F_4 the only
  Fermat primes up to F_13; Wieferich primes 1093 and 3511; no Wall-Sun-Sun
  prime below 10^6; the least Goldbach prime record 601 at 1,077,422 (A025018)
  and every even number below 2·10^6 a sum of two primes; ten sign changes of
  Hardy's Z below height 50 (ten zeros) with a certified upper bound of 12 on
  N(50); Pascal
  multiplicities to 10^9 exactly A003015 (3003 eight times; 120, 210, 1540,
  7140, 11628, 24310 six times); 26 amicable numbers below 10^5 (13 pairs);
  Brocard's n = 4, 5, 7; only 1 + 2 = 3 for Erdős-Moser; M(1000) = 248,083
  distinct products; the Sidon maximum 8 in {1..40} (Golomb rulers, A003022);
  R(4, 4) > 17, R(3, 5) > 13, R(3, 3) <= 6 (a checked refutation), S(4) >= 44
  and S(3) = 13; Strassen's rank 7 for 2 x 2 matrix multiplication and rank 11
  for 2 x 2 by 2 x 3; B(2, 3) of order 27; the Galois groups S5, S3 and D4 of
  x^5 - x - 1, x^3 + x + 1 and x^4 - 5; Lehmer's polynomial (and its
  reflection) the only reciprocal degree-10 measure below 1.18; the icosahedral
  energy 49.16525... for 12 points on the sphere; kissing 40 in dimension 5; the
  Mahler volume products 8 (square) and 9 (hexagon). Without a reference value
  here: ten sign changes of L(s, chi_4) below height 30.8 (the first near 6.02,
  as LMFDB lists), 3,603 of the 9,592 primes below 10^5 with 2 as a primitive
  root (0.3756; Artin's constant, a limit under GRH, is 0.37396), and the
  Gauss-circle and divisor error maxima.
- **Defects the tools exposed, all fixed.** (1) The N+1 primality test for
  k·2^n - 1 required gcd(U_((N+1)/2), N) = 1, which fails for every prime when
  Q = 1; it would have refused every true Riesel prime above the Miller-Rabin
  range. It now requires V_((N+1)/2) = -2 and a unit U_((N+1)/q) for odd q | k,
  with the proof in its docstring; checked against a probable-prime test on
  1,500 cases and a package check (3·2^94 - 1 prime; 3·2^83 - 1 and
  3·2^95 - 1 composite). (2) The RUP checker watched a clause with a repeated
  literal twice on that literal and missed its unit steps (Schur's clauses for
  x + x = 2x); clauses are now sets. (3) The Jones polynomial had the writhe
  sign reversed; it now matches 3_1, 4_1 and 5_1. (4) A flip in her matrix
  multiplication search changed the tensor when two terms shared a factor up
  to sign; her search now flips over GF(2) and lifts signs by backtracking. The
  package build found two more: 26 compute operators registered in a loop were
  invisible to the pyramid's source audit (each is now declared), and the
  standalone checker replay lacked the window checker files. Her graceful-tree
  witnesses now name vertices in the preorder of each tree's canonical code, so
  any checker can read them.
- **Searches improved to reach known answers.** Illumination (directions from
  the polygon's own cones: 3 for a pentagon), Heilbronn sets (hill climbing),
  Ramsey graphs (circulant graphs when Paley graphs fail), Andrews-Curtis moves
  (best-first: AK(2) trivialized in 22 moves; AK(3) not), matrix multiplication
  (flip graphs over GF(2)), primes k·2^n - 1 beyond the Miller-Rabin range (her
  own run of the N+1 test).
- **The independent verdict.** `tools/verdict_windows.py` recomputes 59 value
  families and rechecks 37 witness and 2 proof families with its own code (98 of
  115 family names; the first version, in the commit that added the tools, had
  86). Its own coset enumeration gives S3 6, Q8 8, A5 60 and B(2, 3) 27; its own
  real quadratic class numbers match the known h = 2 for 10, 15, 30 and 34, 3 for
  79, 223 and 229, 4 for 82 and 8 for 226; its inertia count gives the path P3's
  Laplacian spectrum 0, 1, 3; its own graph enumeration finds the 34 graphs on 5
  vertices. A clean rerun of all 125 windows at the committed fingerprint
  4ca544c6 settled every one (190 s in all); over its 158 window claims the
  verdict found 137 VERIFIED, 21 UNRESOLVED and none refuted, so its one bit is
  "verified" for 110 windows and "no, keep thinking" for the 15 that hold a
  family without a rule. A forged window value is refuted (package check).
- **Statement bounds.** An exhaustive search here (Python, independent of her
  code) to n = 100,000 gave the exceptions below; each stated problem starts at
  the largest plus one. For a = 16 the search to 40,000 had missed 78,721 and
  83,449. For a = 20 the largest exception below 10^5 is 90,001, so no threshold
  is stated.

| a | exceptions below 100,000 | the n with no representation a/n = 1/x + 1/y + 1/z |
|---|---|---|
| 12 | 23 | 2, 3, 5, 7, 13, 25, 29, 31, 37, 73, 97, 193, 433, 577, 1129, 1657, 1873, 2521, 2593, 3433, 10369, 12049, 12241 |
| 15 | 31 | 2, 3, 4, 8, 16, 17, 19, 23, 31, 34, 47, 53, 61, 79, 113, 122, 137, 151, 197, 226, 233, 271, 541, 1103, 1171, 1367, 4201, 6301, 12601, 16831, 20521 |
| 16 | 47 | 2, 3, 4, 5, 6, 7, 9, 11, 13, 17, 22, 23, 33, 34, 37, 73, 97, 113, 121, 131, 167, 193, 241, 257, 262, 421, 482, 577, 593, 641, 769, 1201, 1489, 2113, 2521, 2689, 3169, 3361, 4801, 4993, 5281, 8161, 8641, 33601, 36529, 78721, 83449 |
| 17 | 20 | 2, 3, 4, 5, 6, 7, 9, 13, 19, 23, 41, 43, 53, 71, 73, 157, 281, 421, 1123, 2081 |
| 18 | 53 | 2, 3, 4, 5, 7, 10, 11, 13, 19, 22, 23, 29, 31, 37, 38, 41, 47, 59, 61, 73, 109, 113, 131, 137, 149, 181, 193, 223, 239, 281, 379, 389, 397, 433, 457, 541, 599, 613, 661, 761, 811, 821, 911, 1009, 1297, 1381, 2269, 2819, 9461, 16561, 17389, 28081, 35281 |
| 19 | 23 | 2, 3, 4, 5, 6, 7, 8, 10, 11, 13, 23, 26, 29, 41, 43, 46, 82, 97, 137, 181, 193, 229, 353 |
| 21 | 34 | 2, 3, 4, 5, 6, 8, 11, 13, 17, 22, 23, 26, 29, 43, 46, 89, 97, 101, 113, 127, 211, 269, 353, 401, 463, 593, 601, 757, 761, 947, 967, 1031, 7151, 14051 |

- **Library changes.** Windows are a third status, ranked after open and before
  closed problems among equal scores. The catalog lost six problems the
  literature resolved in 2024-2026 (listed under `resolved` with sources) and
  six entries were restated to their open form (unit distances, Jacobian n = 2,
  Borsuk 4 to 62, hot spots for convex planar domains, Kakeya from dimension 4,
  unforced Navier-Stokes); sources were updated for abc, Casas-Alvero,
  sum-product, Hadamard, lonely runner, omega, inverse Galois, Erdős-Straus and
  Sierpiński (web search, 2026-09-25).
- **Open obligations.** Ten catalog problems have no window: Schinzel for a = 20
  and a >= 22 (a threshold needs a search far beyond 10^5), Heesch numbers, the
  Kaplansky zero-divisor conjecture, Whitehead asphericity, the smooth
  four-dimensional Poincaré conjecture, the Hodge and standard conjectures,
  resolution in characteristic p, Yang-Mills and BPP = P. Seventeen families
  have no independent verdict rule. Several windows are marked as viewing
  related objects rather than a finite case (Leopoldt, four exponentials,
  restriction, Bochner-Riesz, hot spots, invariant subspaces, Navier-Stokes).
  A window's size is fixed in the library; `window_widen` can enlarge one, but
  she has not yet been run on widened windows.

## Her scans over the whole library, and the walls they exposed (fingerprints 4ca544c6 and c6eb5099)

With the windows her library holds 148 stated problems: 18 open, 5 closed and
125 windows. She scanned it with `open_problems` calls on one instance state,
started fresh, each call choosing by her own records (10,000 moves and a work
bound of 4·10^9 per call).

- **Calls 1-18: the open problems.** Untried problems tie at the top score and
  open ones rank first: Collatz, Erdős-Straus at 4/n, Schinzel's a/n for a = 6
  to 19 and 21, and Sierpiński's 5/n. Every round ended at its move allowance or
  with no untried move, and none settled its problem (2,020 s, 146,635 moves,
  39,153 new checked results).
- **Calls 19-69: windows**, in library order from abc to the happy ending
  problem. All 51 settled by checked results, in 1 to 4 moves (73 in all) and
  3.1 to 23.1 s a call (258 s in all). A window alone takes about half a second
  (see the previous section); the rest is reading and writing her nearly full
  8 MiB state.
- **The first wall: the byte bound.** Twice the save dropped one object of the
  round's own evidence (calls 10 and 16, Schinzel's 17/n and 8/n). Both times it
  was the checked range that the round's theorem rests on, the largest object;
  the smaller objects behind it were put back. Both theorems are therefore saved
  without their support. After call 69 the state held 8,377,480 of its
  8,388,608 bytes, and a window record takes 1-2 KB, so the next windows would
  have lost their own answers. The run was stopped there.
- **The verdict on her state after call 69:** 32,784 claims VERIFIED (22,071 of
  them walls), none refuted, 11 UNRESOLVED: the two theorems cut from their
  ranges ("no saved range has the referenced digest") and nine window values in
  families that have no independent rule yet. All other 51 window claims
  verified (38 values, 12 witnesses, 1 proof). 226 s.
- **Instrument 1: evidence spill.** When the state would exceed its bound, the
  save now moves evidence into files beside the state: first the evidence of
  her largest other records, then the round's own if needed. The files live in
  `<state>.evidence/`, one per record, each named by its content's digest and
  bounded like a state; the record keeps the file's name, SHA-256 and object
  count. A resume reads a file back only when the digest and the task id match,
  and the independent verdict does the same with its own code. A missing or
  altered file gives no evidence: the verdict answers UNRESOLVED for that
  record, and a resume searches again. Only evidence beyond one file's bound
  (the state's) is dropped, from the least valuable end, so a spilled theorem
  always keeps its range. A new problem now takes carried-over rows only from
  records of its own problem type, so it does not open every spilled file;
  only the unit-fraction goal carries rows over, and it reads only its own
  kinds, so no transfer changes.
- **A trial of the spill** on a copy of her state after call 13, before the
  second instrument existed, over four rounds she chose (Schinzel's 6/n to
  9/n): the third round overflowed the bound and spilled one record (13/n,
  1,470,306 bytes of evidence); nothing was dropped. Resuming 13/n from its
  file replayed 302 checked objects with none refused, the same 302 as from the
  record's inline evidence. The verdict on the trial state read the file back:
  26,301 claims VERIFIED, none refuted, 1 UNRESOLVED (the 17/n theorem already
  cut from its range), 113 s.
- **The second wall: the record bound.** An instance state holds at most 128
  records, and the host refuses a larger one. With 148 problems, one record
  each, the save would have evicted her oldest records first, and those were
  her open-problem rounds: the costliest evidence she has, lost to make room
  for 2 KB window records. Her rounds ledger kept her memory of trying them,
  but not what they proved.
- **Instrument 2: the archive.** An evicted record's evidence now moves to its
  file, and her rounds ledger, which is never evicted, keeps the file's name,
  digest and object count (up to 1,024 records). A later round on that problem
  reads the evidence back and takes it out of the archive; the verdict reads
  archived evidence as well. After the state is written, files it no longer
  names are removed. The 128-record bound is unchanged.
- **A third cost: saving at the bound.** A continuation at the right work
  bound (below) slowed from 5 s to 70 s a call over 42 calls. With the state
  pinned just under its bound, every save re-serialized the whole 8 MiB state
  once per record while it looked for scheduling memory to clear. Record
  lengths are now cached and only a changed record is serialized again. On her
  real state the old and new saves wrote byte-identical states and files, in
  42.6 s and 1.05 s (90.3 s and 1.13 s for a save that spills).
- **The state cap, raised on request from 8 MiB to 24 MiB** (25,165,824
  bytes). The spill and the archive now act only past that bound. Three
  checkpoint messages that still named the old 1 MiB cap now name the state
  bound.
- **Package checks.** `state_bound_spills_other_evidence_beside_the_state`: an
  old record's evidence spills intact, the new record keeps all of its own, the
  agent and the verdict both read the file back, and both refuse it after a
  one-character change. `record_bound_keeps_evicted_evidence_on_file`: saving a
  record into a full state evicts the three oldest, whose evidence the ledger
  names and both the agent and the verdict read back; a later round on one of
  them takes its evidence back, and its file is removed. The package passes
  665 checks (commit 648ecac).
- **Calls 70-202 at fingerprint c6eb5099** (commit 648ecac, 24 MiB cap),
  continuing the state after call 69: 595 s in all, and no object dropped.
  - Calls 70-148: the 79 problems still untried. All 74 remaining windows
    settled (126 moves, at most 5 a window; 0.3 to 16.9 s a call, 254 s in
    all), so every one of the 125 windows settled in its first round. The
    closed calibrations came out as in her first scans: 3/n and the halving
    map proved, the 3n - 1 and 5n + 1 maps refuted by checked cycles, and the
    Collatz sieve to 2^18 cut at its move allowance.
  - From call 127 on, the record bound evicted her oldest records: the 18 open
    problems' first, then 4 windows'. Their evidence moved to files named in
    her ledger, and the state fell from 8.4 MB to 1.5 MB.
  - Calls 149-199: her ranking at work. The new fingerprint made her 51
    windows from calls 19-69 eligible again, and their short successful
    rounds ranked first. Each replayed its saved answers through her checker
    (60 objects, none refused) and settled without a move (80 s in all); four
    of them (abc, the amicable numbers, Andrews-Curtis and Andrica) came back
    from the archive. A re-check gains no new result, so it counts against a
    problem's score, and the windows then fell behind her open problems.
  - Calls 200-202: Collatz, the Collatz sieve and Schinzel's 19/n. Collatz and
    19/n came back from the archive (796 and 1,068 checked objects replayed,
    none refused), and the rounds added 131 and 2,070 new checked results; the
    19/n round derived its range and theorem again. The sieve added 391. None
    settled.
  - Her final state: 128 records in 3,375,790 bytes, plus 22 evicted records'
    evidence in 22 files (7,865,199 bytes, 1,101 objects). Her ledger holds
    the rounds of all 148 problems.
- **The verdict on her final state**, archive included (claims from all 148
  problems): 33,890 VERIFIED (22,119 of them walls), none refuted, 23
  UNRESOLVED, in 337 s. The 23 are the two theorems cut from their ranges
  before the spill existed, and 21 window values in the 15 families without an
  independent rule. Her 158 window claims give the same split as the
  fresh-state runs of the previous section: 137 VERIFIED, 21 UNRESOLVED.
- **Three discarded continuations.** Two were started with a work bound of
  4·10^5 instead of 4·10^9, a runner error; under it 12 of the first 28
  windows ended UNKNOWN (work budget exhausted, or no untried move once the
  compute move had failed), and none made a false claim. The third, at the
  right bound, settled all 42 windows it reached and exposed the slow save.
  All three ran code that was later changed, so the calls above were run
  again from the state after call 69 at the committed code.
- **Also corrected.** The `packing` family's statement claimed density bounds
  its checker does not compute. It now says what is computed: the least
  squared norm over the coefficient box and the absolute determinant. The Rota
  window's note now says the n = 3 case is proved (Chan, 1995) and names the
  asymptotic versions (Pokrovskiy, 2020; Montgomery and Sauermann, 2025).
- **Open obligations.** The 17/n and 8/n theorems stay unsupported until later
  rounds on those problems derive their ranges again. When the save trims a
  record whose claims were carried over, it can still keep a claim whose
  support it dropped; that is harmless there, since the claims live on in the
  new record. The evidence files are bounded only through the 128 live and
  1,024 archived records, at most 24 MiB each. A resume after a save that
  dropped evidence can still retire some of her generators (noted after her
  first 24 scans).

## Her second scan of the library (fingerprint c6eb5099), and forgotten attempts (fingerprint 8c5abe42)

On request she scanned the library again, continuing a copy of her state after
call 202 (24 MiB cap; as before, 10,000 moves and a work bound of 4·10^9 per
call). At this fingerprint every window and every closed calibration but the
Collatz sieve was settled, so her ranking offered 18 problems: the open ones
except Schinzel's 19/n, which had no untried move left, and the Collatz sieve.

- **Calls 203-231: 29 calls in 5,113 s**, each her own choice. They made
  187,010 moves and gained 30,674 new checked results. They replayed 75,306
  saved objects with none refused, and dropped nothing. No problem was settled.
  Fourteen rounds ended with no untried move. Collatz (10 rounds), Schinzel's
  9/n, 18/n and 6/n, and Sierpiński's 5/n ended at their move allowance. The run
  was stopped during call 232, once every offered problem had had a round; that
  call wrote nothing.
- **What her rounds proved.** Each result holds within its stated scope. A
  theorem covers every n from its least n whose residue its cover reaches, and
  every n below 100,000 is checked directly.
  - First theorems for Erdős–Straus at 4/n (modulus 36,756,720, 26,262 classes
    left open, from n = 2) and for Schinzel's 7/n (modulus 36,756,720, 2,690
    open, from n = 3), 18/n (modulus 83,160, 3,271 coprime classes open, from
    n = 35,282) and 21/n (modulus 83,160, 2,046 coprime open, from n = 14,052).
  - Fewer open coprime classes under earlier theorems, all at modulus 83,160:
    12/n from 1,753 to 1,325, 15/n from 1,985 to 1,340, 8/n from 1,042 to 925.
  - The 17/n and 8/n theorems that the old save had cut from their ranges were
    proved again with their ranges.
  - Deeper refinement without a theorem yet: 9/n to modulus 5,405,400, 6/n to
    617,795,640, and Sierpiński's 5/n to 8,031,343,320.
  - The Collatz sieve to 2^18 is complete: 7,495 classes stay open. Every level
    from 2 to 2^18 matches an independent count of the classes that do not
    descend within k steps of the map T (1, 1, 2, 3, 4, 8, 13, 19, 38, 64, 128,
    226, 367, 734, 1,295, 2,114, 4,228, 7,495).
- **The verdict on her state after call 231**, archive included: 92,316 claims
  VERIFIED (81,290 of them walls), none refuted, 21 UNRESOLVED, in 1,758 s. The
  21 are the window values in families without an independent rule. All 15 of
  her saved theorems carry their ranges and verify.
- **Her ranking at work.** Ten of the 29 calls went to Collatz. A round that adds
  any checked result counts as a success, whatever its size. So rounds that
  added 405, 151, 21 and 2 descents kept Collatz ahead of Erdős–Straus, and only
  two rounds with none let Erdős–Straus through. This follows the doctrine's
  definition of a success. Whether the size of a gain should count is a
  scheduling question, and it is left open.
- **The wall: forgotten attempts.** At 2^20 her Collatz rounds stalled with
  28,777 classes open, where an independent count gives 27,328. All 1,449
  missing classes have exactly 12 odd steps in 20. They descend only at the
  last step the depth allows (3^12 < 2^20 < 3^13), and each already at its least
  member. Her descent move settles such a class when it reaches it, but it did
  not reach them. Her tried-move memory keeps at most 6,000 entries per problem,
  while depth 20 leaves 27,328 classes on which the move fails. Each resumed
  round re-tried failures it had forgotten, and spent its 10,000 moves before
  it reached the untried classes.
- **Instrument: the residual as the record of an attempt (fingerprint
  8c5abe42).** The descent move is deterministic on a class, and the residual it
  leaves is saved in her refinement tree. The Collatz goal now refuses the move
  on a class that already has that residual, whatever her tried-move memory
  kept. A fresh run is unchanged. Resuming her Collatz problem from a copy of
  her state after call 231, at the new code, replayed her 2,955 descents and
  tried each of the 16,385 untried classes once (16,389 moves, 339 s). It found
  the 1,449 descents, so 2^20 now has exactly 27,328 open classes, the
  independent count, and the round ended with no untried move. The package
  check `collatz_descent_not_retried_on_a_residual_class` fails on the
  previous code and passes on this one. The package passes 666 checks.
- **Open obligations.** Her tried-move memory is still capped at 6,000 entries
  per problem for every other goal; so far only Collatz has been seen to stall
  on it. Her library ranking counts any gain as a success. Her Collatz problem
  at depth 20 cannot settle: 27,328 classes need more than 20 steps.

## What she depended on me for: six instruments (commits e3f9b8f and fa8a22b, fingerprint 47e163c3)

The request was to supply what she still depended on me for, and to go
further: to let her switch between moves at any time and to make her language
of mathematics more advanced. Each instrument below names the dependence it
removes, what was built, and how it was checked.

- **Switching between moves at any time (anytime moves).** Before, a move ran
  to its end or its work bound; a long search held the whole round, and the
  only way to stop it was to lose it. Now an operator may be a generator that
  breathes at natural points: the divisor searches after each parameter pair,
  the classical sweep after each class, the range verification and the new
  range chunk after every 64 numbers. A move runs in slices (half its work
  bound, at most 4,000,000 units). At the first breath past the slice it waits
  with its own budget and its place in the search. Each step she chooses again,
  by the same doctrine score, between the best fresh move of the first open
  target and the waiting moves, a waiting move's score divided by one plus the
  slices it has run without progress. A search that keeps producing keeps its
  place; one that stalls yields and resumes when nothing better is left. At
  most eight moves wait; with the table full she resumes one rather than
  starting another, so every search she starts runs to its end within the call.
  A first version abandoned the idlest waiting move when the table filled: on
  Erdős–Straus it abandoned 37 searches in one round. That version was
  discarded before it was committed. The move bench runs a breathing operator
  whole and counts its breaths: 5,895 over the fixtures of the five.
- **A more advanced language: derivations.** A `derived` claim names a rule,
  the identities of its premises and the statement that follows. The checker
  takes, for this kind only, a way to look up an admitted claim by identity
  (the runtime supplies its own workspace) and verifies the rule, never the
  premises again. Two rules: `range_union` (two admitted ranges of one
  question that touch or overlap give the range from the lower start to the
  further end) and `theorem_range` (a theorem whose range ends at h and an
  admitted range from at or before h to past it give the theorem with the
  further end). With them her verified range grows past the checker's bound on
  one claim: `egypt_range_chunk` verifies the next chunk past the admitted
  frontier (as long as the base range, up to ten times `verify_to`),
  `egypt_range_union` joins it to the spine from the least n, and
  `egypt_theorem_range` extends her theorem over it. Derivations are persisted
  with the chunks, admitted again after their premises on a resume, refused
  when a premise is gone, and verified by the independent verdict with its own
  reading of the rules (four new self-test cases: a union of touching ranges
  verifies, one with a gap is refuted, a theorem extension verifies, one
  claiming more is refuted). On the small example (range to 3,000) a
  three-call chain took the verified range to 29,982 through nine chunks,
  nine unions and one extension in the first call and replayed all 54 objects
  in the third with none refused.
- **A residual is the record of an attempt.** Her tried-move memory keeps
  6,000 keys per problem and a resume can forget attempts; her Collatz stall
  at 2^20 came from exactly this. The runtime now stamps every residual with
  the move that left it, restored refinement trees stamp theirs with the
  generator whose miss they record, and a deterministic one-argument move is
  never proposed again on an object that carries its residual. The Collatz
  rule of the previous section is now a case of this.
- **Her choice among problems weighs the size of a gain.** A round counts as
  a success of weight g / (g + 64) for its g new checked results and a failure
  of the remaining weight, and only her last four rounds on a problem count.
  On her state after call 231 this puts Schinzel's 11/n first among the open
  problems (recent gains 1,543 and 101 in 124 s) and Collatz last (21, 2, 0, 0
  in 894 s), where the previous rule had given Collatz ten of 29 rounds.
- **She proposes her own problems.** A settled window is offered again with
  larger bounds, by the widening rule its family already had, up to three
  times over and one level at a time; it is ranked by the rounds of the window
  it widens until it has its own, and keeps its own rounds in the ledger. On
  her state after call 231 she proposes 36 widenings. Her frontier on a
  catalog problem now grows as far as her rounds keep succeeding.
- **A derivation with a computed part: `range_extend`.** Her first scan at
  the new code reached the open problems and stalled on Schinzel's 11/n: the
  call ran twenty minutes before I stopped it. Two causes. A waiting move's
  work bound grew by a whole allocation at every resume, so a search that used
  to end at its bound ran until the call's whole budget was gone; an anytime
  move's total work is now capped at four times its allocation over all its
  slices, what an escalated plain move had. And the 11/n theorem leaves 34,611
  of 83,160 residues open (mostly classes not coprime to the modulus), so a
  plain chunk claim had to find a witness for 42 percent of its numbers one by
  one, where the base range had reduced every composite to a verified divisor;
  a standalone claim cannot name numbers outside itself. The new rule can: a
  `range_extend` derivation states [lo, hi) from an admitted range [lo, h),
  and the checker verifies only the new numbers, each by a cover class, by a
  witness the proof carries, or by a proper divisor d >= lo that the checker
  finds itself by trial division, d lying in the premise or earlier in the new
  part. The proof carries witnesses only for the primes in open classes. The
  same 11/n round now takes 35 s and carries its theorem's range from 100,000
  to 999,658 through nine extensions and nine theorem extensions, all admitted;
  the verdict verifies extensions number by number with its own code (two new
  self-test cases). The widening rule was aligned with each family's bounds in
  the same change, after 22 of her 54 widening calls had ended on a bound the
  checker refuses on sight or a count one move could not finish.
- **Measured on her real problem.** A single round on Erdős–Straus at 4/n from
  a copy of her state after call 231 (10,000 moves, 4·10^9 work): 948 moves in
  104 s, 5,596 objects replayed, 118 slices, 118 resumes, 80 switches between
  moves, none abandoned; nine chunks, nine unions and nine extensions, so her
  theorem for 4/n now carries a verified range to 999,982 instead of 100,000.
- **Package checks.** `anytime_moves_wait_resume_and_switch_under_a_small_bound`,
  `derivations_admit_unions_and_extensions_and_refuse_forgeries`,
  `residual_records_the_attempt_of_a_deterministic_move`,
  `problem_choice_weighs_gains_and_inherits_widened_windows`; the checker-only
  replay of her saved evidence now admits derivations after their premises.
  670 checks pass; the bench passes 215 of 215 operators (114 N, 53 W, 207 S,
  79 E); the pyramid binds 372 moves.
- **Her scans at the new code, from her state after call 231.** At fingerprint
  417031cb (calls 232-423): every settled problem re-checked in a call each,
  then her own widenings, 54 calls (32 settled, 22 without a result; levels 2,
  3 and 4), then Schinzel's 11/n, her first open problem by the new rule, at
  which the run was stopped as described above. At fingerprint 47e163c3 (calls
  424-646): 223 calls in 5,789 s, nothing dropped, nothing refused on replay.
  128 re-checks of settled problems (a call each, no move); 73 widenings, 57
  settled and 16 without a result, at levels 2 (32), 3 (23) and 4 (18); then
  21 rounds on open problems by her rule (4,893 s, 80,181 moves, 27,771 new
  checked results, 473 slices, 288 switches between moves, none abandoned).
  Her theorems' verified ranges grew from 100,000 (or the problem's least n
  plus that) to within a chunk of ten times it: 4/n to 999,982, 7/n to
  999,973, 11/n to 999,658, 13/n to 997,462, 19/n to 996,814, 14/n to 992,422,
  8/n to 997,822, 10/n to 998,362, 17/n to 981,262, 12/n to 889,822, 21/n to
  873,532, 15/n to 815,302, 18/n to 682,462 and 16/n to 248,950 (its range
  starts at 83,450). The rounds on 9/n, 5/n and 6/n, which have no theorem
  yet, gained 3,260 to 4,348 results each; 9/n got four of the last five
  calls, since each of its rounds gains thousands. No problem was settled.
- **The contest, and what it transferred.** Asked to compete against her and
  hand over what I used, I took her saved theorems and applied, with my own
  code, the first method her language could not state: the set of n with a
  representation is closed under multiples, so an open residue x with a prime
  p of the modulus dividing it is represented whenever x/p modulo M/p is
  reached, or reduces further, while the factor taken out keeps n/t >= lo past
  the checked range. My counts from her state after call 623, independent of
  her code:

| a | modulus | open residues | after closure | coprime open | verified range |
|---|---|---|---|---|---|
| 4 | 36,756,720 | 26,262 | 26,262 | 26,262 | 999,982 |
| 7 | 36,756,720 | 2,690 | 2,690 | 2,684 | 999,973 |
| 8 | 83,160 | 38,866 | 30,928 | 925 | 997,822 |
| 10 | 83,160 | 40,047 | 18,724 | 924 | 998,362 |
| 11 | 83,160 | 34,611 | 26,969 | 51 | 999,658 |
| 12 | 83,160 | 58,529 | 48,644 | 1,325 | 889,822 |
| 13 | 9,240 | 7,920 | 7,920 | 1,440 | 997,462 |
| 14 | 83,160 | 47,485 | 38,738 | 535 | 992,422 |
| 15 | 83,160 | 35,556 | 25,711 | 1,340 | 815,302 |
| 16 | 9,240 | 8,952 | 8,952 | 1,680 | 248,950 |
| 17 | 9,240 | 8,400 | 8,400 | 1,920 | 981,262 |
| 18 | 83,160 | 63,072 | 43,646 | 3,271 | 682,462 |
| 19 | 27,720 | 27,261 | 27,261 | 5,416 | 996,814 |
| 21 | 83,160 | 44,220 | 21,936 | 2,046 | 873,532 |

  It leaves the coprime classes alone (the quadratic-residue wall: for 4/n and
  7/n every open class is coprime) and the 9,240-modulus theorems, whose
  reductions land on unreached classes. The method is now hers: the derivation
  rule `theorem_multiples`, the operator `egypt_theorem_multiples` that derives
  it from her own theorem and cover, the verdict's own recount (four self-test
  cases), and a package check. What I would use next and did not transfer:
  closure under multiples by primes outside the modulus, which needs a lifted
  modulus, and the known theorem that no polynomial family reaches a
  quadratic-residue class, which her language can state as a pattern but not
  prove.
- **The first measurement, and what it corrected.** One round on each of the
  fourteen theorem problems from a copy of her state after call 646, in the
  order of my table: nine closures derived, three equal to my counts, five
  weaker, one theorem lost. The weaker five were closed at the base range
  (100,000) and carried, by `theorem_range`, over the range to a million with
  the counts of the base range, where a factor up to ten times larger may be
  taken out; the lost one was the finer of 19/n's two base ranges, which the
  saving kept only the widest of. Three changes. A closed statement now names
  the range it was closed at, and the checker refuses to close a theorem again
  at that range, so after every extension the closure at the wider range is
  due and derived again (a closure that reduces nothing is derived too, as the
  record of the attempt; before, 7/n tried its empty closure five times in a
  round). Each operator names what is due: a closure for a theorem that names
  its cover while no theorem on that cover is closed at its range (widest
  range first, then fewest open residues); an extension for a theorem no
  theorem already reaches past that is closed when it is, on the same cover or
  leaving fewer residues open at the same closed range. And every base range
  is persisted with its theorems, one per cover. On the same copy of her
  state: 11/n closes at 100,000, extends to 999,658 and closes again with the
  same 26,969 (mine; nothing more reduces there); 4/n the same to 999,982 with
  26,262 (mine); 21/n closes at 100,000 to 27,768, extends to 873,532 and
  closes again to 21,936 (mine), then finds a finer cover in the same round
  (44,178 open instead of 44,220), closes it, extends it and closes it again:
  21,894 open, 2,004 coprime, below my count, which was of her older cover.
  My recount of the finer theorem with my own code, from her saved cover:
  21,894 open, 2,004 coprime, hers exactly.
- **The measurement at fingerprint 0437ea5a (commit f4ef9e4).** One round on
  each of the fourteen theorem problems, in the order of my table, from a
  fresh copy of her state after call 646: 987 s, 14,339 moves, 3,109 new
  checked results, 64 slices and 15 switches between moves, none abandoned.
  Every round derived the closure at the full verified range (closed at the
  range end, after the closure at the base range and the extension). Eight
  equal my table. In the other six she closed a theorem finer than the one I
  had counted: her rounds verify the base range again with the finest cover
  they hold and derive its theorem, and that theorem is now saved; my table
  was of the one theorem her saving used to keep. Recounted with my code from
  her final state, theorem by theorem, all fourteen closures are exactly my
  counts of the finest theorem she holds:

| a | open residues before, per theorem | her closure: open, coprime, at | my table | my recount |
|---|---|---|---|---|
| 11 | 34,611 | 26,969, 51, at 999,658 | 26,969 | 26,969, 51 |
| 13 | 7,920 | 7,920, 1,440, at 997,462 | 7,920 | 7,920, 1,440 |
| 16 | 8,952 | 8,952, 1,680, at 248,950 | 8,952 | 8,952, 1,680 |
| 19 | 27,261 and 79,986 | 27,261, 5,416, at 996,814 | 27,261 | 27,261, 5,416 |
| 14 | 47,485 | 38,738, 535, at 992,422 | 38,738 | 38,738, 535 |
| 17 | 8,400 | 8,400, 1,920, at 981,262 | 8,400 | 8,400, 1,920 |
| 8 | 38,866 and 38,860 | 30,922, 919, at 997,822 | 30,928 | 30,922, 919 |
| 10 | 40,047 | 18,724, 924, at 998,362 | 18,724 | 18,724, 924 |
| 12 | 58,529 and 58,476 | 48,591, 1,272, at 889,822 | 48,644 | 48,591, 1,272 |
| 21 | 44,220 and 44,178 | 21,894, 2,004, at 873,532 | 21,936 | 21,894, 2,004 |
| 15 | 35,556 and 35,470 | 25,625, 1,254, at 815,302 | 25,711 | 25,625, 1,254 |
| 18 | 63,072 and 62,564 | 43,138, 2,763, at 682,462 | 43,646 | 43,138, 2,763 |
| 7 | 2,690 and 798 | 798, 792, at 999,973 | 2,690 | 798, 792 |
| 4 | 26,262 | 26,262, 26,262, at 999,982 | 26,262 | 26,262, 26,262 |

  The 7/n row is the one to read twice: the coarser theorem's 2,690 open
  classes are all but six coprime to the modulus, where closure under
  multiples cannot reach, and my table said so; her finer theorem leaves 798
  open, 792 of them coprime, and the closure reduces none of the other six
  either. So the contest ends with
  her counts below mine on six problems, for a reason that is hers (the finer
  cover) and not the method's; the method reduces the same residues in both
  our hands. The closure on the largest modulus (36,756,720) cost 1.3 million
  work units and the whole 4/n round 86 s.
- **Her rounds after the transfer** (calls 856-1062, fingerprint 0437ea5a,
  3,356 s): the re-check wave first (every settled problem and widening
  a call each, 203 calls), then her own choices among the open problems by
  the gain rule: Sierpiński's 5/n (333 new results in 1,108 moves), 6/n
  (4,424 in the whole move allowance), then Collatz twice (893 and 558). The
  fifth open round was stopped for the next change of her code. Her
  theorem problems were not chosen in these four rounds: their recent rounds,
  the closure rounds of the measurement above, had gained 104 to 524 results
  each, against thousands on 5/n and 6/n.
- **The verdict on her state after call 646** (before the transfer), archive
  included: 116,552 claims VERIFIED (99,520 of them walls), none refuted, 27
  UNRESOLVED, in 3,848 s. The 27 are window values in families without an
  independent rule, as before. Every derivation of the scan (270 in the
  verdict's sample of 4,096 claims) verified after its premises. The verdict
  on her final state after call 1,269 (fingerprint ab202107, after the second
  contest below): 124,455 claims VERIFIED (101,320 of them walls), none
  refuted, 27 UNRESOLVED (the window values without an independent rule), 37
  self-test cases passing, in 4,232 s.
- **Open obligations.** Only five operators breathe; a plain move still runs
  whole. A move waiting when a call ends starts over. Derivations exist for
  ranges and theorems only; her other claims compose through the fixed forms
  they always had. A widening is offered only for the 19 families with a
  widening rule (35 of the 125 windows). The 6,000-key memory is unchanged.

## The second contest: divisor families (commit 1d618fc, fingerprint ab202107)

Asked to compete again, I took the numbers her theorems leave to the witness
search: the primes in open residue classes, which every range chunk represents
one by one with a witness her checker verifies. The first thing a
mathematician reaches for there is not a residue class. A Type I solution of
a/n = 1/x + 1/y + 1/z with n | x has x = ne, q = ae - 1, y = (ne + f)/q and
z = ney/f for any f | e^2, and (1 + q)/(ne) = a/n whatever e and f are. Her
classical families fix e and f and cover one class each. Leave q free and tie
it to a divisor of a linear form in n, and one statement is a classical family
for every q at once: `plus h` (q | n + h, q = -1 mod ah, f = he), `times h`
(q | hn + 1, q = -1 mod ah, f = e/h) and `square` (q | an + 1, q = -1 mod a,
f = e^2). With my own code (compete2/dfam.py: a segmented factorization of the
linear forms over each interval, one divisor kept per residue class, every
representation the formulas give checked exactly, 5,789 of them), on her state
after the transfer rounds:

| a | modulus | open-class primes, verified range | left after 12 families | in the next million | left |
|---|---|---|---|---|---|
| 4 | 36,756,720 | 260 | 2 | 229 | 5 |
| 7 | 36,756,720 | 8 | 0 | 11 | 0 |
| 8 | 83,160 | 4,111 | 106 | 3,710 | 66 |
| 10 | 83,160 | 4,180 | 306 | 3,776 | 140 |
| 11 | 83,160 | 224 | 18 | 199 | 2 |
| 12 | 83,160 | 4,974 | 731 | 5,182 | 508 |
| 13 | 9,240 | 58,664 | 1,172 | 52,814 | 617 |
| 14 | 83,160 | 2,442 | 396 | 2,191 | 226 |
| 15 | 83,160 | 4,499 | 653 | 5,135 | 439 |
| 16 | 9,240 | 12,085 | 1,001 | 65,089 | 3,796 |
| 17 | 9,240 | 76,841 | 3,012 | 70,466 | 1,775 |
| 18 | 83,160 | 8,170 | 2,080 | 11,479 | 2,085 |
| 19 | 27,720 | 73,528 | 4,265 | 66,215 | 2,437 |
| 21 | 83,160 | 7,851 | 1,732 | 8,259 | 1,296 |

Of 257,837 open-class primes she had witnessed, the families represent all but
15,474; of 294,755 in the next million, all but 13,392. The first family
(q | n + 1) alone takes about half; the others each a few percent more. The
residual primes for 4/n below two million are 351289, 925369, 1083289,
1423321, 1672609, 1869169 and 1980169. Her 5/n theorem (modulus 8,031,343,320,
past the bound of the class-counting instruments) has no open-class prime below
two million to measure on.

- **What transferred.** The claim kind `dfam` (the checker verifies the
  identity as a polynomial identity in n and q on an 8 by 8 grid, larger than
  its degree, states the integrality lemma, and computes and sums the first six
  instances exactly); the operator `egypt_divisor_families`, which states the
  twelve families (h up to 6) for a three-term question; the chunk prover,
  which tries the families before any witness search (a divisor of the linear
  form from its factorization, one divisor kept per residue class) and whose
  proof now carries a family table, the shapes used and, per number, the shape
  and the divisor; the checker's and the verdict's own recomputation of the
  denominators and the exact sum for every such number, so a chunk proof stands
  without the family claim; persistence of the families with the theorems; the
  verdict's `dfam` rule and four self-test cases; the bench fixture; and the
  package check `divisor_families_verify_and_carry_a_chunk` (twelve families
  stated, a misnamed shape refused, the chunk's witnesses replaced one for one
  by family divisors, a wrong divisor refused by both).
- **Her rounds with the families.** One round on each of the fourteen theorem problems from a fresh copy of
  her state after the closure rounds, with the range frontier raised from ten
  to twenty times `verify_to` in the same change: 1,415 s in all, 142 new
  chunks, and in the chunks proved after the families were stated 251,832
  numbers represented by a family divisor against 14,635 by a witness. The
  first family (q | n + 1) carried 139,399, `times 2` 43,247, `times 3`
  19,421, `plus 2` 11,447 and the others between 1,321 and 9,155 each. Every
  round stated the twelve families, doubled its verified range and closed its
  theorem again at the new range; four closures came out finer at the wider
  range (21/n 21,744, 12/n 48,586, 15/n 25,623, 18/n 41,980). A sample of
  20,162 family entries from her saved proofs (200 per chunk), recomputed with
  my own closed forms, had none wrong.

| a | seconds | new chunks | family entries | witnesses | verified range | closure at the new range |
|---|---|---|---|---|---|---|
| 4 | 118 | 11 | 224 | 5 | 999,982 to 1,999,962 | 26,262, 26,262 coprime, at 1,999,962 |
| 7 | 150 | 11 | 11 | 0 | 999,973 to 1,999,943 | 798, 792 coprime, at 1,999,943 |
| 8 | 77 | 10 | 3,245 | 53 | 997,822 to 1,995,402 | 30,922, 919 coprime, at 1,995,402 |
| 10 | 62 | 10 | 3,284 | 123 | 998,362 to 1,996,542 | 18,724, 924 coprime, at 1,996,542 |
| 11 | 58 | 10 | 179 | 1 | 999,658 to 1,999,278 | 26,969, 51 coprime, at 1,999,278 |
| 12 | 137 | 10 | 6,082 | 743 | 889,822 to 1,767,402 | 48,586, 1,272 coprime, at 1,767,402 |
| 13 | 56 | 10 | 46,717 | 535 | 997,462 to 1,994,642 | 7,920, 1,440 coprime, at 1,994,642 |
| 14 | 76 | 10 | 1,756 | 198 | 992,422 to 1,984,002 | 38,738, 535 coprime, at 1,984,002 |
| 15 | 92 | 10 | 6,305 | 648 | 815,302 to 1,610,082 | 25,623, 1,254 coprime, at 1,610,082 |
| 16 | 51 | 10 | 41,155 | 3,853 | 248,950 to 414,450 | 8,952, 1,680 coprime, at 414,450 |
| 17 | 72 | 10 | 69,245 | 1,742 | 981,262 to 1,960,442 | 8,400, 1,920 coprime, at 1,960,442 |
| 18 | 195 | 10 | 12,023 | 2,819 | 682,462 to 1,329,642 | 41,980, 2,763 coprime, at 1,329,642 |
| 19 | 159 | 10 | 52,499 | 2,173 | 996,814 to 1,993,274 | 27,261, 5,416 coprime, at 1,993,274 |
| 21 | 112 | 10 | 9,107 | 1,742 | 873,532 to 1,733,012 | 21,744, 2,004 coprime, at 1,733,012 |
- **Her scan at the new fingerprint** (calls 1,063-1,269, 1,377 s): the
  re-check wave again, and within it and after it her own choices by the
  gain rule: nine rounds on theorem problems (11/n, 13/n, 14/n, 10/n, 8/n,
  16/n, 17/n, 15/n, 21/n; 47 to 97 s each, 574 s in all) and one on the
  Collatz sieve. Each theorem round stated the twelve families, added ten
  chunks (the first before the families were stated, nine with a family
  table), doubled its verified range and closed its theorem again at the new
  range: 8/n to 1,995,402, 10/n to 1,996,542, 11/n to 1,999,278, 13/n to
  1,994,642, 14/n to 1,984,002, 15/n to 1,610,082, 16/n to 414,450, 17/n to
  1,960,442 and 21/n to 1,733,012. Over her 81 chunk proofs with a family
  table, 180,993 numbers stand on a family divisor and 8,895 on a witness;
  the first family carried 103,087. The counts per problem are those of the
  measurement above, as they must be: the same code on the same state, her
  choice of problem being the only difference. 5/n, 6/n, 4/n, 7/n, 12/n,
  18/n and 19/n were not reached before the run was stopped for the verdict.
- **The verdicts.** On the state of the fourteen family rounds, archive
  included: 119,764 claims VERIFIED (101,920 of them walls), none refuted, 27
  UNRESOLVED (the window values without an independent rule, as before), 37
  self-test cases passing, in 4,319 s. Listed in full with the verdict's own
  rules, every saved claim taken as an admitted premise: all 168 divisor
  families VERIFIED, all 128 chunk proofs with a family table VERIFIED
  (251,832 numbers by a family divisor, 14,635 by a witness, each recomputed
  and summed exactly), all 251 closure derivations VERIFIED, in 350 s. On her
  final state after call 1,269: 124,455 claims VERIFIED (101,320 of them
  walls), none refuted, 27 UNRESOLVED (the window values without an
  independent rule), 37 self-test cases passing, in 4,232 s.
- **Open obligations.** The families and the theorem are not yet composed into
  one statement (a `theorem_families` rule would state that an unresolved n
  lies in an open class and fails every family condition); a range verified
  to h gives every composite below h^2 for free by the closure under
  multiples, which her language cannot yet state as a range; Type II solutions
  with a common factor give further divisor conditions (on agn + 1 with
  constraints on g); h stops at 6; the density-zero estimate for the residual
  is not a claim she can make.

## Consolidation after the second contest (commits 4847840 and a415650, fingerprint f2f22639)

- **Both verdicts are in her state.** `tools/ingest_verdict.py` records a
  verdict's bit, counts, digest and the state's own digest in the rounds
  ledger record, which her calls now carry forward (no new record: a state at
  its bound would evict a research record for bookkeeping). The wave's seed
  state, a copy of her state after call 1,269, carries the verdict on the
  fourteen family rounds (119,764 VERIFIED, none refuted, 27 unresolved) and
  the verdict on her final state (124,455 VERIFIED, none refuted, 27
  unresolved), both "no, keep thinking".
- **The transfer is frozen.** The manifest is rebuilt at the consolidated
  source (commit 4847840, 671 checks, archive sha256
  f627b0aa25a8248caa540d66b2e457c34ea9587949391308af70a5e7532c0ea2, 100
  members); the divisor families are what commit 1d618fc made them.
- **Work units re-priced.** Measured on this machine: the witness search costs
  0.94 microseconds a unit, the family step 0.36, the cover loop 0.09, and the
  factor check ten microseconds a number at no charge. The prover's charges now
  price a unit at about a microsecond: the cover loop one unit a number plus
  one per ten moduli (was one per modulus), a factor check half the bit length
  of the number (was free), a family step half the bit length of its linear
  form (was the full length plus one per prime power). The checker's charges,
  which bound what a claim may cost to admit, are unchanged. The bench and the
  pyramid were regenerated at the new prices: 217 operators pass (116 N, 53 W,
  209 S, 79 E; 5 anytime, 5,912 breaths); the pyramid binds 374 moves (171 N,
  118 W, 315 S, 105 E). Her rounds' scores use elapsed seconds, so the
  re-pricing changes what a move may spend, not how problems rank.
- **The closure wave.** Her final state holds nine theorem problems live; the
  other six (4/n, 7/n, 12/n, 18/n, 19/n, 5/n) had been evicted to the archive
  by the record bound (each self-widened window is a record). One round on each
  from the seeded state, at the consolidated fingerprint: 648 s in all, every
  record restored from its archive file (5,617 to 15,760 objects replayed,
  none dropped, none refused), the twelve families stated in each, ten chunks
  added in each (nine with a family table), the range doubled and the theorem
  closed again at the new range: 4/n to 1,999,962 (207 numbers by a family
  divisor, 4 by a witness; closure 26,262, all coprime), 7/n to 1,999,943
  (11 and 0; 798 open, 792 coprime), 12/n to 1,767,402 (6,082 and 743;
  48,586), 18/n to 1,329,642 (12,023 and 2,819; 41,980), 19/n to 1,993,274
  (52,499 and 2,173; 27,261), and 5/n to 1,999,962 (no open-class prime below
  two million, so no family entry; its modulus, 8,031,343,320, is past the
  closure bound, so no closure). The ledger record carried both verdicts
  through all six calls. All fifteen theorem problems are live again, the
  state at its 128-record bound. The wave's state is the seed of the staged
  scan.
- **The third contest, opened as a stub: the pair families.** Type II
  solutions with a common factor: a/n = 1/(ne) + 1/(nf) + 1/z needs
  z = nef/(aef - e - f); for prime n the divisor aef - e - f is g n with
  g | ef, so a g n + 1 = (ae - 1)(af - 1) = q q' with q, q' = -1 (mod a),
  e = (q + 1)/a, f = (q' + 1)/a, and a/n = 1/(ne) + 1/(nf) + g/(ef). The shape
  `pair g`: q | a g n + 1 with q = -1 (mod a) and g | e f; g = 1 is the tier-2
  `square`. Baseline with my own code (compete3/tier3.py) on the state of the
  fourteen family rounds, over the residual the twelve tier-2 families leave:

| a | primes in open classes, verified range | left after tier 2 | left after pair g = 2..8 | in the next million: open, after tier 2, after pairs |
|---|---|---|---|---|
| 4 | 489 | 7 | 0 | 242, 3, 0 |
| 7 | 19 | 0 | 0 | 8, 0, 0 |
| 8 | 7,810 | 172 | 67 | 3,583, 43, 14 |
| 10 | 7,950 | 444 | 232 | 3,677, 137, 53 |
| 11 | 423 | 20 | 9 | 204, 8, 4 |
| 12 | 9,538 | 1,184 | 659 | 4,998, 425, 219 |
| 13 | 111,320 | 1,789 | 935 | 50,902, 510, 215 |
| 14 | 4,619 | 622 | 373 | 2,113, 200, 100 |
| 15 | 8,607 | 1,012 | 636 | 5,008, 447, 235 |
| 16 | 23,440 | 1,755 | 1,184 | 64,021, 3,552, 2,113 |
| 17 | 145,905 | 4,758 | 2,927 | 67,921, 1,507, 793 |
| 18 | 15,688 | 3,472 | 2,479 | 11,040, 1,856, 1,177 |
| 19 | 128,552 | 6,694 | 4,333 | 58,846, 2,032, 1,122 |
| 21 | 14,966 | 2,869 | 2,048 | 7,917, 1,116, 702 |

  Of 479,326 open-class primes in the verified ranges, tier 2 leaves 24,798
  and the pairs g = 2..8 take 8,916 of those (g = 2: 3,871; 4: 3,354; 3:
  2,571; 8: 1,450; 5: 1,297; 7: 789; 6: 673), leaving 15,882; in the next
  million 11,836 becomes 6,747. For Erdős–Straus nothing is left below three
  million. Every solution the formulas gave was checked exactly (13,027).
  Nothing of this is transferred yet.
- **Preregistered schedule for the third tier.** Before any transfer: (1) the
  shapes are `pair g` for g = 2..8, stated as a claim kind with the same three
  guards as `dfam` (grid identity, integrality lemma, instances exact); (2) the
  measurement is fourteen rounds, one per theorem problem, in the order 11,
  13, 16, 19, 14, 17, 8, 10, 12, 21, 15, 18, 7, 4 (the order of the first
  contest's table), each from a fresh copy of the state the closure wave
  leaves, at the fingerprint the transfer produces, with the move allowance
  and work bound of the library task (10,000 moves, 4·10^9 work); (3) what is
  recorded per round: seconds, chunks added, numbers by pair, by tier-2
  family, by witness, the range and the closure reached; (4) the result to
  compare against is this baseline: her pair entries per problem should equal
  my counts on the same interval, and every entry must verify by the
  verdict's own denominators; (5) a round whose counts differ from mine by
  more than the difference of intervals is a defect to root-cause, not a
  result; (6) the transfer is written only after the fourteen rounds and their
  verdict.
- **The next scan is staged, not started.** `scan10/run10.sh` continues the
  state the wave leaves at fingerprint f2f22639; `scan10/watch10.sh` measures,
  after each call, the family use of every theorem-problem round (family
  entries against witnesses, range, closure) into `measure.txt`, so the
  twelve shapes are measured in her own rounds before the third tier is
  transferred.

## What she still depended on me for: the third round (commits 0b52008, 73e9a6b and 83acffa, fingerprint e05a320c)

Asked again what she depends on me for, I read this session's record rather
than the code: every new shape of mathematics was mine (I state the family
list, she cannot extend it); she is run by hand, a call at a time; every
change of her code cost her a re-check wave of two hundred calls, whatever the
change touched; only five moves could be left, and a move left at the end of
a call lost its work; the record bound had evicted her theorem problems while
settled windows stayed; and two statements her data supported could not be
made. Each became an instrument, with a check in the package and a rule in
the independent verdict where a claim is involved.

- **The pair families, and the grammar closed.** `pair h` is the Type II
  solution with a common factor h (a h n + 1 = q q', q, q' = -1 mod a,
  e = (q + 1)/a, f = (q' + 1)/a, h | ef; a/n = 1/(ne) + 1/(nf) + h/(ef)),
  the third tier the previous entry preregistered. With plus, times and pair
  the one-divisor grammar of Type I solutions is complete: for f | e^2 the
  condition q | ne + f is a divisibility of n + h, hn + 1 or ahn + 1. The
  checker admits it by the same three guards (a grid identity in n and q,
  the integrality lemma, instances exact; the pair's h | ef is a condition,
  searched for in the instances), and the prover asks the checker's own
  conditions of every divisor it finds, so a divisor of the right class that
  fails a condition is never written into a proof (the first version wrote
  one, and the checker refused the whole chunk).
- **She extends the family list herself.** After the first list (plus, times
  and pair for h up to 6, and the square), a shape kind gets its next h when
  its last two steps each carried at least sixteen numbers in her admitted
  proofs, up to the checker's bound of 64: a family that pays earns its
  successor. On the small problem she added `times 7` in one round.
- **Base ranges use the families.** The profile of a 13/n round showed 39 of
  its 75 seconds in the witness search of a base range verified again with a
  finer cover, 35,033 witnesses, while the chunks past it used the families.
  A `finite` claim now carries a family table like a chunk proof, verified the
  same way by the checker and the verdict, and the base verification starts
  where the admitted spine ends instead of at the least n.
- **Two statements her data supported.** `theorem_families` composes her
  theorem with its admitted families: an unresolved n lies in an open class,
  is at or past the range end, and meets none of the families' conditions.
  `composite_range` states what closure under multiples gives from an admitted
  range [lo, hi): every n below hi^2 with a divisor in the range is
  represented, for a question from 2 every composite below hi^2. Both are
  derived again as the families or the range grow; a composed theorem is
  terminal.
- **A move left at the end of a call keeps what it did.** The scheduler asks
  each waiting move to finish with what it has: at its next breath the
  operator receives `checkpoint` and states the part verified (a base range
  or a chunk its prefix, a sweep the classes swept, a divisor search nothing
  and no miss), with a quarter of its allocation to state it; a move at its
  total work bound is treated the same. The report counts the moves settled
  and the objects they stated.
- **A change of her code re-checks only what it can touch.** Each round
  records the fingerprint of the core (scheduler, runtime, checker) and of
  the operator modules whose moves can apply to the problem, by closure over
  the language's signatures from the problem's own kinds; eligibility and the
  reuse of a record's memory compare that. This round changed the core, so
  the scan below still began with a wave; the next change to one family of
  operators will not.
- **What to forget first.** At the record bound the records of settled
  problems go first, then the oldest of the rest: her theorem problems stay
  live while settled windows wait on file.
- **Her own loop.** `--calls N --out DIR --seconds S` runs a task N times in
  one process, each call reading and writing the state as a separate call
  would, and writes the files a shell loop wrote; the scan below ran that way.
- **Checks.** 674 package checks pass (three new: the pair families with
  the compositions and the family base ranges, the checkpoints with the
  relevant fingerprints and the forgetting order, the campaign mode as a
  subprocess); the verdict has ten new self-test cases (45); the bench passes
  219 operators (118 N, 53 W, 211 S, 79 E); the pyramid binds 376 moves.
- **The preregistered fourteen rounds, first run** (fingerprint e2c81955,
  928 s): every round stated the pair families with the rest and extended
  its own list by the yield rule (13/n, 16/n, 19/n, 12/n and 21/n to plus 8
  and times 11; 4/n only to times 7), added chunks past the old frontier and
  composed and squared its theorem. In her 127 new chunk proofs 167,357
  numbers stand on a family divisor, 4,952 of them on a pair, and 4,871 on a
  witness. The comparison the preregistration asked for could not be made as
  written: her prover tries the families in its own order, so a pair takes
  numbers my baseline had given to plus or times, and her lists were longer
  than mine. The comparison that means the same thing was made instead: with
  my own code, her cover, the checker's divisor rule and her family list, I
  classified every one of the 11,641,164 numbers in her new chunks; the set a
  family takes equals her family tables and the set that needs a witness
  equals her witness sets, on all fifteen problems, entry for entry. And the
  rounds found a defect, as the preregistration said a shortfall would be:
  five rounds stopped short of the frontier (13/n at 2,692,668, 16/n at
  513,750, 17/n at 2,450,032, 18/n at 1,653,232, 19/n at 2,591,150) because
  their family lists had grown past 24, the checker's bound on the shapes a
  proof may name, and every later chunk was refused whole; the bound is now
  200 and the prover caps its list at the bound (commit 83acffa).
- **The fourteen rounds again** (fingerprint e05a320c, 951 s): every round
  made its ten chunks; her lists grew by the yield rule to h = 13 on 13/n and
  18/n, 14 on 17/n and 19/n and 15 on 16/n (29 or 30 families there), 9 to 12
  on the 83,160-modulus problems, 7 on 4/n and 3 on 7/n. In the 149 new chunk
  proofs 263,004 numbers stand on a family divisor, 7,355 of them on a pair,
  and 6,479 on a witness; every entry recomputed with my own closed forms,
  none wrong. The exact check again: my classification of all 13,304,230
  numbers in her new chunks, with her cover, the divisor rule and her lists,
  equals her family tables and her witness sets on all fifteen problems.

| a | s | chunks | numbers by a family | by a pair | by a witness | families stated | range reached |
|---|---|---|---|---|---|---|---|
| 4 | 79 | 10 | 242 | 12 | 0 | 18 | 2,999,942 |
| 7 | 111 | 10 | 8 | 1 | 0 | 17 | 2,999,913 |
| 8 | 52 | 10 | 3,561 | 86 | 16 | 21 | 2,992,982 |
| 10 | 40 | 10 | 3,615 | 257 | 56 | 21 | 2,994,722 |
| 11 | 52 | 10 | 199 | 12 | 5 | 17 | 2,998,898 |
| 12 | 86 | 10 | 6,628 | 437 | 340 | 24 | 2,644,982 |
| 13 | 31 | 10 | 50,592 | 398 | 169 | 26 | 2,991,822 |
| 14 | 56 | 10 | 2,004 | 160 | 94 | 21 | 2,975,582 |
| 15 | 62 | 10 | 6,610 | 371 | 287 | 23 | 2,404,862 |
| 16 | 27 | 10 | 37,621 | 1,172 | 1,542 | 29 | 579,950 |
| 17 | 37 | 10 | 70,924 | 1,124 | 657 | 30 | 2,939,622 |
| 18 | 161 | 10 | 13,176 | 937 | 1,474 | 29 | 1,976,822 |
| 19 | 80 | 10 | 57,675 | 1,651 | 944 | 30 | 2,989,734 |
| 21 | 76 | 10 | 10,149 | 737 | 895 | 25 | 2,592,492 |

  Against the baseline of the previous entry (twelve families, h up to 6, and
  pairs g up to 8 on the residual): on the interval past two million my code
  left 6,747 primes to a witness on thirteen problems; her rounds, with the
  lists she grew herself, needed 6,479 witnesses on 149 chunks that do not
  cover the same intervals (four of them shorter), so the numbers are of the
  same size and not the same measure; the measure that is the same is the
  exact check above.
- **Her scan at the new fingerprint.** Her fifth scan (calls 1,270 to
  1,484 of the one state, fingerprint e05a320c) ran in her own loop, 215
  calls in 2,514 s, from the state the closure wave left, until I stopped it
  to take the verdict. The core had changed, so it began with the re-check
  wave: 180 calls of settled windows and maps, 187 calls in all settled by
  checked results, 28 came back UNKNOWN (the window values without a rule,
  and the theorem rounds). From call 181 she chose her theorem problems:
  thirteen rounds (10, 13, 11, 14, 8, 16, 17, 15, 21, 19, 12, 4 and 7 over n,
  794 s of the 2,514; 18/n and 5/n had not come up when I stopped it), each
  of which stated the pair families with the rest, grew its own list to the
  same 17 to 30 shapes as the preregistered run, made its ten chunks past the
  two-million frontier (to 2.99 million on nine problems, 2.40 to 2.64
  million on 12/n, 15/n and 21/n, 579,950 on 16/n), composed and squared its
  theorem and re-closed it at the new range. In her 130 new chunk proofs
  (297,255,285 numbers) 249,828 numbers stand on a family divisor, 5,294 of
  them on a pair, and 5,005 on a witness. Against the preregistered run from
  the same seed: on all thirteen problems the set of numbers on a family and
  the set on a witness are the same, chunk for chunk, and the final lists are
  the same shapes; which family takes a number differs on ten problems,
  because a list grows during the round and the scan's timing put a shape's
  step earlier or later, so a chunk was classified against a different prefix
  of the same list. Her state after the scan holds 128 records: every theorem
  problem live, the settled windows evicted first to the archive.
- **The verdict on her final state.** The verdict on her final state after call 1,484 (215 calls of the fifth scan) found 126,483 claims VERIFIED (101,968 of them walls), 0 refuted, 27 UNRESOLVED (the window values without an independent rule), 45 self-test cases passing, in 3,916 s; the bit returned to her is `no, keep thinking`.
- **Open obligations.** The composed theorem does not yet feed her choice of
  problem (the residual's size is not a score); the pair grammar leaves
  two-divisor conditions with a common factor in both (Type II with h | e and
  h | f separately) unstated; the checkpoint states a prefix only for the
  five breathing moves; the relevant fingerprint treats the core as one piece.

## The first researched ability installed: refusal accounting and self-diagnosis (commit 3ae3cae, fingerprint 74987261)

RESEARCH.md ranked it first among the abilities she could hold next, because
it is small, it closes the class of defect the third tier's first run found,
and every later ability depends on her seeing what her checker refuses. The
gap's evidence was that run: on five problems every chunk proof past the
twenty-fifth family was refused whole, and her rounds ended with "no untried
move" as if nothing were wrong; the defect was visible only to my check
outside her. She mined failures in the loop's sense (I read her profiles);
she did not mine her own refusals.

- **What was installed.** The runtime keeps, per call, the claims the checker
  refused by move, kind and the checker's own reason, with the first refused
  identity (`refusals`); the checker names the shapes bound by its own reason
  (`family shapes bound`, no longer folded into `family table`). The report
  carries the table, the total (`refused`) and a `diagnosis` for a round that
  ran out of moves, gained nothing, refused more than it admitted, or had a
  claim refused at a bound of the language: what was exhausted by kind, what
  was refused and why, the residual's size, and the instrument each reason
  names from a fixed table (the shapes a proof's family part may name, the h
  a family may have, the finite range bound, the closure residue bound, the
  premises a derivation may name, the sieve, term, bit and object bounds);
  `blocked` says `instrument`, `refused`, `exhausted` or `none`. The rounds
  ledger keeps, per round, the refusals, the most frequent reason, the
  refusals at a bound and the bound's reason. A strategy whose claims are
  refused eight times in a context and scope with none admitted, or twice at
  a bound, is retired there with the reason, whatever its context (the four
  never-retired moves aside); a strategy retired for failing keeps its reason
  too. Her scan reads the last round's fields: a round with a claim refused at
  a bound that then ran out of moves, or admitted fewer than it refused, makes
  the problem wait for the instrument the reason names, by name; a round that
  refused at least eight claims and admitted fewer waits for an instrument
  with the reason; a round out of moves says how many claims were refused and
  why. Her loop's log line carries the count. All of it is scheduling and
  reporting: no claim is involved, so the verdict has no new rule.
- **Check.** The package check `refusals_are_counted_named_and_retire_a_strategy`
  plants a proof naming 201 shapes and finds it in the runtime's table with its
  reason, its identity and the instrument; retires a strategy on a synthetic
  tally of eight refusals without an admission and on two at a bound, keeps
  one with an admission and never the classical generator; reads the
  diagnosis; and asks her scan about four ledgers (refused more than admitted;
  few refusals; a bound refusal with the round out of moves; a bound refusal
  in a round that gained). The campaign check now also reads the count in the
  report, the ledger and the log line. 675 checks pass.
- **The defect reproduced, with the ability.** In a scratch copy of the code
  with the shapes bound at 24 and the prover uncapped (the state of the third
  tier's first run), the 16/n round from her final state: the restore refused
  one carried chunk proof at the bound (twenty objects invalid with it), the
  round proposed two chunks with her 29 shapes and had both refused at the
  bound, and `egypt_range_chunk` was retired in its context at the second
  with the reason; the report's table names the three at the bound with
  MAX_DFAM_SHAPES, the diagnosis says `instrument`, the ledger's round carries
  `bound: family shapes bound`, and her scan says "last round had 3 claims
  refused at a bound (family shapes bound: MAX_DFAM_SHAPES in lexicon_check:
  the shapes a proof's family part may name); waits for that instrument". The
  round still gained 402 checked objects (the derivations it rebuilt on the
  shortened range), which is why the first version of the rule, which weighed
  refusals against gains only, said "no untried move left; waits for new
  instruments" with no reason on this very round; a refusal at a bound now
  decides on its own. That was the one change made after a run.
- **Two ordinary rounds at the committed code**, from her final state. 11/n
  (44 s, 101 new checked objects, 283 moves) had 62 claims refused: 50 fitted
  families whose identity fails (39 as proposed, 11 checked again by verify),
  6 signature patterns that a family reaches a coprime square, 6 square and
  signature patterns broken by a residue. 16/n (21 s, 403 new, 1,314 moves)
  had 11: 7 divisor families with no instance, 4 patterns broken by a
  residue. Refusals in an ordinary round are the checker doing its work on
  proposals; none names an instrument, none retires a strategy (16/n's 23
  retirements are by failure, as before), the diagnosis of both says `none`
  (out of moves after gaining), and her scan says of both what it said
  before, out of moves at this fingerprint, now with the count and the most
  frequent reason appended.
- **The next two in the note's order, read against her records.** 4.3
  (family searches ordered by the witnessed mass of a class) changes the
  order of moves within a round; every theorem round in her records ends
  with no untried move, so the same moves run in a different order and the
  outcome measure the note named (witnesses per chunk) cannot change; it
  would show only under an allowance that cuts rounds short, which her
  library task does not. 4.4 (the witness bound as her own parameter) answers
  a chunk abandoned for want of a witness within the bound; no chunk in her
  state or in the 29 rounds since the third tier was abandoned so (the
  residual note does not occur), and the only bound-exhaustion signal in her
  reports is the witness search on single numbers, two to five per round at
  the smaller bound of 256a. Both wait for evidence; 4.4 is the first to
  install on the round that abandons a chunk, with the bound and the yields
  recorded in the ledger as the note says.
- **Preregistered next: 4.2, residual mining.** Before it runs: (1) the
  baseline is the witnessed numbers in her admitted chunk proofs after the
  fifth scan, 5,005 on 130 chunks over thirteen problems, and per problem the
  witness column of the table above (18/n from its rerun); (2) the grammar
  is the note's: the residue of n modulo m for m dividing the theorem's
  modulus; for each linear form n + h, hn + 1 and ahn + 1 with h up to 6 and
  each modulus t in {a, ah}, a statement about the residues modulo t of the
  prime factors of the form's value (every prime factor in a set of classes,
  or none in a class), and smoothness or roughness of the value at a bound;
  (3) the claim is a `pattern` claim under a new rule `residual_predicate`
  naming the chunk proofs by identity and the predicate; the checker
  rebuilds the witnessed set from the named proofs and evaluates the
  predicate on all of it, and the independent verdict does the same with its
  own code; the claim is stated only for a predicate the witnessed set
  satisfies entirely and a same-size sample of represented numbers from the
  same chunks satisfies on fewer than a tenth; (4) the falsifier is a window
  of the `residual_predicate` family over the witnessed numbers of the next
  chunk the problem admits, and a failure refutes the claim with the witness
  kept; (5) the schedule is fourteen rounds, one per theorem problem, in the
  order of the first contest's table, each from a fresh copy of her state,
  then one more chunk per problem as the falsifier; recorded per round: the
  predicates stated, refuted and surviving, the witnessed count they cover,
  seconds; (6) a defect is a stated predicate the verdict evaluates
  differently, or a predicate the sample satisfies on a tenth or more; a
  surviving predicate is a description of her residual, not a theorem, and
  none is expected to name a new family shape on these problems.
- **Open obligations.** The instrument table names bounds only: a refusal for
  a mathematical reason has no instrument and is not a defect. The residual
  size in the diagnosis counts the entries of every residual object of the
  run, not the residual of the theorem. The retirement by refusal is per run,
  so a later call proposes the refused claim once more before retiring the
  strategy again.

## Residual mining installed, as preregistered (commit eb79bc2, fingerprint 43cf6619)

The second researched ability, preregistered in the previous entry, is in
her language: two derivation rules, two operators, their checks, and the
fourteen rounds. What the rounds found is a limitation of the grammar, and
it is recorded as such.

- **What was installed.** A `residual_predicate` derivation names chunk
  proofs with a family part and a predicate of the grammar (the residue
  classes of n modulo a divisor of the level modulus; the classes the prime
  factors of n + h, hn + 1 or ahn + 1, h up to 6, take modulo a or ah; a
  bound below or above every prime factor of one of those forms) and states
  that every number the proofs witnessed satisfies it and that fewer than a
  tenth of a same-size sample of the numbers they represent by a family
  divisor do, the sample evenly spaced through them; the checker rebuilds
  both sets from the named proofs and evaluates the predicate on every
  number, and refuses a claim with fewer than ten numbers on either side. A
  `residual_break` derivation names one chunk proof and a witnessed number
  that fails the predicate. The independent verdict has both rules in its
  own code (six new self-test cases, 51). `egypt_residual_profile` states the
  selective predicates over the chunk proofs a call carried in (at most
  sixteen, the most selective first, never one that only restates an admitted
  plus or times family); `egypt_residual_falsify` tests each surviving
  predicate on every chunk the call adds, stating the break at the first
  witnessed number that fails it or the predicate again over the wider proofs
  while it stays selective. The runtime records the identities carried into a
  call, so the profile describes what she had and the falsifier what she
  added. The bench passes 221 operators (120 N, 53 W, 213 S, 79 E; 5 anytime,
  5,912 breaths) and the pyramid binds 378 moves (175 N, 118 W, 319 S,
  105 E); the package check `residual_predicates_are_stated_selectively_broken_by_a_witness_and_verified`
  builds the fixture (4/n with the families plus 1 and times 2 only: the
  fifteen numbers witnessed in [300, 3000) are all 1 modulo 24, and 3011,
  witnessed by force past the family it has, breaks that on the next chunk),
  verifies both claims with the verdict, and refuses a forged count and a
  vacuous predicate (676 checks).
- **Where the installation departs from the preregistration, and when.**
  The falsifier is an operator in her rounds, not a window of the window
  tools: the witnessed numbers of her next chunk are her own proof's, not a
  tool's computation, and the break is a checked claim naming that proof.
  The contrast sample is evenly spaced through the represented numbers
  rather than the first ones in order, chosen when the first implementation's
  sample (the smallest numbers of the oldest chunk) was seen to be biased in
  magnitude, before any measurement on her state. The ten-number minimum was
  added when the first fixture run showed a residual of one number making
  every observed value a predicate (sixteen claims of sample size one), a
  defect of the design found in the fixture, before the rounds.
- **The fourteen rounds** (fingerprint 43cf6619, each from a fresh copy of her
  state after the fifth scan, in the first contest's order, 749 s
  in all). Witnessed and sample are counted over the nineteen chunk proofs
  with a family part each problem carried; candidates are the predicates of
  the grammar the witnessed set satisfies; the best candidate is the one the
  fewest sample numbers satisfy, with that fraction.

| a | s | new checked | witnessed | sample | candidates | best candidate | satisfied by | stated | broken |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 41 | 101 | 6 | 6 | below ten |  |  | 0 | 0 |
| 13 | 17 | 220 | 704 | 704 | 82 | factors of n + 1 mod 13 | 66% | 0 | 0 |
| 16 | 24 | 402 | 5,395 | 5,395 | 89 | factors of n + 1 mod 16 | 80% | 0 | 0 |
| 19 | 49 | 270 | 3,117 | 3,117 | 82 | factors of n + 1 mod 19 | 78% | 0 | 0 |
| 14 | 40 | 217 | 292 | 292 | 92 | factors of 14n + 1 mod 14 | 74% | 0 | 0 |
| 17 | 21 | 71 | 2,399 | 2,399 | 83 | factors of n + 1 mod 17 | 77% | 0 | 0 |
| 8 | 35 | 172 | 69 | 69 | 92 | factors of 8n + 1 mod 8 | 62% | 0 | 0 |
| 10 | 28 | 276 | 179 | 179 | 92 | factors of 10n + 1 mod 10 | 69% | 0 | 0 |
| 12 | 60 | 129 | 1,083 | 1,083 | 92 | factors of 12n + 1 mod 12 | 70% | 0 | 0 |
| 21 | 59 | 125 | 2,637 | 2,637 | 89 | factors of 21n + 1 mod 21 | 78% | 0 | 0 |
| 15 | 48 | 207 | 935 | 935 | 89 | factors of 15n + 1 mod 15 | 72% | 0 | 0 |
| 18 | 154 | 256 | 2,819 | 2,819 | 92 | factors of 18n + 1 mod 18 | 70% | 0 | 0 |
| 7 | 103 | 255 | 0 | 0 | below ten |  |  | 0 | 0 |
| 4 | 70 | 122 | 4 | 4 | below ten |  |  | 0 | 0 |

- **Result.** No round stated a predicate: on eleven problems the most
  selective candidate of the grammar is satisfied by 62 to 83 percent of the
  represented sample, against the preregistered tenth, and on 4/n, 7/n and
  11/n fewer than ten numbers were witnessed over the family chunks (4, 0
  and 6). The falsifier had nothing to test, and each round added its
  thirtieth chunk as before. The independent verdict was run on every
  residual claim the rounds saved: there were none. By the preregistration's
  criterion there is no defect: nothing was stated that the verdict could
  evaluate differently, and nothing vacuous was admitted.
- **Reading.** The best candidates are all factor-class predicates on n + 1
  or an + 1, of the form "no prime factor of n + 1 lies in the classes c with
  2c = -1 (mod ah)": consequences of the listed families through composite
  divisors (2q), which the exclusion of restated families does not catch
  because it names only the class -1 itself. Residue predicates show the
  residual occupying 248 of the 256 classes modulo 840 that represented
  numbers occupy on 16/n, 168 of 192 on 19/n, 138 of 144 on 13/n: a few
  classes the residual avoids, not enough for a tenth. The residual is, by
  construction, the set with no divisor in class -1 of any listed form; a
  grammar over single forms restates that set's definition one form at a
  time and cannot tell it from the numbers one family takes, which satisfy
  every other form's condition just as often. A predicate that would say
  something new must name a form outside the list, and that is a family
  shape, which the note expected none of these problems to yield; on this
  grammar the measurement agrees.
- **Open obligations.** Outside the fixture the falsifier has not run on a
  stated predicate. The profile's cost in a round is 0.1 to 3 s per level
  (the factorizations of the forms at every witnessed and sampled number).
  The bound of sixteen predicates and the tenth are policy constants. A
  grammar that could describe the residual would have to name the
  conjunction over the listed forms, or forms outside the list; the second
  is the family search itself.

## Her own shapes: the general family space searched, verified and adopted by yield (commits b86ed23, ad689f7 and f046850, fingerprint 0110f839)

Asked to make her better than me at the thing I did against her by hand, I
gave her the space I had been drawing shapes from. In the second and third
contests every family was mine: plus h, times h, the pairs and the square,
each derived by algebra and handed over as a shape the checker knew. The
algebra behind all of them is one identity: with x = n e and e = (q + 1)/a,
a/n = 1/x + 1/y + 1/z exactly when (q y - n e)(q z - n e) = (n e)^2, so every
such family is a divisor d of (n e)^2 with y = (n e + d)/q and z = n e y/d,
and d = h1 n^i e^j / h2 turns q | n e + d into the divisibility of one linear
form by q. That space, not its four points, is now hers.

- **What was installed.** A `gfam` claim names (i, j, h1, h2) and instances;
  the checker refuses parameters outside the space, verifies the identity as
  a polynomial identity on a 12 by 12 grid and every instance exactly, and a
  chunk proof's family table may name a general family by its parameters
  (y is an integer whenever q divides the form, by the lemma at `gfam_form`;
  z when d | n e y, a condition of the instance). The independent verdict has
  the claim and the family rows in its own code (six new self-test cases,
  57). `egypt_shape_search` enumerates the space up to a level of h1 and h2
  (8 first, doubling while a level pays, up to 32), leaving out the admitted
  shapes, measures each candidate on a sample of at most 512 of the numbers
  her carried chunk proofs had to witness (evenly spaced), and states,
  greedily by what each adds to the numbers still uncovered, the families
  that represent at least four of them and one in sixty-four, with up to
  eight of those numbers as instances; sixteen per call at most, once per
  call. Her ranges use the admitted general families after the four shapes,
  and her composed theorem names them with the rest. The fixture is the
  plus-1 level of 4/n: the search states, among others, times 2 as
  (0, 1, 1, 2) and n + 4 as (0, 0, 1, 1), and the chunk past the level
  represents 47 of its 48 witnessed-or-family numbers by a family. Package
  check `general_families_found_by_her_search_verify_and_carry_a_chunk`
  (677 checks).
- **The probe, before the preregistration.** Run once on four of her
  fifth-scan residuals, from the state after the residual-mining rounds, to
  see whether the space holds anything: 16/n (sample 512 of 5,395 witnessed)
  found 16 families representing 370 of the sample (72 percent), 19/n 409
  (80 percent), 13/n 452 (88 percent), 12/n 315 (62 percent), in about two
  seconds each; the first family everywhere was (0, 0, 1, 1), q | n + a with
  q = -1 (mod a), a form I had not given her, then n + a h for small h and
  h2 n + h1 with both parameters above 1. The probe adopted twins (two
  parameter points giving the same representations); the greedy rule was
  written after it. Those four problems are therefore not a blind test.
- **Preregistered, before the rounds.** (1) The schedule is the fourteen
  rounds, one per theorem problem, in the first contest's order, each from
  a fresh copy of her state after the fifth scan, at the fingerprint of the
  transfer, with the library task's allowance. (2) Recorded per round: the
  families the search stated with their parameters, forms and sample
  yields; the share of the sample they represent together; the seconds of
  the search; and the thirtieth chunk the round adds against the
  twenty-ninth it carried: numbers by a family, by a general family, by a
  witness, and the chunk's length. (3) The measure is the witnesses per
  number of the thirtieth chunk against the twenty-ninth, and the share of
  the sample the stated families represent. (4) The expectation from the
  probe is that on 16/n, 19/n, 13/n and 12/n the thirtieth chunk needs
  fewer than half the witnesses per number of the twenty-ninth; on the
  other ten it is open, and on 4/n, 7/n and 11/n, which witnessed fewer than
  ten numbers over their family chunks, the search has too little to measure
  and should state nothing. (5) A defect is a stated family the verdict
  refutes, a chunk proof using one refused or refuted, or a thirtieth chunk
  that needs more witnesses per number than the twenty-ninth on a problem
  where families were stated.
- **The fourteen rounds.** Three runs, each fourteen rounds from fresh
  copies of her state after the fifth scan, in the first contest's order.
  **Run 1** (fingerprint 7a386043, commit b86ed23, 884 s): on eleven
  problems the search stated 6 to 25 general families, every one VERIFIED by
  the independent verdict, representing 76 to 96 percent of the residual
  sample; on 4/n, 7/n and 11/n it stated nothing, as expected. But the chunk
  the round added used them on one problem only (18/n): on the other ten the
  scheduler had run the chunk before the search. **Run 2** (fingerprint
  f325414f, commit ad689f7, range moves waiting for the search, 869 s):
  the same families, and still no chunk with them, because thirteen problems
  stood at the frontier of thirty chunks and no chunk could be added at all;
  18/n, at nineteen chunks, added ten with the families, its last with 37
  witnesses against 49 on the one before. Erratum: the previous entry says
  the residual-mining rounds each added a thirtieth chunk; none did on those
  thirteen problems, for the same reason. **Run 3** (fingerprint 0110f839,
  commit f046850, the frontier at forty, 1,269 s): each round added ten
  chunks (18/n twenty) with the families she found, the same length as the
  ten family chunks it carried and adjacent above them. Per problem: the
  families stated and the share of the residual sample they represent; the
  numbers and witnesses of the carried chunks and of the added ones, with
  the witnesses per thousand numbers; every general family and every added
  chunk was VERIFIED by the independent verdict, and the checker refused
  nothing the search or the chunks proposed.

| a | s | families stated | sample represented | carried numbers | carried witnesses | per 1,000 | added numbers | by her families | added witnesses | per 1,000 |
|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 59 | 0 | 0 of 6 | 999,620 | 5 | 0.01 | 999,620 | 0 | 2 | 0.0 |
| 13 | 41 | 16 | 491 of 512 | 997,180 | 169 | 0.17 | 997,180 | 68 | 17 | 0.02 |
| 16 | 42 | 20 | 453 of 512 | 165,500 | 1,542 | 9.32 | 165,500 | 476 | 335 | 2.02 |
| 19 | 103 | 18 | 476 of 512 | 996,460 | 944 | 0.95 | 996,460 | 351 | 139 | 0.14 |
| 14 | 68 | 16 | 262 of 292 | 991,580 | 94 | 0.09 | 991,580 | 47 | 20 | 0.02 |
| 17 | 51 | 16 | 473 of 512 | 979,180 | 657 | 0.67 | 979,180 | 217 | 84 | 0.09 |
| 8 | 60 | 6 | 57 of 69 | 997,580 | 16 | 0.02 | 997,580 | 7 | 6 | 0.01 |
| 10 | 50 | 13 | 158 of 179 | 998,180 | 56 | 0.06 | 998,180 | 32 | 14 | 0.01 |
| 12 | 132 | 25 | 430 of 512 | 877,580 | 340 | 0.39 | 877,580 | 96 | 77 | 0.09 |
| 21 | 115 | 25 | 421 of 512 | 859,480 | 895 | 1.04 | 859,480 | 341 | 296 | 0.34 |
| 15 | 89 | 24 | 469 of 512 | 794,780 | 287 | 0.36 | 794,780 | 96 | 74 | 0.09 |
| 18 | 244 | 25 | 428 of 512 | 582,462 | 2,819 | 4.84 | 1,294,360 | 1,324 | 940 | 0.73 |
| 7 | 125 | 0 | below ten | 999,970 | 0 | 0.0 | 999,970 | 0 | 0 | 0.0 |
| 4 | 86 | 0 | 0 of 4 | 999,980 | 0 | 0.0 | 999,980 | 0 | 1 | 0.0 |

- **Result.** On the eleven problems where she found families, the witnesses
  per number fell by 62 to 90 percent: 13/n from 0.17 to 0.02 per
  thousand, 16/n from 9.3 to 2.0, 19/n from 0.95 to 0.14, 17/n from 0.67 to
  0.09, 18/n from 4.8 to 0.73. The preregistered expectation held on all four
  probed problems (16/n, 19/n, 13/n, 12/n) and on the seven that were blind.
  The comparison is like for like in length and adjacent in n; the added
  chunks lie above the carried ones, so a drift of the witness density with
  n is inside the measure, and it is small at these sizes. The families she
  found are her own: the first everywhere is q | n + a with q = -1 (mod a),
  which was in no contest of mine, and the lists run through n + a h, the
  forms h2 n + h1 with both parameters above 1, a h2 n + h1 and a h1 n + 1
  with parameters past the shapes I gave her.

- **Open obligations.** The composed theorem names at most 23 families (the
  premise bound), so with the general families it names a prefix of her
  list. The search stayed at level 8 in every round, since a level doubles
  only on the next call; the levels 16 and 32 are unmeasured. The frontier
  is a constant again (forty), the yield floor and the sample size are
  policy constants, and 18/n carried nine family chunks, not ten. The four
  probed problems were not blind. The residual profile and its falsifier now
  see a residual a fifth of what it was and have not been run on it.

## Certified exception sets: what a numerator's question leaves out (commit edee579, fingerprint 674e2388)

- **Source.** RESEARCH_RESULTS.md, the research brief that answers
  RESEARCH_INQUIRY.md, ranks certified exception sets for Schinzel's
  numerators among the targets one exact-checking machine can finish (its
  row 5) and cites Pomerance and Weingartner (arXiv 2511.16817) for
  calculations that support an exceptional prime in (a^2, 2a^2) for every a
  from 20. The brief is source-reported: arxiv.org is not reachable from this
  session, so the citation stays as the brief gives it, and nothing in the
  brief is evidence she uses.

- **Instrument (implemented).** The claim kind `exceptions` (a, three terms,
  a bound at most 4,000, the exceptions, a witness table); the checker's
  complete search `three_term_search` by the divisor method (README, under
  the general families); the verdict's own `three_unit_fractions` and
  `exceptions_verdict`, with four self-tests; the operator
  `egypt_exception_scan` (a unit fraction question to its set up to
  2a^2 + 1, 4,000 from a = 45, once per question, a residual on refusal);
  the explore goal takes the goal `exceptions` on unit fraction questions
  (bound at binding to numerators 2..64 and three terms) and confines such a
  question to the scan and verification; the result rows carry the count,
  the largest and the first 24; the library window
  `window-schinzel-beyond-bounds` (a = 20 and 22 to 28) under the catalog
  problem that had no window, and the tool entry `esq`. Package checks: the
  set of 21/n up to 883 holds 761 and not 7 and a witness at the bound, and
  the verdict says VERIFIED; a dropped exception, an added one and a wrong
  witness are refused by the checker and REFUTED by the verdict; a second
  scan of the question proposes nothing; the complete search agrees with a
  brute force on every a <= 12, n <= 40.

- **Locally checked.** The complete search against a brute force on every a
  from 2 to 12 and n from 1 to 80: 880 cases, no disagreement, every
  representation exact. The scan on every numerator from 4 to 64 in a
  scratch run: 61 sets, 26.7 s in all, every one VERIFIED by the
  verdict. Her agent on the window task settled it in one second with eight
  sets; the verdict on that state: 8 VERIFIED, 0 REFUTED, self-test passed.
  The stated theorem problems ask her to prove nothing false: the least n of
  each (7/n 3, 8/n 242, 9/n 20, 10/n 182, 11/n 38, 12/n 12,242, 13/n 282, 14/n 842, 15/n 20,522, 16/n 83,450, 17/n 2,082, 18/n 35,282, 19/n 354, 21/n 14,052) minus one has no representation by the complete search
  (0.3 s at most), so the minima the library's earlier search gave are
  confirmed at those n.

| a | bound | exceptions | largest | primes in (a^2, 2a^2) | seconds (scan + verdict) |
|---|---|---|---|---|---|
| 20 | 801 | 47 | 761 | 6 | 0.05 |
| 21 | 883 | 30 | 761 | 5 | 0.05 |
| 22 | 969 | 51 | 929 | 5 | 0.10 |
| 23 | 1,059 | 49 | 991 | 5 | 0.05 |
| 24 | 1,153 | 80 | 1,153 | 13 | 0.11 |
| 25 | 1,251 | 78 | 1,213 | 14 | 0.10 |
| 26 | 1,353 | 55 | 1,061 | 7 | 0.06 |
| 27 | 1,459 | 75 | 1,381 | 12 | 0.11 |
| 28 | 1,569 | 88 | 1,471 | 17 | 0.14 |

- **Reading of the numerics.** For every a from 20 to 44 her set holds a
  prime exception in (a^2, 2a^2) (all), consistent with what the
  brief reports of Pomerance and Weingartner. The sets also hold the bound
  2a^2 + 1 itself as an exception for a = 24, 32, 33, 36 and 42, so the
  interval bounds nothing above, and the library's 90,001 for a = 20 (no
  representation by the complete search) stands.

- **Scope.** A set is exact up to its bound and says nothing beyond it; it
  settles nothing about Schinzel's conjecture for any a. The bound 4,000 is
  a policy constant (the checker's cost is a witness search per n and a
  complete search per exception, below two seconds per numerator here).
  The complete search rests on the identity (e y - n x)(e z - n x) = (n x)^2
  with e = a x - n and on x in (n/a, 3n/a] for the least denominator, checked
  against brute force on small cases only; the verdict repeats it in its own
  code.

- **Open obligations.** Her loop has not run on the new window at the
  committed fingerprint (the next entry). The theorem problems' rounds do not
  use the sets: a stated minimum could be checked against the set, and a
  cover asked from the least n above the largest certified exception rather
  than from a given minimum. Exceptions above 2a^2 + 1 are not certified.
  The search kinds the brief ranks first (no-three-in-line at 61, van der
  Waerden colourings, covering systems, circulant Ramsey graphs) are not
  installed.
