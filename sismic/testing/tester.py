from sismic.stories import Story, Pause
from sismic.model import Event, Statechart, MacroStep
from sismic.interpreter import Interpreter
from sismic import exceptions

__all__ = ['ExecutionWatcher', 'teststory_from_trace']


def _teststory_from_macrostep(macrostep: MacroStep):
    story = Story()
    story.append(Event('step'))

    if macrostep.event:
        story.append(Event('consumed', consumed_event=macrostep.event))

    for microstep in macrostep.steps:
        for state in microstep.exited_states:
            story.append(Event('exited', exited_state=state))
        if microstep.transition:
            story.append(Event('processed', source_state=microstep.transition.source,
                               target_state=microstep.transition.target,
                               consumed_event=macrostep.event))
        for state in microstep.entered_states:
            story.append(Event('entered', entered_state=state))
    return story


class ExecutionWatcher:
    """
    This can be used to associate a statechart tester with a tested statechart.
    An instance of this class is built upon an *Interpreter* instance (the tested one).

    It provides a method, namely *watch_with* which takes a tester statechart
    (and a set of optional parameters that can be used to tune the interpreter that will be built upon this tester statechart)
    and returns the resulting *Interpreter* instance for this tester.

    If started (using *start), whenever something happens during the execution of the tested interpreter, events are automatically sent to every
    associated tester statecharts. Their internal clock are synchronized and, the context of the tested statechart is
    also exposed to the statechart testers, ie. if *x* is a variable in the context of a tested statechart, then
    *context.x* is dynamically exposed to every associated statechart tester.

    :param tested_interpreter: Interpreter to watch
    """
    def __init__(self, tested_interpreter: Interpreter):
        self._tested = tested_interpreter
        self._testers = []
        self._started = False

        self._tested_execute_once_function = tested_interpreter.execute_once

    class DynamicContext:
        def __init__(self, interpreter):
            self.__interpreter = interpreter

        def __getattr__(self, item):
            try:
                return self.__interpreter.context[item]
            except KeyError:
                raise AttributeError('Context has no attribute {}'.format(self, item))

        def __copy__(self):
            return None

    def watch_with(self, tester_statechart: Statechart, interpreter_klass=None, **kwargs):
        """
        Watch the execution of the tested interpreter with given tester statechart.

        *interpreter_klass* is a callable that accepts a *Statechart* instance, an *initial_context* parameter and
        any additional parameters provided to this method. This callable must return an *Interpreter* instance
        """
        interpreter_klass = interpreter_klass if interpreter_klass else Interpreter

        # Make context available
        context = kwargs.pop('initial_context', {})
        context['context'] = ExecutionWatcher.DynamicContext(self._tested)

        tester = interpreter_klass(tester_statechart, initial_context=context, **kwargs)
        self._testers.append(tester)

        return tester

    def start(self):
        """
        Send a *started* event to the tester statecharts, and starts watching the execution of
        the tested statechart.
        """
        if self._started:
            raise exceptions.ExecutionError('Cannot start an already started watcher!')

        self._started = True
        self._tested.execute_once = self.__execute_once

        for tester in self._testers:
            tester.time = self._tested.time
            tester.queue(Event('started')).execute()

    def stop(self):
        """
        Send a *stopped* event to the tester statecharts, and stops watching the execution of the
        tested statechart.
        """
        if not self._started:
            raise exceptions.ExecutionError('Cannot stop a stopped watcher!')

        for tester in self._testers:
            tester.time = self._tested.time
            tester.queue(Event('stopped')).execute()

        self._started = False
        self._tested.execute_once = self._tested_execute_once_function

    def __execute_once(self, *args, **kwargs):
        # Execute tester
        time = self._tested.time
        step = self._tested_execute_once_function(*args, **kwargs)

        story = _teststory_from_macrostep(step) if step else Story()

        # Send to testers
        for tester in self._testers:
            tester.time = time
            story.tell(tester)

        return step


def teststory_from_trace(trace: list) -> Story:
    """
    Return a test story based on the given *trace*, a list of macro steps.
    See documentation to see which are the events that are generated.

    Notice that this function adds a *pause* if there is any delay between pairs of consecutive steps.

    The story does follow the interpretation order:

    1. an event is possibly consumed
    2. For each transition

       a. states are exited
       b. transition is processed
       c. states are entered
       d. statechart is stabilized (some states are exited and/or entered)

    :param trace: a list of *MacroStep* instances
    :return: A story
    """
    story = Story()
    story.append(Event('started'))
    time = 0

    for macrostep in trace:
        if macrostep.time > time:
            story.append(Pause(macrostep.time - time))
        story.extend(_teststory_from_macrostep(macrostep))
        time = macrostep.time

    story.append(Event('stopped'))
    return story
