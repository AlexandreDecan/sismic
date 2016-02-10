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
    def add_to(self, statechart: Statechart, id: str, parent_state_id: str,
               success_state_id: str, failure_state_id: str):
        """
        Place states and transitions into an existing statechart in order to represent the transition.
        :param statechart: the statechart in which the states and transitions must be placed.
        :param id: the id of the state that represents the condition.
        :param parent_state_id: the id of the parent in which the representative state must be placed.
        :param success_state_id: the id of the (preexisting) state the success transition must point to.
        :param failure_state_id: the id of the (preexisting) state the failure transition must point to.
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

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str, success_state_id: str,
               failure_state_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_state_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)

        statechart.add_transition(Transition(source=waiting_id, target=success_state_id))


class FalseCondition(Condition):
    """
    This condition is always false, so that entering the representative state
    always ends up to the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str, success_state_id: str,
               failure_state_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_state_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)
        statechart.add_transition(Transition(source=waiting_id, target=failure_state_id))


class UndeterminedCondition(Condition):
    """
    This condition is never evaluated, so that entering the representative state
    never ends up to the success or the failure transition.
    """

    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str,
               success_state_id: str, failure_state_id: str):
        waiting_state = BasicState(id)
        statechart.add_state(waiting_state, parent_state_id)

        # These transitions are not followable, but are added so that success and failure transitions exist.
        statechart.add_transition(Transition(source=id, target = success_state_id, guard='False'))
        statechart.add_transition(Transition(source=id, target = failure_state_id, guard='False'))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
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

        statechart.add_transition(Transition(source=id, target=success_state_id, guard='active("{}")'.format(exit_id)))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
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

        statechart.add_transition(Transition(source=id, target=success_state_id, guard='active("{}")'.format(exit_id)))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        parallel_state = OrthogonalState(id)
        statechart.add_state(parallel_state, parent=parent_id)
        a_id = Counter.random()
        b_id = Counter.random()

        composite_a_id = Counter.random()
        composite_b_id = Counter.random()

        success_a_id = Counter.random()
        success_b_id = Counter.random()

        # These sentry states are required because one can not have two transitions leaving two states in different
        # parallel regions for reaching a third state being out of these regions.
        failure_a_id = Counter.random()
        failure_b_id = Counter.random()

        composite_a = CompoundState(composite_a_id, initial=a_id)
        statechart.add_state(composite_a, parent=id)

        success_a = BasicState(success_a_id)
        statechart.add_state(success_a, parent=composite_a_id)

        failure_a = BasicState(failure_a_id)
        statechart.add_state(failure_a, parent=composite_a_id)

        self.a.add_to(statechart, a_id, composite_a_id, success_a_id, failure_a_id)

        composite_b = CompoundState(composite_b_id, initial=b_id)
        statechart.add_state(composite_b, parent=id)

        success_b = BasicState(success_b_id)
        statechart.add_state(success_b, parent=composite_b_id)

        failure_b = BasicState(failure_b_id)
        statechart.add_state(failure_b, parent=composite_b_id)

        self.b.add_to(statechart, b_id, composite_b_id, success_b_id, failure_b_id)

        statechart.add_transition(Transition(source=id,
                                             target=success_state_id,
                                             guard='active("{}") and active("{}")'.format(success_a_id, success_b_id)))

        statechart.add_transition(Transition(source=id,
                                             target=failure_state_id,
                                             guard='active("{}") or active("{}")'.format(failure_a_id, failure_b_id)))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        parallel_state = OrthogonalState(id)
        statechart.add_state(parallel_state, parent=parent_id)
        a_id = Counter.random()
        b_id = Counter.random()

        composite_a_id = Counter.random()
        composite_b_id = Counter.random()

        success_a_id = Counter.random()
        success_b_id = Counter.random()

        # These sentry states are required because one can not have two transitions leaving two states in different
        # parallel regions for reaching a third state being out of these regions.
        failure_a_id = Counter.random()
        failure_b_id = Counter.random()

        composite_a = CompoundState(composite_a_id, initial=a_id)
        statechart.add_state(composite_a, parent=id)

        success_a = BasicState(success_a_id)
        statechart.add_state(success_a, parent=composite_a_id)

        failure_a = BasicState(failure_a_id)
        statechart.add_state(failure_a, parent=composite_a_id)

        self.a.add_to(statechart, a_id, composite_a_id, success_a_id, failure_a_id)

        composite_b = CompoundState(composite_b_id, initial=b_id)
        statechart.add_state(composite_b, parent=id)

        success_b = BasicState(success_b_id)
        statechart.add_state(success_b, parent=composite_b_id)

        failure_b = BasicState(failure_b_id)
        statechart.add_state(failure_b, parent=composite_b_id)

        self.b.add_to(statechart, b_id, composite_b_id, success_b_id, failure_b_id)

        statechart.add_transition(Transition(source=id,
                                             target=success_state_id,
                                             guard='active("{}") or active("{}")'.format(success_a_id, success_b_id)))

        statechart.add_transition(Transition(source=id,
                                             target=failure_state_id,
                                             guard='active("{}") and active("{}")'.format(failure_a_id, failure_b_id)))


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        condition_id = Counter.random()
        composite = CompoundState(id, initial=condition_id)
        statechart.add_state(composite, parent_id)

        self.condition.add_to(statechart, condition_id, id,
                              success_state_id=failure_state_id, failure_state_id=success_state_id)


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        a_id = Counter.random()
        b_id = Counter.random()

        composite = CompoundState(id, initial=a_id)
        statechart.add_state(composite, parent_id)

        self.b.add_to(statechart, b_id, id, success_state_id=success_state_id, failure_state_id=failure_state_id)
        self.a.add_to(statechart, a_id, id, success_state_id=a_id, failure_state_id=failure_state_id)


