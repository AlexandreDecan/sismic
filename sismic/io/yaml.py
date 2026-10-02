import os
from io import StringIO

from ruamel import yaml

from ..model import Statechart
from .datadict import export_to_dict, import_from_dict

__all__ = ["export_to_yaml", "import_from_yaml"]


def import_from_yaml(
    text: str | None = None,
    filepath: str | bytes | os.PathLike | None = None,
    *,
    ignore_schema: bool = False,
    ignore_validation: bool = False,
) -> Statechart:
    """
    Import a statechart from a YAML representation (first argument) or a YAML file (filepath
    argument).

    Unless specified, the structure contained in the YAML is validated against a predefined
    schema (see *sismic.io.SCHEMA*), and the resulting statechart is validated using its
    *validate()* method.

    :param text: A YAML text. If not provided, filepath argument has to be provided.
    :param filepath: A path to a YAML file.
    :param ignore_schema: set to *True* to disable yaml validation.
    :param ignore_validation: set to *True* to disable statechart validation.
    :return: a *Statechart* instance
    """
    if not text and not filepath:
        raise TypeError(
            "A YAML must be provided, either using first argument or filepath argument.",
        )
    elif text and filepath:
        raise TypeError("Either provide first argument or filepath argument, not both.")
    elif filepath:
        with open(filepath, "r") as f:
            text = f.read()

    yml = yaml.YAML(typ="safe", pure=True)
    data = yml.load(text)

    return import_from_dict(data, ignore_schema=ignore_schema, ignore_validation=ignore_validation)


def export_to_yaml(
    statechart: Statechart,
    filepath: str | bytes | os.PathLike | None = None,
) -> str:
    """
    Export given *Statechart* instance to YAML. Its YAML representation is returned by
    this function. Automatically save the output to filepath, if provided.

    :param statechart: statechart to export
    :param filepath: save output to given filepath, if provided
    :return: A textual YAML representation
    """
    output = StringIO()

    yml = yaml.YAML(typ="safe", pure=True)
    yml.dump(export_to_dict(statechart), output)

    if filepath:
        with open(filepath, "w") as f:
            f.write(output.getvalue())

    return output.getvalue()
