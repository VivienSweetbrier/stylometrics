from typing import TypedDict, Optional

class VerificationState(TypedDict):
    quote_id: str
    raw_source_text: str
    raw_citing_text: str
    
    extraction: Optional[dict]
    
    semantic_evaluation: Optional[dict]
    causal_evaluation: Optional[dict]
    formal_evaluation: Optional[dict]
    
    posterior_misuse_probability: Optional[float]
    credible_interval: Optional[list[float]]
