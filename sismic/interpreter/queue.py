import heapq

from typing import Tuple, List

from ..model import Event, InternalEvent, DelayedEvent


__all__ = ['EventQueue']


class EventQueue:
    """
    Simple event queue that supports delayed and internal events. 

    This class acts as a priority queue based on time. 

    :param internal_first: set to True (default) if internal events should have priority.
    """
    def __init__(self, *, internal_first=True) -> None:
        self._queue = []  # type: List[Tuple[float, bool, int, Event]]
        self._nb = 0
        self._internal_first = internal_first

    def _get_event(self, t):
        return (t[0], t[-1])

    def _set_event(self, time, event):
        self._nb += 1
        return (
            time + (event.delay if isinstance(event, DelayedEvent) else 0), 
            (1 - int(isinstance(event, InternalEvent))) if self._internal_first else 0,
            self._nb,
            event
        )

    def push(self, time: float, event: Event) -> None:
        """
        Put given event in the queue. 

        If given event is a DelayedEvent, appropriate modifications to time 
        will be done by this queue. 
        
        :param time: Current time. 
        :param event: Event to queue. 
        """
        heapq.heappush(self._queue, self._set_event(time, event))

    def pop(self) -> Tuple[float, Event]:
        """
        Return and dismiss first event. 

        :return: A pair (time, event). 
        """
        return self._get_event(heapq.heappop(self._queue))

    @property
    def first(self) -> Tuple[float, Event]:
        """
        Return the first event. 

        :return: A pair (time, event).
        """
        return self._get_event(self._queue[0])

    @property
    def empty(self) -> bool:
        """
        Holds if current queue is empty. 
        """
        return len(self._queue) == 0

    def __len__(self) -> int:
        return len(self._queue)

