import asyncio
from typing import Callable, List

from behave.runner import ModelRunner

from sismic.bdd.async_support import (clear_async_context,
                                      create_async_context, get_async_context,
                                      run_async_loop, testing_async)
from sismic.bdd.steps import *
from sismic.helpers import log_trace
from sismic.interpreter.default import Interpreter
from sismic.io.yaml import import_from_yaml
from sismic.model.statechart import Statechart

__all__ = [
    "setup_behave_context",
]


def setup_sismic_from_context(context):
    # Create interpreter
    if hasattr(context, 'interpreter'):
        return context.interpreter
    statechart = context.config.userdata.get("statechart")
    interpreter_klass = context.config.userdata.get("interpreter_klass")
    context.interpreter = interpreter_klass(statechart)

    # Log trace
    context.trace = log_trace(context.interpreter)
    context._monitoring = False
    context.monitored_trace = None

    # Bind property statecharts
    for property_statechart in context.config.userdata.get(
            "property_statecharts"):
        context.interpreter.bind_property_statechart(
            property_statechart, interpreter_klass=interpreter_klass)


def setup_behave_context(
    context,
    statechart_path=None,
    statechart: Statechart = None,
    property_statecharts: List[Statechart] = None,
    interpreter_klass: Callable[[Statechart], Interpreter] = Interpreter,
    is_async=False,
    async_task=None,
):
    property_statecharts = property_statecharts if property_statecharts else []
    sc = statechart
    if statechart_path:
        sc = import_from_yaml(filepath=statechart_path)
    if not sc:
        raise Exception("No statechart found")
    context.config.update_userdata({
        "statechart": sc,
        "interpreter_klass": interpreter_klass,
        "is_async": is_async,
        "property_statecharts": property_statecharts,
        "async_task": async_task,
    })

    if is_async:
        create_async_context(context)

    behave_run_hook = ModelRunner.run_hook

    def run_hook(self, name, context, *args):
        if name == "before_all":
            sismic_before_all(context, *args)
        elif name == "before_scenario":
            sismic_before_scenario(context, *args)
        elif name == "before_step":
            sismic_before_step(context, *args)

        behave_run_hook(self, name, context, *args)

        if name == "after_step":
            sismic_after_step(context, *args)
        elif name == "after_scenario":
            sismic_after_scenario(context, *args)
        elif name == "after_all":
            sismic_after_all(context, *args)

    ModelRunner.run_hook = run_hook


def sismic_before_all(context):
    pass


def sismic_after_all(context):
    if testing_async(context):
        clear_async_context(context)


def sismic_before_scenario(context, scenario):
    if testing_async(context):
        # First time thru, don't recreate
        if len(context.runners) > 1:
            clear_async_context(context)
            create_async_context(context)
        sismic_async_application(context)
    else:
        sismic_application(context)
    setup_sismic_from_context(context)


def sismic_after_scenario(context, scenario):
    # this resets the interpreter between scenarios
    context.interpreter = None


def sismic_before_step(context, step):
    # "Then" steps must at least follow one "when" step
    if step.step_type == "then":
        # Stop monitoring
        context._monitoring = False

        if context.monitored_trace is None:
            raise ValueError(
                'Scenario must at least contain one "when" step before any "then" step.'
            )


def sismic_after_step(context, step):
    if not hasattr(context, "interpreter"):
        return

    # "Given" triggers execution
    if step.step_type == "given":
        context.interpreter.execute()

    # "When" triggers monitored execution
    if step.step_type == "when":
        sismic_execute_interpreter(context)

    # Hook to enable debugging
    if (step.step_type == "then" and step.status == "failed"
            and context.config.userdata.get("debug_on_error")):
        try:
            import ipdb as pdb
        except ImportError:
            import pdb

        print("--------------------------------------------------------------")
        print("Dropping into (i)pdb.", end="\n\n")
        print("Variable context holds the current execution context of Behave")
        print("You can access the interpreter using context.interpreter, the")
        print("trace using context.trace and the monitored trace using")
        print("context.monitored_trace.")
        print("--------------------------------------------------------------")

        pdb.post_mortem(step.exc_traceback)


def sismic_application(context):
    setup_sismic_from_context(context)


# I'd love for these to be in async_support, but it must call setup_sismic_from_context
async def default_async_task(context):
    setup_sismic_from_context(context)
    async_task = context.config.userdata.get("async_task")
    try:
        if async_task:
            await async_task()
        await asyncio.sleep(0)
    except Exception as ex:
        print(ex)


def sismic_async_application(context):
    async_context = get_async_context(context)
    task = async_context.loop.create_task(default_async_task(context))
    async_context.tasks.append(task)


def sismic_execute_interpreter(context):
    macrosteps = context.interpreter.execute()

    if not context._monitoring:
        context._monitoring = True
        context.monitored_trace = []

    context.monitored_trace.extend(macrosteps)
    if testing_async(context):
        run_async_loop(context)
