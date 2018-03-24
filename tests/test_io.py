import pytest

from sismic.model import Statechart
from sismic.exceptions import StatechartError
from sismic.io import import_from_yaml, export_to_yaml, export_to_plantuml


def compare_statecharts(s1, s2):
    assert s1.name == s2.name
    assert s1.description == s2.description
    assert s2.preamble == s2.preamble

    assert set(s1.states) == set(s2.states)
    assert set(s1.transitions) == set(s2.transitions)

    for state in s1.states:
        assert s1.parent_for(state) == s2.parent_for(state)
        assert set(s1.children_for(state)) == set(s2.children_for(state))


@pytest.mark.parametrize('data', [1, -1, 1.0, 'yes', 'True', 'no', '', [], [1, 2], {}, {1: 1}])
def test_yaml_parser_types_handling(data):
    yaml = ('statechart:'
            '\n  name: ' + str(data) +
            '\n  preamble: Nothing'
            '\n  root state:'
            '\n    name: s1')
    item = import_from_yaml(yaml).name
    assert isinstance(item, str)


def test_import_from_yaml_args():
    with pytest.raises(TypeError):
        import_from_yaml()
    with pytest.raises(TypeError):
        import_from_yaml('A', filepath='B')


class TestImportFromYaml:
    def test_import_example_from_tests(self, example_from_tests):
        assert isinstance(example_from_tests, Statechart)

    def test_import_example_from_docs(self, example_from_docs):
        assert isinstance(example_from_docs, Statechart)

    def test_transitions_to_unknown_state(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
                transitions:
                  - target: s2
        """
        with pytest.raises(StatechartError) as e:
            import_from_yaml(yaml)
        assert 'Unknown target state' in str(e.value)

    def test_history_not_in_compound(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
                parallel states:
                 - name: s2
                   type: shallow history
        """
        with pytest.raises(StatechartError) as e:
            import_from_yaml(yaml)
        assert 'cannot be used as a parent for' in str(e.value)

    def test_declare_both_states_and_parallel_states(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
            parallel states:
              - name: s2
        """

        with pytest.raises(StatechartError) as e:
            import_from_yaml(yaml)
        assert 'root cannot declare both a "states" and a "parallel states" property' in str(e.value)


class TestExportToYaml:
    def test_export_example_from_tests(self, example_from_tests):
        assert len(export_to_yaml(example_from_tests)) > 0

    def test_export_example_from_docs(self, example_from_docs):
        assert len(export_to_yaml(example_from_docs)) > 0

    def test_validity_for_example_from_tests(self, example_from_tests):
        assert import_from_yaml(export_to_yaml(example_from_tests)).validate()

    def test_validity_for_example_from_docs(self, example_from_docs):
        assert import_from_yaml(export_to_yaml(example_from_docs)).validate()

    def test_identity_for_example_from_tests(self, example_from_tests):
        compare_statecharts(example_from_tests, import_from_yaml(export_to_yaml(example_from_tests)))

    def test_identity_for_example_from_docs(self, example_from_docs):
        compare_statecharts(example_from_docs, import_from_yaml(export_to_yaml(example_from_docs)))


class TestExportToPlantUML:
    def test_export_example_from_tests(self, example_from_tests):
        export = export_to_plantuml(
            example_from_tests,
            statechart_name=True,
            statechart_description=True,
            statechart_preamble=True,
            state_contracts=True,
            state_action=True,
            transition_contracts=True,
            transition_action=True
        )
        assert len(export) > 0

    def test_export_example_from_docs(self, example_from_docs):
        export = export_to_plantuml(
            example_from_docs,
            statechart_name=True,
            statechart_description=True,
            statechart_preamble=True,
            state_contracts=True,
            state_action=True,
            transition_contracts=True,
            transition_action=True
        )
        assert len(export) > 0

    def test_export_based_on_filepath(self, elevator):
        filepath = 'docs/examples/elevator/elevator.plantuml'
        statechart = elevator.statechart
        with open(filepath, 'r') as f:
            p1 = f.read()

        assert p1 != export_to_plantuml(statechart)
        assert p1 == export_to_plantuml(statechart, based_on=p1)
        assert p1 == export_to_plantuml(statechart, based_on_filepath=filepath)


