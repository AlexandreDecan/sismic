from .stories import Story, Pause
from .model import Event
import copy


class ConditionFailed(AssertionError):
    """
    Base exception for situations in which an assertion is not satisfied.
    All the parameters are optional, and will be exposed to ease debug.

    :param configuration: list of active states
    :param step: a ``MicroStep`` or ``MacroStep`` instance.
    :param obj: the object that is concerned by the assertion
    :param assertion: the assertion that failed
    :param context: the context in which the condition failed
    """

    def __init__(self, configuration=None, step=None, obj=None, assertion=None, context=None):
        super().__init__(self)
        self._configuration = copy.copy(configuration)
        self._step = copy.copy(step)
        self._obj = copy.copy(obj)
        self._assertion = copy.copy(assertion)
        self._context = {k: copy.copy(v) for k, v in context.items()} if context else {}

    @property
    def configuration(self):
        return self._configuration

    @property
    def step(self):
        return self._step

    @property
    def obj(self):
        return self._obj

    @property
    def condition(self):
        return self._assertion

    @property
    def context(self):
        return self._context

    def __str__(self):  # pragma: no cover
        message = ['{} not satisfied!'.format(self.__class__.__name__.replace('Failed', ''))]
        if self._obj:
            message.append('Object: {}'.format(self._obj))
        if self._assertion:
            message.append('Assertion: {}'.format(self._assertion))
        if self._configuration:
            message.append('Configuration: {}'.format(self._configuration))
        if self._step:
            message.append('Step: {}'.format(self._step))
        if self._context:
            message.append('Evaluation context:')
            for key, value in self._context.items():
                message.append(' - {key} = {value}'.format(key=key, value=value))

        return '\n'.join(message)


class PreconditionFailed(ConditionFailed):
    """
    A precondition is not satisfied.
    """
    pass


class PostconditionFailed(ConditionFailed):
    """
    A postcondition is not satisfied.
    """
    pass


class InvariantFailed(ConditionFailed):
    """
    An invariant is not satisfied.
    """
    pass


def story_from_trace(trace: list) -> Story:
    """
    Return a story based on the given *trace*, a list of macro steps.

    The story is constructed as follows:

     - the story begins with a *started* event.
     - the delay between pairs of consecutive steps creates a ``Pause`` instance.
     - each time an event is consumed, a *consumed* event is created.
       the consumed event is available through the ``event`` attribute.
     - each time a state is exited, an *exited* event is created.
       the name of the state is available through the ``state`` attribute.
     - each time a transition is processed, a *processed* event is created.
       the source state name and the target state name (if any) are available respectively through
       the ``source`` and ``target`` attributes.
       The event processed by the transition is available through the ``event`` attribute.
     - each time a state is entered, an *entered* event is created.
       the name of the state is available through the ``state`` attribute.
     - the story ends with a *stopped* event.

    The story does follow the interpretation order:

    1. an event is possibly consumed
    2. For each transition

       a. states are exited
       b. transition is processed
       c. states are entered
       d. statechart is stabilized (states are entered)

    :param trace: a list of ``MacroStep`` instances
    :return: A story
    """
    story = Story()
    story.append(Event('started'))
    time = 0

    for macrostep in trace:
        if macrostep.time > time:
            story.append(Pause(macrostep.time - time))
            time = macrostep.time

        if macrostep.event:
            story.append(Event('consumed', {'event': macrostep.event}))

        for microstep in macrostep.steps:
            for state in microstep.exited_states:
                story.append(Event('exited', {'state': state}))
            if microstep.transition:
                story.append(Event('processed', {'source': microstep.transition.from_state,
                                                 'target': microstep.transition.to_state,
                                                 'event': macrostep.event}))
            for state in microstep.entered_states:
                story.append(Event('entered', {'state': state}))

    story.append(Event('stopped'))
    return story
