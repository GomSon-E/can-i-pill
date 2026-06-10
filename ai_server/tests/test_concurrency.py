import asyncio

from app import concurrency


def test_max_concurrent_gemini_calls_is_20():
    assert concurrency.MAX_CONCURRENT_GEMINI_CALLS == 20


def test_gemini_semaphore_is_asyncio_semaphore_with_value_20():
    assert isinstance(concurrency.GEMINI_SEMAPHORE, asyncio.Semaphore)
    assert concurrency.GEMINI_SEMAPHORE._value == 20


async def _run_under_semaphore(semaphore, current, max_seen):
    async with semaphore:
        current[0] += 1
        max_seen[0] = max(max_seen[0], current[0])
        await asyncio.sleep(0.01)
        current[0] -= 1


def test_semaphore_limits_concurrent_tasks_to_20():
    semaphore = asyncio.Semaphore(concurrency.MAX_CONCURRENT_GEMINI_CALLS)
    current = [0]
    max_seen = [0]

    async def run_all():
        await asyncio.gather(
            *(_run_under_semaphore(semaphore, current, max_seen) for _ in range(25))
        )

    asyncio.run(run_all())

    assert max_seen[0] <= 20
