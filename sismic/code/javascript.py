from typing import cast, Iterator, Mapping
from typing import Dict, Iterator, cast, Any, Mapping, MutableMapping

import js2py
from .evaluator import Evaluator
from sismic.model import Event, InternalEvent, Transition, StateMixin, Statechart
from sismic.exceptions import CodeEvaluationError

__all__ = ['JavascriptEvaluator']


class JavascriptEvaluator(Evaluator):
    def __init__(self, interpreter=None, *, initial_context: Mapping=None) -> None:
        super().__init__()

        self._interpreter = interpreter
        self._js = js2py.EvalJs(initial_context if initial_context else {})

    @property
    def context(self):
        return self._js.__dict__['_var']

    def __send(self, name, parameters=None):
        if parameters is not None:
            parameters = parameters.to_dict()
        else:
            parameters = {}
        self._interpreter.queue(InternalEvent(name, **parameters))

    def _execute_code(self, code: str, *, additional_context: Mapping=None) -> None:
        exposed_context = {
            'send': self.__send,
        }
        exposed_context.update(additional_context if additional_context else {})

        for k, v in exposed_context.items():
            setattr(self._js, k, v)

        try:
            self._js.execute(code)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def _evaluate_code(self, code: str, *, additional_context: Mapping=None) -> bool:
        exposed_context = {}
        exposed_context.update(additional_context if additional_context else {})

        for k, v in exposed_context.items():
            setattr(self._js, k, v)

        try:
            return self._js.eval(code)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

