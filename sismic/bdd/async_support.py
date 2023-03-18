import asyncio
from typing import Any, Callable, List

from behave.api.async_step import AsyncContext, use_or_create_async_context

from sismic.bdd.LoopRunner import LoopRunner


def testing_async(context):
    return context.config.userdata.get("is_async")


def create_async_context(context) -> AsyncContext:
    if not hasattr(context, 'runners'):
        context.runners = []

    count = len(context.runners) + 1
    name = f"sismic{count}"

    # start a new loop runner
    runner = LoopRunner(asyncio.new_event_loop(), name)
    runner.start()
    asyncio.set_event_loop(runner.loop)

    # save it in the context
    setattr(runner.loop, 'sismicbdd', name)

    async_context = use_or_create_async_context(context,
                                                name,
                                                loop=runner.loop)
    context.runners.append([True, runner, async_context])

    return async_context


def get_async_context(context) -> AsyncContext:
    runners = getattr(context, "runners", [])  # type: List[List[Any]]
    for active, runner, context in runners:
        if active:
            return context
    return create_async_context(context)


def clear_async_context(context):
    runners = getattr(context, "runners", [])  # type: List[List[Any]]
    for i in range(len(runners)):
        active, runner, context = runners[i]
        if active:
            runner.stop_if_running()
            runner.join()
            runners[i][0] = False


def run_async_loop(context):
    runners = getattr(context, "runners", [])  # type: List[List[Any]]
    for i in range(len(runners)):
        active, runner, context = runners[i]
        if active:
            runner.run_coroutine(asyncio.sleep(0))
