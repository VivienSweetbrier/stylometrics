from pydantic import BaseModel, Field
from typing import List

class CausalTriple(BaseModel):
    subject: str = Field(description="The exposure or cause variable.")
    relation: str = Field(description="The directional causal verb (e.g., 'causes', 'prevents').")
    object: str = Field(description="The outcome or effect variable.")

class LeanProposition(BaseModel):
    variable_name: str = Field(description="PascalCase identifier for the boolean proposition.")
    natural_language_mapping: str = Field(description="The exact text string this variable represents.")

class OrchestratorExtraction(BaseModel):
    quote_id: str
    structural_edit_count: int = Field(description="Count of brackets or ellipses in the destination text.")
    
    # Payload for the R dagitty subprocess
    source_causal_triples: List[CausalTriple]
    destination_causal_triples: List[CausalTriple]
    
    # Payload for the Lean 4 subprocess
    source_propositions: List[LeanProposition]
    source_axioms_lean_syntax: List[str] = Field(description="Lean 4 axiom statements.")
    destination_theorem_lean_syntax: str = Field(description="Lean 4 theorem statement.")
    
    # Payload for the Semantic divergence calculation
    source_context_window: str
    destination_context_window: str
