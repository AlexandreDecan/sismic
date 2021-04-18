import asyncio
from typing import Callable, List

from behave.api.async_step import AsyncContext, use_or_create_async_context

from sismic.bdd.LoopRunner import LoopRunner


def testing_async(context):
    return context.config.userdata.get("is_async")


def get_async_context(context) -> AsyncContext:
    name = getattr(context, "contextname", None)
    async_context = getattr(context, name)
    return async_context


def create_async_context(context) -> AsyncContext:
    runners = getattr(context, 'runners', 0)
    runners += 1
    setattr(context, 'runners', runners)
    name = f"sismic{runners}"
    runner = LoopRunner(asyncio.new_event_loop())
    runner.start()
    asyncio.set_event_loop(runner.loop)
    async_context = use_or_create_async_context(context, name, loop=runner.loop)
    setattr(context, "contextname", name)
    setattr(context, name, async_context)
    setattr(context, "runner", runner)
    return async_context


def clear_async_context(context):
    runner = getattr(context, "runner", None)
    if runner:
        runner.stop_if_running()
        runner.join()


def run_async_loop(context):
    runner = getattr(context, 'runner')  # type: LoopRunner
    if runner.loop.is_running():
        runner.run_coroutine(asyncio.sleep(0))
