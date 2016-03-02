import abc
from sismic.model import Statechart, BasicState, FinalState, Transition, CompoundState, OrthogonalState
from collections import defaultdict
from uuid import uuid4


class UniqueIdProvider(object):
    """
    This class provides unique id of elements included in a spacename.
    If the id of an element is requested for the first time, a unique id is provided.
    After that initialisation, the id associated to a specific remains the same.
    """

    def __init__(self):
        """
        Creates an id provider.
        """
        self.__d = defaultdict(uuid4)

    def __call__(self, element):
        """
        Provides the id associated to a given element, according to the following rules:

        - Two calls to the same instance of UniqueIdProvider, with the same parameter, will result in the same id.
        - Two calls to different instances of UniqueIdProvider, with the same parameter, will result in different ids.
        - Two calls to any instances of UniqueIdProvider, with different parameters, will result in different ids.

        In other words, the retrieved ids are unique for a given instance of UniqueIdProvider and for a given parameter.

        :param element: the element whose the id must be returned.
        :return: the unique id associated to element in this provider.
        """

        return str(self.__d[element])


class Condition(metaclass=abc.ABCMeta):
    """
    A condition is a property being true, false, or undetermined.
    Such a condition is expressed thanks to a set of states and transitions that can be added to a statechart.
    The resulting representation of the condition is a state having two output transitions.
    The success transition will be followed if the property is true.
    The failure transition will be followed if the property is false.
    While the property remains undetermined, none of these transitions are followed.
    """

    STEP_ENDED_EVENT = 'step ended'
    CONSUMED_EVENT_EVENT = 'event consumed'
    STATE_ENTERED_EVENT = 'state entered'
    STATE_EXITED_EVENT = 'state exited'
    EXECUTION_STARTED_EVENT = 'execution started'
    EXECUTION_STOPPED_EVENT = 'execution stopped'
    STEP_STARTED_EVENT = 'step started'
    TRANSITION_PROCESSED_EVENT = 'transition processed'
    
    def __init__(self):
        self._uname = UniqueIdProvider()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        """
        Places states and transitions into an existing statechart in order to represent the transition.
        :param statechart: the statechart in which the states and transitions must be placed.
        :param condition_state: the id of the state that represents the condition.
        :param parent_state: the id of the parent in which the representative state must be placed.
        :param success_state: the id of the (preexisting) state the success transition must point to.
        :param failure_state: the id of the (preexisting) state the failure transition must point to.
        :param status_state: the id of the (preexisting) orthogonal state placed as a direct child of the initial state
         of the statechart. Children of this orthogonal states run as long as the statechart is running.
        """
        raise NotImplementedError()

    def __invert__(self):
        """
        Inverts this condition.

        :return: the negation of this condition.
        """
        return Not(self)

    def __and__(self, other):
        """
        Combines this condition and an other one by a logic AND.

        :param other: an other condition.
        :return: (self AND other)
        """
        return And(self, other)

    def __or__(self, other):
        """
        Combines this condition and an other one by a logic OR.

        :param other: an other condition.
        :return: (self OR other)
        """
        return Or(self, other)

    def __xor__(self, other):
        """
        Combines this condition and an other one by a logic XOR.

        :param other: an other condition.
        :return: (self XOR other)
        """
        return Xor(self, other)

    def then(self, other):
        """
        Combines this condition and an other one by a temporal dependency.

        :param other: an other condition.
        :return: (self THEN other)
        """
        return Then(self, other)


class TrueCondition(Condition):
    """
    This condition is always true, so that entering the representative state
    always ends up to the success transition.
    """

    def __init__(self):
        super().__init__()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(Transition(source=condition_state, target=success_state))

    def __repr__(self):
        return self.__class__.__name__ + "()"


class FalseCondition(Condition):
    """
    This condition is always false, so that entering the representative state
    always ends up to the failure transition.
    """

    def __init__(self):
        super().__init__()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        Not(TrueCondition()).add_to_statechart(statechart,
                                               condition_state,
                                               parent_state,
                                               status_state,
                                               success_state,
                                               failure_state)

    def __repr__(self):
        return self.__class__.__name__ + "()"


class UndeterminedCondition(Condition):
    """
    This condition is never evaluated, so that entering the representative state
    never ends up to the success or the failure transition.
    """

    def __init__(self):
        super().__init__()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent_state)

    def __repr__(self):
        return self.__class__.__name__ + "()"


class EnterAnyState(Condition):
    """
    A condition based on the fact that any state has been entered.
    """

    def __init__(self):
        super().__init__()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent_state)
        statechart.add_transition(
                Transition(
                    source=condition_state,
                    target=success_state,
                    event=Condition.STATE_ENTERED_EVENT
                )
        )

    def __repr__(self):
        return self.__class__.__name__ + '()'


class EnterState(Condition):
    """
    A condition based on the fact that a given state has been entered.
    The condition remains undetermined until one of the considered states is entered.
    """

    def __init__(self, state: str, *states: str):
        """
        :param state: name of the state to observe.
        :param states: names of other states to observe.
        """
        super().__init__()
        self._states = [state] + list(states)

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        conditions = map(lambda x: '(event.state == "{}")'.format(x), self._states)
        condition = ' or '.join(conditions)

        waiting = BasicState(condition_state)
        statechart.add_state(waiting, parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.STATE_ENTERED_EVENT,
                guard=condition
            )
        )

    def __repr__(self):
        states_s = map(lambda x: "'{}'".format(x), self._states)
        return self.__class__.__name__ + '({})'.format(', '.join(states_s))


class ExitState(Condition):
    """
    A condition based on the fact that a given state has been exited.
    The condition remains undetermined until one of the considered states is exited.
    """

    def __init__(self, state: str, *states: str):
        """
        :param state: name of the state to observe.
        :param states: names of other states to observe.
        """
        super().__init__()
        self._states = [state] + list(states)

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        conditions = map(lambda x: '(event.state == "{}")'.format(x), self._states)
        condition = ' or '.join(conditions)

        waiting = BasicState(condition_state)
        statechart.add_state(waiting, parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.STATE_EXITED_EVENT,
                guard=condition
            )
        )

    def __repr__(self):
        from functools import reduce
        states_s = map(lambda x: "'{}'".format(x), self._states)
        return self.__class__.__name__ + '({})'.format(', '.join(states_s))


class ExitAnyState(Condition):
    """
    A condition based on the fact that any state has been exited.
    """

    def __init__(self):
        super().__init__()

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        waiting = BasicState(condition_state)
        statechart.add_state(waiting, parent_state)
        statechart.add_transition(
            Transition(
                    source=condition_state,
                    target=success_state,
                    event=Condition.STATE_EXITED_EVENT
            )
        )

    def __repr__(self):
        return self.__class__.__name__ + '()'


class CheckGuard(Condition):
    """
    A condition based on the verification of a guard.

    This condition is asynchronous, and may therefore lead to "infinite loops".
    """

    def __init__(self, guard: str):
        """
        :param guard: an arbitrary condition that must be verified to make the condition verified.
        """
        super().__init__()
        self._guard = guard

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        statechart.add_state(
            BasicState(
                condition_state,
                on_entry='send("{}")'.format(self._uname('event'))
            ),
            parent=parent_state
        )

        statechart.add_transition(
            Transition(
                source=condition_state,
                target=failure_state,
                event=self._uname('event')
            )
        )

        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                guard=self._guard
            )
        )

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self._guard)


class ConsumeEvent(Condition):
    """
    A property consisting in the consumption of a given event.
    This property remains undetermined until one of the considered events is consumed.
    """

    def __init__(self, event: str, *events: str):
        """
        :param event: a event that must be consumed for making this property true.
        :param events: alternative events, the consumption of which makes this property verified.
        """
        super().__init__()
        self._events = [event] + list(events)

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        conditions = map(lambda x: "(event.event.name == '{}')".format(x), self._events)
        condition = ' or '.join(conditions)

        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.CONSUMED_EVENT_EVENT,
                guard=condition
            )
        )

    def __repr__(self):
        from functools import reduce
        events_s = map(lambda x: "'{}'".format(x), self._events)
        return self.__class__.__name__ + '({})'.format(', '.join(events_s))


class StartExecution(Condition):
    """
    A property consisting in the fact that the execution of the tested statechart starts.
    """

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.EXECUTION_STARTED_EVENT
            )
        )


class StopExecution(Condition):
    """
    A property consisting in the fact that the execution of the tested statechart stops.
    """

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )


class StartStep(Condition):
    """
    A property consisting in the fact that a micro step starts.
    """

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.STEP_STARTED_EVENT
            )
        )


class EndStep(Condition):
    """
    A property consisting in the fact that a micro step ends.
    """

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.STEP_ENDED_EVENT
            )
        )


class ConsumeAnyEvent(Condition):
    """
    A property consisting in the consumption of any event.
    This property remains undetermined until any event is consumed.
    """

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.CONSUMED_EVENT_EVENT
            )
        )


class ConsumeAnyEventBut(Condition):
    """
    A property consisting in the consumption of any event, except some specific ones.
    This property remains undetermined until an event that doesn't belong to the forbidden event is consumed.
    """

    def __init__(self, event: str, *events: str):
        """
        :param event: the id of a forbidden event.
        :param events: the id of other forbidden events.
        """
        super().__init__()
        self._events = [event] + list(events)

    def __repr__(self):
        events_s = map(lambda x: "'{}'".format(x), self._events)
        return self.__class__.__name__ + '({})'.format(', '.join(events_s))

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        conditions = map(lambda x: "event.event.name != '{}'", self._events)
        condition = ' and '.join(conditions)

        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.CONSUMED_EVENT_EVENT,
                guard=condition
            )
        )


class TransitionProcess(Condition):
    """
    A property consisting in the process of a transition.
    One can restrict the nature of the processed transition based on its source, its target, or its event.
    """
    def __init__(self, source=None, target=None, event=None):
        """
        :param source: the name of the source the transition must come from in order to be accepted. If not provided,
        any source is acceptable.
        :param target: the name of the target the transition must point to in order to be accepted. If not provided,
        any target is acceptable.
        :param event: the name of the target the transition must depend on in order to be accepted. If not provided,
        any event (or the lack of event) is acceptable. An empty value means that the considered transition must
        be eventless.
        """

        super().__init__()
        self._source = source
        self._target = target
        self._event = event

    def __repr__(self):
        source_repr = 'source="{}"'.format(self._source) if self._source else ''
        target_repr = 'target="{}"'.format(self._target) if self._target else ''
        event_repr = 'event="{}"'.format(self._event) if self._event else ''

        parameters = filter(lambda x: len(x)>0, [source_repr, target_repr, event_repr])

        return self.__class__.__name__ + '({})'.format(', '.join(parameters))

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        condition_source = '(event.source == "{}")'.format(self._source) if self._source else 'True'
        condition_target = '(event.target == "{}")'.format(self._target) if self._target else 'True'

        if self._event is None:
            condition_event = 'True'
        elif self._event == '':
            condition_event = '(event.event is None)'
        else:
            condition_event = '(event.event.name == "{}")'.format(self._event)

        condition = condition_source + ' and ' + condition_target + ' and ' + condition_event

        statechart.add_state(BasicState(condition_state), parent=parent_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                event=Condition.TRANSITION_PROCESSED_EVENT,
                guard=condition
            )
        )


class And(Condition):
    """
    A condition performing a logic AND between two conditions, according the following table:

    true AND true                   => true
    true AND false                  => false
    true AND undetermined           => undetermined

    false AND X                     => false

    undetermined AND true           => undetermined
    undetermined AND false          => false
    undetermined AND undetermined   => undetermined
    """

    def __init__(self, a: Condition, b: Condition):
        """
        :param a: a condition to combine
        :param b: an other condition to combine
        """
        super().__init__()
        self._a = a
        self._b = b

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        def payload(statechart: Statechart,
                     id: str,
                     parent_id: str,
                     success_a: str,
                     failure_a: str,
                     success_b: str,
                     failure_b: str,
                     success_id: str,
                     failure_id: str):
            """
            Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
             arbitrary conditions, must be combined with a logic AND.
            :param statechart: the statechart in which the AND operator must be placed.
            :param id: the id of the composite state representing the AND operator.
            :param parent_id: the id of the parent state in which the composite state representing the AND operator
             must be placed.
            :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
            :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
            :param success_id: the id of the state a transition must point to if the AND operator succeeds.
            :param failure_id: the id of the state a transition must point to if the AND operator fails.
            """

    

            # This composite state is only created so that the payload
            # is entirely included in a state, and has no "floating"
            # states
            composite = CompoundState(id, initial=self._uname('waiting'))
            statechart.add_state(composite, parent_id)

            waiting = BasicState(self._uname('waiting'))
            statechart.add_state(waiting, id)

            partial = BasicState(self._uname('partial'))
            statechart.add_state(partial, id)

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('partial'),
                    event=success_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('partial'),
                    event=success_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=failure_id,
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=failure_id,
                    event=failure_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=failure_id,
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=failure_id,
                    event=failure_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=success_id,
                    event=success_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=success_id,
                    event=success_b
                )
            )

        _add_parallel_condition(statechart,
                                id=condition_state,
                                parent_id=parent_state,
                                status_id=status_state,
                                success_id=success_state,
                                failure_id=failure_state,
                                condition_a=self._a,
                                condition_b=self._b,
                                payload_function=payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._a, self._b)


class Or(Condition):
    """
    A condition performing a logic OR between two conditions, according the following table:

    true OR X                       => true

    false OR true                   => true
    false OR false                  => false
    false OR undetermined           => undetermined

    undetermined OR true            => true
    undetermined OR false           => undetermined
    undetermined OR undetermined    => undetermined
    """

    def __init__(self, a: Condition, b: Condition):
        """
        :param a: a condition to combine
        :param b: an other condition to combine
        """
        super().__init__()
        self._a = a
        self._b = b

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        def payload(statechart: Statechart,
                     id: str,
                     parent_id: str,
                     success_a: str,
                     failure_a: str,
                     success_b: str,
                     failure_b: str,
                     success_id: str,
                     failure_id: str):
            """
            Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
             arbitrary conditions, must be combined with a logic OR.
            :param statechart: the statechart in which the OR operator must be placed.
            :param id: the id of the composite state representing the OR operator.
            :param parent_id: the id of the parent state in which the composite state representing the OR operator
             must be placed.
            :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
            :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
            :param success_id: the id of the state a transition must point to if the OR operator succeeds.
            :param failure_id: the id of the state a transition must point to if the OR operator fails.
            """

            # This composite state is only created so that the payload is entirely included in a state,
            # and has no "floating" states
            composite = CompoundState(id, initial=self._uname('waiting'))
            statechart.add_state(composite, parent_id)

            statechart.add_state(BasicState(self._uname('waiting')), id)
            statechart.add_state(BasicState(self._uname('partial')), id)

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('partial'),
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('partial'),
                    event=failure_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=failure_id,
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('partial'),
                    target=failure_id,
                    event=failure_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=id,
                    target=success_id,
                    event=success_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=id,
                    target=success_id,
                    event=success_b
                )
            )

        _add_parallel_condition(statechart,
                                id=condition_state,
                                parent_id=parent_state,
                                status_id=status_state,
                                success_id=success_state,
                                failure_id=failure_state,
                                condition_a=self._a,
                                condition_b=self._b,
                                payload_function=payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._a, self._b)


class Xor(Condition):
    """
    A condition performing a logic Exclusive OR between two conditions, according the following table:

    undetermined XOR undetermined   => undetermined
    undetermined XOR true           => undetermined
    undetermined XOR false          => undetermined

    true         XOR undetermined   => undetermined
    true         XOR true           => false
    true         XOR false          => true

    false        XOR undetermined   => undetermined
    false        XOR true           => true
    false        XOR false          => false
    """

    def __init__(self, a: Condition, b: Condition):
        """
        :param a: a condition to combine
        :param b: an other condition to combine
        """
        super().__init__()
        self._a = a
        self._b = b

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        def payload(statechart: Statechart,
                     id: str,
                     parent_id: str,
                     success_a: str,
                     failure_a: str,
                     success_b: str,
                     failure_b: str,
                     success_id: str,
                     failure_id: str):
            """
            Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
             arbitrary conditions, must be combined with a logic XOR (exclusive OR).
            :param statechart: the statechart in which the XOR operator must be placed.
            :param id: the id of the composite state representing the XOR operator.
            :param parent_id: the id of the parent state in which the composite state representing the XOR operator
             must be placed.
            :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
            :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
            :param success_id: the id of the state a transition must point to if the XOR operator succeeds.
            :param failure_id: the id of the state a transition must point to if the XOR operator fails.
            """

            # This composite state is only created so that the payload is entirely included in a state,
            # and has no "floating" states
            composite = CompoundState(id, initial=self._uname('waiting'))
            statechart.add_state(composite, parent_id)

            waiting = BasicState(self._uname('waiting'))
            statechart.add_state(waiting, id)

            a_success = BasicState(self._uname('a_success'))
            statechart.add_state(a_success, id)

            a_failure = BasicState(self._uname('a_failure'))
            statechart.add_state(a_failure, id)

            b_success = BasicState(self._uname('b_success'))
            statechart.add_state(b_success, id)

            b_failure = BasicState(self._uname('b_failure'))
            statechart.add_state(b_failure, id)

            # First property
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('a_success'),
                    event=success_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('a_failure'),
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('b_success'),
                    event=success_b
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=self._uname('b_failure'),
                    event=failure_b
                )
            )

            # Second property
            statechart.add_transition(
                Transition(
                    source=self._uname('a_success'),
                    target=success_id,
                    event=failure_b
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('a_success'),
                    target=failure_id,
                    event=success_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('a_failure'),
                    target=success_id,
                    event=success_b
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('a_failure'),
                    target=failure_id,
                    event=failure_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('b_success'),
                    target=success_id,
                    event=failure_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('b_success'),
                    target=failure_id,
                    event=success_a
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('b_failure'),
                    target=success_id,
                    event=success_a
                )
            )
            statechart.add_transition(
                Transition(
                    source=self._uname('b_failure'),
                    target=failure_id,
                    event=failure_a
                )
            )

        _add_parallel_condition(statechart,
                                id=condition_state,
                                parent_id=parent_state,
                                status_id=status_state,
                                success_id=success_state,
                                failure_id=failure_state,
                                condition_a=self._a,
                                condition_b=self._b,
                                payload_function=payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._a, self._b)


class Not(Condition):
    """
    A condition performing a logic negation of an other condition, according the following table:

    Not(true)           => false
    Not(false)          => true
    Not(undetermined)   => undetermined
    """

    def __init__(self, cond: Condition):
        """
        :param cond: the condition to reverse
        """
        super().__init__()
        self._condition = cond

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        composite = CompoundState(condition_state, initial=self._uname('condition'))
        statechart.add_state(composite, parent_state)

        self._condition.add_to_statechart(statechart,
                                          condition_state=self._uname('condition'),
                                          parent_state=condition_state,
                                          status_state=status_state,
                                          success_state=failure_state,
                                          failure_state=success_state)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self._condition)


class Then(Condition):
    """
    This condition is verified if a first condition is verified, and after that a second condition is verified.
    The verification of the second condition does not start before the first condition is verified.

    true THEN X         => X
    false THEN X        => false
    undetermined THEN X => undetermined
    """

    def __init__(self, a: Condition, b: Condition):
        """
        :param a: the condition that must be verified before testing the second condition.
        :param b: the condition that will be evaluated after a is verified.
        """
        super().__init__()
        self._a = a
        self._b = b

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        composite = CompoundState(condition_state, initial=self._uname('a'))
        statechart.add_state(composite, parent_state)

        self._b.add_to_statechart(statechart,
                                  condition_state=self._uname('b'),
                                  parent_state=condition_state,
                                  status_state=status_state,
                                  success_state=success_state,
                                  failure_state=failure_state)

        self._a.add_to_statechart(statechart,
                                  condition_state=self._uname('a'),
                                  parent_state=condition_state,
                                  status_state=status_state,
                                  success_state=self._uname('b'),
                                  failure_state=failure_state)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._a, self._b)


class Before(Condition):
    """
    This condition is verified if a first condition a is verified, and this
     condition is verified before a second condition b is verified.

    In other words,
    - if b is verified before a, the condition is not verified.
    - if a is verified before b, the condition is verified.
    - if a and b become simultaneously verified, the condition is not verified.
    - if a is not verified, the condition is not verified.
    - if b is not verified, the verification of the condition is equivalent to the verification of a.
    """

    def __init__(self, a: Condition, b: Condition):
        super().__init__()
        self._a = a
        self._b = b

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        def payload(statechart: Statechart,
                     id: str,
                     parent_id: str,
                     success_a: str,
                     failure_a: str,
                     success_b: str,
                     failure_b: str,
                     success_id: str,
                     failure_id: str):
            """
            Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
             arbitrary conditions, must be combined with a logic Before.

            :param statechart: the statechart in which the Before operator must be placed.
            :param id: the id of the composite state representing the Before operator.
            :param parent_id: the id of the parent state in which the composite state representing the Before operator
             must be placed.
            :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
            :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
            :param failure_b: the name of the event that will be generated by the statechart if condition B fails.
            :param success_id: the id of the state a transition must point to if the Before operator succeeds.
            :param failure_id: the id of the state a transition must point to if the Before operator fails.
            """

            # This composite state is only created so that the payload is entirely included in a state,
            # and has no "floating" states
            composite = CompoundState(id, initial=self._uname('waiting_comp'))
            statechart.add_state(composite, parent=parent_id)

            waiting_comp = CompoundState(self._uname('waiting_comp'), initial=self._uname('waiting'))
            statechart.add_state(waiting_comp, parent=id)

            statechart.add_state(BasicState(self._uname('waiting')), parent=self._uname('waiting_comp'))

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting_comp'),
                    target=success_id,
                    event=success_a
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=failure_id,
                    event=success_b
                )
            )

            statechart.add_transition(
                Transition(
                    source=self._uname('waiting'),
                    target=failure_id,
                    event=failure_a
                )
            )

        _add_parallel_condition(statechart,
                                id=condition_state,
                                parent_id=parent_state,
                                status_id=status_state,
                                success_id=success_state,
                                failure_id=failure_state,
                                condition_a=self._a,
                                condition_b=self._b,
                                payload_function=payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._a, self._b)


class During(Condition):
    """
    This condition is verified iff an other condition is verified during a specified time interval.
    The time interval is specified as a pair of positive integers (start, length), so that the condition
    must be verified in the [start, start+length] interval.

    The time is expressed in the unit than in the rest of Sismic. The interval limits are relative to
    the moment at which the During condition begins to be checked.
    """

    def __init__(self, cond: Condition, start: int, lenght: int):
        """
        :param cond: the condition to check. This condition will be verified if cond is verified after
         start and before start+length
        :param start: the begining of the time interval during which a verification of cond leads
         to the verification of this condition. Must be positive or null. If start equals 0, the checked
         condition can be instantly verified.
        :param lenght: the lenght of the time interval during which a verification of cond leads
         to the verification of this condition. Must be positive or null.
        """

        super().__init__()
        self._cond = cond
        self._start = start
        self._length = lenght

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        parallel_id = condition_state


        parallel = OrthogonalState(condition_state)
        statechart.add_state(parallel, parent_state)

        cond_block = CompoundState(self._uname('cond_block'),
                                   initial=self._uname('condition'))
        statechart.add_state(cond_block, parallel_id)

        success_a = BasicState(self._uname('success_a'),
                               on_entry='send("{}")'.format(self._uname('success_event')))
        statechart.add_state(success_a, self._uname('cond_block'))

        failure_a = BasicState(self._uname('failure_a'),
                               on_entry='send("{}")'.format(self._uname('failure_event')))
        statechart.add_state(failure_a, self._uname('cond_block'))

        self._cond.add_to_statechart(statechart,
                                     condition_state=self._uname('condition'),
                                     parent_state=self._uname('cond_block'),
                                     status_state=status_state,
                                     success_state=self._uname('success_a'),
                                     failure_state=self._uname('failure_a'))

        time_block = CompoundState(self._uname('time_block'), initial=self._uname('too_early'))
        statechart.add_state(time_block, parallel_id)
        statechart.add_state(BasicState(self._uname('too_early')), self._uname('time_block'))
        statechart.add_state(BasicState(self._uname('valid')), self._uname('time_block'))

        statechart.add_transition(
            Transition(
                source=self._uname('too_early'),
                target=self._uname('valid'),
                guard='after({})'.format(self._start)
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('too_early'),
                target=failure_state,
                event=self._uname('success_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('too_early'),
                target=failure_state,
                event=self._uname('failure_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('valid'),
                target=success_state,
                event=self._uname('success_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('valid'),
                target=failure_state,
                event=self._uname('failure_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('valid'),
                target=failure_state,
                guard='after({})'.format(self._length)
            )
        )

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self._cond, self._start, self._length)


class IfElse(Condition):
    """
    This condition is equivalent to an other condition, depending of the value of a third condition.
    """
    def __init__(self, condition: Condition, then: Condition, otherwise: Condition):
        """
        :param condition: a test condition that determines the condition that will be equivalent to the IfElse
         condition. The IfElse condition may remain undetermined while condition remains undetermined.
         If condition is determined, then or otherwise is chosen based on the value of the condition :

         if(condition) then else otherwise

         Due to the fail-fast mechanism, the IfElse condition may be determined even if condition is not (yet)
         determined. For instance, the following condition is determined:

         IfElse(UndeterminedCondition(), FalseCondition(), FalseCondition())

        :param then: the condition that is used if condition is verified.
        :param otherwise: the condition that is used if condition is not verified.
        """
        super().__init__()
        self._then = then
        self._otherwise = otherwise
        self._condition = condition

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        Or(
            And(self._condition, self._then),
            And(Not(self._condition), self._otherwise)
        ).add_to_statechart(statechart,
                            condition_state,
                            parent_state,
                            status_state,
                            success_state,
                            failure_state)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self._condition, self._then, self._otherwise)


class DelayedCondition(Condition):
    """
    This condition adopts a defined behavior after a given delay.
    """

    def __init__(self, condition: Condition, delay: int):
        """
        :param condition: a condition the behavior of which this DelayedCondition adopts after the given
        delay expires.
        :param delay: a positive or null value representing the time
        to wait before the DelayedCondition adopts the given condition.
        """
        super().__init__()
        self._condition = condition
        self._delay = delay

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        statechart.add_state(CompoundState(condition_state), parent_state)

        self._condition.add_to_statechart(statechart,
                                          condition_state=self._uname('condition'),
                                          parent_state=parent_state,
                                          status_state=status_state,
                                          success_state=success_state,
                                          failure_state=failure_state)
        statechart.add_transition(
            Transition(
                source=condition_state,
                target=self._uname('condition'),
                guard='after({})'.format(self._delay)
            )
        )

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self._condition, self._delay)


class DelayedTrueCondition(Condition):
    """
    This condition becomes true after a given delay.
    """

    def __init__(self, delay: int):
        """
        :param delay: A positive or null value representing the time
        to wait before the condition becomes verified.
        """
        super().__init__()
        self._delay = delay

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        DelayedCondition(TrueCondition(), self._delay).add_to_statechart(statechart,
                                                                         condition_state=condition_state,
                                                                         parent_state=parent_state,
                                                                         status_state=status_state,
                                                                         success_state=success_state,
                                                                         failure_state=failure_state)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self._delay)


class DelayedFalseCondition(Condition):
    """
    This condition becomes false after a given delay.
    """

    def __init__(self, delay: int):
        super().__init__()
        self._delay = delay

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):
        DelayedCondition(FalseCondition(), self._delay).add_to_statechart(statechart,
                                                                          condition_state=condition_state,
                                                                          parent_state=parent_state,
                                                                          status_state=status_state,
                                                                          success_state=success_state,
                                                                          failure_state=failure_state)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self._delay)


class ActiveState(Condition):
    """
    This condition is verified if a given state is active when evaluated. Otherwise, the condition is not verified.
    This property is asynchronous and may therefore lead to an "infinite loop".
    """

    def __init__(self, state: str):
        """
        :param state: the id of the state to check.
        """
        super().__init__()
        self._state = state

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        statechart.add_state(
            CompoundState(
                self._uname('composite'),
                initial=self._uname('inactive_state')
            ),
            parent=status_state
        )

        statechart.add_state(BasicState(self._uname('inactive_state')), parent=self._uname('composite'))
        statechart.add_state(BasicState(self._uname('active_state')), parent=self._uname('composite'))

        statechart.add_transition(
            Transition(
                source=self._uname('inactive_state'),
                target=self._uname('active_state'),
                event=Condition.STATE_ENTERED_EVENT,
                guard='event.state == "{}"'.format(self._state)
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('active_state'),
                target=self._uname('inactive_state'),
                event=Condition.STATE_EXITED_EVENT,
                guard='event.state == "{}"'.format(self._state)
            )
        )

        statechart.add_state(BasicState(condition_state), parent_state)

        statechart.add_transition(
            Transition(
                source=condition_state,
                target=success_state,
                guard='active("{}")'.format(self._uname('active_state'))
            )
        )

        statechart.add_transition(
            Transition(
                source=condition_state,
                target=failure_state,
                guard='active("{}")'.format(self._uname('inactive_state'))
            )
        )

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self._state)


class InactiveState(Condition):
    """
    This condition is verified if a given state is inactive when evaluated. Otherwise, the condition is not verified.
    This condition is artificially made synchronous by waiting a 'end step' event to occur before
    leaving its undetermined state.
    """
    def __init__(self, state):
        super().__init__()
        self._state = state

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        Not(ActiveState(self._state)).add_to_statechart(statechart=statechart,
                                                        condition_state=condition_state,
                                                        parent_state=parent_state,
                                                        status_state=status_state,
                                                        success_state=success_state,
                                                        failure_state=failure_state)

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self._state)


class SynchronousCondition(Condition):
    """
    This condition forces an arbitrary condition to remain in an undetermined status
    until a 'step ended' event occurs.
    More precisely, the condition to synchronize is evaluated as usually, but transitions to
    a success or a failure states are blocked until a 'step ended' event occurs.
    """

    def __init__(self, condition: Condition):
        super().__init__()
        self._condition = condition

    def add_to_statechart(self,
                          statechart: Statechart,
                          condition_state: str,
                          parent_state: str,
                          status_state: str,
                          success_state: str,
                          failure_state: str):

        statechart.add_state(
            CompoundState(
                condition_state,
                initial=self._uname('condition')
            ),
            parent=parent_state
        )

        statechart.add_state(BasicState(self._uname('waiting_success')), parent=condition_state)
        statechart.add_state(BasicState(self._uname('waiting_failure')), parent=condition_state)

        statechart.add_transition(
            Transition(
                source=self._uname('waiting_success'),
                target=success_state,
                event=Condition.STEP_ENDED_EVENT
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('waiting_failure'),
                target=failure_state,
                event=Condition.STEP_ENDED_EVENT
            )
        )

        self._condition.add_to_statechart(statechart=statechart,
                                          condition_state=self._uname('condition'),
                                          parent_state=condition_state,
                                          status_state=status_state,
                                          success_state=self._uname('waiting_success'),
                                          failure_state=self._uname('waiting_failure'))

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self._condition)


def _add_parallel_condition(statechart: Statechart,
                            id: str,
                            parent_id: str,
                            status_id: str,
                            success_id: str,
                            failure_id: str,
                            condition_a: Condition,
                            condition_b: Condition,
                            payload_function):
    """
    Adds to a statechart an orthogonal state with 3 parallel composite states:
    1 - a composite state containing the composite state checking condition A, plus success and failure states for A
    2 - a composite state containing the composite state checking condition B, plus success and failure states for B
    3 - a 'condition' combining conditions A and B, based on received events revealing success or failure of A and B.

    :param statechart: the statechart in which the parallel condition must be added.
    :param parent_id: the id of the state in which the parallel condition must be added.
    :param status_id: the id of the orthogonal state placed as a child of the initial state of the statechart.
    :param success_id: the id of the state that must be reached if the condition succeeds.
    :param failure_id: the id of the state that must be reached if the condition fails.
    :param condition_a: a condition.
    :param condition_b: an other condition.
    :param payload_function: The way to combine conditions using sent events
    """

    ip = UniqueIdProvider()

    parallel_state = OrthogonalState(id)
    statechart.add_state(parallel_state, parent_id)

    compound_a = CompoundState(ip('compound_a'), initial=ip('a'))
    statechart.add_state(compound_a, id)
    success_a = BasicState(ip('success_a'), on_entry='send("{}")'.format(ip('a_true')))
    statechart.add_state(success_a, ip('compound_a'))
    failure_a = BasicState(ip('failure_a'), on_entry='send("{}")'.format(ip('a_false')))
    statechart.add_state(failure_a, ip('compound_a'))
    condition_a.add_to_statechart(statechart,
                                  condition_state=ip('a'),
                                  parent_state=ip('compound_a'),
                                  status_state=status_id,
                                  success_state=ip('success_a'),
                                  failure_state=ip('failure_a'))

    compound_b = CompoundState(ip('compound_b'), initial=ip('b'))
    statechart.add_state(compound_b, id)
    success_b = BasicState(ip('success_b'), on_entry='send("{}")'.format(ip('b_true')))
    statechart.add_state(success_b, ip('compound_b'))
    failure_b = BasicState(ip('failure_b'), on_entry='send("{}")'.format(ip('b_false')))
    statechart.add_state(failure_b, ip('compound_b'))
    condition_b.add_to_statechart(statechart,
                                  condition_state=ip('b'),
                                  parent_state=ip('compound_b'),
                                  status_state=status_id,
                                  success_state=ip('success_b'),
                                  failure_state=ip('failure_b'))

    payload_function(statechart, 
                     id=ip('payload_id'), 
                     parent_id=id, 
                     success_a=ip('a_true'), 
                     failure_a=ip('a_false'), 
                     success_b=ip('b_true'), 
                     failure_b=ip('b_false'), 
                     success_id=success_id, 
                     failure_id=failure_id)


class TemporalExpression(metaclass=abc.ABCMeta):
    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        self._decision = decision
        self._premise = premise
        self._consequence = consequence
        self._uname = UniqueIdProvider()

    def _prepare_statechart(self,
                            parallel_id: str,
                            rule_satisfied_id: str,
                            rule_not_satisfied_id: str):
        """
        Generates a partial statechart for representing the expression of a rule.

        :param parallel_id: name of the parallel state containing the machine and the other parallel states.
        :param rule_satisfied_id: the name of the state representing the fact that the rule is satisfied.
        :param rule_not_satisfied_id: the name of the state representing the fact that the rule is not satisfied.
        :return: a prepared statechart
        """

        statechart = Statechart(self._uname('statechart'))

        statechart.add_state(CompoundState(self._uname('global_id'), initial=parallel_id), None)
        statechart.add_state(OrthogonalState(parallel_id), parent=self._uname('global_id'))

        statechart.add_state(FinalState(self._uname('final_state')), parent=self._uname('global_id'))

        statechart.add_state(BasicState(rule_satisfied_id), parent=self._uname('global_id'))
        if self._decision:
            statechart.add_transition(Transition(source=rule_satisfied_id, target=self._uname('final_state')))

        statechart.add_state(BasicState(rule_not_satisfied_id), parent=self._uname('global_id'))
        if not self._decision:
            statechart.add_transition(Transition(source=rule_not_satisfied_id, target=self._uname('final_state')))

        return statechart

    def generate_statechart(self) -> Statechart:
        """
        Generates a statechart that represents this expression. The generated statechart can be considered as a tester
        of an other statechart.

        - If the generated statechart ends in a final pseudo-state, that means the execution of the tested statechart
        led to the validation of this expression.
        - If the generated statechart ends in a state which is not a final pseudo-state, that means the exection of the
        tested statechart led to the invalidation of this expression.

        The resulting statemachine is such that, after the premise is verified, the next verification of this premise
        only occurs after the condition is verified.

        :return: a statechart representing this expression.
        """
        raise NotImplementedError()

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self._decision,
                                                               self._premise.__repr__(),
                                                               self._consequence.__repr__())


class FirstTime(TemporalExpression):
    """
    An expression that checks if a consequence is verified the first time an associated premise is verified.

    For instance, prepare_first_time_expression(False, A, B) means that, after the first time A is verified,
    B must not be verified.

    If the premise is never verified, the rule shall be deemed verified.
    """
    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        """
        :param decision: determine the behaviour to adopt when a rule made of a premise and an associated consequence
         are verified (or not):

         - *True* means the rule is required, and the consequence must be verified each time the premise is verified.
         - *False* means the rule is forbidden, and the consequence must be not verified each time the premise is verified.

        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time the premise is verified.
        """

        super().__init__(decision, premise, consequence)

    def generate_statechart(self):
        statechart = self._prepare_statechart(parallel_id=self._uname('parallel'),
                                              rule_satisfied_id=self._uname('rule_satisfied'),
                                              rule_not_satisfied_id=self._uname('rule_not_satisfied'))

        statechart.add_state(
            CompoundState(
                self._uname('global'),
                initial=self._uname('premise')
            ),
            parent=self._uname('parallel')
        )

        self._consequence.add_to_statechart(statechart,
                                            condition_state=self._uname('consequence'),
                                            parent_state=self._uname('global'),
                                            status_state=self._uname('parallel'),
                                            success_state=self._uname('rule_satisfied'),
                                            failure_state=self._uname('rule_not_satisfied'))

        statechart.add_transition(
            Transition(
                source=self._uname('consequence'),
                target=self._uname('rule_not_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        SynchronousCondition(self._premise).add_to_statechart(statechart,
                                                              condition_state=self._uname('premise'),
                                                              parent_state=self._uname('global'),
                                                              status_state=self._uname('parallel'),
                                                              success_state=self._uname('consequence'),
                                                              failure_state=self._uname('premise'))

        statechart.add_transition(
            Transition(
                source=self._uname('premise'),
                target=self._uname('rule_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        return statechart


class EveryTime(TemporalExpression):
    """
    An expression that checks if a consequence is verified each time an associated premise is verified.

    For instance, EveryTime(False, A, B) means that, each time A is verified, B must be not verified afterwards.

    If the premise is never verified, the rule shall be deemed verified.
    """
    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        """
        :param decision: determine the behaviour to adopt when a rule made of a premise and an associated consequence
        are verified (or not):

        - *True* means the rule is required, and *consequence* must be verified each time the premise is verified.
        - *False* means the rule is forbidden, and *consequence* must be not verified each time the premise is
        verified.

        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time *premise* is verified.
        """
        super().__init__(decision, premise, consequence)

    def generate_statechart(self):
        statechart = self._prepare_statechart(parallel_id=self._uname('parallel'),
                                              rule_satisfied_id=self._uname('rule_satisfied'),
                                              rule_not_satisfied_id=self._uname('rule_not_satisfied'))

        statechart.add_state(
            CompoundState(
                self._uname('global'),
                initial=self._uname('premise')
            ),
            parent=self._uname('parallel')
        )

        statechart.add_state(
            CompoundState(
                self._uname('consequence_wrapper'),
                initial=self._uname('consequence')
            ),
            parent=self._uname('global')
        )

        SynchronousCondition(self._premise).add_to_statechart(statechart,
                                                              condition_state=self._uname('premise'),
                                                              parent_state=self._uname('global'),
                                                              status_state=self._uname('parallel'),
                                                              success_state=self._uname('consequence_wrapper'),
                                                              failure_state=self._uname('premise'))

        self._consequence.add_to_statechart(statechart,
                                            condition_state=self._uname('consequence'),
                                            parent_state=self._uname('consequence_wrapper'),
                                            status_state=self._uname('parallel'),
                                            success_state=self._uname('premise'),
                                            failure_state=self._uname('rule_not_satisfied'))

        statechart.add_transition(Transition(source=self._uname('consequence'),
                                             target=self._uname('rule_not_satisfied'),
                                             event=Condition.EXECUTION_STOPPED_EVENT))

        statechart.add_transition(Transition(source=self._uname('premise'),
                                             target=self._uname('rule_satisfied'),
                                             event=Condition.EXECUTION_STOPPED_EVENT))

        return statechart


class LastTime(TemporalExpression):
    """
    An expression that checks if a consequence is verified after the last time an associated premise is verified.

    For instance, LastTime(False, A, B) means that, the last time A is verified, B must not be verified afterwards.

    If the premise is never verified, the rule shall be deemed verified.
    """
    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        """
        :param decision: determine the behaviour to adopt when a rule made of a premise and an associated consequence
        are verified (or not):

        - *True* means the rule is required, and *consequence* must be verified each time *premise* is verified.
        - *False* means the rule is forbidden, and *consequence* must be not verified each time *premise* is verified.

        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time *premise* is verified.
        """
        super().__init__(decision, premise, consequence)

    def generate_statechart(self):
        statechart = self._prepare_statechart(parallel_id=self._uname('parallel'),
                                              rule_satisfied_id=self._uname('rule_satisfied'),
                                              rule_not_satisfied_id=self._uname('rule_not_satisfied'))

        # For the premise
        statechart.add_state(
            CompoundState(
                self._uname('premise_parallel'),
                initial=self._uname('premise')
            ),
            parent=self._uname('parallel')
        )

        statechart.add_state(
            BasicState(
                self._uname('premise_success'),
                on_entry='send("{}")'.format(self._uname('reset_event'))
            ),
            parent=self._uname('premise_parallel')
        )

        SynchronousCondition(self._premise).add_to_statechart(statechart,
                                                              condition_state=self._uname('premise'),
                                                              parent_state=self._uname('premise_parallel'),
                                                              status_state=self._uname('parallel'),
                                                              success_state=self._uname('premise_success'),
                                                              failure_state=self._uname('premise'))

        statechart.add_transition(
            Transition(
                source=self._uname('premise_success'),
                target=self._uname('premise')
            )
        )

        # For the consequence
        statechart.add_state(
            CompoundState(
                self._uname('consequence_parallel'),
                initial=self._uname('waiting')
            ),
            parent=self._uname('parallel')
        )

        statechart.add_state(
            BasicState(self._uname('waiting')),
            parent=self._uname('consequence_parallel')
        )

        statechart.add_state(
            CompoundState(
                self._uname('consequence_comp'),
                initial=self._uname('consequence')
            ),
            parent=self._uname('consequence_parallel')
        )

        statechart.add_transition(
            Transition(
                source=self._uname('consequence_comp'),
                target=self._uname('consequence_comp'),
                event=self._uname('reset_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('waiting'),
                target=self._uname('rule_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT)
        )

        statechart.add_transition(
            Transition(
                source=self._uname('waiting'),
                target=self._uname('consequence_comp'),
                event=self._uname('reset_event')
            )
        )

        consequence_success = BasicState(self._uname('consequence_success'))
        statechart.add_state(consequence_success, parent=self._uname('consequence_comp'))
        statechart.add_transition(
            Transition(
                source=self._uname('consequence_success'),
                target=self._uname('rule_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        consequence_failure = BasicState(self._uname('consequence_failure'))
        statechart.add_state(consequence_failure, parent=self._uname('consequence_comp'))
        statechart.add_transition(
            Transition(
                source=self._uname('consequence_failure'),
                target=self._uname('rule_not_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        self._consequence.add_to_statechart(statechart,
                                            condition_state=self._uname('consequence'),
                                            parent_state=self._uname('consequence_comp'),
                                            status_state=self._uname('parallel'),
                                            success_state=self._uname('consequence_success'),
                                            failure_state=self._uname('consequence_failure'))

        statechart.add_transition(
            Transition(
                source=self._uname('consequence'),
                target=self._uname('rule_not_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        return statechart


class AtLeastOnce(TemporalExpression):
    """
    An expression that checks if a consequence is verified at least one time after an associated premise
    has been verified.

    For instance, AtLeastOnce(False, A, B) means that, after has been verified at least one time,
    B must never be verified.

    If the premise is never verified, the rule shall be deemed verified, and consequently, if the rule was required, the
    expression is also verified; if the rule was forbidden, the expression is not verified.
    """

    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        """
        :param decision: determine the behaviour to adopt when a rule made of a *premise* and an associated *consequence*
        are verified (or not):

        - *True* means the rule is required, and *consequence* must be verified each time *premise* is verified.
        - *False* means the rule is forbidden, and *consequence* must be not verified each time *premise* is verified.
        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time *premise* is verified.
        """
        super().__init__(decision, premise, consequence)

    def generate_statechart(self):
        statechart = self._prepare_statechart(parallel_id=self._uname('parallel'),
                                              rule_satisfied_id=self._uname('rule_satisfied'),
                                              rule_not_satisfied_id=self._uname('rule_not_satisfied'))

        # For the premise and the consequence
        statechart.add_state(
            CompoundState(
                self._uname('premise_consequence'),
                initial=self._uname('premise')
            ),
            parent=self._uname('parallel')
        )

        statechart.add_state(BasicState(self._uname('premise_success')), parent=self._uname('premise_consequence'))

        SynchronousCondition(self._premise).add_to_statechart(statechart,
                                                              condition_state=self._uname('premise'),
                                                              parent_state=self._uname('premise_consequence'),
                                                              status_state=self._uname('parallel'),
                                                              success_state=self._uname('premise_success'),
                                                              failure_state=self._uname('premise'))

        self._consequence.add_to_statechart(statechart=statechart,
                                            condition_state=self._uname('consequence'),
                                            parent_state=self._uname('premise_consequence'),
                                            status_state=self._uname('parallel'),
                                            success_state=self._uname('rule_satisfied'),
                                            failure_state=self._uname('premise'))

        statechart.add_transition(
            Transition(
                source=self._uname('premise_success'),
                target=self._uname('consequence'),
                action='send("{}")'.format(self._uname('checked_event'))
            )
        )

        # For the fact that the premise has been checked at least one time
        statechart.add_state(
            CompoundState(
                self._uname('checked_parallel'),
                initial=self._uname('never')
            ),
            parent=self._uname('parallel')
        )

        statechart.add_state(
            BasicState(self._uname('never')),
            parent=self._uname('checked_parallel')
        )

        statechart.add_state(
            BasicState(self._uname('checked')),
            parent=self._uname('checked_parallel')
        )

        statechart.add_transition(
            Transition(
                source=self._uname('never'),
                target=self._uname('checked'),
                event=self._uname('checked_event')
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('never'),
                target=self._uname('rule_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        statechart.add_transition(
            Transition(
                source=self._uname('checked'),
                target=self._uname('rule_not_satisfied'),
                event=Condition.EXECUTION_STOPPED_EVENT
            )
        )

        return statechart