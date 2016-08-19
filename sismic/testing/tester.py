from sismic.stories import Story, Pause
from sismic.model import Event, Statechart, MacroStep
from sismic.interpreter import Interpreter
from sismic import exceptions

from typing import List, Callable

__all__ = ['ExecutionWatcher', 'teststory_from_trace']


def _teststory_from_macrostep(macrostep: MacroStep) -> Story:
    story = Story()
    story.append(Event('step started'))

    if macrostep.event:
        story.append(Event('event consumed', event=macrostep.event))

    for microstep in macrostep.steps:
        for state in microstep.exited_states:
            story.append(Event('state exited', state=state))
        if microstep.transition:
            story.append(Event('transition processed', source=microstep.transition.source,
                               target=microstep.transition.target,
                               event=macrostep.event))
        for state in microstep.entered_states:
            story.append(Event('state entered', state=state))
        for event in microstep.sent_events:
            story.append(Event('event sent', event=event))

    story.append(Event('step ended'))
    return story


class ExecutionWatcher:
    """
    This can be used to associate a property statechart with a statechart under test.
    An instance of this class is built upon an *Interpreter* instance (the tested one).

    It provides a method, namely *watch_with* which takes a property statechart
    (and a set of optional parameters that can be used to tune the interpreter that will be built upon this
    property statechart) and returns the resulting *Interpreter* instance for this tester.

    If started (using *start*), whenever something happens during the execution of the interpreter under test,
    events are automatically sent to every associated statechart properties.
    Their internal clock are synchronized, and the context of the statechart under test is
    also exposed to the property statechart, ie. if *x* is a variable in the context of a statechart under test, then
    *context.x* is dynamically exposed to every associated property statechart.

    :param tested_interpreter: Interpreter to watch
    """
    def __init__(self, tested_interpreter: Interpreter) -> None:
        self._tested = tested_interpreter
        self._testers = []  # type: List[Interpreter]
        self._failsfast = []  # type: List[bool]
        self._started = False

        self._tested_execute_once_function = tested_interpreter.execute_once

    class DynamicContext:
        def __init__(self, interpreter: Interpreter) -> None:
            self.__interpreter = interpreter

        def __getattr__(self, item):
            try:
                return self.__interpreter.context[item]
            except KeyError:
                raise AttributeError('Property statechart\'s context has no attribute {}'.format(item))

        def __copy__(self):
            return None

    def watch_with(self, property_statechart: Statechart,
                   fails_fast: bool=False,
                   interpreter_klass: Callable[..., Interpreter]=Interpreter,
                   **kwargs) -> Interpreter:
        """
        Watch the execution of the tested interpreter with given sproperty statechart.

        *interpreter_klass* is a callable that accepts a *Statechart* instance, an *initial_context* parameter and
        any additional parameters provided to this method. This callable must return an *Interpreter* instance

        :param property_statechart: a property statechart (instance of *Statechart*)
        :param fails_fast: If True (default is False), the execution of the statechart under test will raise an AssertionError
            as soon as given property statechart reaches a final state.
        :param interpreter_klass: a callable that accepts a *Statechart* instance, an *initial_context* and any
            additional (optional) parameters provided to this method.
        :return: the interpreter instance that wraps given property statechart.
        """
        # Make context available
        context = kwargs.pop('initial_context', {})
        context['context'] = ExecutionWatcher.DynamicContext(self._tested)

        tester = interpreter_klass(property_statechart, initial_context=context, **kwargs)
        self._testers.append(tester)
        self._failsfast.append(fails_fast)

        return tester

    def start(self) -> None:
        """
        Send a *started* event to the statechart properties, and starts watching the execution of
        the statechart under test.
        """
        if self._started:
            raise exceptions.ExecutionError('Cannot start an already started watcher!')

        self._started = True
        self._tested.execute_once = self.__execute_once  # type: ignore

        for tester in self._testers:
            tester.time = self._tested.time
            tester.queue(Event('execution started')).execute()

    def stop(self) -> None:
        """
        Send a *stopped* event to the statechart properties, and stops watching the execution of the
        statechart under test.
        """
        if not self._started:
            raise exceptions.ExecutionError('Cannot stop a stopped watcher!')

        for tester in self._testers:
            tester.time = self._tested.time
            tester.queue(Event('execution stopped')).execute()

        self._started = False
        self._tested.execute_once = self._tested_execute_once_function  # type: ignore

    def __execute_once(self, *args, **kwargs) -> MacroStep:
        # Execute tester
        time = self._tested.time
        step = self._tested_execute_once_function(*args, **kwargs)  # type: ignore

        story = _teststory_from_macrostep(step) if step else Story()

        # Send to testers
        for fails_fast, tester in zip(self._failsfast, self._testers):
            tester.time = time
            story.tell(tester)
            if fails_fast and tester.final:
                raise AssertionError('Property statechart "{}" is in a final state'.format(tester.statechart.name))

        return step


def teststory_from_trace(trace: List[MacroStep]) -> Story:
    """
    Return a test story based on the given *trace*, a list of macro steps.
    See documentation to see which are the events that are generated.

    Notice that this function adds a *pause* if there is any delay between pairs of consecutive steps.

    :param trace: a list of *MacroStep* instances
    :return: A story
    """
    story = Story()
    story.append(Event('execution started'))
    time = 0  # type: float

    for macrostep in trace:
        if macrostep.time > time:
            story.append(Pause(macrostep.time - time))
        story.extend(_teststory_from_macrostep(macrostep))
        time = macrostep.time

    story.append(Event('execution stopped'))
    return story
