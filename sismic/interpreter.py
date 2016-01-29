from collections import deque
from itertools import combinations

from sismic import model
from sismic.exceptions import NonDeterminismError, ConflictingTransitionsError
from sismic.exceptions import InvariantError, PreconditionError, PostconditionError
from sismic.code import PythonEvaluator

__all__ = ['Interpreter', 'run_in_background']


class Interpreter:
    """
    A discrete interpreter that executes a statechart according to a semantic close to SCXML.

    :param statechart: statechart to interpret
    :param evaluator_klass: An optional callable (eg. a class) that takes an interpreter and an optional initial
        context as input and return an *Evaluator* instance that will be used to initialize the interpreter.
        By default, the *PythonEvaluator* class will be used.
    :param initial_context: an optional initial context that will be provided to the evaluator.
        By default, an empty context is provided
    :param initial_time: can be used to defined the initial value of the internal clock (see *time*).
    :param ignore_contract: set to True to ignore contract checking during the execution.
    """

    def __init__(self, statechart: model.Statechart, evaluator_klass=None,
                 initial_context: dict=None, initial_time: int=0, ignore_contract: bool=False):
        # Internal variables
        self._ignore_contract = ignore_contract
        self._initial_time = initial_time
        self._statechart = statechart

        self._time = initial_time  # Internal clock
        self._memory = {}  # History states memory
        self._configuration = set()  # Set of active states
        self._events = deque()  # Events queue
        self._trace = []  # A list of micro steps
        self._bound = []  # List of bound event callbacks

        # Evaluator
        self._evaluator = (evaluator_klass if evaluator_klass else PythonEvaluator)(self, initial_context)
        self._evaluator.execute_statechart(statechart)

        # Initial step and stabilization
        step = model.MicroStep(entered_states=[self._statechart.root])
        self._execute_step(step)
        self._trace.append(model.MacroStep(time=self.time, steps=[step] + self.__stabilize()))

    @property
    def time(self) -> int:
        """
        Time value (in seconds) for the internal clock
        """
        return self._time

    @time.setter
    def time(self, value):
        """
        Set the time of the internal clock
        :param value: time value (in seconds)
        """
        self._time = value

    @property
    def configuration(self) -> list:
        """
        List of active states names, ordered by depth. Ties are broken according to the lexicographic order
        on the state name.
        """
        return sorted(self._configuration, key=lambda s: (self._statechart.depth_for(s), s))

    @property
    def context(self) -> dict:
        """
        The context of execution.
        """
        return self._evaluator.context

    @property
    def final(self) -> bool:
        """
        Boolean indicating whether this interpreter is in a final configuration.
        """
        return len(self._configuration) == 0

    @property
    def trace(self):
        """
        The list of executed macro steps.
        """
        return self._trace

    @property
    def statechart(self):
        """
        Embedded statechart
        """
        return self._statechart

    def bind(self, interpreter_or_callable):
        """
        Bind an interpreter or a callable to the current interpreter.
        Each time an internal event is sent by this interpreter, any bound object will be called
        with the same event. If *interpreter_or_callable* is an *Interpreter* instance,  its *queue* method is called.
        This is, if *i1* and *i2* are interpreters, *i1.bind(i2)* is equivalent to *i1.bind(i2.queue)*.

        :param interpreter_or_callable: interpreter or callable to bind
        :return: *self* so it can be chained
        """
        if isinstance(interpreter_or_callable, Interpreter):
            bound_callable = interpreter_or_callable.queue
        else:
            bound_callable = interpreter_or_callable

        self._bound.append(bound_callable)
        return self

    def queue(self, event: model.Event):
        """
        Queue an event to the interpreter.
        Internal events are propagated to bound callables (see *bind* method).

        :param event: an *Event* or *InternalEvent* instance. If internal, the event is
            prepended to the events queue and propagated to bound interpreters or callables.
        :return: *self* so it can be chained.
        """
        if isinstance(event, model.InternalEvent):
            self._events.appendleft(event)
            external_event = model.Event(event.name, **event.data)
            for bound_callable in self._bound:
                bound_callable(external_event)
        elif isinstance(event, model.Event):
            self._events.append(event)
        else:
            raise ValueError('{} is not an Event instance'.format(event))
        return self

    def execute(self, max_steps: int=-1) -> list:
        """
        Repeatedly calls *execute_once* and return a list containing
        the returned values of *execute_once*.

        Notice that this does NOT return an iterator but computes the whole list first
        before returning it.

        :param max_steps: An upper bound on the number steps that are computed and returned.
            Default is -1, no limit. Set to a positive integer to avoid infinite loops
            in the statechart execution.
        :return: A list of *MacroStep* instances
        """
        returned_steps = []
        i = 0
        macro_step = self.execute_once()
        while macro_step:
            returned_steps.append(macro_step)
            i += 1
            if 0 < max_steps == i:
                break
            macro_step = self.execute_once()
        return returned_steps

    def execute_once(self) -> model.MacroStep:
        """
        Processes a transition based on the oldest queued event (or no event if an eventless transition
        can be processed), and stabilizes the interpreter in a stable situation (ie. processes initial states,
        history states, etc.). When multiple transitions are selected, they are atomically processed:
        states are exited, transition is processed, states are entered, statechart is stabilized and only
        after that, the next transition is processed.

        :return: a macro step or *None* if nothing happened
        """
        # Eventless transitions first
        event = None
        transitions = self._select_eventless_transitions()

        if len(transitions) == 0:
            # Consumes event if any
            if len(self._events) > 0:
                event = self._events.popleft()  # consumes event
                transitions = self._select_transitions(event)
                # If the event can not be processed, discard it
                if len(transitions) == 0:
                    macrostep = model.MacroStep(time=self.time, steps=[model.MicroStep(event=event)])
                    # Update trace
                    self._trace.append(macrostep)
                    return macrostep
            else:
                return None  # No step to do!

        transitions = self._sort_transitions(transitions)

        # Compute and execute the steps for the transitions
        returned_steps = []
        steps = self._compute_transitions_steps(event, transitions)
        for step in steps:
            self._execute_step(step)
            returned_steps.append(step)
            for stabilization_step in self.__stabilize():
                returned_steps.append(stabilization_step)

        macro_step = model.MacroStep(time=self.time, steps=returned_steps)

        # Check state invariants
        for name in self._configuration:
            state = self._statechart.state_for(name)
            self.__evaluate_contract_conditions(state, 'invariants', macro_step)

        # Update trace
        self._trace.append(macro_step)
        return macro_step

    def _select_eventless_transitions(self) -> list:
        """
        Return a list of eventless transitions that can be triggered.

        :return: a list of *Transition* instances
        """
        return self._select_transitions(event=None)

    def _select_transitions(self, event: model.Event=None) -> list:
        """
        Return a list of transitions that can be triggered according to the given event, or eventless
        transition if *event* is None.
        Transitions are kept according to a inner-first/source-state semantic.
        :param event: event to consider
        :return: a list of *Transition* instances
        """
        transitions = set()

        # Retrieve the firable transitions for all active state
        for transition in self._statechart.transitions:
            if (transition.event == getattr(event, 'name', None) and transition.source in self._configuration and
                    (transition.guard is None or self._evaluator.evaluate_guard(transition, event))):
                transitions.add(transition)

        # inner-first/source-state
        removed_transitions = set()
        for transition in transitions:
            source_state_descendants = self._statechart.descendants_for(transition.source)
            for other_transition in transitions:
                if other_transition.source in source_state_descendants:
                    removed_transitions.add(transition)
                    break

        return transitions.difference(removed_transitions)

    def _sort_transitions(self, transitions: list) -> list:
        """
        Given a list of triggered transitions, return a list of transitions in an order that represents
        the order in which they have to be processed.

        :param transitions: a list of *Transition* instances
        :return: an ordered list of *Transition* instances
        :raise ExecutionError: In case of non-determinism (*NonDeterminismError*) or conflicting
            transitions (*ConflictingTransitionsError*).
        """
        if len(transitions) > 1:
            # If more than one transition, we check (1) they are from separate regions and (2) they do not conflict
            # Two transitions conflict if one of them leaves the parallel state
            for t1, t2 in combinations(transitions, 2):
                # Check (1)
                lca = self._statechart.least_common_ancestor(t1.source, t2.source)
                lca_state = self._statechart.state_for(lca)

                # Their LCA must be an orthogonal state!
                if not isinstance(lca_state, model.OrthogonalState):
                    raise NonDeterminismError(
                        'Non-determinist choice between transitions {t1} and {t2}'
                        '\nConfiguration is {c}\nEvent is {e}\nTransitions are:{t}\n'
                        .format(c=self.configuration, e=t1.event, t=transitions, t1=t1, t2=t2)
                    )

                # Check (2)
                # This check must be done wrt. to LCA, as the combination of from_states could
                # come from nested parallel regions!
                for transition in [t1, t2]:
                    last_before_lca = transition.source
                    for state in self._statechart.ancestors_for(transition.source):
                        if state == lca:
                            break
                        last_before_lca = state
                    # Target must be a descendant (or self) of this state
                    if (transition.target and
                            (transition.target not in
                             [last_before_lca] + self._statechart.descendants_for(last_before_lca))):
                        raise ConflictingTransitionsError(
                            'Conflicting transitions: {t1} and {t2}'
                            '\nConfiguration is {c}\nEvent is {e}\nTransitions are:{t}\n'
                            .format(c=self.configuration, e=t1.event, t=transitions, t1=t1, t2=t2)
                        )

            # Define an arbitrary order based on the depth and the name of source states.
            transitions = sorted(transitions, key=lambda t: (-self._statechart.depth_for(t.source), t.source))

        return transitions

    def _compute_transitions_steps(self, event: model.Event, transitions: list) -> list:
        """
        Return a (possibly empty) list of micro steps. Each micro step corresponds to the process of a transition
        matching given event.

        :param event: the event to consider, if any
        :param transitions: the transitions that should be processed
        :return: a list of micro steps.
        """
        returned_steps = []
        for transition in transitions:
            # Internal transition
            if transition.target is None:
                returned_steps.append(model.MicroStep(event, transition, [], []))
                continue

            lca = self._statechart.least_common_ancestor(transition.source, transition.target)
            from_ancestors = self._statechart.ancestors_for(transition.source)
            to_ancestors = self._statechart.ancestors_for(transition.target)

            # Exited states
            exited_states = []

            # last_before_lca is the "highest" ancestor or from_state that is a child of LCA
            last_before_lca = transition.source
            for state in from_ancestors:
                if state == lca:
                    break
                last_before_lca = state

            # Take all the descendants of this state and list the ones that are active
            for descendant in self._statechart.descendants_for(last_before_lca)[::-1]:  # Mind the reversed order!
                # Only leave states that are currently active
                if descendant in self._configuration:
                    exited_states.append(descendant)

            # Add last_before_lca as it is a child of LCA that must be exited
            if last_before_lca in self._configuration:
                exited_states.append(last_before_lca)

            # Entered states
            entered_states = [transition.target]
            for state in to_ancestors:
                if state == lca:
                    break
                entered_states.insert(0, state)

            returned_steps.append(model.MicroStep(event, transition, entered_states, exited_states))

        return returned_steps

    def _compute_stabilization_step(self) -> model.MicroStep:
        """
        Return a stabilization step, ie. a step that lead to a more stable situation
        for the current statechart. Stabilization means:

         - Enter the initial state of a compound state with no active child
         - Enter the memory of a history state
         - Enter the children of an orthogonal state with no active child
         - Exit active states if all "deepest" (leaves) states are final

        :return: A *MicroStep* instance or *None* if this statechart can not be more stabilized
        """
        # Check if we are in a set of "stable" states
        leaves_names = self._statechart.leaf_for(list(self._configuration))
        leaves = map(self._statechart.state_for, leaves_names)
        leaves = sorted(leaves, key=lambda s: (-self._statechart.depth_for(s.name), s.name))

        # Final states?
        if len(leaves) > 0 and all([isinstance(s, model.FinalState) for s in leaves]):
            # Leave all states
            exited_states = sorted(self._configuration, key=lambda s: (-self._statechart.depth_for(s), s))
            return model.MicroStep(exited_states=exited_states)

        # Otherwise, develop history, compound and orthogonal states.
        for leaf in leaves:
            if isinstance(leaf, model.HistoryStateMixin):
                states_to_enter = self._memory.get(leaf.name, [leaf.memory])
                states_to_enter.sort(key=lambda x: (self._statechart.depth_for(x), x))
                return model.MicroStep(entered_states=states_to_enter, exited_states=[leaf.name])
            elif isinstance(leaf, model.OrthogonalState):
                return model.MicroStep(entered_states=sorted(self._statechart.children_for(leaf.name)))
            elif isinstance(leaf, model.CompoundState) and leaf.initial:
                return model.MicroStep(entered_states=[leaf.initial])

    def _execute_step(self, step: model.MicroStep):
        """
        Apply given *MicroStep* on this statechart

        :param step: *MicroStep* instance
        """
        entered_states = list(map(self._statechart.state_for, step.entered_states))
        exited_states = list(map(self._statechart.state_for, step.exited_states))

        # Exit states
        for state in exited_states:
            # Execute exit action
            self._evaluator.execute_onexit(state)

            # Postconditions
            self.__evaluate_contract_conditions(state, 'postconditions', step)

        # Deal with history: this only concerns compound states
        exited_compound_states = list(filter(lambda s: isinstance(s, model.CompoundState), exited_states))
        for state in exited_compound_states:
            # Look for an HistoryStateMixin among its children
            for child_name in self._statechart.children_for(state.name):
                child = self._statechart.state_for(child_name)
                if isinstance(child, model.DeepHistoryState):
                    # This MUST contain at least one element!
                    active = self._configuration.intersection(self._statechart.descendants_for(state.name))
                    assert len(active) >= 1
                    self._memory[child.name] = list(active)
                elif isinstance(child, model.ShallowHistoryState):
                    # This MUST contain exactly one element!
                    active = self._configuration.intersection(self.statechart.children_for(state.name))
                    assert len(active) == 1
                    self._memory[child.name] = list(active)
        # Update configuration
        self._configuration = self._configuration.difference(step.exited_states)

        # Execute transition
        if step.transition and step.transition.action:
            # Preconditions and invariants
            self.__evaluate_contract_conditions(step.transition, 'preconditions', step)
            self.__evaluate_contract_conditions(step.transition, 'invariants', step)

            # Execution
            self._evaluator.execute_action(step.transition, step.event)

            # Postconditions and invariants
            self.__evaluate_contract_conditions(step.transition, 'postconditions', step)
            self.__evaluate_contract_conditions(step.transition, 'invariants', step)

        # Enter states
        for state in entered_states:
            # Preconditions
            self.__evaluate_contract_conditions(state, 'preconditions', step)

            # Execute entry action
            self._evaluator.execute_onentry(state)

        # Update configuration
        self._configuration = self._configuration.union(step.entered_states)

    def __stabilize(self) -> list:
        """
        Compute, apply and return stabilization steps.

        :return: A list of *MicroStep* instances
        """
        # Stabilization
        steps = []
        step = self._compute_stabilization_step()
        while step:
            steps.append(step)
            self._execute_step(step)
            step = self._compute_stabilization_step()
        return steps

    def __evaluate_contract_conditions(self, obj, cond_type: str, step=None):
        """
        Evaluate the conditions for given object.

        :param obj: object with preconditions, postconditions or invariants
        :param cond_type: either "preconditions", "postconditions" or "invariants"
        :param step: step in which the check occurs.
        :raises ContractError: if a condition fails and *ignore_contract* is False.
        """
        if self._ignore_contract:
            return

        exception_klass = {'preconditions': PreconditionError,
                           'postconditions': PostconditionError,
                           'invariants': InvariantError}[cond_type]

        unsatisfied_conditions = getattr(self._evaluator, 'evaluate_' + cond_type)(obj, getattr(step, 'event', None))

        for condition in unsatisfied_conditions:
            raise exception_klass(configuration=self.configuration, step=step, obj=obj,
                                  assertion=condition, context=self._evaluator.context)

    def __repr__(self):
        return '{}[{}]({})'.format(self.__class__.__name__, self._statechart, ', '.join(self.configuration))


def run_in_background(interpreter: Interpreter, delay: float=0.05, callback=None):
    """
    Run given interpreter in background. The time is updated according to
    *time.time() - starttime*. The interpreter is ran until it reachs a final configuration.
    You can manually stop the thread using the added *stop* of the returned Thread object.
    This is for convenience only and should be avoided, because a call to *stop* puts the interpreter in
    an empty (and thus final) configuration, without properly leaving the active states.

    :param interpreter: an interpreter
    :param delay: delay between each call to *execute()*
    :param callback: a function that accepts the result of *execute*.
    :return: started thread (instance of *threading.Thread*)
    """
    import time
    import threading

    def _task():
        starttime = time.time()
        while not interpreter.final:
            interpreter.time = time.time() - starttime
            steps = interpreter.execute()
            if callback:
                callback(steps)
            time.sleep(delay)
    thread = threading.Thread(target=_task)

    def stop_thread():
        interpreter._configuration = []

    thread.stop = stop_thread

    thread.start()
    return thread

