Defining reproducible scenarios
===============================

While events can be sent to an interpreter using its ``send`` method, it can be very convenient
to define and store scenarios, ie. sequences of events, that can drive the execution of a statechart.

Such scenarios are called *stories* in sismic, and can be used to accurately reproduce the execution of a statechart.

Writing stories
---------------

The module :py:mod:`sismic.stories` provides the building bricks to facilitate statechart execution.
The key concept of this module is the notion of *story*, which is a reproducible sequence of
events and pauses that drives a statechart interpreter.
For our running elevator example, a story may encode things like "*select the 4th floor, then
wait 5 seconds, then select the 2th floor, then wait 10 seconds*".

.. testcode::

    from sismic.stories import Story, Pause, Event

    story = Story()
    story.append(Event('floorSelected', data={'floor': 4}))
    story.append(Pause(5))
    story.append(Event('floorSelected', data={'floor': 2}))
    story.append(Pause(10))

For syntactical convenience, a story can also be created using a Python iterable:

.. testcode::

    story = Story([Event('floorSelected', data={'floor': 4}),
                   Pause(5),
                   Event('floorSelected', data={'floor': 2}),
                   Pause(10)])

A instance of :py:class:`~sismic.stories.Story` exhibits a :py:meth:`~sismic.stories.Story.tell`
method that can *tell* the story to an interpreter. Using this method, you can easily reproduce
a scenario.

.. testsetup::

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    with open('../examples/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)


.. testcode::

    # ...  (an interpreter is created for our elevator statechart)
    assert isinstance(interpreter, Interpreter)

    story.tell(interpreter)
    print(interpreter._evaluator.context['current'])
    print(interpreter.time)

.. testoutput::

    0
    15


Storywriters
------------

The module :py:mod:`sismic.stories` contains several helpers to write stories.
We expect this module to quickly growth and to provide many ways to automatically generate stories.

Currently, the module contains the following helpers:

.. automodule:: sismic.stories
    :members: random_stories_generator
    :exclude-members: Story, Pause
    :noindex:
