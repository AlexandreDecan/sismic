Testing statecharts
===================

Like any executable software artefacts, statecharts can and should be tested during their development.

One possible appproach is to test the execution of a statechart *by hand*.
The Sismic interpreter stores and returns several values that can be inspected during the execution, including
the active configuration, the list of entered or exited states, etc.
The functional tests in *tests/test_interpreter.py* on the GitHub repository are several examples
of this kind of tests.

This way of testing statecharts is, however, quite cumbersome, especially if one would also like to test a
statechart's contracts (i.e., its invariants and behavioral pre- and postconditions).

To overcome this, Sismic provides a module :py:mod:`sismic.testing` that makes it easy to test
statecharts using statecharts themselves!


Using stories to write tests
----------------------------

**Remark**: in the following, the term *statechart under test* refers to the statechart that is to be tested,
while the term *tester statechart* (or *tester* for short) refers to a statechart that expresses conditions or
invariants that should be satisfied by the statechart under test.

While *contracts* can be used to verify assertions on the context of a statechart during its execution,
*tester statecharts* can be used to test specific behavior of a *statechart under test*.

A *tester statechart* defines a property that should (or not) be satisfied by other statecharts.
A *tester statechart* is like any other statechart, in the sense that neither their syntax nor their semantics
differs from any other statechart. The difference comes from the events it receives and the role it plays.
A run of a *tester statechart* must end in a final state, meaning the test did not fail.
The run of such a *tester statechart* is driven by a specific sequence of events and pauses, which represents
what happens during the execution of a *statechart under test*.

For example, such a sequence contains *consumed* evnets, *entered* events, *exited* events, ...
Take a careful look at the documentation of :py:func:`~sismic.testing.teststory_from_trace` to find out
which events are generated for a story.

This function provides an easy way to construct a story for *statechart testers* from the trace obtained
by executing a *statechart under test*:

.. autofunction:: sismic.testing.teststory_from_trace
    :noindex:

To summarize, if you want to test a *statechart under test* ``tested``, you need to:

    1. construct a *tester statechart* ``tester`` that expresses the property you want to test.
    2. execute ``tested`` (using a story or directly by sending events).
    3. get its trace with ``trace = tested.trace``.
    4. generate a new story from this trace with :py:func:`~sismic.testing.teststory_from_trace`.
    5. tell this story to the *tester statechart* ``tester``.

If ``tester`` ends in a final configuration, ie. ``tester.final`` holds, then the test is considered successful.

Examples
--------

The following *tester statechart* examples are relative to :ref:`this statechart <elevator_example>`.
They show the specification of some testers in YAML, and how to execute them.
Note that these testers are currently used as unit tests for Sismic.

7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^

This *tester statechart* ensures that the 7th floor is never reached.
It stores the current floor based on the number of times the elevator goes up
and goes down.

.. literalinclude:: /examples/tester_elevator_7th_floor_never_reached.yaml
   :language: yaml

It can be tested as follows:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached

You can even simulate a failure:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached_fails

Elevator moves after 10 seconds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This *tester statechart* checks that the elevator automatically moves after some idle time if it is not on
the ground floor. The test sets a timeout of 12 seconds, but it should work for any number strictly greater than
10 seconds.

.. literalinclude:: /examples/tester_elevator_moves_after_10s.yaml
   :language: yaml

We check this tester using several stories, as follows:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_elevator_moves_after_10s
