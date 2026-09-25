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
