from sismic.stories import Story, Pause
from sismic.model import Event

__all__ = ['teststory_from_trace']


def teststory_from_trace(trace: list) -> Story:
    """
    Return a test story based on the given *trace*, a list of macro steps.

    The story is constructed as follows:

     - the story begins with a *started* event.
     - the delay between pairs of consecutive steps creates a *pause* instance.
     - each time a step begins, a *step* event is created.
     - each time an event is consumed, a *consumed* event is created.
       the consumed event is available through the *event* attribute.
     - each time a state is exited, an *exited* event is created.
       the name of the state is available through the *state* attribute.
     - each time a transition is processed, a *processed* event is created.
       the source state name and the target state name (if any) are available respectively through
       the *source* and *target* attributes.
       The event processed by the transition is available through the *event* attribute.
     - each time a state is entered, an *entered* event is created.
       the name of the state is available through the *state* attribute.
     - the story ends with a *stopped* event.

    The story does follow the interpretation order:

    1. an event is possibly consumed
    2. For each transition

       a. states are exited
       b. transition is processed
       c. states are entered
       d. statechart is stabilized (some states are exited and/or entered)

    :param trace: a list of *MacroStep* instances
    :return: A story
    """
    story = Story()
    story.append(Event('started'))
    time = 0

    for macrostep in trace:
        if macrostep.time > time:
            story.append(Pause(macrostep.time - time))
            time = macrostep.time

        story.append(Event('step'))

        if macrostep.event:
            story.append(Event('consumed', event=macrostep.event))

        for microstep in macrostep.steps:
            for state in microstep.exited_states:
                story.append(Event('exited', state=state))
            if microstep.transition:
                story.append(Event('processed', source=microstep.transition.source,
                                   target=microstep.transition.target,
                                   event=macrostep.event))
            for state in microstep.entered_states:
                story.append(Event('entered', state=state))

    story.append(Event('stopped'))
    return story
