from .evaluator import Evaluator
from typing import Mapping

__all__ = ['DummyEvaluator']


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    def __init__(self, interpreter=None, *, initial_context=None):
        super().__init__()

    @property
    def context(self):
        return dict()

    def _evaluate_code(self, code: str, *, additional_context: Mapping=None) -> bool:
        return True

    def _execute_code(self, code: str, *, additional_context: Mapping=None) -> None:
        return
