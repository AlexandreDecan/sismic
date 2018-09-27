import copy
from types import CodeType
from typing import Any, Callable, Dict, List, Mapping, Optional

from . import EnhancedEvaluator
from ..exceptions import CodeEvaluationError
from ..model import (Event, InternalEvent, MetaEvent)

__all__ = ['PythonEvaluator']


def _create_send_function(event_list: List[Event]) -> Callable[..., None]:
    def send(name, **kwargs):
        event_list.append(InternalEvent(name, **kwargs))
    return send

def _create_notify_function(event_list: List[Event]) -> Callable[..., None]:
    def notify(name, **kwargs):
        event_list.append(MetaEvent(name, **kwargs))
    return notify


class PythonEvaluator(EnhancedEvaluator):
    """
    A code evaluator that understands Python.

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an *Interpreter* instance
    :param initial_context: a dictionary that will be used as *__locals__*
    """

    def __init__(self, interpreter=None, *, initial_context: Mapping[str, Any]=None) -> None:
        super().__init__(interpreter, initial_context=initial_context)

        # Precompiled code
        self._evaluable_code = {}  # type: Dict[str, CodeType]
        self._executable_code = {}  # type: Dict[str, CodeType]

    def _evaluate_code(self, code: Optional[str], *, additional_context: Mapping[str, Any]=None) -> bool:
        """
        Evaluate given code using Python.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        if code is None:
            return True

        compiled_code = self._evaluable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self._evaluable_code.setdefault(code, compile(code, '<string>', 'eval'))

        exposed_context = {
            'active': self._active,
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            return eval(compiled_code, exposed_context, self._context)  # type: ignore
        except Exception as e:
            raise CodeEvaluationError('"{}" occurred while evaluating "{}"'.format(e, code)) from e

    def _execute_code(self, code: Optional[str], *, additional_context: Mapping[str, Any]=None) -> List[Event]:
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        :return: a list of sent events
        """
        if code is None:
            return []

        compiled_code = self._executable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self._executable_code.setdefault(code, compile(code, '<string>', 'exec'))

        # Handle sent events
        sent_events = []  # type: List[Event]

        exposed_context = {
            'active': self._active,
            'send': _create_send_function(sent_events),
            'notify': _create_notify_function(sent_events),
            'time': self._interpreter.time,
            'setdefault': self._setdefault,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            exec(compiled_code, exposed_context, self._context)  # type: ignore
            return sent_events
        except Exception as e:
            raise CodeEvaluationError('"{}" occurred while executing "{}"'.format(e, code)) from e

    def __getstate__(self):
        attributes = self.__dict__.copy()
        attributes['_executable_code'] = dict()  # Code fragment cannot be pickled
        attributes['_evaluable_code'] = dict()  # Code fragment cannot be pickled
        return attributes
