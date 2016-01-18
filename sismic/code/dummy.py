from sismic.code import Evaluator

__all__ = ['DummyEvaluator']


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    @property
    def context(self):
        return dict()

    def _evaluate_code(self, code: str, additional_context: dict = None) -> bool:
        return True

    def _execute_code(self, code: str, additional_context: dict = None):
        return
