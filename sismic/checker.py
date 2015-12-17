from sismic import model
from .model import Event, StateChart
from .interpreter import Interpreter, MacroStep

from collections import namedtuple


TestedContext = namedtuple('TestedContext', ['entered', 'exited', 'active', 'processed', 'consumed', 'context'])


class StateChartTester:
    """
    A tester with given interpreter (that interprets the statechart to test),
    a list of testers (interpreters that runs tests) and a list of events (scenario).

    :param interpreter: The interpreter containing the statechart to test
    :param testers: A list of ``Interpreter`` containing the tests
    :param events: A list of ``Event`` that represents a scenario
    """
    def __init__(self, interpreter: Interpreter, testers: list, events: list):
        self._interpreter = interpreter
        self._testers = testers
        self._events = events

        # Initialize testers with a start event
        event = Event('start')
        context = self._create_context()
        self._execute_tester(MacroStep([]), event, context)

        # Send the events to the simulator to be tested
        for event in self._events:
            self._interpreter.send(event)

    def _create_context(self, step: MacroStep=None):
        """
        Return a context that will be passed to the tests. The context exposes several
        Boolean functions: entered(state_name), exited(state_name), active(state_name),
        processed(event_name), consumed(event_name), and a dictionary structure representing
        the current context of the simulator to test.
        :param step: A ``MacroStep`` instance from which the context is (optionally) build upon.
        :return: A context to be passed to the tests.
        """

        try:
            processed_event_name = step.transitions[0].event.name
        except (AttributeError, IndexError):
            processed_event_name = None
        try:
            consumed_event_name = step.event.name
        except AttributeError:
            consumed_event_name = None

        return TestedContext(
            entered=lambda s: s in getattr(step, 'entered_states', []),
            exited=lambda s: s in getattr(step, 'exited_states', []),
            active=lambda s: s in self._interpreter.configuration,
            processed=lambda e: processed_event_name == e,
            consumed=lambda e: consumed_event_name == e,
            context=self._interpreter.evaluator.context)

    def _execute_tester(self, step: MacroStep, event: Event, context: TestedContext):
        """
        Send the event and update the context of the testers.
        """
        for tester in self._testers:
            tester.send(event)
            tester.evaluator._context['step'] = context
            try:
                tester.execute()
            except AssertionError as e:
                raise model.ConditionFailed(configuration=self._interpreter.configuration, step=step, obj=tester,
                                            context=tester.evaluator._context) from e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def stop(self):
        """
        Stop the execution of the testers.
        """
        event = Event('stop')
        context = self._create_context()
        self._execute_tester(MacroStep([]), event, context)

    def execute_once(self) -> MacroStep:
        """
        Call execute_once() on the underlying interpreter, and consequently call execute() on the testers.

        :return: The ``interpreter.MacroStep`` instance returned by the underlying call.
        """
        # Execute the simulator to be tested
        step = self._interpreter.execute_once()

        if step:
            event = Event('step')
            context = self._create_context(step)

            # Execute testers
            self._execute_tester(step, event, context)

        return step

    def execute(self, max_steps=-1) -> list:
        """
        Repeatedly calls ``self.execute_once()`` and return a list containing
        the returned values of ``self.execute_once()``.

        :param max_steps: An upper bound on the number steps that are computed and returned.
            Default is -1, no limit. Set to a positive integer to avoid infinite loops in the statechart execution.
        :return: A list of ``MacroStep`` instances produced by the underlying interpreter.
        """
        steps = []
        i = 0
        step = self.execute_once()
        while step:
            steps.append(step)
            i += 1
            if 0 < max_steps == i:
                break
            step = self.execute_once()
        return steps


class TesterConfiguration:
    """
    A tester configuration mainly serves as a data class to prepare tests.
    Such a configuration remembers which is the statechart to test, using which evaluator and
    which simulator.

    :param statechart: A ``model.StateChart`` instance
    :param evaluator_klass: An optional callable (eg. a class) that takes no input and return a
        ``evaluator.Evaluator`` instance that will be used to initialize the simulator.
    :param interpreter_klass: An optional callable (eg. a class) that takes as input a ``model.StateChart`` instance
        and an optional ``evaluator.Evaluator`` instance, and return an instance of ``simulator.Simulator``
        (or anything that acts as such).
    """
    def __init__(self, statechart: StateChart, evaluator_klass=None, interpreter_klass=None):
        self._statechart = statechart
        self._evaluator_klass = evaluator_klass
        self._interpreter_klass = interpreter_klass
        self._statechart_tests = []

    def add_test(self, statechart: StateChart, evaluator_klass=None, interpreter_klass=None):
        """
        Add the given statechart as a test.

        :param statechart: A ``model.StateChart`` instance.
        :param evaluator_klass: An optional callable (eg. a class) that takes no input and return a
            ``evaluator.Evaluator`` instance that will be used to initialize the simulator.
        :param interpreter_klass: An optional callable (eg. a class) that takes as input a ``model.StateChart`` instance
            and an optional ``evaluator.Evaluator`` instance, and return an instance of ``interpreter.Interpreter``
            (or anything that acts as such).
        """
        self._statechart_tests.append((statechart, evaluator_klass, interpreter_klass))

    def build_tester(self, events: list) -> StateChartTester:
        """
        Build a ``StateChartTester`` from current configuration.

        :param events: A list of ``model.Events`` instances that serves as a scenario
        :return: A ``StateChartTester`` instance.
        """
        evaluator = self._evaluator_klass if self._evaluator_klass else None  # Explicit is better than implicit
        interpreter_klass = self._interpreter_klass if self._interpreter_klass else Interpreter
        interpreter = interpreter_klass(self._statechart, evaluator)

        testers = []
        for t_statechart, t_evaluator_klass, t_interpreter_klass in self._statechart_tests:
            t_evaluator = t_evaluator_klass if t_evaluator_klass else None  # Explicit is better than implicit
            t_interpreter_klass = t_interpreter_klass if t_interpreter_klass else Interpreter
            t_interpreter = t_interpreter_klass(t_statechart, t_evaluator)
            testers.append(t_interpreter)
        return StateChartTester(interpreter, testers, events)

