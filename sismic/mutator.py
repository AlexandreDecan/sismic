from sismic import model
from copy import deepcopy


class Mutator(object):
    def __init__(self, statechart: model.Statechart = None):
        self.type = "GenericMutator"
        self.statechart = statechart

    def separate_instance(self) -> model.Statechart:
        assert isinstance(self.statechart, model.Statechart)
        return deepcopy(self.statechart)

    def mutate(self) -> list:
        pass


class StateMissing(Mutator):
    def __init__(self, statechart: model.Statechart = None):
        super(StateMissing, self).__init__(statechart=statechart)
        self.type = "StateMissing"

    def mutate(self) -> list:
        mutants = list()

        for state in self.statechart.states:
            new_mutant = self.separate_instance()
            new_mutant.type = self.type

            assert isinstance(new_mutant, model.Statechart)
            assert hasattr(state, 'name')

            try:
                new_mutant.remove_state(state.name)
                new_mutant.validate()
            except:
                continue

            mutants.append(new_mutant)

        return mutants


class ArcMissing(Mutator):
    def __init__(self, statechart: model.Statechart = None):
        super(ArcMissing, self).__init__(statechart=statechart)
        self.type = "ArcMissing"

    def mutate(self) -> list:
        mutants = list()

        for transition in self.statechart.transitions:
            new_mutant = self.separate_instance()
            assert isinstance(new_mutant, model.Statechart)

            new_mutant.type = self.type
            # new_mutant.removed_transitions = [transition]
            new_mutant.remove_transition(transition)

            # try:
            #     new_mutant.validate()
            # except AssertionError as e:
            #     # print (new_mutant.removed_state, new_mutant.removed_transitions, e)
            #     continue

            mutants.append(new_mutant)

        return mutants

# TODO: needs to be completely rewritten according to new model changes
# class WrongStartingState(Mutator):
#     def __init__(self, statechart: model.Statechart = None):
#         super(WrongStartingState, self).__init__(statechart=statechart)
#         self.type = "WrongStartingState"
#
#     def mutate(self) -> list:
#         mutants = list()
#         state_names = set(self.statechart.children)
#         state_names.remove(self.statechart.initial)
#
#         for state_name in state_names:
#             new_mutant = self.separate_instance()
#             new_mutant.type = self.type
#             assert isinstance(new_mutant, model.Statechart)
#
#             new_mutant.initial = state_name
#
#             # try:
#             #     new_mutant.validate()
#             # except AssertionError as e:
#             #     continue
#
#             mutants.append(new_mutant)
#
#         for state in self.statechart.states:
#             if isinstance(state, model.CompositeStateMixin) and hasattr(state, "initial"):
#                 state_names = set(state.children)
#                 state_names.remove(state.initial)
#
#                 for state_name in state_names:
#                     new_mutant = self.separate_instance()
#                     new_mutant.type = self.type
#                     assert isinstance(new_mutant, model.Statechart)
#
#                     new_mutant.initial = state_name
#
#                     # try:
#                     #     new_mutant.validate()
#                     # except AssertionError as e:
#                     #     continue
#
#                     mutants.append(new_mutant)
#
#         return mutants
