# Frozen-source diff ledger

These are the only deliberate semantic/formal deviations admitted in the final
Hindi reader. The frozen English source remains untouched.

## OLP-HI-DIFF-0001 — duplicate label in alternate reduction exercise

- Source: \`sets-functions-relations/size-of-sets/reduction-alt.tex:106\`
- Frozen source hash: \`46381B85C0E9A1AB48CB9301518DE91F073D649C3B1119325C1409F5A6C1D663\`
- Source label: \`sfr:siz:red:prob:nat-nat\`
- Duplicate witness: \`sets-functions-relations/size-of-sets/reduction.tex:108\`
- Hindi target: \`sets-functions-relations/size-of-sets/reduction-alt.tex:103\`
- Hindi target hash: \`92C34A99A716B284981E132839AD9244C756BDFFD74343C76737EBB821AB7763\`
- Disposition: the alternate exercise uses
  \`sfr:siz:red-alt:prob:nat-nat\`.
- Rationale: both files occur in the complete reader; retaining the frozen
  duplicate creates a multiply-defined label.
- Confidence: high.
- Smallest upstream diff: give the alternate exercise the \`red-alt\` label.

## OLP-HI-DIFF-0002 — real zero mistyped as rational zero

- Source: \`sets-functions-relations/arithmetization/cauchy.tex:150\`
- Frozen source hash: \`35D0A39913340EADCAB7FB9D7742B56AEF0D0F29868CD65EECA9DC53694E8AC2\`
- Frozen formula: \`$\equivrep{f}{}\neq 0_\Rat$\`
- Hindi target: \`sets-functions-relations/arithmetization/cauchy.tex:142\`
- Hindi target hash: \`B11E6D6BBBDBE80706E1B9C98D16057750DF722F09E223226478B2099DFAE045\`
- Disposition: \`$\equivrep{f}{}\neq 0_\Real$\`.
- Rationale: the surrounding definition concerns an equivalence class
  representing a real number; the same section later compares with
  \`0_\Real\`.
- Confidence: high.
- Smallest upstream diff: replace \`0_\Rat\` with \`0_\Real\`.

## OLP-HI-DIFF-0003 — wrong object named after two recursive sequences

- Source: \`set-theory/card-arithmetic/ch.tex:35-36\`
- Frozen source hash: \`B1BDEE185CE2A21EEBA54CCE52EBEC13154B54B77A6652820AD4F7AC61E8B212\`
- Frozen wording: “The rest of the definition of
  \`$\cardfont{a}$\` is provided by transfinite recursion.”
- Hindi target: \`set-theory/card-arithmetic/ch.tex:35\`
- Hindi target hash: \`EB955878C813419183BE59361BB357D4CBC52393CC611F0286D782162187CB7C\`
- Disposition: the translation identifies the intended recursive sequence
  rather than claiming that the arbitrary cardinal \`a\` is being defined.
- Rationale: the immediately preceding display defines the aleph and beth
  sequences; \`\cardfont{a}\` is only the arbitrary cardinal used to explain
  cardinal successor.
- Confidence: high that the frozen phrase is wrong; medium on the smallest
  editorial wording.
- Smallest upstream diff: “The remaining clauses of these sequence definitions
  are provided by transfinite recursion.”

No independent second writer replayed these findings. They were rechecked by the
single controlling Hindi writer against the frozen source, the translated TeX,
and the compiled complete reader.
