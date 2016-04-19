from sismic.model import Statechart
import itertools
from typing import List

__all__ = ['export_to_tree']


def export_to_tree(statechart: Statechart, spaces: int=3) -> List[str]:
    """
    Provides a textual representation of the hierarchy of states belonging to
    a statechart. Only states are represented.

    :param statechart: A statechart instance
    :param spaces: spaces needed to indent a nested state
    :return: A list of lines, representation of the hierarchy of states belonging to a statechart.
    """
    def to_tree(state: str) -> List[str]:
        children = sorted(statechart.children_for(state))  # type: List[str]

        trees = map(to_tree, children)
        flat_trees = itertools.chain(*trees)
        children_repr = map(lambda x: spaces * ' ' + x, flat_trees)
        return [state] + list(children_repr)

    return to_tree(statechart.root)