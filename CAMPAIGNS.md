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
