from typing import Any


class Event:
    """
    Simple event with a name and (optionally) some data.
    Unless the attribute already exists, each key from *data* is exposed as an attribute
    of this class.

    The list of defined attributes can be obtained using *dir(event)*.

    :param name: Name of the event
    :param data: additional data (mapping, dict-like)
    """

    __slots__ = ['name', 'data']

    def __init__(self, name: str, **additional_parameters: Any) -> None:
        self.name = name
        self.data = additional_parameters

    def __eq__(self, other):
        return (self.name == other.name and self.data == other.data) if isinstance(other, Event) else NotImplemented

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError('{} has no attribute {}'.format(self, attr))

    def __getstate__(self):
        # For pickle and implicitly for multiprocessing
        return (self.name, self.data)

    def __setstate__(self, state):
        # For pickle and implicitly for multiprocessing
        self.name, self.data = state

    def __hash__(self):
        return hash(self.name)

    def __dir__(self):
        return ['name'] + list(self.data.keys())

    def __repr__(self):
        if self.data:
            return '{}({!r}, {})'.format(self.__class__.__name__,
                                         self.name,
                                         ', '.join('{}={!r}'.format(k, v) for k, v in self.data.items()))
        else:
            return '{}({!r})'.format(self.__class__.__name__, self.name)


class InternalEvent(Event):
    """
    Subclass of Event that represents an internal event.
    """
    pass
