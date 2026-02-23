import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def running_listener(listener, startup_delay: float = 0.5):
    task = asyncio.create_task(listener.start())
    await asyncio.sleep(startup_delay)
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
