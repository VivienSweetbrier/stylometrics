import asyncio
import os
import json
import sys

# Ensure the src module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.state import VerificationState
from src.nodes import ingestion_node

async def run_test():
    # Example: Charles Darwin on the Eye
    source_text = (
        "To suppose that the eye... could have been formed by natural selection, "
        "seems, I freely confess, absurd in the highest possible degree. Yet reason tells me, "
        "that if numerous gradations from a perfect and complex eye to one very imperfect and simple... "
        "can be shown to exist... then the difficulty of believing that a perfect and complex eye "
        "could be formed by natural selection, though insuperable by our imagination, can hardly be considered real."
    )
    
    citing_text = (
        "Even Charles Darwin admitted his theory was fundamentally flawed, stating: "
        "'To suppose that the eye... could have been formed by natural selection, seems, "
        "I freely confess, absurd in the highest possible degree.'"
    )
    
    state: VerificationState = {
        "quote_id": "test_darwin_001",
        "raw_source_text": source_text,
        "raw_citing_text": citing_text,
        "extraction": None,
        "semantic_evaluation": None,
        "causal_evaluation": None,
        "formal_evaluation": None,
        "posterior_misuse_probability": None,
        "credible_interval": None
    }
    
    if os.getenv("OPENAI_API_KEY", "dummy") == "dummy":
        print("WARNING: OPENAI_API_KEY is not set or is 'dummy'. The API call will fail with a 401 error.")
        print("To run this test properly, execute: $env:OPENAI_API_KEY='your-key'; python test_extraction.py\n")

    print("Sending text to ingestion_node...")
    try:
        result = await ingestion_node(state)
        print("\n--- LLM EXTRACTION RESULT ---")
        print(json.dumps(result["extraction"], indent=2))
    except Exception as e:
        print(f"\nExecution failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
