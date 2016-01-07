Defining reproducible scenarios
===============================

While events can be sent to an interpreter using its ``send`` method, it can be very convenient
to define and store scenarios, ie. sequences or traces of events, that can control the execution of a statechart.

Such scenarios are called *stories* in sismic, and can be used to accurately reproduce the execution of a statechart.
They are also very instrumental for testing statecharts.

Writing stories
---------------

The module :py:mod:`sismic.stories` provides the building bricks to automate statechart execution.
The key concept of this module is the notion of *story*, which is a reproducible sequence of
events and pauses that control a statechart interpreter.
For our running elevator example, a story may encode things like "*first select the 4th floor, then
wait 5 seconds, then select the 2th floor, then wait for another 10 seconds*".
This would look as follows:

.. testcode::

    from sismic.stories import Story, Pause, Event

    story = Story()
    story.append(Event('floorSelected', data={'floor': 4}))
    story.append(Pause(5))
    story.append(Event('floorSelected', data={'floor': 2}))
    story.append(Pause(10))

For syntactical convenience, the same story can also be written more compactly using a Python iterable:

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

    # ...  (assume that some interpreter has been created for our elevator statechart)
    assert isinstance(interpreter, Interpreter)

    story.tell(interpreter)
    print(interpreter.time)
    print(interpreter.context['current'])

After having *told* the story to the interpreter, we observe that 15 seconds have passed, and the elevator has moved to the ground floor.

.. testoutput::

    15
    0


Storywriters
------------

The module :py:mod:`sismic.stories` contains several helper methods to write stories.
We expect this module to quickly growth and to provide many ways to automatically generate stories.

Currently, the module contains the following helpers:

.. automodule:: sismic.stories
    :members: random_stories_generator
    :exclude-members: Story, Pause
    :noindex:
