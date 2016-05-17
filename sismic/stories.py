from sismic.model import Event, InternalEvent
from sismic.model.steps import MacroStep
from sismic.interpreter import Interpreter

import random
from typing import List, Generator, Union, Tuple, Iterable, Sequence

__all__ = ['Pause', 'Story', 'random_stories_generator', 'story_from_trace']

Tellable = Union[Event, 'Pause']


class Pause:
    """
    A convenience class to represent pause, ie. delay between sent events.

    :param duration: the duration of this pause
    """
    def __init__(self, duration: float) -> None:
        self._duration = duration

    @property
    def duration(self) -> float:
        """
        The duration of this pause
        """
        return self._duration

    def __repr__(self):
        return 'Pause({})'.format(self.duration)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.duration == other.duration


class Story(list):
    """
    A story is a sequence of *Event* and *Pause*.

    """
    def tell(self, interpreter: Interpreter, *args, **kwargs) -> List[MacroStep]:
        """
        Tells the whole story to the interpreter.

        :param interpreter: an interpreter instance
        :param args: additional positional arguments that are passed to *interpreter.execute*.
        :param kwargs: additional keywords arguments that are passed to *interpreter.execute*.
        :return: the resulting trace of execution (a list of *MacroStep*)
        """
        trace = []  # type: List[MacroStep]
        for item in self:
            if isinstance(item, Event):
                interpreter.queue(item)
            elif isinstance(item, Pause):
                interpreter.time += item.duration
            step = interpreter.execute(*args, **kwargs)
            if step:
                trace.extend(step)
        return trace

    def tell_by_step(self, interpreter, *args, **kwargs) -> Generator[Tuple[Tellable, List[MacroStep]], None, None]:
        """
        Tells the story to the interpreter, step by step.
        This method returns a generator which yields the event or the pause that was told to the interpreter and
        the result of *interpreter.execute*.

        :param interpreter: an interpreter instance
        :param args: additional positional arguments that are passed to *interpreter.execute*.
        :param kwargs: additional keywords arguments that are passed to *interpreter.execute*.
        :return: a generator that yields (told event or pause, result of *interpreter.execute*).
        """
        for item in self:
            if isinstance(item, Event):
                interpreter.queue(item)
            elif isinstance(item, Pause):
                interpreter.time += item.duration
            yield item, interpreter.execute(*args, **kwargs)

    def __repr__(self):
        return 'Story({})'.format(super().__repr__())


def random_stories_generator(items: Sequence[Union[Event, Pause]],
                             length: int=None,
                             number: int=None) -> Generator[Story, None, None]:
    """
    A generator that returns random stories whose elements come from *items*.
    Parameter *items* can be any iterable containing events and/or pauses.

    :param items: Items to pick from
    :param length: Length of the story, or *len(items)*
    :param number: number of stories to generate (None = infinite)
    :return: An infinite Story generator
    """
    length = length if length else len(items)
    number = number if number else -1
    while number != 0:
        story = Story()
        for _ in range(length):
            story.append(random.choice(items))  # Not random.sample, replacements needed
        yield story
        number -= 1


def story_from_trace(trace: Iterable[MacroStep]) -> Story:
    """
    Return a story that is built upon the given trace (a list of macro steps).

    The story is composed of the same pauses and the same events than the ones
    that generated the given trace. The use case is when you want to reproduce
    the scenario of an observed behavior.

    Notice that internal events are ignored.

    :param trace: A list of *MacroStep* instances.
    :return: A story
    """
    story = Story()
    time = 0  # type: float

    for macrostep in trace:
        if macrostep.time > time:
            story.append(Pause(macrostep.time - time))
            time = macrostep.time

        if macrostep.event and not isinstance(macrostep.event, InternalEvent):
            story.append(macrostep.event)
    return story
