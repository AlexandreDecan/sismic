Testing statecharts
===================

Like any executable software artefacts, statecharts can and should be tested during their development.

One possible appproach is to test the execution of a statechart *by hand*.
The Sismic interpreter stores and returns several values that can be inspected during the execution, including
the active configuration, the list of entered or exited states, etc.
The functional tests in *tests/test_interpreter.py* on the GitHub repository are several examples
of this kind of tests.

This way of testing statecharts is, however, quite cumbersome, especially if one would also like to test a statechart's contracts (i.e., its invariants and behavioral pre- and postconditions).

To overcome this, Sismic provides a module :py:mod:`sismic.stories` that makes it easy to test statecharts using statecharts themselves!


Writing stories
---------------

The module :py:mod:`sismic.stories` provides the building bricks to facilitate statechart testing.
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


Using stories to write tests
----------------------------

**Remark**: in the following, the term *statechart under test* refers to the statechart that is to be tested,
while the term *tester statechart* (or *tester* for short) refers to a statechart that expresses conditions or
invariants that should be satisfied by the statechart under test.

While *contracts* can be used to verify assertions on the context of a statechart during its execution,
*tester statecharts* can be used to test specific behavior of a *statechart under test*.
This tester is typically executed separately from the statechart's execution.

The :py:func:`~sismic.stories.story_from_trace` function provides an easy way to create *tester statecharts*:

1. Construct a story for the *statechart under test*.
2. Tell the story to the interpreter, and retrieve its :py:attr:`~sismic.interpreter.Interpreter.trace` trace.
3. Use the trace to generate a new story with :py:func:`~sismic.stories.story_from_trace`.
4. Tell this story on *tester statecharts*.

*Tester statecharts* are like any other statechart, in the sense that neither their syntax nor their semantics differ
from *statecharts under test*. The main difference comes from the events they receive.
Take a careful look at the documentation of :py:func:`~sismic.stories.story_from_trace` to find out
which events are generated for a story.

Another difference, which is more a useful convention than a rule, is that testers are
expected to end in a final state if the test did not fail.
This is, when ``stopped`` event is received, the tester should go in a final state if and
only if the test is successful.

The following *tester statechart* examples are relative to :ref:`this statechart <yaml_example>`.
They show the specification of some testers in YAML, and how to execute them.
Note that these testers are currently used as unit tests for Sismic.

Example tester statechart: 7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This *tester statechart* ensures that the 7th floor is never reached.
It stores the current floor based on the number of times the elevator goes up
and goes down.

.. literalinclude:: ../examples/tester_elevator_7th_floor_never_reached.yaml
   :language: yaml

It can be tested as follows:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached

You can even simulate a failure:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached_fails

Example tester statechart: Elevator moves after 10 seconds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This *tester statechart* checks that the elevator automatically moves after some idle time if it is not on
the ground floor. The test sets a timeout of 12 seconds, but it should work for any number strictly greater than
10 seconds.

.. literalinclude:: ../examples/tester_elevator_moves_after_10s.yaml
   :language: yaml

We check this tester using several stories, as follows:

.. literalinclude:: ../tests/test_story.py
    :pyobject: ElevatorStoryTests.test_elevator_moves_after_10s
