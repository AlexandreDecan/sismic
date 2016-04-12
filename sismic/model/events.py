from typing import Any


class Event:
    """
    Simple event with a name and (optionally) some data.
    Unless the attribute already exists, each key from *data* is exposed as an attribute
    of this class.

    :param name: Name of the event
    :param data: additional data (mapping, dict-like)
    """

    def __init__(self, name: str, **additional_parameters: Any) -> None:
        self.name = name
        self.data = additional_parameters

    def __eq__(self, other):
        return (isinstance(other, Event) and
                self.name == other.name and
                self.data == other.data)

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except:
            raise AttributeError('{} has no attribute {}'.format(self, attr))

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        if self.data:
            return '{}({}, {})'.format(self.__class__.__name__,
                                       self.name,
                                       ', '.join('{}={}'.format(k, v) for k, v in self.data.items()))
        else:
            return '{}({})'.format(self.__class__.__name__, self.name)


class InternalEvent(Event):
    """
    Subclass of Event that represents an internal event.
    """
    pass
