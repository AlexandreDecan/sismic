from pyss import statemachine
from pyss.evaluator import Evaluator


class Simulator:
    def __init__(self, sm: statemachine.StateMachine, evaluator: Evaluator=None):
        """
        A simulator that interprets a state machine according to a specific semantic.
        :param sm: state machine to interpret
        :param evaluator: Code evaluator (optional)
        """
        self.evaluator = evaluator
        self.sm = sm
        self.configuration = []  # List of active states
        self.events = []

    def fire_event(self, event: statemachine.Event):
        self.events.append(event)

    def microstep(self):
        """
        Perform an atomic micro step.
        """
        raise NotImplementedError()

    def macrostep(self):
        """
        Perform a macro step, ie. a sequence of micro steps until a stable configuration is reached.
        Corresponds to the processing of exactly ONE transition.
        """
        raise NotImplementedError()

    def __repr__(self):
        return '{}[{}]'.format(self.__class__.__name__, ' '.join(self.configuration))


class HierarchicalAutomataSimulator(Simulator):
    """
    A state machine simulator that considers the state machine as a simple
    hierarchical automaton, ie. with no support for history states and
    orthogonal states.
    """
    pass


class SCXMLSimulator(Simulator):
    """
    A state machine simulator that implements SCXML semantic.
    """
    pass
