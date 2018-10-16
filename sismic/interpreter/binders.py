


class BindInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod # TODO Abstract the class, so that BindInterface cannot be instantiated. Necessary? So far its a NOP anyway.
    def __init__(self, Interpreter):
        self._interpreter = Interpreter

        pass

    def __eq__(self, other):
        # TODO : check it actually works ...
        if other is self:
            return True
        elif ofter is self._Interpreter
            return True

        # TODO handle Statechart, and the "Anonymous" class which handles a "callable"
        return False

    def raise(self, event):
        # Raise events on the Bind Target.
        return [] # Returns a list of events to be raised on the Bind Source.

    def execute(self):
        return None

    @property
    def final(self): # This is default behaviour, derived Bind Class will override as necessary.
        return False


class StatechartBind(BindInterface):
    # This is the normal Statechart Bind.

    def __init__(self, Interpreter):
        self._target = Interpreter

        pass

    def raise(self, event):
        # Raise the event on the Bind Target.
        if isinstance(event, InternalEvent):
            self._target.queue(Event(event.name, **event.data))

            # Return Metaevents to the Bind Source.
            meta_events = []
            meta_events.append(MetaEvent('event sent', event=external_event))
            if hasattr(event, 'delay'):
                # Deprecated since 1.4.0:
                meta_events.append(MetaEvent('delayed event sent', event=external_event))

            return meta_events
        return []

class CallableBind(BindInterface):
    #  TODO For the Callable target ... if this can work it will be great!

    def __init__(self, Callable):
        self._target = Callable

        pass

    def raise(self, event):
        # Raise the event on the Bind Target.
        if isinstance(event, InternalEvent):
            self._target(Event(event.name, **event.data))

            # Return Metaevents to the Bind Source.
            meta_events = []
            meta_events.append(MetaEvent('event sent', event=external_event))
            if hasattr(event, 'delay'):
                # Deprecated since 1.4.0:
                meta_events.append(MetaEvent('delayed event sent', event=external_event))

            return meta_events
        return []

class PropertyStatechartBind(BindInterface):
    # This is the Property Statechart Bind.
    def __init__(self, Interpreter):
        self._target = Interpreter

        pass

    def raise(self, event):
        # Raise the event on the Bind Target.
        if isinstance(event, MetaEvent):
            self._target.queue(event)
        return []

    def execute(self):
        self._target.execute()

        return None

    @property
    def final(self):
        return self._target.final
