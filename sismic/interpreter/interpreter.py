from collections import deque
from itertools import combinations
from typing import (Any, Callable, Dict, Iterable, List, Mapping, Optional,
                    Set, Union, cast, Deque)

from ..model import (
    MacroStep, MicroStep, Event, InternalEvent, MetaEvent,
    Statechart, Transition,
    StateMixin, HistoryStateMixin,
    FinalState, OrthogonalState, CompoundState, DeepHistoryState, ShallowHistoryState,
)

from ..code import Evaluator, PythonEvaluator
from ..exceptions import (ConflictingTransitionsError, InvariantError, PropertyStatechartError,
                          ExecutionError, NonDeterminismError, PostconditionError, PreconditionError)

__all__ = ['Interpreter']


class Interpreter:
    """
    A discrete interpreter that executes a statechart according to a semantic close to SCXML.

    :param statechart: statechart to interpret
    :param evaluator_klass: An optional callable (eg. a class) that takes an interpreter and an optional initial
        context as input and return an *Evaluator* instance that will be used to initialize the interpreter.
        By default, the *PythonEvaluator* class will be used.
    :param initial_context: an optional initial context that will be provided to the evaluator.
        By default, an empty context is provided
    :param ignore_contract: set to True to ignore contract checking during the execution.
    """

    def __init__(self, statechart: Statechart, *,
                 evaluator_klass: Callable[..., Evaluator]=PythonEvaluator,
                 initial_context: Mapping[str, Any]=None,
                 ignore_contract: bool=False) -> None:
        # Internal variables
        self._ignore_contract = ignore_contract
        self._statechart = statechart

        self._initialized = False

        # Internal clock
        self._time = 0  # type: float

        # History states memory
        self._memory = {}  # type: Dict[str, Optional[List[str]]]

        # Set of active states
        self._configuration = set()  # type: Set[str]

        # External events queue
        self._external_events = deque()  # type: Deque[Event]

        # Internal events queue
        self._internal_events = deque()  # type: Deque[InternalEvent]

        # Bound callables
        self._bound = []  # type: List[Callable[[Event], Any]]

        # Bound property statecharts
        self._bound_properties = []  # type: List[Interpreter]

        # Evaluator
        self._evaluator = evaluator_klass(self, initial_context=initial_context)  # type: ignore
        self._evaluator.execute_statechart(statechart)

    @property
    def time(self) -> float:
        """
        Time value (in seconds) for the internal clock
        """
        return self._time

    @time.setter
    def time(self, value: float):
        """
        Set the time of the internal clock

        :param value: time value (in seconds)
        """
        if self._time > value:
            raise ExecutionError('Time must be monotonic, cannot set time to {} from {}'.format(value, self._time))
        self._time = value

        # Update bound properties
        for property_statechart in self._bound_properties:
            property_statechart.time = self._time

    @property
    def configuration(self) -> List[str]:
        """
        List of active states names, ordered by depth. Ties are broken according to the lexicographic order
        on the state name.
        """
        return sorted(self._configuration, key=lambda s: (self._statechart.depth_for(s), s))

    @property
    def context(self) -> Mapping[str, Any]:
        """
        The context of execution.
        """
        return self._evaluator.context

    @property
    def final(self) -> bool:
        """
        Boolean indicating whether this interpreter is in a final configuration.
        """
        return self._initialized and len(self._configuration) == 0

    @property
    def statechart(self) -> Statechart:
        """
        Embedded statechart
        """
        return self._statechart

    def bind(self, interpreter_or_callable: Union['Interpreter', Callable[[Event], Any]]) -> None:
        """
        Bind an interpreter or a callable to the current interpreter.
        Each time an internal event is sent by this interpreter, any bound object will be called
        with the same event. If *interpreter_or_callable* is an *Interpreter* instance,  its *queue* method is called.
        This is, if *i1* and *i2* are interpreters, *i1.bind(i2)* is equivalent to *i1.bind(i2.queue)*.

        :param interpreter_or_callable: interpreter or callable to bind
        :return: *self* so it can be chained
        """
        if isinstance(interpreter_or_callable, Interpreter):
            self._bound.append(interpreter_or_callable.queue)
        else:
            self._bound.append(interpreter_or_callable)

    def bind_property_statechart(self, statechart_or_interpreter: Union[Statechart, 'Interpreter']) -> None:
        """
        Bind a property statechart to the current interpreter.
        A property statechart receives meta-events from the current interpreter depending on what happens:

         - step started: when a macro step starts.
         - step ended: when a macro step ends.
         - event consumed: when an event is consumed. The consumed event is exposed through the ``event`` attribute.
         - event sent: when an event is sent. The sent event is exposed through the ``event`` attribute.
         - state exited: when a state is exited. The exited state is exposed through the ``state`` attribute.
         - state entered: when a state is entered. The entered state is exposed through the ``state`` attribute.
         - transition processed: when a transition is processed. The source state, target state and the event are
           exposed respectively through the ``source``, ``target`` and ``event`` attribute.

        The internal clock of all property statecharts will be synced with the one of the current interpreter.
        As soon as a property statechart reaches a final state, a ``PropertyStatechartError`` will be raised, 
        implicitly meaning that the property expressed by the corresponding property statechart is not satisfied.

        :param statechart_or_interpreter: A property statechart or an interpreter of a property statechart.
        """
        # Create interpreter if required
        if isinstance(statechart_or_interpreter, Statechart):
            interpreter = Interpreter(statechart_or_interpreter)
        else:
            interpreter = statechart_or_interpreter

        # Sync clock
        interpreter.time = self.time

        # Add to the list of properties
        self._bound_properties.append(interpreter)

    def queue(self, event_or_name: Union[str, Event], *events_or_names: Union[str, Event]) -> 'Interpreter':
        """
        Queue one or more events to the interpreter external queue.

        :param event_or_name: an *Event* instance, or the name of an event.
        :param events_or_names: additional *Event* instances, or names of events.
        :return: *self* so it can be chained.
        """
        if len(events_or_names) == 0:
            events_or_names = tuple()

        for item in [event_or_name] + list(events_or_names):
            if isinstance(item, Event):
                self._external_events.append(item)
            elif isinstance(item, str):
                self._external_events.append(Event(item))
            else:
                raise ValueError('{} is not a string nor an Event instance.'.format(item))

        return self

    def execute(self, max_steps: int = -1) -> List[MacroStep]:
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

    def execute_once(self) -> Optional[MacroStep]:
        """
        Processes a transition based on the oldest queued event (or no event if an eventless transition
        can be processed), and stabilizes the interpreter in a stable situation (ie. processes initial states,
        history states, etc.). When multiple transitions are selected, they are atomically processed:
        states are exited, transition is processed, states are entered, statechart is stabilized and only
        after that, the next transition is processed.

        :return: a macro step or *None* if nothing happened
        """
        event = None  # type: Optional[Event]

        # Initialization
        if not self._initialized:
            computed_steps = [MicroStep(entered_states=[self._statechart.root])]
            self._initialized = True
        else:
            # Look for eventless transitions first
            transitions = self._select_transitions(event=None)
            if len(transitions) == 0:
                # Look for transitions with event
                event = self._select_event()
                if event is None:
                    # No event implies no step!
                    # However, we need to check properties
                    self._check_properties(None)
                    return None
                transitions = self._select_transitions(event=event)

            # No transition? Empty step!
            if len(transitions) == 0:
                computed_steps = [MicroStep(event=event)]
            else:
                # Select the transitions that will be performed
                transitions = self._sort_transitions(
                    self._filter_transitions(transitions)
                )
                computed_steps = self._create_steps(event, transitions)

        # Notify properties
        self._notify_properties('step started')
        if event:
            self._notify_properties('event consumed', event=event)

        # Execute the steps
        self._evaluator.on_step_starts(event)

        executed_steps = []
        for step in computed_steps:
            executed_steps.append(self._apply_step(step))
            executed_steps.extend(self._stabilize())

        macro_step = MacroStep(time=self.time, steps=executed_steps)

        # Check state invariants
        configuration = self.configuration  # Use self.configuration to benefit from the sorting by depth
        for name in configuration:
            state = self._statechart.state_for(name)
            self._evaluate_contract_conditions(state, 'invariants', macro_step)

        # End step and check for property statechart violations
        self._notify_properties('step ended')
        self._check_properties(macro_step)

        return macro_step

    def _raise_event(self, event: Event) -> None:
        """
        Raise an event from the statechart.
        Events are propagated to bound interpreters as non-internal events, and added to the internal queue of the
        current interpreter.

        :param event: raised event.
        """
        if isinstance(event, InternalEvent):
            # Add to current interpreter's internal queue
            self._internal_events.append(event)

            # Propagate event to bound callable as an "external" event
            external_event = Event(event.name, **event.data)
            for bound_callable in self._bound:
                bound_callable(external_event)
        else:
            raise ValueError('Only InternalEvent instances are supported, not {}.'.format(type(event)))

    def _notify_properties(self, event_name: str, **kwargs):
        """
        Notify the property statecharts bound to this interpreter.

        :param event_name: name of the event
        :param kwargs: additional parameters that should be made available as event parameters
        """

        # Create meta-event
        event = MetaEvent(event_name, **kwargs)

        # Send meta-event to the bound properties
        for property_statechart in self._bound_properties:
            property_statechart.queue(event)

        # Execute property statecharts
        for property_statechart in self._bound_properties:
            property_statechart.execute()

    def _check_properties(self, macro_step: Optional[MacroStep]):
        """
        Check property statecharts for failure (ie. final state is reached).

        :param macro_step: current macro step being processed
        """
        for property_statechart in self._bound_properties:
            # Check for failure
            if property_statechart.final:
                raise PropertyStatechartError(property_statechart, self.configuration, macro_step, self.context)

    def _select_event(self) -> Optional[Event]:
        """
        Return (and consume!) the next available event if any.
        This method prioritizes internal events over external ones.

        :return: An instance of Event or None if no event is available
        """
        # Internal events are processed first
        if len(self._internal_events) > 0:
            return self._internal_events.popleft()
        elif len(self._external_events) > 0:
            return self._external_events.popleft()
        else:
            return None

    def _select_transitions(self, event: Event = None) -> List[Transition]:
        """
        Return a list of transitions that can be triggered according to the given event, or eventless
        transition if *event* is None.

        :param event: event to consider
        :return: a list of *Transition* instances
        """
        transitions = []

        # Retrieve the firable transitions for all active state
        for transition in self._statechart.transitions:
            if (transition.event == getattr(event, 'name', None) and transition.source in self._configuration and
                    (transition.guard is None or self._evaluator.evaluate_guard(transition, event))):
                transitions.append(transition)
        return transitions

    def _filter_transitions(self, transitions: List[Transition]) -> List[Transition]:
        """
        Given a list of transitions, return a filtered list of transitions with respect to the
        inner-first/source-state semantic.

        :param transitions: a list of *Transition* instances
        :return: a list of *Transition* instances
        """
        removed_transitions = set()
        for transition in transitions:
            source_state_descendants = self._statechart.descendants_for(transition.source)
            for other_transition in transitions:
                if other_transition.source in source_state_descendants:
                    removed_transitions.add(transition)
                    break

        return list(set(transitions).difference(removed_transitions))

    def _sort_transitions(self, transitions: List[Transition]) -> List[Transition]:
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
                if not isinstance(lca_state, OrthogonalState):
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

    def _create_steps(self, event: Event,
                      transitions: Iterable[Transition]) -> List[MicroStep]:
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
                returned_steps.append(MicroStep(event=event, transition=transition))
                continue

            lca = self._statechart.least_common_ancestor(transition.source, transition.target)
            from_ancestors = self._statechart.ancestors_for(transition.source)
            to_ancestors = self._statechart.ancestors_for(transition.target)

            # Exited states
            exited_states = []

            # last_before_lca is the "highest" ancestor of from_state that is a child of LCA
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

            returned_steps.append(MicroStep(event=event, transition=transition,
                                                  entered_states=entered_states, exited_states=exited_states))

        return returned_steps

    def _create_stabilization_step(self, names: Iterable[str]) -> Optional[MicroStep]:
        """
        Return a stabilization step, ie. a step that lead to a more stable situation
        for the current statechart. Stabilization means:

         - Enter the initial state of a compound state with no active child
         - Enter the memory of a history state
         - Enter the children of an orthogonal state with no active child
         - Exit active states if all "deepest" (leaves) states are final

        :param names: List of states to consider (usually, the active configuration)
        :return: A *MicroStep* instance or *None* if this statechart can not be more stabilized
        """
        # Check if we are in a set of "stable" states
        leaves_names = self._statechart.leaf_for(names)
        leaves = sorted(map(self._statechart.state_for, leaves_names),
                        key=lambda s: (-self._statechart.depth_for(s.name), s.name))

        # Final states?
        if len(leaves) > 0 and all([isinstance(s, FinalState) for s in leaves]):
            # Leave all states
            exited_states = sorted(self._configuration, key=lambda s: (-self._statechart.depth_for(s), s))
            return MicroStep(exited_states=exited_states)

        # Otherwise, develop history, compound and orthogonal states.
        for leaf in leaves:
            name = cast(StateMixin, leaf).name
            if isinstance(leaf, HistoryStateMixin):
                states_to_enter = self._memory.get(name, [leaf.memory])
                states_to_enter.sort(key=lambda x: (self._statechart.depth_for(x), x))
                return MicroStep(entered_states=states_to_enter, exited_states=[name])
            elif isinstance(leaf, OrthogonalState) and self._statechart.children_for(leaf.name):
                return MicroStep(entered_states=sorted(self._statechart.children_for(leaf.name)))
            elif isinstance(leaf, CompoundState) and leaf.initial:
                return MicroStep(entered_states=[leaf.initial])

        return None

    def _apply_step(self, step: MicroStep) -> MicroStep:
        """
        Apply given *MicroStep* on this statechart

        :param step: *MicroStep* instance
        :return: a new MicroStep, completed with sent events
        """
        entered_states = list(map(self._statechart.state_for, step.entered_states))
        exited_states = list(map(self._statechart.state_for, step.exited_states))

        active_configuration = set(self._configuration)  # Copy

        sent_events = []  # type: List[Event]

        # Exit states
        for state in exited_states:
            # Execute exit action
            sent_events.extend(self._evaluator.execute_on_exit(state))

            # Deal with history
            if isinstance(state, CompoundState):
                # Look for an HistoryStateMixin among its children
                for child_name in self._statechart.children_for(state.name):
                    child = self._statechart.state_for(child_name)
                    if isinstance(child, DeepHistoryState):
                        # This MUST contain at least one element!
                        active = active_configuration.intersection(self._statechart.descendants_for(state.name))
                        assert len(active) >= 1
                        self._memory[child.name] = list(active)
                    elif isinstance(child, ShallowHistoryState):
                        # This MUST contain exactly one element!
                        active = active_configuration.intersection(self.statechart.children_for(state.name))
                        assert len(active) == 1
                        self._memory[child.name] = list(active)

            # Remove state from active configuration
            self._configuration.remove(state.name)

            # Postconditions
            self._evaluate_contract_conditions(state, 'postconditions', step)

            # Notify properties
            self._notify_properties('state exited', state=state.name)

        # Execute transition
        if step.transition:
            # Preconditions and invariants
            self._evaluate_contract_conditions(step.transition, 'preconditions', step)
            self._evaluate_contract_conditions(step.transition, 'invariants', step)

            sent_events.extend(self._evaluator.execute_action(step.transition, step.event))

            # Postconditions and invariants
            self._evaluate_contract_conditions(step.transition, 'postconditions', step)
            self._evaluate_contract_conditions(step.transition, 'invariants', step)

            # Notify properties
            self._notify_properties(
                'transition processed',
                source=step.transition.source,
                target=step.transition.target,
                event=step.event
            )

        # Enter states
        for state in entered_states:
            # Preconditions
            self._evaluate_contract_conditions(state, 'preconditions', step)

            # Execute entry action
            sent_events.extend(self._evaluator.execute_on_entry(state))

            # Update configuration
            self._configuration.add(state.name)

            # Notify properties
            self._notify_properties('state entered', state=state.name)

        # Send events
        for event in sent_events:
            self._raise_event(event)

            # Notify properties
            self._notify_properties('event sent', event=event)

        return MicroStep(event=step.event, transition=step.transition,
                               entered_states=step.entered_states, exited_states=step.exited_states,
                               sent_events=sent_events)

    def _stabilize(self) -> List[MicroStep]:
        """
        Compute, apply and return stabilization steps.

        :return: A list of applied  *MicroStep* instances,
        """
        # Stabilization
        steps = []
        step = self._create_stabilization_step(self._configuration)
        while step is not None:
            steps.append(self._apply_step(step))
            step = self._create_stabilization_step(self._configuration)
        return steps

    def _evaluate_contract_conditions(self, obj: Union[Transition, StateMixin],
                                      cond_type: str,
                                      step: Union[MacroStep, MicroStep]=None) -> None:
        """
        Evaluate the conditions for given object.

        :param obj: object with preconditions, postconditions or invariants
        :param cond_type: either "preconditions", "postconditions" or "invariants"
        :param step: step in which the check occurs.
        :raises ContractError: if a condition fails and *ignore_contract* is False.
        """
        if self._ignore_contract:
            return

        exception_klass = cast(Callable[..., Exception], {'preconditions': PreconditionError,
                                                          'postconditions': PostconditionError,
                                                          'invariants': InvariantError}[cond_type])

        unsatisfied_conditions = getattr(self._evaluator, 'evaluate_' + cond_type)(obj, getattr(step, 'event', None))

        for condition in unsatisfied_conditions:
            raise exception_klass(configuration=self.configuration, step=step, obj=obj,
                                  assertion=condition, context=self.context)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self._statechart)
