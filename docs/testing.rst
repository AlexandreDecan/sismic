Testing statecharts
===================

Like software, statecharts can be tested too.

It is always possible to test the execution of a statechart *by hand*.
The interpreter stores and returns several values that can be inspected during the execution, including
the active configuration, the list of entered or exited states, etc.
The functional tests in *tests/test_interpreter.py* on the GitHub repository are several examples
of this kind of tests.

However, this approach is not really pleasant to test statecharts, and even less when it comes to specify
invariants or behavioral conditions.

Thanks to Sismic, module :py:mod:`sismic.stories` makes it easy to test statecharts.
In particular, this module brings an easy way to test statecharts using... statecharts!


Writing stories
---------------

The module :py:mod:`sismic.stories` provides the building bricks to make it easy to test statecharts.
The core of this module is the concept of *story*. A story is a reproducible sequence of
events and pauses that drives a statechart interpreter.
For our running elevator example, a story may encode things like "*select the 4th floor, then
wait 5 seconds, then select the 2th floor, then wait 10 seconds*".

.. code:: python

    from sismic.stories import Story, Pause, Event

    story = Story()
    story.append(Event('floorSelected', data={'floor': 4}))
    story.append(Pause(5))
    story.append(Event('floorSelected', data={'floor': 2}))
    story.append(Pause(10))

For convenience, a story can be created using an iterable:

.. code:: python

    story = Story([Event('floorSelected', data={'floor': 4}), Pause(5),
                   Event('floorSelected', data={'floor': 2}), Pause(10)])

A instance of :py:class:`~sismic.stories.Story` exhibits a :py:meth:`~sismic.stories.Story.tell`
method that can *tell* a story to an interpreter. Using this method, you can easily reproduce
a scenario.

.. code:: python

    # ...  (an interpreter is created for our elevator statechart)
    assert isinstance(interpreter, Interpreter)

    story.tell(interpreter)
    print(interpreter._evaluator.context['current'])  # Displays "0"
    print(interpreter.time)  # Displays "15"


.. autoclass:: sismic.stories.Story
    :members:


Storywriters
------------

The module :py:mod:`sismic.stories` contains several helpers to write stories.
We expect this module to quickly growth and to provide many ways to automatically generate stories.

Currently, the module contains the following helpers:

.. automodule:: sismic.stories
    :members: random_stories_generator, story_from_trace
    :exclude-members: Story, Pause


Writing tests
-------------

**Remark**: in the following, the term *tested statechart* refers to the statechart that will be tested,
while the term *statechart testers* (or simply *testers*) refers to the ones that express conditions or
invariants that should be satisfied by the tested statechart.

While contract can be used to test assertion on the context of a statechart, a statechart tester
can be used to test the behavior of a tested statechart.

The :py:func:`~sismic.stories.story_from_trace` function makes it very easy to test statecharts:

1. Construct a story for the statechart you want to test.
2. Tell the story to the interpreter, and get its :py:attr:`~sismic.interpreter.Interpreter.trace` trace.
3. Use the trace with :py:func:`~sismic.stories.story_from_trace` to generate a new story.
4. Tell this story on *statechart testers*.

Statechart testers
******************

Statechart testers are classical statechart, in the sense that their syntax nor their semantic differ
from tested statecharts. The main difference comes from the events they receive.
Look carefully at the documentation of :py:func:`~sismic.stories.story_from_trace` to know
which are the events that are generated for a story.

Another difference, which is more a convention than a rule, is that statechart testers are
expected to end in a final configuration if the test did not fail.
This is, when ``stopped`` event is received, the tester should go in a final state if and
only if the test is successful.

The following statechart testers examples are relative to :ref:`this statechart <yaml_example>`.
They show definition of statechart testers in YAML, and how to execute the tests.
Notice that these pieces of code are currently used as unit test for Sismic.

7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^

This dummy statechart tester ensures that the 7th floor is never reached.
It stores the current floor based on the number of times the elevator goes up
and goes down.

.. literalinclude:: ../examples/testers/elevator_7th_floor_never_reached.yaml
   :language: yaml

It can be tested as follows:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached

You can even simulate a failure:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached_fails

Go to ground floor after 10 seconds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This statechart tester ensures that the elevator automatically goes to the ground floor
if nothing happened after 10 seconds. This example uses a parallel state to guess the current floor.

Notice that the timeout is set to 12 seconds (this should work for any number strictly greater than 10 seconds).

.. literalinclude:: ../examples/testers/elevator_go_ground_after_10s.yaml
   :language: yaml

We check this tester using several stories, as follows:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_go_ground_after_10s
