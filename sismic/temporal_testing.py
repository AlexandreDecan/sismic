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
        self.d = defaultdict(uuid4)

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

        return str(self.d[element])


class Condition:
    """
    A condition is a property being true, false, or undetermined.
    Such a condition is expressed thanks to a set of states and transitions that can be added to a statechart.
    The resulting representation of the condition is a state having two output transitions.
    The success transition will be followed if the property is true.
    The failure transition will be followed if the property is false.
    While the property remains undetermined, none of these transitions are followed.
    """

    END_STEP_EVENT = 'step ended'
    STOPPED_EVENT = 'execution stopped'
    CONSUME_EVENT = 'event consumed'
    STATE_ENTERED_EVENT = 'state entered'
    STATE_EXITED_EVENT = 'state exited'
    EXECUTION_STARTED_EVENT = 'execution started'
    EXECUTION_STOPPED_EVENT = 'execution stopped'
    START_STEP_EVENT = 'step started'
    TRANSITION_PROCESS_EVENT = 'transition processed'

    def __init__(self):
        pass

    def add_to(self,
               statechart: Statechart,
               id: str,
               parent_id: str,
               status_id: str,
               success_id: str,
               failure_id: str):
        """
        Places states and transitions into an existing statechart in order to represent the transition.
        :param statechart: the statechart in which the states and transitions must be placed.
        :param id: the id of the state that represents the condition.
        :param parent_id: the id of the parent in which the representative state must be placed.
        :param success_id: the id of the (preexisting) state the success transition must point to.
        :param failure_id: the id of the (preexisting) state the failure transition must point to.
        :param status_id: the id of the (preexisting) orthogonal state placed as a direct child of the initial state
        of the statechart. Children of this orthogonal states run as long as the statechart is running.
        """
        pass

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
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id))

    def __repr__(self):
        return self.__class__.__name__ + "()"


class FalseCondition(Condition):
    """
    This condition is always false, so that entering the representative state
    always ends up to the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        Not(TrueCondition()).add_to(statechart, id, parent_id, status_id, success_id, failure_id)

    def __repr__(self):
        return self.__class__.__name__ + "()"


class UndeterminedCondition(Condition):
    """
    This condition is never evaluated, so that entering the representative state
    never ends up to the success or the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        waiting_state = BasicState(id)
        statechart.add_state(waiting_state, parent_id)

    def __repr__(self):
        return self.__class__.__name__ + "()"


class EnterAnyState(Condition):
    """
    A condition based on the fact that any state has been entered.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        waiting = BasicState(id)
        statechart.add_state(waiting, parent_id)
        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             event=Condition.STATE_ENTERED_EVENT))

    def __repr__(self):
        return self.__class__.__name__ + '()'


class EnterState(Condition):
    """
    A condition based on the fact that a given state has been entered.
    """

    def __init__(self, *states: str):
        """
        :param states: the ids of the states to observe.
        """
        Condition.__init__(self)
        self.states = states

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        from functools import reduce

        conditions = map(lambda x: '(event.state == "{}")'.format(x), self.states)
        condition = reduce(lambda x, y: x + ' or ' + y, conditions)

        waiting = BasicState(id)
        statechart.add_state(waiting, parent_id)
        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             event=Condition.STATE_ENTERED_EVENT,
                                             guard=condition))

    def __repr__(self):
        from functools import reduce
        states_s = map(lambda x: "'{}'".format(x), self.states)
        return self.__class__.__name__ + '({})'.format(reduce(lambda x, y: x + ', ' + y, states_s))


class ExitState(Condition):
    """
    A condition based on the fact that a given state has been exited.
    """

    def __init__(self, *states: str):
        """
        :param states: the ids of the states to observe.
        """
        Condition.__init__(self)
        self.states = states

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        from functools import reduce

        conditions = map(lambda x: '(event.state == "{}")'.format(x), self.states)
        condition = reduce(lambda x, y: x + ' or ' + y, conditions)

        waiting = BasicState(id)
        statechart.add_state(waiting, parent_id)
        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             event=Condition.STATE_EXITED_EVENT,
                                             guard=condition))

    def __repr__(self):
        from functools import reduce
        states_s = map(lambda x: "'{}'".format(x), self.states)
        return self.__class__.__name__ + '({})'.format(reduce(lambda x, y: x + ', ' + y, states_s))


class ExitAnyState(Condition):
    """
    A condition based on the fact that any state has been exited.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        waiting = BasicState(id)
        statechart.add_state(waiting, parent_id)
        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             event=Condition.STATE_EXITED_EVENT))

    def __repr__(self):
        return self.__class__.__name__ + '()'


class CheckGuard(Condition):
    """
    A condition based on the verification of a guard.

    In order to keep it synchronous, this condition is only evaluated after a 'endstep' event is
    submitted to the generated statechart representing the condition.

    variables.
    """

    def __init__(self, guard: str):
        """
        :param guard: an arbitrary condition that must be verified to make the condition verified.
        """
        Condition.__init__(self)
        self.guard = guard
    
    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self.guard)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        # TODO: One probably want to use the context of the tested statechart to determine the value of existing
        ip = UniqueIdProvider()

        statechart.add_state(BasicState(id), parent_id)
        statechart.add_state(CompoundState(ip('composite'), initial=ip('test')), parent_id)
        statechart.add_state(BasicState(ip('test')), ip('composite'))

        statechart.add_transition(Transition(source=id, target=ip('composite'), event=Condition.END_STEP_EVENT))
        statechart.add_transition(Transition(source=ip('test'), target=success_id, guard=self.guard))
        statechart.add_transition(Transition(source=ip('composite'), target=failure_id))


class ConsumeEvent(Condition):
    """
    A property consisting in the consumption of a given event.
    This property remains undetermined until the considered event is consumed.
    """

    def __init__(self, *events: str):
        """
        :param event: the events that must be consumed for making this property verified.
        """
        Condition.__init__(self)
        self.events = events

    def __repr__(self):
        from functools import reduce
        events_s = map(lambda x: "'{}'".format(x), self.events)
        return self.__class__.__name__ + '({})'.format(reduce(lambda x, y: x + ', ' + y, events_s))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        from functools import reduce

        conditions = map(lambda x: "(event.event.name == '{}')".format(x), self.events)
        condition = reduce(lambda x, y: x + ' or ' + y, conditions)

        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id,
                                             event=Condition.CONSUME_EVENT,
                                             guard=condition))


class ExecutionStart(Condition):
    """
    A property consisting in the fact that the execution of the tested statechart starts.
    """

    def __init__(self):
        Condition.__init__(self)

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.EXECUTION_STARTED_EVENT))


class ExecutionStop(Condition):
    """
    A property consisting in the fact that the execution of the tested statechart stops.
    """

    def __init__(self):
        Condition.__init__(self)

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.EXECUTION_STOPPED_EVENT))


class StartStep(Condition):
    """
    A property consisting in the fact that a micro step starts.
    """

    def __init__(self):
        Condition.__init__(self)

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.START_STEP_EVENT))


class EndStep(Condition):
    """
    A property consisting in the fact that a micro step ends.
    """

    def __init__(self):
        Condition.__init__(self)

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.END_STEP_EVENT))


class ConsumeAnyEvent(Condition):
    """
    A property consisting in the consumption of any event.
    This property remains undetermined until any event is consumed.
    """

    def __init__(self):
        Condition.__init__(self)

    def __repr__(self):
        return self.__class__.__name__ + '()'

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.CONSUME_EVENT))


class ConsumeAnyEventBut(Condition):
    """
    A property consisting in the consumption of any event, except some specific ones.
    This property remains undetermined until an event that doesn't belong to the forbidden event is consumed.
    """

    def __init__(self, *events: str):
        """
        :param events: the id of the forbidden events.
        """
        Condition.__init__(self)
        self.events = events

    def __repr__(self):
        from functools import reduce
        events_s = map(lambda x: "'{}'".format(x), self.events)
        return self.__class__.__name__ + '({})'.format(reduce(lambda x, y: x + ', ' + y, events_s))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        from functools import reduce

        conditions = map(lambda x: "(not(event.event.name == '{}'))", self.events)
        condition = reduce(lambda x, y: x + ' and ' + y, conditions)

        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             event=Condition.CONSUME_EVENT,
                                             guard=condition))


class TransitionProcess(Condition):
    """
    A property consisting in the process of a transition.
    One can restrict the nature of the processed transition based on its source, its target, or its event.
    """
    def __init__(self, source=None, target=None, event=None):
        """
        :param source: the name of the source the transition must come from in order to be accepted. A None value means
        that any source is acceptable.
        :param target: the name of the target the transition must point to in order to be accepted. A None value means
        that any target is acceptable.
        :param event: the name of the target the transition must depend on in order to be accepted. A None value means
        that any event (or the lack of event) is acceptable. An empty value means that the considered transition must
        be eventless.
        """

        Condition.__init__(self)
        self.source = source
        self.target = target
        self.event = event

    def __repr__(self):
        source_repr = '"{}"'.format(self.source) if self.source is not None else 'None'
        target_repr = '"{}"'.format(self.target) if self.target is not None else 'None'
        event_repr = '"{}"'.format(self.event) if self.event is not None else 'None'

        return self.__class__.__name__ + '({}, {}, {})'.format(source_repr, target_repr, event_repr)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        condition_source = '(event.source == "{}")'.format(self.source) if self.source is not None else 'True'
        condition_target = '(event.target == "{}")'.format(self.target) if self.target is not None else 'True'

        if self.event is None:
            condition_event = 'True'
        elif self.event == '':
            condition_event = '(event.event is None)'
        else:
            condition_event = '(event.event.name == "{}")'.format(self.event)

        statechart.add_state(BasicState(id), parent=parent_id)
        statechart.add_transition(Transition(source=id, target=success_id, event=Condition.TRANSITION_PROCESS_EVENT,
                                             guard=condition_source + ' and ' + condition_target + ' and ' + condition_event))


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
        Condition.__init__(self)
        self.a = a
        self.b = b

    @staticmethod
    def _payload(statechart: Statechart,
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
        :param parent_state_id: the id of the parent state in which the composite state representing the AND operator
         must be placed.
        :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
        :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
        :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
        :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
        :param success_id: the id of the state a transition must point to if the AND operator succeeds.
        :param failure_id: the id of the state a transition must point to if the AND operator fails.
        """

        ip = UniqueIdProvider()

        # This composite state is only created so that the payload
        # is entirely included in a state, and has no "floating"
        # states
        composite = CompoundState(id, initial=ip('waiting'))
        statechart.add_state(composite, parent_id)

        waiting = BasicState(ip('waiting'))
        statechart.add_state(waiting, id)

        partial = BasicState(ip('partial'))
        statechart.add_state(partial, id)

        statechart.add_transition(Transition(source=ip('waiting'), target=ip('partial'), event=success_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('partial'), event=success_b))

        statechart.add_transition(Transition(source=ip('waiting'), target=failure_id, event=failure_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=failure_id, event=failure_b))

        statechart.add_transition(Transition(source=ip('partial'), target=failure_id, event=failure_a))
        statechart.add_transition(Transition(source=ip('partial'), target=failure_id, event=failure_b))

        statechart.add_transition(Transition(source=ip('partial'), target=success_id, event=success_a))
        statechart.add_transition(Transition(source=ip('partial'), target=success_id, event=success_b))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart,
                                id=id,
                                parent_id=parent_id,
                                status_id=status_id,
                                success_id=success_id,
                                failure_id=failure_id,
                                condition_a=self.a,
                                condition_b=self.b,
                                payload_function=And._payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


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
        Condition.__init__(self)
        self.a = a
        self.b = b

    @staticmethod
    def _payload(statechart: Statechart,
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

        ip = UniqueIdProvider()

        # This composite state is only created so that the payload
        # is entirely included in a state, and has no "floating"
        # states
        composite = CompoundState(id, initial=ip('waiting'))
        statechart.add_state(composite, parent_id)

        statechart.add_state(BasicState(ip('waiting')), id)
        statechart.add_state(BasicState(ip('partial')), id)

        statechart.add_transition(Transition(source=ip('waiting'), target=ip('partial'), event=failure_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('partial'), event=failure_b))

        statechart.add_transition(Transition(source=ip('partial'), target=failure_id, event=failure_a))
        statechart.add_transition(Transition(source=ip('partial'), target=failure_id, event=failure_b))

        statechart.add_transition(Transition(source=id, target=success_id, event=success_a))
        statechart.add_transition(Transition(source=id, target=success_id, event=success_b))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart,
                                id=id,
                                parent_id=parent_id,
                                status_id=status_id,
                                success_id=success_id,
                                failure_id=failure_id,
                                condition_a=self.a,
                                condition_b=self.b,
                                payload_function=Or._payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


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
        Condition.__init__(self)
        self.a = a
        self.b = b

    @staticmethod
    def _payload(statechart: Statechart,
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

        ip = UniqueIdProvider()

        # This composite state is only created so that the payload
        # is entirely included in a state, and has no "floating"
        # states
        composite = CompoundState(id, initial=ip('waiting'))
        statechart.add_state(composite, parent_id)

        waiting = BasicState(ip('waiting'))
        statechart.add_state(waiting, id)

        a_success = BasicState(ip('a_success'))
        statechart.add_state(a_success, id)

        a_failure = BasicState(ip('a_failure'))
        statechart.add_state(a_failure, id)

        b_success = BasicState(ip('b_success'))
        statechart.add_state(b_success, id)

        b_failure = BasicState(ip('b_failure'))
        statechart.add_state(b_failure, id)

        # First property
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('a_success'), event=success_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('a_failure'), event=failure_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('b_success'), event=success_b))
        statechart.add_transition(Transition(source=ip('waiting'), target=ip('b_failure'), event=failure_b))

        # Second property
        statechart.add_transition(Transition(source=ip('a_success'), target=success_id, event=failure_b))
        statechart.add_transition(Transition(source=ip('a_success'), target=failure_id, event=success_b))

        statechart.add_transition(Transition(source=ip('a_failure'), target=success_id, event=success_b))
        statechart.add_transition(Transition(source=ip('a_failure'), target=failure_id, event=failure_b))

        statechart.add_transition(Transition(source=ip('b_success'), target=success_id, event=failure_a))
        statechart.add_transition(Transition(source=ip('b_success'), target=failure_id, event=success_a))

        statechart.add_transition(Transition(source=ip('b_failure'), target=success_id, event=success_a))
        statechart.add_transition(Transition(source=ip('b_failure'), target=failure_id, event=failure_a))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart,
                                id=id,
                                parent_id=parent_id,
                                status_id=status_id,
                                success_id=success_id,
                                failure_id=failure_id,
                                condition_a=self.a,
                                condition_b=self.b,
                                payload_function=Xor._payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


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
        Condition.__init__(self)
        self.condition = cond

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        ip = UniqueIdProvider()
        composite = CompoundState(id, initial=ip('condition'))
        statechart.add_state(composite, parent_id)

        self.condition.add_to(statechart,
                              id=ip('condition'),
                              parent_id=id,
                              status_id=status_id,
                              success_id=failure_id,
                              failure_id=success_id)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self.condition)


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
        Condition.__init__(self)
        self.a = a
        self.b = b

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        ip = UniqueIdProvider()

        composite = CompoundState(id, initial=ip('a'))
        statechart.add_state(composite, parent_id)

        self.b.add_to(statechart,
                      id=ip('b'),
                      parent_id=id,
                      status_id=status_id,
                      success_id=success_id,
                      failure_id=failure_id)

        self.a.add_to(statechart,
                      id=ip('a'),
                      parent_id=id,
                      status_id=status_id,
                      success_id=ip('b'),
                      failure_id=failure_id)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


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
        self.a = a
        self.b = b

    @staticmethod
    def _payload(statechart: Statechart,
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
        :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
        :param success_id: the id of the state a transition must point to if the Before operator succeeds.
        :param failure_id: the id of the state a transition must point to if the Before operator fails.
        """

        ip = UniqueIdProvider()

        # This composite state is only created so that the payload
        # is entirely included in a state, and has no "floating" states
        composite = CompoundState(id, initial=ip('waiting_comp'))
        statechart.add_state(composite, parent=parent_id)

        waiting_comp = CompoundState(ip('waiting_comp'), initial=ip('waiting'))
        statechart.add_state(waiting_comp, parent=id)

        statechart.add_state(BasicState(ip('waiting')), parent=ip('waiting_comp'))

        statechart.add_transition(Transition(source=ip('waiting_comp'), target=success_id, event=success_a))
        statechart.add_transition(Transition(source=ip('waiting'), target=failure_id, event=success_b))
        statechart.add_transition(Transition(source=ip('waiting'), target=failure_id, event=failure_a))

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart,
                                id=id,
                                parent_id=parent_id,
                                status_id=status_id,
                                success_id=success_id,
                                failure_id=failure_id,
                                condition_a=self.a,
                                condition_b=self.b,
                                payload_function=Before._payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


class During(Condition):
    """
    This condition is verified iff an other condition is verified during a specified time interval.
    The time interval is specified as a pair of positive integers (start, length), so that the condition
    must be verified in the [start, start+length] interval.

    The time is expressed in the unit than in the rest of Sismic. The interval limits are relative to
    the moment at which the InTime condition begins to be checked.
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
        self.cond = cond
        self.start = start
        self.length = lenght

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        parallel_id = id
        ip = UniqueIdProvider()

        parallel = OrthogonalState(id)
        statechart.add_state(parallel, parent_id)

        cond_block = CompoundState(ip('cond_block'), initial=ip('condition'))
        statechart.add_state(cond_block, parallel_id)

        success_a = BasicState(ip('success_a'), on_entry='send("{}")'.format(ip('success_event')))
        statechart.add_state(success_a, ip('cond_block'))

        failure_a = BasicState(ip('failure_a'), on_entry='send("{}")'.format(ip('failure_event')))
        statechart.add_state(failure_a, ip('cond_block'))

        self.cond.add_to(statechart,
                         id=ip('condition'),
                         parent_id=ip('cond_block'),
                         status_id=status_id,
                         success_id=ip('success_a'),
                         failure_id=ip('failure_a'))

        time_block = CompoundState(ip('time_block'), initial=ip('too_early'))
        statechart.add_state(time_block, parallel_id)
        statechart.add_state(BasicState(ip('too_early')), ip('time_block'))
        statechart.add_state(BasicState(ip('valid')), ip('time_block'))

        statechart.add_transition(Transition(source=ip('too_early'),
                                             target=ip('valid'),
                                             guard='after({})'.format(self.start)))
        statechart.add_transition(Transition(source=ip('too_early'),
                                             target=failure_id,
                                             event=ip('success_event')))
        statechart.add_transition(Transition(source=ip('too_early'),
                                             target=failure_id,
                                             event=ip('failure_event')))

        statechart.add_transition(Transition(source=ip('valid'),
                                             target=success_id,
                                             event=ip('success_event')))
        statechart.add_transition(Transition(source=ip('valid'),
                                             target=failure_id,
                                             event=ip('failure_event')))
        statechart.add_transition(Transition(source=ip('valid'),
                                             target=failure_id,
                                             guard='after({})'.format(self.length)))

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self.cond, self.start, self.length)


class IfElse(Condition):
    """
    This condition is equivalent to an other condition, depending of the value of a third condition.
    """
    def __init__(self, condition: Condition, a: Condition, b: Condition):
        """
        :param condition: a test condition that determines the condition that will be equivalent to the IfElse condition.
        The IfElse condition may remain undetermined while the test condition remains undetermined.
        If the test condition is determined, condition a or condition b is chosen based on the value of the condition :

        if(condition) a else b

        Due to the fail-fast mechanism, the IfElse condition may be determined even if the test condition is not (yet)
        determined. For instance, the following condition is determined:

        IfElse(UndeterminedCondition(), FalseCondition(), FalseCondition())

        :param a: the condition that is equivalent to the changing condition before a given condition is verified.
        :param b: the condition that is equivalent to the changing condition after the given condition is verified.
        """
        Condition.__init__(self)
        self.a = a
        self.b = b
        self.condition = condition

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        Or(And(self.condition, self.a),
           And(Not(self.condition), self.b)).add_to(statechart, id, parent_id, status_id, success_id, failure_id)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self.condition, self.a, self.b)


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
        Condition.__init__(self)
        self.condition = condition
        self.delay = delay

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        ip = UniqueIdProvider()

        statechart.add_state(CompoundState(id), parent_id)

        self.condition.add_to(statechart,
                              id=ip('condition'),
                              parent_id=parent_id,
                              status_id=status_id,
                              success_id=success_id,
                              failure_id=failure_id)
        statechart.add_transition(Transition(source=id, target=ip('condition'), guard='after({})'.format(self.delay)))

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.condition, self.delay)


class DelayedTrueCondition(Condition):
    """
    This condition becomes true after a given delay.
    """

    def __init__(self, delay: int):
        """
        :param delay: A positive or null value representing the time
        to wait before the condition becomes verified.
        """
        Condition.__init__(self)
        self.delay = delay

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        DelayedCondition(TrueCondition(), self.delay).add_to(statechart,
                                                             id=id,
                                                             parent_id=parent_id,
                                                             status_id=status_id,
                                                             success_id=success_id,
                                                             failure_id=failure_id)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self.delay)


class DelayedFalseCondition(Condition):
    """
    This condition becomes false after a given delay.
    """

    def __init__(self, delay: int):
        Condition.__init__(self)
        self.delay = delay

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        DelayedCondition(FalseCondition(), self.delay).add_to(statechart,
                                                              id=id,
                                                              parent_id=parent_id,
                                                              status_id=status_id,
                                                              success_id=success_id,
                                                              failure_id=failure_id)

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self.delay)


class ActiveState(Condition):
    """
    This condition is verified if a given state is active when evaluated. Otherwise, the condition is not verified.
    This property is asynchronous and may therefore lead to an "infinite loop".
    """

    def __init__(self, state: str):
        """
        :param state: the id of the state to check.
        """
        Condition.__init__(self)
        self.state = state

    def add_to(self, statechart: Statechart, id: str, parent_id: str, status_id: str, success_id: str, failure_id: str):
        ip = UniqueIdProvider()

        statechart.add_state(CompoundState(ip('composite'), initial=ip('inactive_state')), parent=status_id)
        statechart.add_state(BasicState(ip('inactive_state')), parent=ip('composite'))
        statechart.add_state(BasicState(ip('active_state')), parent=ip('composite'))

        statechart.add_transition(Transition(source=ip('inactive_state'),
                                             target=ip('active_state'),
                                             event=Condition.STATE_ENTERED_EVENT,
                                             guard='event.state == "{}"'.format(self.state)))
        statechart.add_transition(Transition(source=ip('active_state'),
                                             target=ip('inactive_state'),
                                             event=Condition.STATE_EXITED_EVENT,
                                             guard='event.state == "{}"'.format(self.state)))

        statechart.add_state(BasicState(id), parent_id)

        statechart.add_transition(Transition(source=id,
                                             target=success_id,
                                             guard='active("{}")'.format(ip('active_state'))))
        statechart.add_transition(Transition(source=id,
                                             target=failure_id,
                                             guard='active("{}")'.format(ip('inactive_state'))))

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self.state)


class InactiveState(Condition):
    """
    This condition is verified if a given state is inactive when evaluated. Otherwise, the condition is not verified.
    This condition is artificially made synchronous by waiting a 'end step' event to occur before
    leaving its undetermined state.
    """
    def __init__(self, state):
        Condition.__init__(self)
        self.state = state

    def add_to(self,
               statechart: Statechart,
               id: str,
               parent_id: str,
               status_id: str,
               success_id: str,
               failure_id: str):
        Not(ActiveState(self.state)).add_to(statechart=statechart,
                                            id=id,
                                            parent_id=parent_id,
                                            status_id=status_id,
                                            success_id=success_id,
                                            failure_id=failure_id)

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self.state)


class SynchronousCondition(Condition):
    """
    This condition forces an arbitrary condition to remain in an undetermined status
    until a 'step ended' event occurs.
    More precisely, the arbitrary condition is evaluated as usually, but transitions to
    a success or a failure states are blocked until a 'step ended' event occurs.
    """

    def __init__(self, condition: Condition):
        Condition.__init__(self)
        self.condition = condition

    def add_to(self,
               statechart: Statechart,
               id: str,
               parent_id: str,
               status_id: str,
               success_id: str,
               failure_id: str):
        ip = UniqueIdProvider()

        statechart.add_state(CompoundState(id, initial=ip('condition')), parent=parent_id)

        statechart.add_state(BasicState(ip('waiting_success')), parent=id)
        statechart.add_state(BasicState(ip('waiting_failure')), parent=id)

        statechart.add_transition(Transition(source=ip('waiting_success'),
                                             target=success_id,
                                             event=Condition.END_STEP_EVENT))
        statechart.add_transition(Transition(source=ip('waiting_failure'),
                                             target=failure_id,
                                             event=Condition.END_STEP_EVENT))

        self.condition.add_to(statechart=statechart,
                              id=ip('condition'),
                              parent_id=id,
                              status_id=status_id,
                              success_id=ip('waiting_success'),
                              failure_id=ip('waiting_failure'))

    def __repr__(self):
        return self.__class__.__name__ + '("{}")'.format(self.condition)


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
    :param condition_payload: The way to combine conditions using sent events
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
    condition_a.add_to(statechart,
                       id=ip('a'),
                       parent_id=ip('compound_a'),
                       status_id=status_id,
                       success_id=ip('success_a'),
                       failure_id=ip('failure_a'))

    compound_b = CompoundState(ip('compound_b'), initial=ip('b'))
    statechart.add_state(compound_b, id)
    success_b = BasicState(ip('success_b'), on_entry='send("{}")'.format(ip('b_true')))
    statechart.add_state(success_b, ip('compound_b'))
    failure_b = BasicState(ip('failure_b'), on_entry='send("{}")'.format(ip('b_false')))
    statechart.add_state(failure_b, ip('compound_b'))
    condition_b.add_to(statechart,
                       id=ip('b'),
                       parent_id=ip('compound_b'),
                       status_id=status_id,
                       success_id=ip('success_b'),
                       failure_id=ip('failure_b'))

    payload_function(statechart, 
                     id=ip('payload_id'), 
                     parent_id=id, 
                     success_a=ip('a_true'), 
                     failure_a=ip('a_false'), 
                     success_b=ip('b_true'), 
                     failure_b=ip('b_false'), 
                     success_id=success_id, 
                     failure_id=failure_id)


class TemporalExpression:
    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        self.decision = decision
        self.premise = premise
        self.consequence = consequence

    def _prepare_statechart(self,
                            parallel_id: str,
                            rule_satisfied_id: str,
                            rule_not_satisfied_id: str):
        """
        Generates a partial statechart for representing the expression of a rule.

        :param parallel_id: id of the parallel state containing the machine and the other parallel states.
        :param rule_satisfied_id: the id of the state representing the fact that the rule is satisfied.
        :param rule_not_satisfied_id: the id of the state representing the fact that the rule is not satisfied.
        :return: a prepared statechart
        """
        ip = UniqueIdProvider()

        statechart = Statechart(ip('statechart'))

        statechart.add_state(CompoundState(ip('global_id'), initial=parallel_id), None)
        statechart.add_state(OrthogonalState(parallel_id), parent=ip('global_id'))

        statechart.add_state(FinalState(ip('final_state')), parent=ip('global_id'))

        statechart.add_state(BasicState(rule_satisfied_id), parent=ip('global_id'))
        if self.decision:
            statechart.add_transition(Transition(source=rule_satisfied_id, target=ip('final_state')))

        statechart.add_state(BasicState(rule_not_satisfied_id), parent=ip('global_id'))
        if not self.decision:
            statechart.add_transition(Transition(source=rule_not_satisfied_id, target=ip('final_state')))

        return statechart

    def generate_statechart(self):
        """
        Generates a statechart representing the expression.
        :return: a tester statechart representing the expression.
        """
        pass

    def __repr__(self):
        return self.__class__.__name__ + "({}, {}, {})".format(self.decision,
                                                               self.premise.__repr__(),
                                                               self.consequence.__repr__())


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
        - True means the rule is required, and the consequence must be verified each time the premise is verified.
        - False means the rule is forbidden, and the consequence must be not verified each time the premise is verified.
        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time the premise is verified.
        """
        TemporalExpression.__init__(self, decision, premise, consequence)

    def generate_statechart(self):
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

        ip = UniqueIdProvider()

        statechart = self._prepare_statechart(parallel_id=ip('parallel'),
                                              rule_satisfied_id=ip('rule_satisfied'),
                                              rule_not_satisfied_id=ip('rule_not_satisfied'))

        statechart.add_state(CompoundState(ip('global'), initial=ip('premise')), parent=ip('parallel'))

        self.consequence.add_to(statechart,
                                id=ip('consequence'),
                                parent_id=ip('global'),
                                status_id=ip('parallel'),
                                success_id=ip('rule_satisfied'),
                                failure_id=ip('rule_not_satisfied'))

        statechart.add_transition(Transition(source=ip('consequence'),
                                             target=ip('rule_not_satisfied'),
                                             event=Condition.STOPPED_EVENT))

        SynchronousCondition(self.premise).add_to(statechart,
                                                  id=ip('premise'),
                                                  parent_id=ip('global'),
                                                  status_id=ip('parallel'),
                                                  success_id=ip('consequence'),
                                                  failure_id=ip('premise'))

        statechart.add_transition(Transition(source=ip('premise'),
                                             target=ip('rule_satisfied'),
                                             event=Condition.STOPPED_EVENT))

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
        - True means the rule is required, and the consequence must be verified each time the premise is verified.
        - False means the rule is forbidden, and the consequence must be not verified each time the premise is verified.
        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time the premise is verified.
        """
        TemporalExpression.__init__(self, decision, premise, consequence)

    def generate_statechart(self):
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

        ip = UniqueIdProvider()

        statechart = self._prepare_statechart(parallel_id=ip('parallel'),
                                              rule_satisfied_id=ip('rule_satisfied'),
                                              rule_not_satisfied_id=ip('rule_not_satisfied'))

        statechart.add_state(CompoundState(ip('global'), initial=ip('premise')), parent=ip('parallel'))

        statechart.add_state(CompoundState(ip('consequence_wrapper'), initial=ip('consequence')), parent=ip('global'))

        SynchronousCondition(self.premise).add_to(statechart,
                                                  id=ip('premise'),
                                                  parent_id=ip('global'),
                                                  status_id=ip('parallel'),
                                                  success_id=ip('consequence_wrapper'),
                                                  failure_id=ip('premise'))

        self.consequence.add_to(statechart,
                                id=ip('consequence'),
                                parent_id=ip('consequence_wrapper'),
                                status_id=ip('parallel'),
                                success_id=ip('premise'),
                                failure_id=ip('rule_not_satisfied'))

        statechart.add_transition(Transition(source=ip('consequence'),
                                             target=ip('rule_not_satisfied'),
                                             event=Condition.STOPPED_EVENT))

        statechart.add_transition(Transition(source=ip('premise'),
                                             target=ip('rule_satisfied'),
                                             event=Condition.STOPPED_EVENT))

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
        - True means the rule is required, and the consequence must be verified each time the premise is verified.
        - False means the rule is forbidden, and the consequence must be not verified each time the premise is verified.
        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time the premise is verified.
        """
        TemporalExpression.__init__(self, decision, premise, consequence)

    def generate_statechart(self):
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

        ip = UniqueIdProvider()

        statechart = self._prepare_statechart(parallel_id=ip('parallel'),
                                              rule_satisfied_id=ip('rule_satisfied'),
                                              rule_not_satisfied_id=ip('rule_not_satisfied'))

        # For the premise
        statechart.add_state(CompoundState(ip('premise_parallel'), initial=ip('premise')), parent=ip('parallel'))
        statechart.add_state(BasicState(ip('premise_success'), on_entry='send("{}")'.format(ip('reset_event'))),
                             parent=ip('premise_parallel'))

        SynchronousCondition(self.premise).add_to(statechart,
                                                  id=ip('premise'),
                                                  parent_id=ip('premise_parallel'),
                                                  status_id=ip('parallel'),
                                                  success_id=ip('premise_success'),
                                                  failure_id=ip('premise'))

        statechart.add_transition(Transition(source=ip('premise_success'),
                                             target=ip('premise')))

        # For the consequence
        statechart.add_state(CompoundState(ip('consequence_parallel'), initial=ip('waiting')), parent=ip('parallel'))

        statechart.add_state(BasicState(ip('waiting')), parent=ip('consequence_parallel'))

        statechart.add_state(CompoundState(ip('consequence_comp'), initial=ip('consequence')),
                             parent=ip('consequence_parallel'))

        statechart.add_transition(Transition(source=ip('consequence_comp'),
                                             target=ip('consequence_comp'),
                                             event=(ip('reset_event'))))

        statechart.add_transition(Transition(source=ip('waiting'),
                                             target=ip('rule_satisfied'),
                                             event=Condition.STOPPED_EVENT))
        statechart.add_transition(Transition(source=ip('waiting'),
                                             target=ip('consequence_comp'),
                                             event=(ip('reset_event'))))

        consequence_success = BasicState(ip('consequence_success'))
        statechart.add_state(consequence_success, parent=ip('consequence_comp'))
        statechart.add_transition(Transition(source=ip('consequence_success'),
                                             target=ip('rule_satisfied'),
                                             event=Condition.STOPPED_EVENT))

        consequence_failure = BasicState(ip('consequence_failure'))
        statechart.add_state(consequence_failure, parent=ip('consequence_comp'))
        statechart.add_transition(
            Transition(source=ip('consequence_failure'),
                       target=ip('rule_not_satisfied'),
                       event=Condition.STOPPED_EVENT))

        self.consequence.add_to(statechart,
                                id=ip('consequence'),
                                parent_id=ip('consequence_comp'),
                                status_id=ip('parallel'),
                                success_id=ip('consequence_success'),
                                failure_id=ip('consequence_failure'))

        statechart.add_transition(Transition(source=ip('consequence'),
                                             target=ip('rule_not_satisfied'),
                                             event=Condition.STOPPED_EVENT))

        return statechart


class AtLeastOnce(TemporalExpression):
    """
    An expression that checks if a consequence is verified at least one time after an associated premise
    has been verified.

    For instance, AtLeastOnce(False, A, B) means that, after has been verified at least one time, B must never be verified.

    If the premise is never verified, the rule shall be deemed verified, and consequently, if the rule was required, the
    expression is also verified; if the rule was forbidden, the expression is not verified.
    """

    def __init__(self, decision: bool, premise: Condition, consequence: Condition):
        """
        :param decision: determine the behaviour to adopt when a rule made of a premise and an associated consequence
        are verified (or not):
        - True means the rule is required, and the consequence must be verified each time the premise is verified.
        - False means the rule is forbidden, and the consequence must be not verified each time the premise is verified.
        :param premise: a condition that can be verified.
        :param consequence: the consequence that must be verified each time the premise is verified.
        """
        TemporalExpression.__init__(self, decision, premise, consequence)

    def generate_statechart(self):
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

        ip = UniqueIdProvider()

        statechart = self._prepare_statechart(parallel_id=ip('parallel'),
                                              rule_satisfied_id=ip('rule_satisfied'),
                                              rule_not_satisfied_id=ip('rule_not_satisfied'))

        # For the premise and the consequence
        statechart.add_state(CompoundState(ip('premise_consequence'), initial=ip('premise')), parent=ip('parallel'))

        statechart.add_state(BasicState(ip('premise_success')), parent=ip('premise_consequence'))

        SynchronousCondition(self.premise).add_to(statechart,
                                                  id=ip('premise'),
                                                  parent_id=ip('premise_consequence'),
                                                  status_id=ip('parallel'),
                                                  success_id=ip('premise_success'),
                                                  failure_id=ip('premise'))

        self.consequence.add_to(statechart=statechart,
                                id=ip('consequence'),
                                parent_id=ip('premise_consequence'),
                                status_id=ip('parallel'),
                                success_id=ip('rule_satisfied'),
                                failure_id=ip('premise'))

        statechart.add_transition(Transition(source=ip('premise_success'),
                                             target=ip('consequence'),
                                             action='send("{}")'.format(ip('checked_event'))))

        # For the fact that the premise has been checked at least one time
        statechart.add_state(CompoundState(ip('checked_parallel'), initial=ip('never')), parent=ip('parallel'))

        statechart.add_state(BasicState(ip('never')), parent=ip('checked_parallel'))
        statechart.add_state(BasicState(ip('checked')), parent=ip('checked_parallel'))

        statechart.add_transition(Transition(source=ip('never'), target=ip('checked'), event=ip('checked_event')))

        statechart.add_transition(Transition(source=ip('never'),
                                             target=ip('rule_satisfied'),
                                             event=Condition.EXECUTION_STOPPED_EVENT))

        statechart.add_transition(Transition(source=ip('checked'),
                                             target=ip('rule_not_satisfied'),
                                             event=Condition.EXECUTION_STOPPED_EVENT))

        return statechart
