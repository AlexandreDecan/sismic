from sismic.model import Statechart, BasicState, FinalState, Transition, CompoundState, OrthogonalState


class Condition:
    def add_to(self, statechart: Statechart, id: str, parent_state_id: str,
               success_state_id: str, failure_state_id: str):
        pass


class TrueCondition(Condition):
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
    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str,
               success_state_id: str, failure_state_id: str):
        waiting_state = BasicState(id)
        statechart.add_state(waiting_state, parent_state_id)

        # Non fireable transitions so that this is linked to success and failure states, as usual
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
    def __init__(self, state_id: str):
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
    def __init__(self, state_id: str):
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


def add_active_state_machine(statechart: Statechart, state: str):
    """
    If a parallel state machine is not already present in the statechart for representing
    the activity of a state, this function creates such a parallel state machine and associates its state representing
    an active state to a state name: {external state: internal state}
    :param statechart:
    :param state:
    :return:
    """
    pass


class And(Condition):
    def __init__(self, a: Condition, b: Condition):
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
    def __init__(self, a: Condition, b: Condition):
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
    def __init__(self, cond :Condition):
        Condition.__init__(self)
        self.condition = cond

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str, failure_state_id: str):
        condition_id = Counter.random()
        composite = CompoundState(id, initial=condition_id)
        statechart.add_state(composite, parent_id)

        self.condition.add_to(statechart, condition_id, id,
                              success_state_id=failure_state_id, failure_state_id=success_state_id)


class Then(Condition):
    pass