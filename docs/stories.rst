Reproducible scenarios
======================

While events can be sent to an interpreter using its :py:meth:`~sismic.interpreter.Interpreter.queue` method, it can be very convenient
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
    story.append(Event('floorSelected', floor=4))
    story.append(Pause(5))
    story.append(Event('floorSelected', floor=2))
    story.append(Pause(10))

For syntactical convenience, the same story can also be written more compactly using a Python iterable:

.. testcode::

    story = Story([Event('floorSelected', floor=4),
                   Pause(5),
                   Event('floorSelected', floor=2),
                   Pause(10)])

A instance of :py:class:`~sismic.stories.Story` exhibits a :py:meth:`~sismic.stories.Story.tell`
method that can *tell* the story to an interpreter. Using this method, you can easily reproduce
a scenario. 

.. testsetup::

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    with open('examples/elevator/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)


.. testcode::

    # ...  (assume that some interpreter has been created for our elevator statechart)
    assert isinstance(interpreter, Interpreter)

    story.tell(interpreter)
    print(interpreter.time, interpreter.context.get('current'))

After having *told* the story to the interpreter, we observe that 15 seconds have passed, and the elevator has moved to the ground floor.

.. testoutput::

    15 0


While telling a whole story at once can be convenient, it is sometimes interesting to tell the story step by step.
The :py:meth:`~sismic.stories.Story.tell_by_step` returns a generator that yields the object (either a pause or an event)
that was told to the interpreter, and the result of calling :py:meth:`~sismic.interpreter.Interpreter.execute`.

.. testcode::

    # Recreate the interpreter
    interpreter = Interpreter(statechart)

    for told, macrosteps in story.tell_by_step(interpreter):
        print(interpreter.time, told, interpreter.context.get('current'))

.. testoutput::

    0 Event(floorSelected, floor=4) 4
    5 Pause(5) 4
    5 Event(floorSelected, floor=2) 2
    15 Pause(10) 0


Storywriters
------------

The module :py:mod:`sismic.stories` contains several helper methods to write stories.
We expect this module to quickly growth and to provide many ways to automatically generate stories.

Currently, the module contains the following helpers:

.. automodule:: sismic.stories
    :members: random_stories_generator, story_from_trace
    :exclude-members: Story, Pause
    :noindex:

