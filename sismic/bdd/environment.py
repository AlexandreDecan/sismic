from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
from sismic.helpers import log_trace


def before_scenario(context, scenario):
    # Get config
    statechart = context.config.userdata.get('statechart', None)
    properties = context.config.userdata.get('properties', None)

    # Load statechart
    assert statechart is not None

    with open(statechart) as fp:
        context.interpreter = Interpreter(import_from_yaml(fp))

    # Log trace
    context.trace = log_trace(context.interpreter)
    context._monitoring = False
    context.monitored_trace = None

    # Load properties
    if properties is not None:
        for property_statechart in properties.split(';'):
            with open(property_statechart) as fp:
                context.interpreter.bind_property_statechart(import_from_yaml(fp))


def before_step(context, step):
    # "Then" steps must at least follow one "when" step
    if step.step_type == 'then':
        # Stop monitoring
        context._monitoring = False

        if context.monitored_trace is None:
            raise ValueError('Scenario must at least contain one "when" step before any "then" step.')


def after_step(context, step):
    # "Given" triggers execution
    if step.step_type == 'given':
        context.interpreter.execute()

    # "When" triggers monitored execution
    if step.step_type == 'when':
        macrosteps = context.interpreter.execute()

        if not context._monitoring:
            context._monitoring = True
            context.monitored_trace = []

        if macrosteps is not None:
            context.monitored_trace.extend(macrosteps)

    # Hook to enable debugging
    if step.step_type == 'then' and step.status == 'failed' and context.config.userdata.get('debug-on-error', None) == 'True':
        try:
            import ipdb as pdb
        except ImportError:
            import pdb

        print('--------------------------------------------------------------')
        print('Dropping into (i)pdb.')
        print('Variable context holds the current execution context of Behave')
        print('You can access the interpreter using context.interpreter, and\nthe trace using context.trace')
        print('--------------------------------------------------------------')

        pdb.post_mortem(step.exc_traceback)