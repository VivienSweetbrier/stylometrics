-- Auto-generated Lean 4 Verification Script Example
import Aesop

-- 1. Declare isolated clauses as Propositional Variables
variable (Malice Punitive : Prop)

-- 2. Define Source Axioms (The Ground Truth)
axiom source_rule : Malice → Punitive

-- 3. Define Destination Claim (The Quote Usage)
-- The citing document affirms the consequent, a logical fallacy.
theorem citing_claim : Punitive → Malice := by
  -- 4. Execute Automated Tactics
  tauto
