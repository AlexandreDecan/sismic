import sys

from pyss import model
from .simulator import Simulator, MacroStep
from .evaluator import Evaluator


class StateChartTester:
    """
    A tester with given simulator (that simulates the statechart to test),
    a list of testers (simulators that runs tests) and a list of events (scenario).

    :param simulator: The simulator containing the statechart to test
    :param testers: A list of ``simulator.Simulator`` containing the tests
    :param events: A list of ``model.Event`` that represents a scenario
    """
    def __init__(self, simulator: Simulator, testers: list, events: list):
        self._simulator = simulator
        self._testers = testers
        self._events = events

        # Initialize testers with a start event
        event = model.Event('start')
        context = self._create_context()
        self._execute_tester(None, event, context)

        # Send the events to the simulator to be tested
        for event in self._events:
            self._simulator.send(event)

    def _create_context(self, step: MacroStep=None):
        """
        Return a context that will be passed to the tests. The context exposes several
        Boolean functions: entered(state_name), exited(state_name), active(state_name),
        processed(event_name), consumed(event_name), and a dictionary structure representing
        the current context of the simulator to test.
        :param step: A ``simulator.MacroStep`` instance from which the context is (optionally) build upon.
        :return: A context to be passed to the tests.
        """

        try:
            processed_event_name = step.transition.event.name
        except AttributeError:
            processed_event_name = None
        try:
            consumed_event_name = step.event.name
        except AttributeError:
            consumed_event_name = None

        return {
            'entered': lambda s: s in getattr(step, 'entered_states', []),
            'exited': lambda s: s in getattr(step, 'exited_states', []),
            'active': lambda s: s in self._simulator.configuration,
            'processed': lambda e: processed_event_name == e,
            'consumed': lambda e: consumed_event_name == e,
            'context': self._simulator.evaluator.context
        }

    def _execute_tester(self, step: MacroStep, event: model.Event, context: dict):
        """
        Send the event and update the context of the testers.
        """
        for tester in self._testers:
            tester.send(event)
            for key, value in context.items():
                tester.evaluator._context[key] = value
            try:
                tester.execute()
            except AssertionError as e:
                msg = ('An AssertionError occurred while testing "{simulator._statechart.name}".\n'
                       'Test statechart "{tester._statechart.name}" returned:\n'
                       '{exception.args}\n\n'
                       'Tester active configuration: {tester.configuration}\n'
                       'Active configuration: {simulator.configuration}\n'
                       'Step: {step}').format(simulator=self._simulator, tester=tester, step=step, exception=e)
                e.args = [msg]
                #print(msg, file=sys.stderr)
                raise

    def stop(self):
        """
        Stop the execution and raise an AssertionError if at least one tester is not in a final configuration.

        :raises AssertionError: if a tester is not in a final configuration
        """
        event = model.Event('stop')
        context = self._create_context()

        for tester in self._testers:
            self._execute_tester(None, event, context)
            assert not tester.running, '"{}" is not in a final configuration!\nConfiguration: {}'.format(tester._statechart.name, tester.configuration)

    def execute_once(self) -> MacroStep:
        """
        Call execute_once() on the underlying simulator, and consequently call execute() on the testers.

        :return: The ``simulator.MacroStep`` instance returned by the underlying call.
        :raises AssertionError: if simulation terminates and a tester is not in a final configuration
        """
        # Execute the simulator to be tested
        step = self._simulator.execute_once()

        if step:
            event = model.Event('step')
            context = self._create_context(step)

            # Execute testers
            self._execute_tester(step, event, context)
        else:
            # If the simulator stopped, testers should be not running
            self.stop()

        return step

    def execute(self, max_steps=-1) -> list:
        """
        Repeatedly calls ``self.execute_once()`` and return a list containing
        the returned values of ``self.execute_once()``.

        :param max_steps: An upper bound on the number steps that are computed and returned.
            Default is -1, no limit. Set to a positive integer to avoid infinite loops in the statechart simulation.
        :return: A list of ``MacroStep`` instances produced by the underlying simulator.
        :raises AssertionError: if simulation terminates and a tester is not in a final configuration
        """
        steps = []
        i = 0
        step = self.execute_once()
        while step:
            steps.append(step)
            i += 1
            if max_steps > 0 and i == max_steps:
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
    :param simulator_klass: An optional callable (eg. a class) that takes as input a ``model.StateChart`` instance
        and an optional ``evaluator.Evaluator`` instance, and return an instance of ``simulator.Simulator``
        (or anything that acts as such).
    """
    def __init__(self, statechart: model.StateChart, evaluator_klass=None, simulator_klass=None):
        self._statechart = statechart
        self._evaluator_klass = evaluator_klass
        self._simulator_klass = simulator_klass
        self._statechart_tests = []

    def add_test(self, statechart: model.StateChart, evaluator_klass=None, simulator_klass=None):
        """
        Add the given statechart as a test.

        :param statechart: A ``model.StateChart`` instance.
        :param evaluator_klass: An optional callable (eg. a class) that takes no input and return a
            ``evaluator.Evaluator`` instance that will be used to initialize the simulator.
        :param simulator_klass: An optional callable (eg. a class) that takes as input a ``model.StateChart`` instance
            and an optional ``evaluator.Evaluator`` instance, and return an instance of ``simulator.Simulator``
            (or anything that acts as such).
        """
        self._statechart_tests.append((statechart, evaluator_klass, simulator_klass))

    def build_tester(self, events: list) -> StateChartTester:
        """
        Build a ``StateChartTester`` from current configuration.

        :param events: A list of ``model.Events`` instances that serves as a scenario
        :return: A ``StateChartTester`` instance.
        """
        evaluator = self._evaluator_klass if self._evaluator_klass else None  # Explicit is better than implicit
        simulator_klass = self._simulator_klass if self._simulator_klass else Simulator
        simulator = simulator_klass(self._statechart, evaluator)

        testers = []
        for t_statechart, t_evaluator_klass, t_simulator_klass in self._statechart_tests:
            t_evaluator = t_evaluator_klass if t_evaluator_klass else None  # Explicit is better than implicit
            t_simulator_klass = t_simulator_klass if t_simulator_klass else Simulator
            t_simulator = t_simulator_klass(t_statechart, t_evaluator)
            testers.append(t_simulator)
        return StateChartTester(simulator, testers, events)

