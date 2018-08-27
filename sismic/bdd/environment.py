from sismic.helpers import log_trace


def before_scenario(context, scenario):
    # Create interpreter
    statechart = context.config.userdata.get('statechart')
    interpreter_klass = context.config.userdata.get('interpreter_klass')
    context.interpreter = interpreter_klass(statechart)

    # Log trace
    context.trace = log_trace(context.interpreter)
    context._monitoring = False
    context.monitored_trace = None

    # Bind property statecharts
    for property_statechart in context.config.userdata.get('property_statecharts'):
        context.interpreter.bind_property_statechart(property_statechart, interpreter_klass=interpreter_klass)


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

        context.monitored_trace.extend(macrosteps)

    # Hook to enable debugging
    if step.step_type == 'then' and step.status == 'failed' and context.config.userdata.get('debug_on_error'):
        try:
            import ipdb as pdb
        except ImportError:
            import pdb

        print('--------------------------------------------------------------')
        print('Dropping into (i)pdb.', end='\n\n')
        print('Variable context holds the current execution context of Behave')
        print('You can access the interpreter using context.interpreter, the')
        print('trace using context.trace and the monitored trace using')
        print('context.monitored_trace.')
        print('--------------------------------------------------------------')

        pdb.post_mortem(step.exc_traceback)