from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from src.db import get_postgres_pool
from src.graph import compile_with_checkpointer

app = FastAPI(title="Semantic Citator Backend")

@app.post("/verify-quote/async")
async def verify_quote_async_endpoint(extraction: dict, background_tasks: BackgroundTasks):
    quote_id = extraction["quote_id"]
    
    async def run_graph_task():
        async with get_postgres_pool() as pool:
            graph = await compile_with_checkpointer(pool)
            initial_state = {
                "quote_id": quote_id,
                "extraction": extraction
            }
            config = {"configurable": {"thread_id": quote_id}}
            await graph.ainvoke(initial_state, config=config)

    background_tasks.add_task(run_graph_task)
    return {"status": "processing", "thread_id": quote_id}


@app.get("/verify-quote/status/{quote_id}")
async def get_verification_status(quote_id: str):
    async with get_postgres_pool() as pool:
        graph = await compile_with_checkpointer(pool)
        config = {"configurable": {"thread_id": quote_id}}
        state_snapshot = await graph.aget_state(config)
        
        if not state_snapshot:
            return {"status": "not_found"}
            
        current_state = state_snapshot.values
        
        if current_state.get("posterior_misuse_probability") is not None:
            return {
                "status": "completed",
                "result": {
                    "posterior_misuse_probability": current_state.get("posterior_misuse_probability"),
                    "credible_interval": current_state.get("credible_interval"),
                    "logical_contradiction": current_state.get("formal_evaluation", {}).get("logical_contradiction"),
                    "causal_edit_distance": current_state.get("causal_evaluation", {}).get("topological_edit_distance")
                }
            }
        
        return {
            "status": "in_progress",
            "next_node": state_snapshot.next
        }
