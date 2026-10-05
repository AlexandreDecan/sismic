from typing import Any

import pytest
from ruamel import yaml

from sismic.exceptions import StatechartError
from sismic.io.datadict import import_from_dict
from sismic.io import export_to_plantuml, export_to_yaml, import_from_yaml
from sismic.io.plantuml import cli
from sismic.model import Statechart


def compare_statecharts(s1, s2):
    assert s1.name == s2.name
    assert s1.description == s2.description
    assert s2.preamble == s2.preamble

    assert set(s1.states) == set(s2.states)
    assert set(s1.transitions) == set(s2.transitions)

    for state in s1.states:
        assert s1.parent_for(state) == s2.parent_for(state)
        assert set(s1.children_for(state)) == set(s2.children_for(state))


@pytest.mark.parametrize("data", [1, -1, 1.0, "yes", "True", "no", "", [], [1, 2], {}, {1: 1}])
def test_yaml_parser_types_handling(data):
    yaml = f"""
    statechart:
        name: {data!s}
        preamble: Nothing
        root state:
            name: s1
    """
    item = import_from_yaml(yaml).name
    assert isinstance(item, str)


def test_import_from_yaml_args():
    with pytest.raises(TypeError):
        import_from_yaml()
    with pytest.raises(TypeError):
        import_from_yaml("A", filepath="B")


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
        assert "Unknown target state" in str(e.value)

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
        assert "cannot be used as a parent for" in str(e.value)

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

        with pytest.raises(
            StatechartError,
            match="root cannot declare both a 'states' and a 'parallel states' property",
        ):
            import_from_yaml(yaml)


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
        compare_statecharts(
            example_from_tests,
            import_from_yaml(export_to_yaml(example_from_tests)),
        )

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
            transition_action=True,
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
            transition_action=True,
        )
        assert len(export) > 0

    def test_export_based_on_filepath(self, elevator):
        filepath = "docs/examples/elevator/elevator.plantuml"
        statechart = elevator.statechart
        with open(filepath, "r") as f:
            p1 = f.read().strip()

        assert p1 != export_to_plantuml(statechart)
        assert p1 == export_to_plantuml(statechart, based_on=p1)
        assert p1 == export_to_plantuml(statechart, based_on_filepath=filepath)

    def test_cli(self, capsys):
        filepath = "docs/examples/elevator/elevator.yaml"
        statechart = import_from_yaml(filepath=filepath)

        # Check default parameters
        cli([filepath])
        out, _ = capsys.readouterr()
        assert export_to_plantuml(statechart) == out.strip()

        # Check all parameters
        cli(
            [
                filepath,
                "--based-on",
                "docs/examples/elevator/elevator.plantuml",
                "--show-description",
                "--show-preamble",
                "--show-state-contracts",
                "--show-transition-contracts",
                "--hide-state-action",
                "--hide-name",
                "--hide-transition-action",
            ],
        )
        out, _ = capsys.readouterr()
        export = export_to_plantuml(
            statechart,
            based_on_filepath="docs/examples/elevator/elevator.plantuml",
            statechart_description=True,
            statechart_preamble=True,
            state_contracts=True,
            transition_contracts=True,
            state_action=False,
            statechart_name=False,
            transition_action=False,
        )
        assert export == out.strip()


class TestImportFromDict:
    def load_simple_statechart(self, tests_dir) -> dict[str, Any]:
        yml = yaml.YAML(typ="safe", pure=True)
        return yml.load(tests_dir / "yaml/simple.yaml")

    def test_import_from_valid_dict(self, tests_dir):
        data = self.load_simple_statechart(tests_dir)
        assert "statechart" in data
        assert data["statechart"] == {
            "name": "simple statechart",
            "root state": {
                "name": "root",
                "initial": "s1",
                "states": [
                    {"name": "s1", "transitions": [{"target": "s2", "event": "goto s2"}]},
                    {"name": "s2", "transitions": [{"target": "s3"}]},
                    {
                        "name": "s3",
                        "transitions": [
                            {"target": "s1", "event": "goto s1"},
                            {"target": "s2", "event": "goto s2"},
                            {"target": "final", "event": "goto final"},
                        ],
                    },
                    {"name": "final", "type": "final"},
                ],
            },
        }

        statechart = import_from_dict(data)
        assert statechart.name == "simple statechart"
        assert statechart.root == "root"
        assert len(statechart.states) == 5

    def test_incorrect_schema(self, tests_dir):
        data = self.load_simple_statechart(tests_dir)
        data["statechart"]["type"] = "incorrect_type"

        with pytest.raises(StatechartError, match="mapping validation failed"):
            import_from_dict(data, ignore_validation=True)

    def test_incorrect_validation(self, tests_dir):
        data = self.load_simple_statechart(tests_dir)
        data["statechart"]["root state"]["initial"] = "s54"

        with pytest.raises(StatechartError, match="Initial state s54 .* does not exist"):
            import_from_dict(data, ignore_schema=True)

    def test_skipped_validation_raises_no_error(self, tests_dir):
        data = self.load_simple_statechart(tests_dir)
        data["statechart"]["type"] = "incorrect_type"
        data["statechart"]["root state"]["initial"] = "s54"
        import_from_dict(data, ignore_schema=True, ignore_validation=True)
