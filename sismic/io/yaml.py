import yaml
import os

from pykwalify.core import Core
from sismic.model import Statechart
from .datadict import import_from_dict, export_to_dict

__all__ = ['import_from_yaml', 'export_to_yaml']

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.yaml')


def import_from_yaml(statechart: str, ignore_schema: bool = False, ignore_validation: bool = False) -> Statechart:
    """
    Import a statechart from a YAML representation.
    YAML is first validated against *io.yaml.SCHEMA_PATH*, and resulting statechart is validated
    using its *validate* method.

    :param statechart: string or any equivalent object
    :param ignore_schema: set to *True* to disable yaml validation.
    :param ignore_validation: set to *True* to disable statechart validation.
    :return: a *StateChart* instance
    """
    data = yaml.load(statechart)
    if not ignore_schema:
        checker = Core(source_data=data, schema_files=[SCHEMA_PATH])
        checker.validate(raise_exception=True)

    statechart = import_from_dict(data)
    if not ignore_validation:
        statechart.validate()
    return statechart


def export_to_yaml(statechart: Statechart) -> str:
    """
    Export given StateChart instance to YAML

    :param statechart:
    :return: A textual YAML representation
    """
    return yaml.dump(export_to_dict(statechart, ordered=False),
                     width=1000, default_flow_style=False, default_style='"')

