import asyncio
from celery.result import AsyncResult

async def await_celery_task(async_result: AsyncResult, poll_interval: float = 0.1) -> dict:
    """
    Yields control back to the asyncio event loop while waiting for the Celery 
    worker to finish updating the Redis result backend.
    """
    while not async_result.ready():
        await asyncio.sleep(poll_interval)
    
    return async_result.get()
