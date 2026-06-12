import asyncio
from concurrent.futures import ThreadPoolExecutor

MAX_CONCURRENT_GEMINI_CALLS = 20
GEMINI_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_GEMINI_CALLS)
GEMINI_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_GEMINI_CALLS)
