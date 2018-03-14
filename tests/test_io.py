import pytest

from sismic.model import Statechart
from sismic.exceptions import StatechartError
from sismic.io import import_from_yaml, export_to_yaml, export_to_plantuml
from sismic.io.text import export_to_tree


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


class TestExporttoTree:
    result = iter([
        ['root', '   s1', '   s2', '   s3'],
        ['root', '   s1', '      s1a', '      s1b', '         s1b1', '         s1b2', '   s2'],
        ['root', '   active', '      active.H*', '      concurrent_processes', '         process_1',
         '            s11', '            s12', '            s13', '         process_2', '            s21',
         '            s22', '            s23', '   pause', '   stop'],
        ['root', '   s1', '   s2', '   stop'],
        ['root', '   active', '   s1', '   s2'],
        ['root', '   s1', '      p1', '         r1', '            i1', '            j1', '            k1',
         '         r2', '            i2', '            j2', '            k2', '            y', '      p2',
         '         r3', '            i3', '            j3', '            k3', '            z', '         r4',
         '            i4', '            j4', '            k4', '            x'],
        ['root', '   s1', '   s2', '   s3'],
        ['root', '   s1', '      p1', '         a1', '         b1', '         c1', '         initial1', '      p2',
         '         a2', '         b2', '         c2', '         initial2'],
        ['root', '   final', '   s1', '   s2', '   s3'],
        ['root', '   s1', '   s2', '   s3', '   s4']
    ])

    def test_output(self, example_from_tests):
        result = next(self.result)
        assert export_to_tree(example_from_tests) == result

    def test_all_states_are_exported(self, example_from_tests):
        assert set(export_to_tree(example_from_tests, spaces=0)) == set(example_from_tests.states)

    def test_indentation_is_correct(self, example_from_tests):
        for r in sorted(export_to_tree(example_from_tests, spaces=1)):
            name = r.lstrip()
            depth = example_from_tests.depth_for(name)
            spaces = len(r) - len(name)
            assert depth - 1 == spaces


class TestExportToPlantUML:
    def test_export_example_from_tests(self, example_from_tests):
        assert len(export_to_plantuml(example_from_tests)) > 0

    def test_export_example_from_docs(self, example_from_docs):
        assert len(export_to_plantuml(example_from_docs)) > 0