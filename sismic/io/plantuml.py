from ..model import (
    BasicState, CompoundState, DeepHistoryState, FinalState,
    OrthogonalState, ShallowHistoryState, Statechart,
    ActionStateMixin, ContractMixin, Transition, HistoryStateMixin)


__all__ = ['export_to_plantuml']


class _Exporter:
    def __init__(
            self,
            statechart: Statechart,
            statechart_name=True,
            statechart_description=True,
            statechart_preamble=True,
            state_contracts=True,
            state_actions=True,
            transition_action=True,
    ):
        self.statechart = statechart
        self.statechart_name = statechart_name
        self.statechart_description = statechart_description
        self.statechart_preamble = statechart_preamble
        self.state_contracts = state_contracts
        self.state_actions = state_actions
        self.transition_action = transition_action

        self._output = []
        self._indent = 0
        self._note_nb = 0

    def indent(self):
        self._indent += 2

    def deindent(self):
        self._indent -= 2

    def concat(self, text, *, wrap=''):
        lines = text.strip().split('\n')

        for line in lines:
            self._output.append(
                '{indent}{wrap}{line}{wrap}'.format(
                    indent=' ' * self._indent,
                    wrap=wrap,
                    line=line
                )
            )

    def state_id(self, name):
        return name.replace(' ', '')

    def export_statechart(self):
        if self.statechart_name or self.statechart_description or self.statechart_preamble:
            self.concat('note top of {}'.format(self.state_id(self.statechart.root)))

            self.indent()
            if self.statechart_name and self.statechart.name:
                self.concat(self.statechart.name, wrap='**')
            if self.statechart_description and self.statechart.description:
                self.concat(self.statechart.description, wrap='//')
            if self.statechart_preamble and self.statechart.preamble:
                self.concat(self.statechart.preamble)

            self.deindent()

            self.concat('end note')

    def export_state(self, name: str):
        state = self.statechart.state_for(name)

        self.export_state_actions(name)
        self.export_state_contracts(name)

        if isinstance(state, BasicState):
            self.concat('state "{}" as {}'.format(name, self.state_id(name)))
        elif isinstance(state, CompoundState):
            self.concat('state "{}" as {} {{'.format(name, self.state_id(name)))
            self.indent()
            for child in self.statechart.children_for(name):
                self.export_state(child)

            if state.initial:
                self.concat('[*] --> {}'.format(self.state_id(state.initial)))

            self.deindent()
            self.concat('}')
        elif isinstance(state, OrthogonalState):
            self.concat('state "{}" as {} {{'.format(name, self.state_id(name)))
            self.indent()

            for i, child in enumerate(self.statechart.children_for(name)):
                if i != 0:
                    self.concat('--')
                self.export_state(child)

            self.deindent()
            self.concat('}')

        elif isinstance(state, FinalState):
            pass
        elif isinstance(state, ShallowHistoryState):
            self.concat('state "H - {}" as {}'.format(name, self.state_id(name)))
        elif isinstance(state, DeepHistoryState):
            self.concat('state "H* - {}" as {}'.format(name, self.state_id(name)))
        else:
            assert False, type(state)

    def export_state_actions(self, name):
        state = self.statechart.state_for(name)

        if not self.state_actions or not isinstance(state, ActionStateMixin):
            return

        # On entry, on exit
        if state.on_entry:
            self.concat('{} : **on entry**:\\n{}'.format(
                self.state_id(name),
                state.on_entry.strip().replace('\n', '\\n')
            ))
        if state.on_exit:
            self.concat('{} : **on exit**:\\n{}'.format(
                self.state_id(name),
                state.on_exit.strip().replace('\n', '\\n')
            ))

        # Internal actions
        transitions = [tr for tr in self.statechart.transitions_from(name) if tr.internal and tr.action]
        if len(transitions) > 0:
            for transition in transitions:
                text = []
                if transition.event:
                    text.append('on event {}'.format(transition.event))
                if transition.guard:
                    text.append('[{}]'.format(transition.guard))

                self.concat('{} : **{}**:\\n{}'.format(
                    self.state_id(name),
                    ''.join(text),
                    transition.action.strip().replace('\n', '\\n'),
                ))

    def export_transition(self, source_name):
        state = self.statechart.state_for(source_name)
        transitions = self.statechart.transitions_from(source_name)

        for transition in transitions:
            if transition.internal:
                continue

            target = self.statechart.state_for(transition.target)
            if isinstance(target, FinalState):
                target_name = '[*]'
            else:
                target_name = self.state_id(target.name)

            text = []
            if transition.event:
                text.append(transition.event)
            if transition.guard:
                text.append('[{}]'.format(transition.guard))
            if transition.action and self.transition_action:
                text.append(' / {}'.format(transition.action.replace('\n', '; ')))

            self.concat('{source} --> {target} : {text}'.format(
                source=self.state_id(source_name),
                target=target_name,
                text=''.join(text),
            ))

    def export_state_contracts(self, name):
        state = self.statechart.state_for(name)

        if isinstance(state, ContractMixin) and self.state_contracts and (
                state.preconditions or state.invariants or state.postconditions):
            #self._note_nb += 1
            self.concat('note bottom of {}'.format(self.state_id(name)))
            # self.concat('note as N{}'.format(self._note_nb))

            self.indent()
            for cond in state.preconditions:
                self.concat('pre: {}'.format(cond))
            for cond in state.invariants:
                self.concat('inv: {}'.format(cond))
            for cond in state.postconditions:
                self.concat('post: {}'.format(cond))
            self.deindent()
            self.concat('end note')

    def export_all(self):
        self.concat('@startuml')

        self.export_statechart()
        self.export_state(self.statechart.root)

        for name in self.statechart.states:
            self.export_transition(name)

        self.concat('@enduml')

        return '\n'.join(self._output)


def export_to_plantuml(
        statechart: Statechart, *,
        statechart_name=True,
        statechart_description=True,
        statechart_preamble=True,
        state_contracts=True,
        state_actions=True,
        transition_action=True
    ):
    """
    Export given statechart to plantUML (see http://plantuml/plantuml).

    :param statechart: statechart to export
    :param statechart_name: include the name of the statechart
    :param statechart_description: include the description of the statechart
    :param statechart_preamble: include the preamble of the statechart
    :param state_contracts: include a note containing state contracts
    :param state_actions: include state actions (on entry, on exit and internal transitions)
    :param transition_action: include actions on transition
    :return:
    """

    exporter = _Exporter(
        statechart,
        statechart_name,
        statechart_description,
        statechart_preamble,
        state_contracts,
        state_actions,
        transition_action
    )

    return exporter.export_all()