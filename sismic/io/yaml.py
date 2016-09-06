import ruamel.yaml as yaml
import schema

from typing import Iterable
from sismic.model import Statechart
from sismic.exceptions import StatechartError
from .datadict import import_from_dict, export_to_dict


__all__ = ['import_from_yaml', 'export_to_yaml']


class SCHEMA:
    contract = {schema.Or('before', 'after', 'always', 'sequentially'): schema.Use(str)}

    transition = {
        schema.Optional('target'): schema.Use(str),
        schema.Optional('event'): schema.Use(str),
        schema.Optional('guard'): schema.Use(str),
        schema.Optional('action'): schema.Use(str),
        schema.Optional('contract'): [contract],
    }

    state = dict()
    state.update({
        'name': schema.Use(str),
        schema.Optional('type'): schema.Or('final', 'shallow history', 'deep history'),
        schema.Optional('on entry'): schema.Use(str),
        schema.Optional('on exit'): schema.Use(str),
        schema.Optional('transitions'): [transition],
        schema.Optional('contract'): [contract],
        schema.Optional('initial'): schema.Use(str),
        schema.Optional('parallel states'): [state],
        schema.Optional('states'): [state],
    })

    statechart = {
        'statechart': {
            'name': schema.Use(str),
            schema.Optional('description'): schema.Use(str),
            schema.Optional('preamble'): schema.Use(str),
            'root state': state,
        }
    }


def import_from_yaml(statechart: Iterable[str], ignore_schema: bool=False, ignore_validation: bool=False) -> Statechart:
    """
    Import a statechart from a YAML representation.

    Unless specified, the structure contained in the YAML is validated against a predefined
    schema (see *sismic.io.SCHEMA*), and the resulting statechart is validated using its *validate()* method.

    :param statechart: string or any equivalent object
    :param ignore_schema: set to *True* to disable yaml validation.
    :param ignore_validation: set to *True* to disable statechart validation.
    :return: a *Statechart* instance
    """
    data = yaml.load(statechart, Loader=yaml.BaseLoader)  # type: dict

    if not ignore_schema:
        try:
            data = schema.Schema(SCHEMA.statechart).validate(data)
        except schema.SchemaError as e:
            raise StatechartError('YAML validation failed') from e

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

