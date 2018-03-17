from typing import Mapping, List
from ..model import (
    DeepHistoryState, FinalState, Transition, CompoundState,
    OrthogonalState, ShallowHistoryState, Statechart,
    ActionStateMixin, ContractMixin, HistoryStateMixin)


__all__ = ['export_to_plantuml']


class PlantUMLExporter:
    def __init__(
            self,
            statechart: Statechart, *,
            statechart_name: bool=True,
            statechart_description: bool=True,
            statechart_preamble: bool=True,
            state_contracts: bool=True,
            state_actions: bool=True,
            transition_contracts: bool=True,
            transition_action: bool=True) -> None:
        self.statechart = statechart
        self.statechart_name = statechart_name
        self.statechart_description = statechart_description
        self.statechart_preamble = statechart_preamble
        self.state_contracts = state_contracts
        self.state_actions = state_actions
        self.transition_contracts = transition_contracts
        self.transition_action = transition_action

        self._states_id = dict()  # type: Mapping[str, str]
        self._output = []  # type: List[str]
        self._indent = 0

    def indent(self):
        self._indent += 2

    def deindent(self):
        self._indent -= 2

    def output(self, text: str, *, wrap: str='') -> None:
        lines = text.strip().split('\n')

        for line in lines:
            # Special case for __old__
            line = line.replace('__old__', '~__old__')

            self._output.append(
                '{indent}{wrap}{line}{wrap}'.format(
                    indent=' ' * self._indent,
                    wrap=wrap,
                    line=line
                )
            )

    @staticmethod
    def state_id(name: str) -> str:
        return ''.join(filter(str.isalnum, name))

    def export_statechart(self):
        if self.statechart_name and self.statechart.name:
            self.output('title {}'.format(self.statechart.name))

        if self.statechart_description and self.statechart.description:
            self.output('caption {}'.format(self.statechart.description.replace('\n', '\\n')))

        if self.statechart_preamble and self.statechart.preamble:
            self.output('note top of {}'.format(self.state_id(self.statechart.root)))
            self.indent()
            self.output(self.statechart.preamble)
            self.deindent()
            self.output('end note')

    def export_state(self, name: str) -> None:
        state = self.statechart.state_for(name)

        # Special case for final state
        if isinstance(state, FinalState):
            # Find transitions leading to it
            for transition in self.statechart.transitions_to(state.name):
                self.export_transition(transition)
            return

        if isinstance(state, ShallowHistoryState):
            self.output('state "H" as {} {{'.format(self.state_id(name)))
        elif isinstance(state, DeepHistoryState):
            self.output('state "H*" as {} {{'.format(self.state_id(name)))
        else:
            self.output('state "{}" as {} {{'.format(name, self.state_id(name)))

        self.indent()

        # Actions
        has_actions = False

        if self.state_actions and isinstance(state, ActionStateMixin):
            # On entry, on exit
            if state.on_entry:
                has_actions = True
                self.output('{} : **entry** / {}'.format(
                    self.state_id(name),
                    state.on_entry.strip().replace('\n', '; ')
                ))
            if state.on_exit:
                has_actions = True
                self.output('{} : **exit** / {}'.format(
                    self.state_id(name),
                    state.on_exit.strip().replace('\n', '; ')
                ))

            # Internal actions
            transitions = [tr for tr in self.statechart.transitions_from(name) if tr.internal and tr.action]
            if len(transitions) > 0:
                has_actions = True
                for transition in transitions:
                    text = []
                    if transition.event:
                        text.append('**{}** '.format(transition.event))
                    if transition.guard:
                        text.append('[{}] '.format(transition.guard))

                    self.output('{} : {}/ {}'.format(
                        self.state_id(name),
                        ''.join(text),
                        transition.action.strip().replace('\n', '; '),
                    ))

        # Contracts
        if isinstance(state, ContractMixin) and self.state_contracts and (
                state.preconditions or state.invariants or state.postconditions):
            if has_actions:
                self.output('{} : '.format(self.state_id(name)))

            for cond in state.preconditions:
                self.output('{} : **pre:** {}'.format(self.state_id(name), cond))
            for cond in state.invariants:
                self.output('{} : **inv:** {}'.format(self.state_id(name), cond))
            for cond in state.postconditions:
                self.output('{} : **post:** {}'.format(self.state_id(name), cond))

        # Nested states
        for i, child in enumerate(self.statechart.children_for(name)):
            if i != 0 and isinstance(state, OrthogonalState):
                self.output('--')
            self.export_state(child)

        # Initial state
        if isinstance(state, CompoundState) and state.initial:
            self.output('[*] -> {}'.format(self.state_id(state.initial)))

        self.deindent()
        self.output('}')

    def export_transitions(self, source_name: str) -> None:
        state = self.statechart.state_for(source_name)

        # History state
        if isinstance(state, HistoryStateMixin) and state.memory:
            self.output('{} -> {}'.format(self.state_id(source_name), self.state_id(state.memory)))

        # Transitions (except internal ones)
        transitions = filter(lambda t: not t.internal, self.statechart.transitions_from(source_name))

        for transition in transitions:
            # Do not treat final states here
            if transition.target and isinstance(self.statechart.state_for(transition.target), FinalState):
                continue

            self.export_transition(transition)

    def export_transition(self, transition: Transition) -> None:
        target = self.statechart.state_for(transition.target)

        if isinstance(target, FinalState):
            target_name = '[*]'
        else:
            target_name = self.state_id(target.name)

        text = []
        if transition.event:
            text.append(transition.event + ' ')
        if transition.guard:
            text.append('[{}] '.format(transition.guard))
        if transition.action and self.transition_action:
            text.append('/ {}'.format(transition.action.replace('\n', '; ')))

        if self.transition_contracts and (
                transition.preconditions or transition.invariants or transition.postconditions):
            text.append('\\n')

            for cond in transition.preconditions:
                text.append('pre: {}\\n'.format(cond))
            for cond in transition.invariants:
                text.append('inv: {}\n'.format(cond))
            for cond in transition.postconditions:
                text.append('post: {}\n'.format(cond))

        self.output('{source} -> {target} : {text}'.format(
            source=self.state_id(transition.source),
            target=target_name,
            text=''.join(text),
        ))

    def export(self) -> str:
        self.output('@startuml')

        self.export_statechart()
        self.export_state(self.statechart.root)

        for name in self.statechart.states:
            self.export_transitions(name)

        self.output('@enduml')

        return '\n'.join(self._output)


def export_to_plantuml(
        statechart: Statechart,
        filepath: str=None, *,
        statechart_name=True,
        statechart_description=True,
        statechart_preamble=True,
        state_contracts=True,
        state_actions=True,
        transition_contracts=True,
        transition_action=True) -> str:
    """
    Export given statechart to plantUML (see http://plantuml/plantuml).

    :param statechart: statechart to export
    :param filepath: save output to given filepath, if provided
    :param statechart_name: include the name of the statechart
    :param statechart_description: include the description of the statechart
    :param statechart_preamble: include the preamble of the statechart
    :param state_contracts: include state contracts
    :param state_actions: include state actions (on entry, on exit and internal transitions)
    :param transition_contracts: include transition contracts
    :param transition_action: include actions on transition
    :return: textual representation using plantuml
    """

    exporter = PlantUMLExporter(
        statechart,
        statechart_name=statechart_name,
        statechart_description=statechart_description,
        statechart_preamble=statechart_preamble,
        state_contracts=state_contracts,
        state_actions=state_actions,
        transition_contracts=transition_contracts,
        transition_action=transition_action,
    )

    output = exporter.export()

    if filepath:
        with open(filepath, 'w') as f:
            f.write(output)

    return output