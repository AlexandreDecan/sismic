import yaml  # type: ignore
import os
from typing import Iterable

from pykwalify.core import Core  # type: ignore
from sismic.model import Statechart
from .datadict import import_from_dict, export_to_dict


__all__ = ['import_from_yaml', 'export_to_yaml']

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.yaml')


def import_from_yaml(statechart: Iterable[str], ignore_schema: bool=False, ignore_validation: bool=False) -> Statechart:
    """
    Import a statechart from a YAML representation.
    YAML is first validated against *sismic.io.yaml.SCHEMA_PATH*, and resulting statechart is validated
    using its *validate* method.

    :param statechart: string or any equivalent object
    :param ignore_schema: set to *True* to disable yaml validation.
    :param ignore_validation: set to *True* to disable statechart validation.
    :return: a *Statechart* instance
    """
    data = yaml.load(statechart)  # type: dict
    if not ignore_schema:
        checker = Core(source_data=data, schema_files=[SCHEMA_PATH])
        checker.validate(raise_exception=True)

    sc = import_from_dict(data)
    if not ignore_validation:
        sc.validate()
    return sc


def export_to_yaml(statechart: Statechart) -> str:
    """
    Export given *Statechart* instance to YAML

    :param statechart:
    :return: A textual YAML representation
    """
    return yaml.dump(export_to_dict(statechart, ordered=False),
                     width=1000, default_flow_style=False, default_style='"')

