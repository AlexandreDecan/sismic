from sismic.model import Statechart, BasicState, FinalState, Transition, CompoundState, OrthogonalState


class Condition:
    def add_to(self, statechart: Statechart, id: str, parent_state_id: str, success_state_id: str):
        pass


class TrueCondition(Condition):
    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str, success_state_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_state_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)

        statechart.add_transition(Transition(source=waiting_id, target=success_state_id))


class FalseCondition(Condition):
    def __init__(self):
        Condition.__init__(self)

    def add_to(self, statechart: Statechart, id: str, parent_state_id: str, success_state_id: str):
        waiting_id = Counter.random()

        composite = CompoundState(id, initial=waiting_id)
        statechart.add_state(composite, parent_state_id)

        waiting = BasicState(waiting_id)
        statechart.add_state(waiting, id)



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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str):
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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str):
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

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str):
        parallel_state = OrthogonalState(id)
        statechart.add_state(parallel_state, parent=parent_id)
        a_id = Counter.random()
        b_id = Counter.random()

        composite_a_id = Counter.random()
        composite_b_id = Counter.random()
        exit_a_id = Counter.random()
        exit_b_id = Counter.random()

        composite_a = CompoundState(composite_a_id, initial=a_id)
        statechart.add_state(composite_a, parent=id)
        exit_a = BasicState(exit_a_id)
        statechart.add_state(exit_a, parent=composite_a_id)
        self.a.add_to(statechart, a_id, composite_a_id, exit_a_id)

        composite_b = CompoundState(composite_b_id, initial=b_id)
        statechart.add_state(composite_b, parent=id)
        exit_b = BasicState(exit_b_id)
        statechart.add_state(exit_b, parent=composite_b_id)
        self.b.add_to(statechart, b_id, composite_b_id, exit_b_id)

        statechart.add_transition(Transition(source=id,
                                             target=success_state_id,
                                             guard='active("{}") and active("{}")'.format(exit_a_id, exit_b_id)))


class Or(Condition):
    def __init__(self, a: Condition, b: Condition):
        Condition.__init__(self)
        self.a = a
        self.b = b

    def add_to(self, statechart: Statechart, id: str, parent_id: str, success_state_id: str):
        parallel_state = OrthogonalState(id)
        statechart.add_state(parallel_state, parent=parent_id)
        a_id = Counter.random()
        b_id = Counter.random()

        composite_a_id = Counter.random()
        composite_b_id = Counter.random()
        exit_a_id = Counter.random()
        exit_b_id = Counter.random()

        composite_a = CompoundState(composite_a_id, initial=a_id)
        statechart.add_state(composite_a, parent=id)
        exit_a = BasicState(exit_a_id)
        statechart.add_state(exit_a, parent=composite_a_id)
        self.a.add_to(statechart, a_id, composite_a_id, exit_a_id)

        composite_b = CompoundState(composite_b_id, initial=b_id)
        statechart.add_state(composite_b, parent=id)
        exit_b = BasicState(exit_b_id)
        statechart.add_state(exit_b, parent=composite_b_id)
        self.b.add_to(statechart, b_id, composite_b_id, exit_b_id)

        statechart.add_transition(Transition(source=id,
                                             target=success_state_id,
                                             guard='active("{}") or active("{}")'.format(exit_a_id, exit_b_id)))


class Then(Condition):
    """
        This condition combines two successive conditions a and b.
        To succeed, a must be verified, and after that, b must be verified.
    """
    def __init__(self, a, b):
        Condition.__init__(self)
        self.a = a
        self.b = b

    def add_to(self, statechart: Statechart, id: str, parent_id: str, output_id: str):
        a_id = Counter.random()
        b_id = Counter.random()

        composite = CompoundState(id, initial=a_id)
        statechart.add_state(composite, parent_id)

        self.b.add_to(statechart, b_id, id, output_id)
        self.a.add_to(statechart, a_id, id, b_id)