import time
from functools import wraps
import logging

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("finance-agent")


def observe(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        tool_name = fn.__qualname__
        input_repr = f"args={args[1:]} kwargs={kwargs}"
        start = time.perf_counter()
        try:
            result = await fn(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            logger.info(f"[OK]  {tool_name} | {latency:.1f}ms | {input_repr}")
            return result
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"[ERR] {tool_name} | {latency:.1f}ms | {input_repr} | {e}")
            raise
    return wrapper


import time
import asyncio
from functools import wraps
import logging

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("finance-agent")


def observe(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        tool_name = fn.__qualname__
        input_repr = f"args={args[1:]} kwargs={kwargs}"
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            logger.info(f"[OK]  {tool_name} | {latency:.1f}ms | {input_repr}")
            return result
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"[ERR] {tool_name} | {latency:.1f}ms | {input_repr} | {e}")
            raise
    return wrapper