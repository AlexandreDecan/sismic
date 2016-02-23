from sismic.model import Statechart, BasicState, FinalState, Transition, CompoundState, OrthogonalState


class Condition:
    """
    A condition is a property being true, false, or undetermined.
    Such a condition is expressed thanks to a set of states and transitions that can be added to a statechart.
    The resulting representation of the condition is a state having two output transitions.
    The success transition will be followed if the property is true.
    The failure transition will be followed if the property is false.
    While the property remains undetermined, none of these transitions are followed.
    """

    def add_to(self, statechart: Statechart, id: str, parent_id: str,
               success_id: str, failure_id: str):
        """
        Places states and transitions into an existing statechart in order to represent the transition.
        :param statechart: the statechart in which the states and transitions must be placed.
        :param id: the id of the state that represents the condition.
        :param parent_id: the id of the parent in which the representative state must be placed.
        :param success_id: the id of the (preexisting) state the success transition must point to.
        :param failure_id: the id of the (preexisting) state the failure transition must point to.
        :return:
        """
        pass


class TrueCondition(Condition):
    """
    This condition is always true, so that entering the representative state
    always ends up to the success transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)

        statechart.add_transition(Transition(source=waiting_id, target=success_id))

    def __repr__(self):
        return self.__class__.__name__ + "()"


class FalseCondition(Condition):
    """
    This condition is always false, so that entering the representative state
    always ends up to the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)
        statechart.add_transition(Transition(source=waiting_id, target=failure_id))

    def __repr__(self):
        return self.__class__.__name__ + "()"


class UndeterminedCondition(Condition):
    """
    This condition is never evaluated, so that entering the representative state
    never ends up to the success or the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        waiting_state = BasicState(id)
        statechart.add_state(waiting_state, parent_id)

        # These transitions are not followable, but are added so that success and failure transitions exist.
        statechart.add_transition(Transition(source=id, target=success_id, guard='False'))
        statechart.add_transition(Transition(source=id, target=failure_id, guard='False'))

    def __repr__(self):
        return self.__class__.__name__ + "()"


class Counter(object):
    next = 1

    @classmethod
    def random(cls):
        ret = cls.next
        cls.next = cls.compute_next(ret)
        return str(ret)

    @classmethod
    def compute_next(cls, previous):
        return previous + 1


class Enter(Condition):
    """
    A condition based on the fact that a given state has been entered at least one time.
    """

    def __init__(self, state_id: str):
        """
        :param state_id: the id of the state to observe.
        """
        Condition.__init__(self)
        self.state_id = state_id

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        waiting_id = Counter.random()
        exit_id = Counter.random()

        waiting = BasicState(waiting_id)
        exit_state = BasicState(exit_id)

        composite_state = CompoundState(name=id, initial=waiting_id)

        statechart.add_state(composite_state, parent_id)
        statechart.add_state(waiting, id)
        statechart.add_state(exit_state, id)

        statechart.add_transition(Transition(source=waiting_id,
                                             target=exit_id,
                                             event='entered',
                                             guard='event.state == "{}"'.format(self.state_id)))

        statechart.add_transition(Transition(source=id, target=success_id, guard='active("{}")'.format(exit_id)))

    def __repr__(self):
        return self.__class__.__name__ + "({})".format(self.state_id)


class Exit(Condition):
    """
    A condition based on the fact that a given state has been exited at least one time.
    """

    def __init__(self, state_id: str):
        """
        :param state_id: the id of the state to observe.
        """
        Condition.__init__(self)
        self.state_id = state_id

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        waiting_id = Counter.random()
        exit_id = Counter.random()

        waiting = BasicState(waiting_id)
        exit = BasicState(exit_id)

        composite_state = CompoundState(name=id, initial=waiting_id)

        statechart.add_state(composite_state, parent_id)
        statechart.add_state(waiting, id)
        statechart.add_state(exit, id)

        statechart.add_transition(Transition(source=waiting_id,
                                             target=exit_id,
                                             event='exited',
                                             guard=('event.state == "{}"'.format(self.state_id))))

        statechart.add_transition(Transition(source=id, target=success_id, guard='active("{}")'.format(exit_id)))

    def __repr__(self):
        return self.__class__.__name__ + "({})".format(self.state_id)


class Consume(Condition):
    def __init__(self, event):
        self.event = event


class Process(Condition):
    def __init__(self, step):
        self.step = step


class Wait(Condition):
    def __init__(self, time):
        self.time = time


class FinishStep(Condition):
    def __init__(self):
        pass


class BeActive(Condition):
    pass


class BeInactive(Condition):
    pass


def _and_payload(statechart: Statechart,
                 id: str,
                 parent_state_id: str,
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

    waiting_id = Counter.random()
    partial_id = Counter.random()

    # This composite state is only created so that the payload
    # is entirely included in a state, and has no "floating"
    # states
    composite = CompoundState(id, initial=waiting_id)
    statechart.add_state(composite, parent_state_id)

    waiting = BasicState(waiting_id)
    statechart.add_state(waiting, id)

    partial = BasicState(partial_id)
    statechart.add_state(partial, id)

    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=success_a))
    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=success_b))

    statechart.add_transition(Transition(source=waiting_id, target=failure_id, event=failure_a))
    statechart.add_transition(Transition(source=waiting_id, target=failure_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=failure_id, event=failure_a))
    statechart.add_transition(Transition(source=partial_id, target=failure_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=success_id, event=success_a))
    statechart.add_transition(Transition(source=partial_id, target=success_id, event=success_b))


def _or_payload(statechart: Statechart,
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

    waiting_id = Counter.random()
    partial_id = Counter.random()

    # This composite state is only created so that the payload
    # is entirely included in a state, and has no "floating"
    # states
    composite = CompoundState(id, initial=waiting_id)
    statechart.add_state(composite, parent_id)

    waiting = BasicState(waiting_id)
    statechart.add_state(waiting, id)

    partial = BasicState(partial_id)
    statechart.add_state(partial, id)

    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=failure_a))
    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=failure_id, event=failure_a))
    statechart.add_transition(Transition(source=partial_id, target=failure_id, event=failure_b))

    statechart.add_transition(Transition(source=id, target=success_id, event=success_a))
    statechart.add_transition(Transition(source=id, target=success_id, event=success_b))


def _xor_payload(statechart: Statechart,
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

    waiting_id = Counter.random()
    a_success_id = Counter.random()
    a_failure_id = Counter.random()
    b_success_id = Counter.random()
    b_failure_id = Counter.random()

    # This composite state is only created so that the payload
    # is entirely included in a state, and has no "floating"
    # states
    composite = CompoundState(id, initial=waiting_id)
    statechart.add_state(composite, parent_id)

    waiting = BasicState(waiting_id)
    statechart.add_state(waiting, id)

    a_success = BasicState(a_success_id)
    statechart.add_state(a_success, id)

    a_failure = BasicState(a_failure_id)
    statechart.add_state(a_failure, id)

    b_success = BasicState(b_success_id)
    statechart.add_state(b_success, id)

    b_failure = BasicState(b_failure_id)
    statechart.add_state(b_failure, id)

    # First property
    statechart.add_transition(Transition(source=waiting_id, target=a_success_id, event=success_a))
    statechart.add_transition(Transition(source=waiting_id, target=a_failure_id, event=failure_a))
    statechart.add_transition(Transition(source=waiting_id, target=b_success_id, event=success_b))
    statechart.add_transition(Transition(source=waiting_id, target=b_failure_id, event=failure_b))

    # Second property
    statechart.add_transition(Transition(source=a_success_id, target=success_id, event=failure_b))
    statechart.add_transition(Transition(source=a_success_id, target=failure_id, event=success_b))

    statechart.add_transition(Transition(source=a_failure_id, target=success_id, event=success_b))
    statechart.add_transition(Transition(source=a_failure_id, target=failure_id, event=failure_b))

    statechart.add_transition(Transition(source=b_success_id, target=success_id, event=failure_a))
    statechart.add_transition(Transition(source=b_success_id, target=failure_id, event=success_a))

    statechart.add_transition(Transition(source=b_failure_id, target=success_id, event=success_a))
    statechart.add_transition(Transition(source=b_failure_id, target=failure_id, event=failure_a))


def _before_payload(statechart: Statechart,
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

    waiting_id = Counter.random()

    # This composite state is only created so that the payload
    # is entirely included in a state, and has no "floating" states
    composite = CompoundState(id, initial=waiting_id)
    statechart.add_state(composite, parent_id)

    waiting = BasicState(waiting_id)
    statechart.add_state(waiting, id)

    statechart.add_transition(Transition(source=waiting_id, target=success_id, event=success_a))
    statechart.add_transition(Transition(source=waiting_id, target=failure_id, event=success_b))
    statechart.add_transition(Transition(source=waiting_id, target=failure_id, event=failure_a))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart, id, parent_id, success_id, failure_id, self.a, self.b, _and_payload)

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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart, id, parent_id, success_id, failure_id, self.a, self.b, _or_payload)

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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart, id, parent_id, success_id, failure_id, self.a, self.b, _xor_payload)

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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        condition_id = Counter.random()
        composite = CompoundState(id, initial=condition_id)
        statechart.add_state(composite, parent_id)

        self.condition.add_to(statechart, id=condition_id, parent_id=id, success_id=failure_id, failure_id=success_id)

    def __repr__(self):
        return self.__class__.__name__ + "({})".format(self.condition)


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        a_id = Counter.random()
        b_id = Counter.random()

        composite = CompoundState(id, initial=a_id)
        statechart.add_state(composite, parent_id)

        self.b.add_to(statechart, id=b_id, parent_id=id, success_id=success_id, failure_id=failure_id)
        self.a.add_to(statechart, id=a_id, parent_id=id, success_id=b_id, failure_id=failure_id)

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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        _add_parallel_condition(statechart, id, parent_id, success_id, failure_id, self.a, self.b, _before_payload)

    def __repr__(self):
        return self.__class__.__name__ + "({}, {})".format(self.a, self.b)


class InTime(Condition):
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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):

        parallel_id = id
        condition_id = Counter.random()
        cond_block_id = Counter.random()
        time_block_id = Counter.random()
        too_early_id = Counter.random()
        valid_id = Counter.random()
        success_a_id = Counter.random()
        failure_a_id = Counter.random()
        success_event_id = Counter.random()
        failure_event_id = Counter.random()

        parallel = OrthogonalState(id)
        statechart.add_state(parallel, parent_id)

        cond_block = CompoundState(cond_block_id, initial=condition_id)
        statechart.add_state(cond_block, parallel_id)

        success_a = BasicState(success_a_id, on_entry='send("{}")'.format(success_event_id))
        statechart.add_state(success_a, cond_block_id)

        failure_a = BasicState(failure_a_id, on_entry='send("{}")'.format(failure_event_id))
        statechart.add_state(failure_a, cond_block_id)

        self.cond.add_to(statechart, condition_id, cond_block_id, success_a_id, failure_a_id)

        time_block = CompoundState(time_block_id, initial=too_early_id)
        statechart.add_state(time_block, parallel_id)
        statechart.add_state(BasicState(too_early_id), time_block_id)
        statechart.add_state(BasicState(valid_id), time_block_id)

        statechart.add_transition(Transition(source=too_early_id,
                                             target=valid_id,
                                             guard='after({})'.format(self.start)))
        statechart.add_transition(Transition(source=too_early_id,
                                             target=failure_id,
                                             event=success_event_id))
        statechart.add_transition(Transition(source=too_early_id,
                                             target=failure_id,
                                             event=failure_event_id))

        statechart.add_transition(Transition(source=valid_id,
                                             target=success_id,
                                             event=success_event_id))
        statechart.add_transition(Transition(source=valid_id,
                                             target=failure_id,
                                             event=failure_event_id))
        statechart.add_transition(Transition(source=valid_id,
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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        Or(And(self.condition, self.a),
           And(Not(self.condition), self.b)).add_to(statechart, id, parent_id, success_id, failure_id)

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

    def add_to(self,
               statechart: Statechart,
               id: str,
               parent_id: str,
               success_id: str,
               failure_id: str):

        condition_id = Counter.random()

        waiting = CompoundState(id)
        statechart.add_state(waiting, parent_id)

        self.condition.add_to(statechart, condition_id, parent_id, success_id, failure_id)
        statechart.add_transition(Transition(source=id, target=condition_id, guard='after({})'.format(self.delay)))

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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        DelayedCondition(TrueCondition(), self.delay).add_to(statechart, id, parent_id, success_id, failure_id)

    def __repr__(self):
        return self.__class__.__name__ + "({})".format(self.delay)


class DelayedFalseCondition(Condition):
    """
    This condition becomes false after a given delay.
    """

    def __init__(self, delay: int):
        Condition.__init__(self)
        self.delay = delay

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_id: str, failure_id: str):
        DelayedCondition(FalseCondition(), self.delay).add_to(statechart, id, parent_id, success_id, failure_id)


    def __repr__(self):
        return self.__class__.__name__ + "({})".format(self.delay)


def _add_parallel_condition(statechart: Statechart,
                            id: str,
                            parent_id: str,
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
    :param success_id: the id of the state that must be reached if the condition succeeds.
    :param failure_id: the id of the state that must be reached if the condition fails.
    :param condition_a: a condition.
    :param condition_b: an other condition.
    :param condition_payload: The way to combine conditions using sent events
    """

    compound_a_id = Counter.random()
    compound_b_id = Counter.random()
    success_a_id = Counter.random()
    failure_a_id = Counter.random()
    success_b_id = Counter.random()
    failure_b_id = Counter.random()
    a_id = Counter.random()
    b_id = Counter.random()
    payload_id = Counter.random()

    a_true = Counter.random()
    a_false = Counter.random()
    b_true = Counter.random()
    b_false = Counter.random()

    parallel_state = OrthogonalState(id)
    statechart.add_state(parallel_state, parent_id)

    compound_a = CompoundState(compound_a_id, initial=a_id)
    statechart.add_state(compound_a, id)
    success_a = BasicState(success_a_id, on_entry='send("{}")'.format(a_true))
    statechart.add_state(success_a, compound_a_id)
    failure_a = BasicState(failure_a_id, on_entry='send("{}")'.format(a_false))
    statechart.add_state(failure_a, compound_a_id)
    condition_a.add_to(statechart, a_id, compound_a_id, success_id=success_a_id, failure_id=failure_a_id)

    compound_b = CompoundState(compound_b_id, initial=b_id)
    statechart.add_state(compound_b, id)
    success_b = BasicState(success_b_id, on_entry='send("{}")'.format(b_true))
    statechart.add_state(success_b, compound_b_id)
    failure_b = BasicState(failure_b_id, on_entry='send("{}")'.format(b_false))
    statechart.add_state(failure_b, compound_b_id)
    condition_b.add_to(statechart, b_id, compound_b_id, success_id=success_b_id, failure_id=failure_b_id)

    payload_function(statechart, payload_id, id, a_true, a_false, b_true, b_false, success_id, failure_id)


def _prepare_statechart(decision: bool, status_id: str, machine_id: str, rule_satisfied_id: str, rule_not_satisfied_id: str, initial_id: str):
    """
    Generates a partial statechart for representing the expression of a rule.

    :param decision: True if the rule must be verified, False if the rule is forbidden.
    :param status_id: the id of the parallel state containing the status of the tested statechart.
    :param machine_id: the id of the parallel state containing the states and transitions representing the rule.
    :param rule_satisfied_id: the id of the state representing the fact that the rule is satisfied.
    :param rule_not_satisfied_id: the id of the state representing the fact that the rule is not satisfied.
    :param initial_id: the id of the initial state.
    :return: a prepared statechart
    """

    statechart = Statechart(Counter.random())

    global_id = Counter.random()
    parallel_id = Counter.random()
    final_state_id = Counter.random()

    statechart.add_state(CompoundState(global_id, initial=parallel_id), None)
    statechart.add_state(OrthogonalState(parallel_id), global_id)

    statechart.add_state(OrthogonalState(status_id), parallel_id)
    # Without this 'useless' basic state, an empty orthogonal state prevents the stachart to finish.
    statechart.add_state(BasicState(Counter.random()), status_id)
    statechart.add_state(CompoundState(machine_id, initial=initial_id), parallel_id)

    final_state = FinalState(final_state_id)
    statechart.add_state(final_state, global_id)

    rule_satisfied = BasicState(rule_satisfied_id)
    statechart.add_state(rule_satisfied, machine_id)
    if decision:
        statechart.add_transition(Transition(source=rule_satisfied_id, target=final_state_id))

    rule_not_satisfied = BasicState(rule_not_satisfied_id)
    statechart.add_state(rule_not_satisfied, machine_id)
    if not decision:
        statechart.add_transition(Transition(source=rule_not_satisfied_id, target=final_state_id))

    return statechart


def prepare_first_time_expression(decision: bool, premise: Condition, consequence: Condition):
    """
    Generate a statechart representing the expression of a rule. Each rule has the following structure:

    decision premise consequence

    Where:

    - premise is a condition
    - consequence is a condition that must be verified if the premise is verified
    - decision determines if the rule verification is desired or not:
    True if the rule must be verified, False if the rule must be not verified.

    The rule is checked after the premise has been verified for the first time.

    For instance, prepare_first_time_expression(False, A, B) means that, after the first time A is verified,
    B must not be verified.

    If the premise is never verified, the rule shall be deemed verified.

    The resulting statechart has a unique final state that is reached if the rule is satisfied.

    :param decision: True if the rule must be verified: False if the rule must not be verified.
    :param premise: a condition
    :param consequence: a condition being checked if premise is verified
    :return: A statechart representing the given expression
    """

    CHECK_EVENT = 'stopped'
    ENDSTEP_EVENT = 'endstep'

    status_id = Counter.random()
    machine_id = Counter.random()
    consequence_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()
    premise_failure_id = Counter.random()
    premise_id = Counter.random()

    statechart = _prepare_statechart(decision, status_id, machine_id,
                                     rule_satisfied_id, rule_not_satisfied_id, premise_id)

    consequence.add_to(statechart,
                       id=consequence_id,
                       parent_id=machine_id,
                       success_id=rule_satisfied_id,
                       failure_id=rule_not_satisfied_id)
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    # This state avoids infinite loops if the premise is "always" false
    statechart.add_state(BasicState(premise_failure_id), machine_id)

    premise.add_to(statechart,
                   id=premise_id,
                   parent_id=machine_id,
                   success_id=consequence_id,
                   failure_id=premise_failure_id)

    statechart.add_transition(Transition(source=premise_failure_id, target=premise_id, event=ENDSTEP_EVENT))
    statechart.add_transition(Transition(source=premise_failure_id, target=rule_satisfied_id, event=CHECK_EVENT))
    statechart.add_transition(Transition(source=premise_id, target=rule_satisfied_id, event=CHECK_EVENT))

    return statechart


def prepare_every_time_expression(decision: bool, premise: Condition, consequence: Condition):
    """
    Generate a statechart representing the expression of a rule. Each rule has the following structure:

    decision premise consequence

    Where:

    - premise is a condition
    - consequence is a condition that must be verified if the premise is verified
    - decision determines if the rule verification is desired or not:
    True if the rule must be verified, False if the rule must be not verified.

    The rule is checked every time the premise is verified.

    For instance, prepare_every_time_expression(False, A, B) means that, each time A is verified,
    B must not be verified afterwards.

    If the premise is never verified, the rule shall be deemed verified.

    The resulting statemachine is such that, after the premise is verified, the next verification of this premise
    only occurs after the condition is verified.

    The resulting statechart has a unique final state that is reached if the rule is satisfied.

    :param decision: True if the rule must be verified: False if the rule must not be verified.
    :param premise: a condition
    :param consequence: a condition being checked if premise is verified
    :return: A statechart representing the given expression
    """
    CHECK_EVENT = 'stopped'
    ENDSTEP_EVENT = 'endstep'

    premise_id = Counter.random()
    premise_wrapper_id = Counter.random()
    consequence_wrapper_id = Counter.random()
    consequence_id = Counter.random()
    status_id = Counter.random()
    machine_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()
    premise_failure_id = Counter.random()

    statechart = _prepare_statechart(decision,
                                     status_id,
                                     machine_id,
                                     rule_satisfied_id,
                                     rule_not_satisfied_id,
                                     premise_wrapper_id)

    # Premise and consequence are wrapped into composite states for
    # 1 - Avoiding a cyclic dependency during their injection in the statechart
    # 2 - Provide a better isolation, so that a "hot" replacement of the premise or the consequence
    # would be easier.
    statechart.add_state(CompoundState(premise_wrapper_id, initial=premise_id), machine_id)
    statechart.add_state(CompoundState(consequence_wrapper_id, initial=consequence_id), machine_id)

    consequence.add_to(statechart, consequence_id, consequence_wrapper_id, premise_wrapper_id, rule_not_satisfied_id)
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    # This state avoids infinite loops if the premise is "always" false
    statechart.add_state(BasicState(premise_failure_id), premise_wrapper_id)

    premise.add_to(statechart, premise_id, premise_wrapper_id, consequence_wrapper_id, premise_failure_id)
    statechart.add_transition(Transition(source=premise_id, target=rule_satisfied_id, event=CHECK_EVENT))

    statechart.add_transition(Transition(source=premise_failure_id, target=premise_id, event=ENDSTEP_EVENT))
    statechart.add_transition(Transition(source=premise_failure_id, target=rule_satisfied_id, event=CHECK_EVENT))

    return statechart


def prepare_last_time_expression(decision: bool, premise: Condition, consequence: Condition):
    """
    Generate a statechart representing the expression of a rule. Each rule has the following structure:

    decision premise consequence

    Where:

    - premise is a condition
    - consequence is a condition that must be verified if the premise is verified
    - decision determines if the rule verification is desired or not:
    True if the rule must be verified, False if the rule must be not verified.

    The rule is checked after the premise is verified for the last time.

    For instance, prepare_last_time_expression(False, A, B) means that, the last time A is verified,
    B must not be verified afterwards.

    If the premise is never verified, the rule shall be deemed verified.

    The resulting statemachine is such that, after the premise is verified, the next verification of this premise
    only occurs after the condition is verified.

    The resulting statechart has a unique final state that is reached if the rule is satisfied.

    :param decision:
    :param premise:
    :param consequence:
    :return:
    """

    CHECK_EVENT = 'stopped'
    RESET_EVENT = 'reset'
    ENDSTEP_EVENT = 'endstep'

    premise_parallel_id = Counter.random()  # Parallel state for consequence stuff
    consequence_parallel_id = Counter.random()  # Parallel state for consequence stuff
    premise_id = Counter.random()
    premise_success_id = Counter.random()
    premise_failure_id = Counter.random()
    status_id = Counter.random()
    machine_id = Counter.random()
    parallel_id = Counter.random()
    consequence_id = Counter.random()
    consequence_comp_id = Counter.random()
    consequence_success_id = Counter.random()
    consequence_failure_id = Counter.random()
    waiting_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()

    statechart = _prepare_statechart(decision,
                                     status_id,
                                     machine_id,
                                     rule_satisfied_id,
                                     rule_not_satisfied_id,
                                     parallel_id)
    statechart.add_state(OrthogonalState(parallel_id), machine_id)

    # For the premise
    statechart.add_state(CompoundState(premise_parallel_id, initial=premise_id), parallel_id)
    statechart.add_state(BasicState(premise_success_id, on_entry='send("{}")'.format(RESET_EVENT)), premise_parallel_id)

    statechart.add_state(BasicState(premise_failure_id), premise_parallel_id)

    premise.add_to(statechart, premise_id, premise_parallel_id, premise_success_id, premise_failure_id)

    statechart.add_transition(Transition(source=premise_success_id, target=premise_id, event=ENDSTEP_EVENT))
    statechart.add_transition(Transition(source=premise_failure_id, target=premise_id, event=ENDSTEP_EVENT))

    # For the consequence
    statechart.add_state(CompoundState(consequence_parallel_id, initial=waiting_id), parallel_id)

    statechart.add_state(BasicState(waiting_id), consequence_parallel_id)

    consequence_comp = CompoundState(consequence_comp_id, initial=consequence_id)
    statechart.add_state(consequence_comp, consequence_parallel_id)
    statechart.add_transition(Transition(source=consequence_comp_id, target=consequence_comp_id, event=RESET_EVENT))

    statechart.add_transition(Transition(source=waiting_id, target=rule_satisfied_id, event=CHECK_EVENT))
    statechart.add_transition(Transition(source=waiting_id, target=consequence_comp_id, event=RESET_EVENT))

    consequence_success = BasicState(consequence_success_id)
    statechart.add_state(consequence_success, consequence_comp_id)
    statechart.add_transition(Transition(source=consequence_success_id, target=rule_satisfied_id, event=CHECK_EVENT))

    consequence_failure = BasicState(consequence_failure_id)
    statechart.add_state(consequence_failure, consequence_comp_id)
    statechart.add_transition(
        Transition(source=consequence_failure_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    consequence.add_to(statechart,
                       consequence_id,
                       consequence_comp_id,
                       success_id=consequence_success_id,
                       failure_id=consequence_failure_id)
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    return statechart
