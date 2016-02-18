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
        Places states and transitions into an existing statechart in order to represent the transition.
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
        statechart.add_transition(Transition(source=id, target=success_state_id, guard='False'))
        statechart.add_transition(Transition(source=id, target=failure_state_id, guard='False'))


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


def _and_payload(statechart: Statechart, id: str, parent_state_id: str,
                 success_a: str, failure_a: str,
                 success_b: str, failure_b: str,
                 success_state_id: str, failure_state_id: str):
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
    :param success_state_id: the id of the state a transition must point to if the AND operator succeeds.
    :param failure_state_id: the id of the state a transition must point to if the AND operator fails.
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

    statechart.add_transition(Transition(source=waiting_id, target=failure_state_id, event=failure_a))
    statechart.add_transition(Transition(source=waiting_id, target=failure_state_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=failure_state_id, event=failure_a))
    statechart.add_transition(Transition(source=partial_id, target=failure_state_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=success_state_id, event=success_a))
    statechart.add_transition(Transition(source=partial_id, target=success_state_id, event=success_b))


def _or_payload(statechart: Statechart, id: str, parent_state_id: str,
                success_a: str, failure_a: str,
                success_b: str, failure_b: str,
                success_state_id: str, failure_state_id: str):
    """
    Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
    arbitrary conditions, must be combined with a logic OR.
    :param statechart: the statechart in which the OR operator must be placed.
    :param id: the id of the composite state representing the OR operator.
    :param parent_state_id: the id of the parent state in which the composite state representing the OR operator
     must be placed.
    :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
    :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
    :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
    :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
    :param success_state_id: the id of the state a transition must point to if the OR operator succeeds.
    :param failure_state_id: the id of the state a transition must point to if the OR operator fails.
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

    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=failure_a))
    statechart.add_transition(Transition(source=waiting_id, target=partial_id, event=failure_b))

    statechart.add_transition(Transition(source=partial_id, target=failure_state_id, event=failure_a))
    statechart.add_transition(Transition(source=partial_id, target=failure_state_id, event=failure_b))

    statechart.add_transition(Transition(source=id, target=success_state_id, event=success_a))
    statechart.add_transition(Transition(source=id, target=success_state_id, event=success_b))


def _xor_payload(statechart: Statechart, id: str, parent_state_id: str,
                 success_a: str, failure_a: str,
                 success_b: str, failure_b: str,
                 success_state_id: str, failure_state_id: str):
    """
    Generates in a preexisting statechart a composite state that represents the way the results of A and B, two
    arbitrary conditions, must be combined with a logic XOR (exclusive OR).
    :param statechart: the statechart in which the XOR operator must be placed.
    :param id: the id of the composite state representing the XOR operator.
    :param parent_state_id: the id of the parent state in which the composite state representing the XOR operator
     must be placed.
    :param success_a: the name of the event that will be generated by the statechart if condition A succeeds.
    :param failure_a: the name of the event that will be generated by the statechart if condition A fails.
    :param success_b: the name of the event that will be generated by the statechart if condition A succeeds.
    :param failure_b: the name of the event that will be generated by the statechart if condition B succeeds.
    :param success_state_id: the id of the state a transition must point to if the XOR operator succeeds.
    :param failure_state_id: the id of the state a transition must point to if the XOR operator fails.
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
    statechart.add_state(composite, parent_state_id)

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
    statechart.add_transition(Transition(source=a_success_id, target=success_state_id, event=failure_b))
    statechart.add_transition(Transition(source=a_success_id, target=failure_state_id, event=success_b))

    statechart.add_transition(Transition(source=a_failure_id, target=success_state_id, event=success_b))
    statechart.add_transition(Transition(source=a_failure_id, target=failure_state_id, event=failure_b))

    statechart.add_transition(Transition(source=b_success_id, target=success_state_id, event=failure_a))
    statechart.add_transition(Transition(source=b_success_id, target=failure_state_id, event=success_a))

    statechart.add_transition(Transition(source=b_failure_id, target=success_state_id, event=success_a))
    statechart.add_transition(Transition(source=b_failure_id, target=failure_state_id, event=failure_a))

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
        add_parallel_condition(statechart, id, parent_id, success_state_id, failure_state_id, self.a, self.b,
                               _and_payload)


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
        add_parallel_condition(statechart, id, parent_id, success_state_id, failure_state_id, self.a, self.b,
                               _or_payload)


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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        add_parallel_condition(statechart, id, parent_id, success_state_id, failure_state_id, self.a, self.b,
                               _xor_payload)


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
        self.a.add_to(statechart, a_id, id, success_state_id=b_id, failure_state_id=failure_state_id)


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

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str,
               success_state_id: str, failure_state_id: str):
        pass


def add_parallel_condition(statechart: Statechart, id: str, parent_id: str, success_state_id: str,
                           failure_state_id: str,
                           condition_a: Condition, condition_b: Condition, payload_function):
    """
    Adds to a statechart an orthogonal state with 3 parallel composite states:
    1 - a composite state containing the composite state checking condition A, plus success and failure states for A
    2 - a composite state containing the composite state checking condition B, plus success and failure states for B
    3 - a 'condition' combining conditions A and B, based on received events revealing success or failure of A and B.

    :param statechart: the statechart in which the parallel condition must be added.
    :param parent_id: the id of the state in which the parallel condition must be added.
    :param success_state_id: the id of the state that must be reached if the condition succeeds.
    :param failure_state_id: the id of the state that must be reached if the condition fails.
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
    condition_a.add_to(statechart, a_id, compound_a_id, success_state_id=success_a_id, failure_state_id=failure_a_id)

    compound_b = CompoundState(compound_b_id, initial=b_id)
    statechart.add_state(compound_b, id)
    success_b = BasicState(success_b_id, on_entry='send("{}")'.format(b_true))
    statechart.add_state(success_b, compound_b_id)
    failure_b = BasicState(failure_b_id, on_entry='send("{}")'.format(b_false))
    statechart.add_state(failure_b, compound_b_id)
    condition_b.add_to(statechart, b_id, compound_b_id, success_state_id=success_b_id, failure_state_id=failure_b_id)

    payload_function(statechart, payload_id, id, a_true, a_false, b_true, b_false, success_state_id, failure_state_id)


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

    statechart = Statechart(Counter.random())

    global_id = Counter.random()
    parallel_id = Counter.random()
    status_id = Counter.random()
    machine_id = Counter.random()
    premise_id = Counter.random()
    consequence_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()
    final_state_id = Counter.random()

    statechart.add_state(CompoundState(global_id, initial=parallel_id), None)
    statechart.add_state(OrthogonalState(parallel_id), global_id)

    statechart.add_state(OrthogonalState(status_id), parallel_id)
    # Without this 'useless' basic state, an empty orthogonal state prevents the stachart to finish.
    statechart.add_state(BasicState(Counter.random()), status_id)
    statechart.add_state(CompoundState(machine_id, initial=premise_id), parallel_id)

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

    consequence.add_to(statechart, consequence_id, machine_id,
                       success_state_id=rule_satisfied_id, failure_state_id=rule_not_satisfied_id)
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    premise.add_to(statechart, premise_id, machine_id,
                   success_state_id=consequence_id, failure_state_id=premise_id)
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

    statechart = Statechart(Counter.random())

    global_id = Counter.random()
    parallel_id = Counter.random()
    status_id = Counter.random()
    machine_id = Counter.random()
    premise_id = Counter.random()
    consequence_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()
    final_state_id = Counter.random()

    statechart.add_state(CompoundState(global_id, initial=parallel_id), None)
    statechart.add_state(OrthogonalState(parallel_id), global_id)

    statechart.add_state(OrthogonalState(status_id), parallel_id)
    # Without this 'useless' basic state, an empty orthogonal state prevents the stachart to finish.
    statechart.add_state(BasicState(Counter.random()), status_id)
    statechart.add_state(CompoundState(machine_id, initial=premise_id), parallel_id)

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

    premise.add_to(statechart, premise_id, machine_id, success_state_id=consequence_id, failure_state_id=premise_id)
    consequence.add_to(statechart, consequence_id, machine_id,
                       success_state_id=premise_id, failure_state_id=rule_not_satisfied_id)

    statechart.add_transition(Transition(source=premise_id, target=rule_satisfied_id, event=CHECK_EVENT))
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

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

    statechart = Statechart(Counter.random())

    global_id = Counter.random()  # initial state
    parallel_id = Counter.random()  # main state
    status_id = Counter.random()  # Parallel state for statuses
    premise_parallel_id = Counter.random()  # Parallel state for premise stuff
    consequence_parallel_id = Counter.random()  # Parallel state for consequence stuff
    premise_id = Counter.random()
    premise_success_id = Counter.random()
    consequence_id = Counter.random()
    consequence_comp_id = Counter.random()
    consequence_success_id = Counter.random()
    consequence_failure_id = Counter.random()
    waiting_id = Counter.random()
    rule_satisfied_id = Counter.random()
    rule_not_satisfied_id = Counter.random()
    final_state_id = Counter.random()

    statechart.add_state(CompoundState(global_id, initial=parallel_id), None)
    statechart.add_state(OrthogonalState(parallel_id), global_id)

    # Linking to final state
    final_state = FinalState(final_state_id)
    statechart.add_state(final_state, global_id)

    rule_satisfied = BasicState(rule_satisfied_id)
    statechart.add_state(rule_satisfied, global_id)
    if decision:
        statechart.add_transition(Transition(source=rule_satisfied_id, target=final_state_id))

    rule_not_satisfied = BasicState(rule_not_satisfied_id)
    statechart.add_state(rule_not_satisfied, global_id)
    if not decision:
        statechart.add_transition(Transition(source=rule_not_satisfied_id, target=final_state_id))

    # For the statuses
    statechart.add_state(OrthogonalState(status_id), parallel_id)
    # Without this 'useless' basic state, an empty orthogonal state prevents the stachart to finish.
    statechart.add_state(BasicState(Counter.random()), status_id)

    # For the premise
    statechart.add_state(CompoundState(premise_parallel_id, initial=premise_id), parallel_id)
    premise.add_to(statechart, premise_id, premise_parallel_id,
                   success_state_id=premise_success_id, failure_state_id=premise_id)
    premise_success = BasicState(premise_success_id)
    statechart.add_state(premise_success, premise_parallel_id)
    statechart.add_transition(
        Transition(source=premise_success_id, target=premise_id, action='send(Event("{}"))'.format(RESET_EVENT)))

    # For the consequence
    statechart.add_state(CompoundState(consequence_parallel_id, initial=waiting_id), parallel_id)

    waiting = BasicState(waiting_id)
    statechart.add_state(waiting, consequence_parallel_id)
    statechart.add_transition(Transition(source=waiting_id, target=rule_satisfied_id, event=CHECK_EVENT))
    statechart.add_transition(Transition(source=waiting_id, target=consequence_comp_id, event=RESET_EVENT))

    consequence_comp = CompoundState(consequence_comp_id, initial=consequence_id)
    statechart.add_state(consequence_comp, consequence_parallel_id)
    statechart.add_transition(Transition(source=consequence_comp_id, target=consequence_comp_id, event=RESET_EVENT))

    consequence_success = BasicState(consequence_success_id)
    statechart.add_state(consequence_success, consequence_comp_id)
    statechart.add_transition(Transition(source=consequence_success_id, target=rule_satisfied_id, event=CHECK_EVENT))

    consequence_failure = BasicState(consequence_failure_id)
    statechart.add_state(consequence_failure, consequence_comp_id)
    statechart.add_transition(
        Transition(source=consequence_failure_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    consequence.add_to(statechart, consequence_id, consequence_comp_id,
                       success_state_id=consequence_success_id, failure_state_id=consequence_failure_id)
    statechart.add_transition(Transition(source=consequence_id, target=rule_not_satisfied_id, event=CHECK_EVENT))

    return statechart
