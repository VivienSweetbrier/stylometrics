from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.state import VerificationState
from src.nodes import ingestion_node, semantic_node, causal_node, formal_node, synthesis_node

def build_verification_graph():
    builder = StateGraph(VerificationState)

    builder.add_node("ingestion", ingestion_node)
    builder.add_node("semantic", semantic_node)
    builder.add_node("causal", causal_node)
    builder.add_node("formal", formal_node)
    builder.add_node("synthesis", synthesis_node)

    builder.add_edge(START, "ingestion")
    builder.add_edge("ingestion", "semantic")
    builder.add_edge("ingestion", "causal")
    builder.add_edge("ingestion", "formal")
    builder.add_edge(["semantic", "causal", "formal"], "synthesis")
    builder.add_edge("synthesis", END)
    
    return builder

async def compile_with_checkpointer(pool):
    builder = build_verification_graph()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return builder.compile(checkpointer=checkpointer)
