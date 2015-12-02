from collections import deque
from pyss import statemachine
from pyss.evaluator import Evaluator, DummyEvaluator


class MicroStep:
    def __init__(self, event: statemachine.Event=None, transition: statemachine.Transition=None,
                 entered_states: list=None, exited_states: list=None):
        """
        Create a micro step. A step consider `event`, takes `transition` and results in a list
        of `entered_states` and a list of `exited_states`.
        Order in the two lists is REALLY important!
        :param event: Event or None in case of eventless transition
        :param transition: Transition or None if no processed transition
        :param entered_states: possibly empty list of entered states
        :param exited_states: possibly empty list of exited states
        """
        self.event = event
        self.transition = transition
        self.entered_states = entered_states if entered_states else []
        self.exited_states = exited_states if exited_states else []

    def __repr__(self):
        return 'MicroStep({}, {}, {}, {})'.format(self.event, self.transition, self.entered_states, self.exited_states)


class MacroStep:
    def __init__(self, main_step:MicroStep, micro_steps: list):
        self.main = main_step
        self.micro_steps = micro_steps

    @property
    def event(self) -> statemachine.Event:
        return self.main.event

    @property
    def transition(self) -> statemachine.Transition:
        return self.main.transition

    @property
    def entered_states(self) -> list:
        states = self.main.entered_states
        for step in self.micro_steps:
            states += step.entered_states
        return states

    @property
    def exited_states(self) -> list:
        states = self.main.exited_states
        for step in self.micro_steps:
            states += step.exited_states
        return states

    def __repr__(self):
        return 'MacroStep({}, {}, {}, {})'.format(self.event, self.transition, self.entered_states, self.exited_states)


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
        self._events = deque()  # Events queue
        self._started = False

    @property
    def configuration(self) -> list:
        return list(self._configuration)

    def send(self, event_or_list):
        """
        Send an event to the state machine. Will be placed in the queue
        :param event: Event to pass, or an iterable of events
        """
        if hasattr(event_or_list, '__iter__'):
            for event in event_or_list:
                self._events.append(event)
        else:
            self._events.append(event_or_list)

    def start(self) -> list:
        """
        Make this machine runnable:
         - Execute state machine initial code
         - Execute until a stable situation is reached.
        :return A (possibly empty) list of executed MicroStep.
        """
        if self._started:
            return []

        # Initialize state machine
        if self._sm.on_entry:
            self._evaluator.execute_action(self._sm.on_entry)

        # Initial step and stabilization
        step = MicroStep(entered_states=[self._sm.initial])
        self._execute_step(step)

        self._started = True
        return [step] + self._stabilize()

    @property
    def running(self) -> bool:
        """
        Return True iff state machine is running.
        """
        if not self._started:
            return False

        for state in self._sm.leaf_for(list(self._configuration)):
            if not isinstance(self._sm.states[state], statemachine.FinalState):
                return True
        return False

    def __iter__(self):
        """
        Return an iterator for current execution.
        It corresponds to successive call to execute().
        You should start() this simulator first!
        Event can be added using iterator.send().
        """
        self.start()
        return self

    def __next__(self):
        steps = self.execute()
        if steps:
            return steps
        else:
            raise StopIteration

    def execute(self) -> MacroStep:
        """
        Execute an eventless transition or an evented transition and put the
        state machine in a stable state.
        :return: A MacroStep instance
        """
        if not self._started:
            raise Exception('You should start the simulator before running it')

        # Try eventless transitions
        main_step = self._transition_step(event=None)  # Explicit is better than implicit

        # If there is no eventless transition, and there exists at least one event to process
        if not main_step and len(self._events) > 0:
            event = self._events.popleft()
            main_step = self._transition_step(event=event)

            # If this event can not be processed, discard it
            if not main_step:
                main_step = MicroStep(event=event)

        if not main_step:  # No actionable eventless nor evented transition
            return None
        else:
            self._execute_step(main_step)
            return MacroStep(main_step, self._stabilize())

    def _actionable_transitions(self, event: statemachine.Event=None) -> list:
        """
        Return a list of transitions that can be actioned wrt.
        the current configuration. The list is ordered: deepest states first.
        :param event: Event to considered or None for eventless transitions
        :return: A (possibly empty) ordered list of Transition instances
        """
        transitions = []
        for transition in self._sm.transitions:
            if transition.event != event:
                continue
            if transition.from_state not in self._configuration:
                continue
            if transition.guard is None or self._evaluator.evaluate_condition(transition.guard, event):
                transitions.append(transition)

        # Order by deepest first
        return sorted(transitions, key=lambda t: self._sm.depth_of(t.from_state), reverse=True)

    def _stabilize_step(self) -> MicroStep:
        """
        Return a stabilization step, ie. a step that lead to a more stable situation
        for the current state machine (expand to initial state, expand to history state, etc.).
        :return: A MicroStep instance or None if this state machine can not be stabilized
        """
        # Check if we are in a set of "stable" states
        leaves = self._sm.leaf_for(list(self._configuration))
        for leaf in leaves:
            leaf = self._sm.states[leaf]
            if isinstance(leaf, statemachine.HistoryState):
                states_to_enter = leaf.memory
                states_to_enter.sort(key=lambda x: self._sm.depth_of(x))
                return MicroStep(entered_states=states_to_enter, exited_states=[leaf.name])
            elif isinstance(leaf, statemachine.OrthogonalState):
                return MicroStep(entered_states=leaf.children)
            elif isinstance(leaf, statemachine.CompoundState) and leaf.initial:
                return MicroStep(entered_states=[leaf.initial])

    def _stabilize(self) -> list:
        """
        Compute, apply and return stabilization steps.
        :return: A list of MicroStep instances
        """
        # Stabilization
        steps = []
        step = self._stabilize_step()
        while step:
            steps.append(step)
            self._execute_step(step)
            step = self._stabilize_step()
        return steps

    def _transition_step(self, event: statemachine.Event=None) -> MicroStep:
        """
        Return the MicroStep (if any) associated with the appropriate transition matching
        given event (or eventless transition if event is None).
        :param event: Event to consider (or None)
        :return: A MicroStep instance or None
        """
        transitions = self._actionable_transitions(event)

        if len(transitions) == 0:
            return None

        transition = transitions[0]
        transition_depth = self._sm.depth_of(transition.from_state)
        for other_transition in transitions:
            if not(other_transition is transition) and self._sm.depth_of(other_transition.from_state) == transition_depth:
                raise Warning('More than one transition can be processed: non-determinism!' +
                              '\nConfiguration is {}\nEvent is {}\nTransitions are:{}\n'
                              .format(self.configuration, event, transitions))

        # Internal transition
        if transition.to_state is None:
            return MicroStep(event, transition, [], [])

        lca = self._sm.least_common_ancestor(transition.from_state, transition.to_state)
        from_ancestors = self._sm.ancestors_for(transition.from_state)
        to_ancestors = self._sm.ancestors_for(transition.to_state)

        exited_states = [transition.from_state]
        for state in from_ancestors:
            if state == lca:
                break
            exited_states.append(state)

        entered_states = [transition.to_state]
        for state in to_ancestors:
            if state == lca:
                break
            entered_states.insert(0, state)

        return MicroStep(event, transition, entered_states, exited_states)

    def _execute_step(self, step: MicroStep):
        """
        Apply given MicroStep on this state machine
        :param step: MicroStep instance
        """
        entered_states = map(lambda s: self._sm.states[s], step.entered_states)
        exited_states = map(lambda s: self._sm.states[s], step.exited_states)

        for state in exited_states:
            # Execute exit action
            if isinstance(state, statemachine.ActionStateMixin) and state.on_exit:
                for event in self._evaluator.execute_action(state.on_exit):
                    # Internal event
                    self._events.appendleft(event)

        # Deal with history: this only concerns compound states
        # TODO: History states are currently NOT tested!!
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
        self._configuration = self._configuration.difference(step.exited_states)

        # Execute transition
        if step.transition and step.transition.action:
            self._evaluator.execute_action(step.transition.action, step.event)

        for state in entered_states:
            # Execute entry action
            if isinstance(state, statemachine.ActionStateMixin) and state.on_entry:
                for event in self._evaluator.execute_action(state.on_entry):
                    # Internal event
                    self._events.appendleft(event)

        # Add state to configuration
        self._configuration = self._configuration.union(step.entered_states)

    def __repr__(self):
        return '{}[{}]'.format(self.__class__.__name__, ' '.join(self._configuration))

