from functools import partial

import js2py
from sismic.code import Evaluator
from sismic.exceptions import CodeEvaluationError
from sismic.model import InternalEvent

__all__ = ['JavascriptEvaluator']


class JavascriptEvaluator(Evaluator):
    def __init__(self, interpreter=None, initial_context: dict=None):
        super().__init__(interpreter, initial_context)
        self._js = js2py.EvalJs(initial_context)

    @property
    def context(self):
        return self._js.__dict__['_var']

    def __send(self, name, parameters=None):
        if not parameters is None:
            parameters = parameters.to_dict()
        else:
            parameters = {}
        self._interpreter.queue(InternalEvent(name, **parameters))

    def _execute_code(self, code: str, additional_context: dict=None):
        exposed_context = {
            'send': self.__send,
        }
        exposed_context.update(additional_context if additional_context else {})

        for k, v in exposed_context.items():
            setattr(self._js, k, v)

        try:
            return self._js.execute(code)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def _evaluate_code(self, code: str, additional_context: dict=None):
        exposed_context = {}
        exposed_context.update(additional_context if additional_context else {})

        for k, v in exposed_context.items():
            setattr(self._js, k, v)

        try:
            return self._js.eval(code)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

