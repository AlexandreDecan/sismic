from .model import Event
import random


class Pause:
    """
    A convenience class to represent pause, ie. delay between sent events.

    :param duration: the duration of this pause
    """
    def __init__(self, duration: int):
        self._duration = duration

    @property
    def duration(self):
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
    A story is a sequence of ``Event`` and ``Pause``.

    """
    def tell(self, interpreter, *args, **kwargs):
        """
        Tells the whole story to the interpreter.

        :param interpreter: an interpreter instance
        :param args: additional positional arguments that are passed to ``interpreter.execute``.
        :param kwargs: additional keywords arguments that are passed to ``interpreter.execute``.
        :return: the interpreter, to chain calls
        """
        for item in self:
            if isinstance(item, Event):
                interpreter.send(item)
            elif isinstance(item, Pause):
                interpreter.time += item.duration
            interpreter.execute(*args, **kwargs)
        return interpreter

    def __repr__(self):
        return 'Story({})'.format(super().__repr__())


def random_stories_generator(items, length: int=None, number: int=None):
    """
    A generator that returns random stories whose elements come from *items*.
    Parameter *items* can be any iterable containing events and/or pauses.

    :param items: Items to pick from
    :param length: Length of the story, or ``len(items)``
    :param number: number of stories to generate (None = infinite)
    :return: An infinite Story generator
    """
    length = length if length else len(items)
    number = number if number else -1
    while number != 0:
        story = Story()
        for i in range(length):
            story.append(random.choice(items))  # Not random.sample, replacements needed
        yield story
        number -= 1

