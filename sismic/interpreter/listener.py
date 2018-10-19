from typing import Callable, Any

from ..model import MetaEvent, InternalEvent, Event

from ..exceptions import PropertyStatechartError


__all__ = ['InternalEventListener', 'PropertyStatechartListener']


class InternalEventListener:
    """
    Listener that filters and propagates internal events as external events. 
    """
    def __init__(self, callable: Callable[[Event], Any]) -> None:
        self._callable = callable

    def __call__(self, event: MetaEvent) -> None:
        if event.name == 'event sent':
            self._callable(Event(event.event.name, **event.event.data))


class PropertyStatechartListener:
    """
    Listener that propagates meta-events to given property statechart, executes
    the property statechart, and checks it.
    """
    def __init__(self, interpreter) -> None:
        self._interpreter = interpreter

    def __call__(self, event: MetaEvent) -> None:
        self._interpreter.queue(event)
        self._interpreter.execute()
        if self._interpreter.final:
            raise PropertyStatechartError(self._interpreter)