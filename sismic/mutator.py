from sismic import model
from copy import deepcopy


class Mutator(object):
    def __init__(self, statechart: model.StateChart = None):
        self.type = "GenericMutator"
        self.statechart = statechart

    def separate_instance(self) -> model.StateChart:
        assert isinstance(self.statechart, model.StateChart)
        return deepcopy(self.statechart)

    def mutate(self) -> list:
        pass


class StateMissing(Mutator):
    def __init__(self, statechart: model.StateChart = None):
        super(StateMissing, self).__init__(statechart=statechart)
        self.type = "StateMissing"

    def mutate(self) -> list:
        mutants = list()

        for state_key in self.statechart.states.keys():
            new_mutant = self.separate_instance()
            new_mutant.type = self.type
            assert isinstance(new_mutant, model.StateChart)
            new_mutant.removed_state = new_mutant.states.pop(state_key)
            new_mutant.removed_transitions = list()

            for transition in new_mutant.transitions:
                if ((not (transition.from_state in new_mutant.states and
                              (not transition.to_state or transition.to_state in new_mutant.states))) or (
                                not transition.event and not transition.guard and not transition.to_state)):
                    new_mutant.removed_transitions.append(transition)

            for transition in new_mutant.removed_transitions:
                new_mutant.transitions.remove(transition)

            try:
                new_mutant.validate()
            except AssertionError as e:
                # print (new_mutant.removed_state, new_mutant.removed_transitions, e)
                continue

            mutants.append(new_mutant)

        return mutants


class ArcMissing(Mutator):
    def __init__(self, statechart: model.StateChart = None):
        super(ArcMissing, self).__init__(statechart=statechart)
        self.type = "ArcMissing"

    def mutate(self) -> list:
        mutants = list()

        for transition in self.statechart.transitions:
            new_mutant = self.separate_instance()
            assert isinstance(new_mutant, model.StateChart)
            new_mutant.type = self.type
            new_mutant.removed_transitions = [transition]
            new_mutant.transitions.remove(transition)

            try:
                new_mutant.validate()
            except AssertionError as e:
                # print (new_mutant.removed_state, new_mutant.removed_transitions, e)
                continue

            mutants.append(new_mutant)

        return mutants
