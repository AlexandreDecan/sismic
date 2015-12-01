from pyss import statemachine
from pyss.evaluator import Evaluator, DummyEvaluator


class Step:
    def __init__(self, event: statemachine.Event, transition: statemachine.Transition,
               entered_states: list, exited_states: list):
        """
        Create a step. A step consider `event`, takes `transition` and results in a list
        of `entered_states` and a list of `exited_states`.
        Order in the two lists is REALLY important!
        :param event: Event or None in case of eventless transition
        :param transition: Transition or None if no matching transition
        :param entered_states: possibly empty list of entered states
        :param exited_states: possibly empty list of exited states
        """
        self.event = event
        self.transition = transition
        self.entered_states = entered_states
        self.exited_states = exited_states


class Simulator:
    def __init__(self, sm: statemachine.StateMachine, evaluator: Evaluator=None):
        """
        A simulator that interprets a state machine according to a specific semantic.
        :param sm: state machine to interpret
        :param evaluator: Code evaluator (optional)
        """
        self._evaluator = evaluator if evaluator else DummyEvaluator()
        self._sm = sm
        self._configuration = set()  # Set of active states
        self._events = []  # Event queue

    @property
    def configuration(self) -> list:
        return list(self._configuration)

    @property
    def events(self) -> list:
        return self._events

    def start(self):
        """
        Make this machine runnable:
         - Execute state machine initial code
         - Execute until a stable situation is reached.
        """
        # Initialize state machine
        if self._sm.execute:
            self._evaluator.execute_action(self._sm.execute)

        # Add initial state to configuration
        self._configuration.add(self._sm.initial)

        step = self._stabilize_step()
        while step:
            self.apply(step)

    @property
    def running(self) -> bool:
        """
        Return True iff state machine is running.
        """
        for state in self._sm.leaf_for(list(self._configuration)):
            if not isinstance(state, statemachine.FinalState):
                return True
        return False

    def fire_event(self, event: statemachine.Event):
        self._events.append(event)

    def actionable_transitions(self, event: statemachine.Event=None) -> list:
        """
        Return a list of transitions that can be enabled with respect to current
        configuration and given event. Should be called only when the state machine
        is stabilized.
        The resulting list is ordered by:
          1) eventless transitions first
          2) deepest states first
          :param event: Event to be considered, or None
        """
        # Order configuration by state depth
        ordered_configuration = sorted(self._configuration, key=lambda x: self._sm.depth_of(x), reverse=True)

        eventless_transitions = []
        eventfull_transitions = []

        for state in ordered_configuration:
            for transition in self._sm.states[state].transitions:
                # keep transitions with matching event, or eventless
                if transition.eventless or transition.event == event:
                    if transition.condition is None or self._evaluator.evaluate_condition(transition.condition, event):
                        if transition.eventless:
                            eventless_transitions.append(transition)
                        else:
                            eventfull_transitions.append(transition)
        return eventless_transitions + eventfull_transitions

    def _stabilize_step(self) -> Step:
        """
        Return a stabilization step, ie. a step that lead to a more stable situation
        for the current state machine (expand to initial state, expand to history state, etc.).
        :return: A Step instance or None if this state machine can not be stabilized
        """
        # Check if we are in a set of "stable" states
        leaves = self._sm.leaf_for(self._configuration)
        for leaf in leaves:
            leaf = self._sm.states[leaf]
            if isinstance(leaf, statemachine.HistoryState):
                states_to_enter = leaf.memory
                states_to_enter.sort(key=lambda x: self._sm.depth_of(x))
                return Step(None, None, states_to_enter, [leaf.name])
            elif isinstance(leaf, statemachine.OrthogonalState):
                return Step(None, None, leaf.children, [])
            elif isinstance(leaf, statemachine.CompoundState):
                return Step(None, None, [leaf.initial], [])

    def apply(self, step: Step):
        """
        Apply given Step on this state machine
        :param step: Step instance
        """
        entered_states = map(lambda s: self._sm.states[s], step.entered_states)
        exited_states = map(lambda s: self._sm.states[s], step.exited_states)

        for state in exited_states:
            # Execute exit action
            if isinstance(state, statemachine.ActionStateMixin):
                self._evaluator.execute_action(state.on_exit)

        # Deal with history: this only concerns compound states
        for state in filter(lambda s: isinstance(s, statemachine.CompoundState), exited_states):
            # Look for an HistoryState among its children
            for child_name in state.children:
                child = self._sm.states[child_name]
                if isinstance(child, statemachine.HistoryState):
                    if child.deep:
                        # This MUST contain at least one element!
                        active = self._configuration.intersection(self._sm.descendants_for(state.name))
                        assert len(active) >= 1
                        child.memory = list(active)
                    else:
                        # This MUST contain exactly one element!
                        active = self._configuration.intersection(state.children)
                        assert len(active) == 1
                        child.memory = list(active)

        # Remove states from configuration
        self._configuration = self._configuration.remove(step.entered_states)

        # Execute transition
        if step.transition.action:
            self._evaluator.execute_action(step.transition.action, step.transition.event)

        for state in entered_states:
            # Execute entry action
            if isinstance(state, statemachine.ActionStateMixin):
                self._evaluator.execute_action(state.on_entry)

        # Add state to configuration
        self._configuration = self._configuration.add(step.entered_states)

    def macrostep(self) -> list:
        """
        Perform a macro step, ie. a sequence of micro steps until a stable configuration is reached.
        Corresponds to the processing of exactly ONE transition.
        This method should return a list of (micro) Step instance.
        """
        raise NotImplementedError()

    def __repr__(self):
        return '{}[{}]'.format(self.__class__.__name__, ' '.join(self._configuration))

