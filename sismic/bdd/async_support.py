import asyncio
from typing import Callable, List

from behave.api.async_step import AsyncContext, use_or_create_async_context
from sismic.bdd.LoopRunner import LoopRunner


runners = []  # type: List[LoopRunner]


def async_test(context):
    return context.config.userdata.get("is_async")


def get_async_context(context) -> AsyncContext:
    name = getattr(context, "contextname", None)
    async_context = getattr(context, name)
    return async_context


def create_async_context(context) -> AsyncContext:
    global runners
    name = f"sismic{len(runners) + 1}"
    runner = LoopRunner(asyncio.new_event_loop())
    runner.start()
    asyncio.set_event_loop(runner.loop)
    async_context = use_or_create_async_context(context, name, loop=runner.loop)
    setattr(context, "contextname", name)
    setattr(context, name, async_context)
    setattr(context, "runner", runner)
    setattr(context, "fixture-setup", True)
    runners.append(runner)
    return async_context


def clear_async_context(context):
    global runners
    name = getattr(context, "contextname", None)
    if name:
        for runner in runners:
            runner.stop()
            runner.join()
