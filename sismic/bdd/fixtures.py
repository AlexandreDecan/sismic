import asyncio
from typing import Callable, List

from behave.api.async_step import AsyncContext, use_or_create_async_context
from behave.fixture import fixture, use_fixture
from behave.runner import ModelRunner
from sismic.bdd.environment import (  # sismic_before_scenario,
    setup_sismic_from_context,
    sismic_after_step,
    sismic_before_scenario,
    sismic_before_step,
)
from sismic.bdd.LoopRunner import LoopRunner
from sismic.helpers import log_trace
from sismic.interpreter.default import Interpreter
from sismic.io.yaml import import_from_yaml
from sismic.model.statechart import Statechart
from sismic.bdd.steps import *

__all__ = [
    "setup_behave_context",
]

runners = []  # type: List[LoopRunner]


def setup_behave_context(
    context,
    statechart_path=None,
    statechart: Statechart = None,
    property_statecharts: List[Statechart] = None,
    interpreter_klass: Callable[[Statechart], Interpreter] = Interpreter,
    async_start_fn=None,
    is_async=False,
    reset_fn=None,
):
    property_statecharts = property_statecharts if property_statecharts else []
    sc = statechart
    if statechart_path:
        sc = import_from_yaml(filepath=statechart_path)
    if not sc:
        raise Exception("No statechart found")
    context.config.update_userdata(
        {
            "statechart": sc,
            "interpreter_klass": interpreter_klass,
            "is_async": is_async,
            "property_statecharts": property_statecharts,
            "async_start_fn": async_start_fn,
            "reset_fn": reset_fn,
        }
    )

    behave_run_hook = ModelRunner.run_hook

    def run_hook(self, name, context, *args):
        if name == "before_scenario":
            sismic_before_scenario(context, *args)
            if async_test(context):
                if getattr(context, "fixture-setup"):
                    setattr(context, "fixture-setup", False)
                else:
                    create_async_context(context)
                    sismic_before_scenario(context, *args)
        elif name == "before_step":
            sismic_before_step(context, *args)
        elif name == "before_tag":
            sismic_before_tag(context, *args)

        behave_run_hook(self, name, context, *args)

        if name == "after_scenario":
            if async_test(context):
                clear_async_context(context)
        elif name == "after_step":
            sismic_after_step(context, *args)
        elif name == "after_all":
            sismic_after_all(context, *args)

    ModelRunner.run_hook = run_hook


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


async def default_task(context):
    async_start_fn = context.config.userdata.get("async_start_fn")
    try:
        if async_start_fn:
            await (async_start_fn)(context)
        setup_sismic_from_context(context)
        await asyncio.sleep(0)
    except Exception as ex:
        print(ex)


@fixture
def sismic_async_application(context):
    reset_fn = context.config.userdata.get("reset_fn")
    if reset_fn:
        (reset_fn)(context)
    async_context = create_async_context(context)
    task = async_context.loop.create_task(default_task(context))
    async_context.tasks.append(task)


@fixture
def sismic_application(context):
    reset_fn = context.config.userdata.get("reset_fn")
    if reset_fn:
        (reset_fn)(context)
    setup_sismic_from_context(context)


def sismic_after_all(context):
    if async_test(context):
        clear_async_context(context)


def sismic_before_tag(context, tag):
    if tag == "fixture.sismic_application":
        use_fixture(sismic_application, context)
    if tag == "fixture.sismic_async_application":
        use_fixture(sismic_async_application, context)
