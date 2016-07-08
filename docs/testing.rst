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


Using statecharts to encode (un)desirable properties
----------------------------------------------------

**Remark**: in the following, the term *statechart under test* refers to the statechart that is to be tested,
while the term *property statechart* refers to a statechart that expresses conditions or
invariants that should be satisfied by the statechart under test.

While *contracts* can be used to verify assertions on the context of a statechart during its execution,
*property statecharts* can be used to test specific behavior of a *statechart under test*.

A *property statechart* defines a property that should (or not) be satisfied by other statecharts.
A *property statechart* is like any other statechart, in the sense that neither their syntax nor their semantics
differs from any other statechart. The difference comes from the events it receives and the role it plays.
If the run of a *statechart property* ends in a final state, it signifies that the property was verified.
In the case of a *desirable* property, this means that the test succeed.
In the case of an *undesirable* property, this means that the test failed.

.. note::

    This is more a convention than a requirement, but you should follow it.

The run of such a *property statechart* is driven by a specific sequence of events and pauses, which represents
what happens during the execution of a *statechart under test*.

For example, such a sequence contains *event consumed* events, *state entered* events, *state exited* events, ...
In particular, the following events are generated:

- A *execution started* event is sent at the beginning.
- each time a step begins, a *step started* event is created.
- each time an event is consumed, a *event consumed* event is created.
  the consumed event is available through the *event* attribute.
- each time a state is exited, an *state exited* event is created.
  the name of the state is available through the *state* attribute.
- each time a transition is processed, a *transition processed* event is created.
  the source state name and the target state name (if any) are available respectively through
  the *source* and *target* attributes.
  The event processed by the transition is available through the *event* attribute.
- each time a state is entered, an *state entered* event is created.
  the name of the state is available through the *state* attribute.
- each time a step ends, a *step ended* event is created.
- A *execution stopped* event is sent at the end.
- each time an event is fired from within the statechart, a *sent event* is created.
  the sent event is available through the *event* attribute.

The sequence does follow the interpretation order:

    1. an event is possibly consumed
    2. For each matching transition

       a. states are exited
       b. transition is processed
       c. states are entered
       d. internal events are sent
       e. statechart is stabilized (some states are exited and/or entered, some events are sent)


Using statechart to check properties on a trace
-----------------------------------------------

The trace of an interpreter is the list of its executed macro steps. The trace can be built upon the values returned by
each call to :py:meth:`~sismic.interpreter.Interpreter.execute` (or :py:meth:`~sismic.interpreter.Interpreter.execute_once`),
or can be automatically built using :py:meth:`sismic.interpreter.helpers.log_trace` function.

Function :py:func:`~sismic.testing.teststory_from_trace` provides an easy way to construct a story for
statechart properties from the trace obtained by executing a *statechart under test*.

.. autofunction:: sismic.testing.teststory_from_trace
    :noindex:

Notice that using this function, the property statechart can not access the context of the statechart under test.

To summarize, if you want to test the **trace** of a *statechart under test* ``tested``, you need to:

    1. construct a *property statechart* ``tester`` that expresses the property you want to test.
    2. execute ``tested`` (using a story or directly by sending events) and log its trace.
    3. generate a new story from this trace with :py:func:`~sismic.testing.teststory_from_trace`.
    4. tell this story to an interpreter of the *property statechart* ``tester``.

If ``tester`` ends in a final configuration, ie. ``tester.final`` holds, then the test is **considered** successful.
The semantic of *successful* depends on the *desirability* of the checked property.

The following *property statechart* examples are relative to :ref:`this statechart <elevator_example>`.
They show the specification of some testers in YAML, and how to execute them.

Note that these statechart properties are currently used as unit tests for Sismic.

7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^

This *property statechart* ensures that the 7th floor is never reached.
It stores the current floor based on the number of times the elevator goes up
and goes down.

.. literalinclude:: /examples/elevator/tester_elevator_7th_floor_never_reached.yaml
   :language: yaml

It can be tested as follows:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached

You can even simulate a failure:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_7th_floor_never_reached_fails

Elevator moves after 10 seconds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This *property statechart* checks that the elevator automatically moves after some idle time if it is not on
the ground floor. The test sets a timeout of 12 seconds, but it should work for any number strictly greater than
10 seconds.

.. literalinclude:: /examples/elevator/tester_elevator_moves_after_10s.yaml
   :language: yaml

We check this tester using several stories, as follows:

.. literalinclude:: ../tests/test_testing.py
    :pyobject: ElevatorStoryTests.test_elevator_moves_after_10s



Using statecharts to check properties at runtime
------------------------------------------------

Sismic provides a convenience class to allow *property statechart* to check properties at runtime.
Class :py:class:`~sismic.testing.ExecutionWatcher` can be used to associate a statechart tester with a *statechart under test*:

.. autoclass:: sismic.testing.ExecutionWatcher
    :noindex:
    :members: start, stop, watch_with


To summarize, if you want to test (**at runtime**) the execution of a *statechart under test* ``tested``, you need to:

    1. create an :py:class:`~sismic.testing.ExecutionWatcher` with ``tested``.
    2. construct at least one *property statechart* ``tester`` that expresses the property you want to test.
    3. associate each ``tester`` to the watcher with :py:meth:`~sismic.testing.ExecutionWatcher.watch_with`.
    4. start watching with :py:meth:`~sismic.testing.ExecutionWatcher.start`.
    5. execute ``tested`` (using a story or directly by sending events).
    6. stop watching with :py:meth:`~sismic.testing.ExecutionWatcher.stop`.

If ``tester`` ends in a final configuration, ie. ``tester.final`` holds, then the test is **considered** successful.
Again, the semantic of a *successful* run depends on the *desirability* of the property.

Destination should be reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This *property statechart* ensures that every chosen destination is finally reached.

.. literalinclude:: /examples/elevator/tester_elevator_destination_reached.yaml
   :language: yaml

It can be tested as follows:

.. testcode:: success

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.testing import ExecutionWatcher
    from sismic.model import Event

    # Load statecharts
    with open('examples/elevator/elevator.yaml') as f:
        elevator_statechart = import_from_yaml(f)
    with open('examples/elevator/tester_elevator_destination_reached.yaml') as f:
        tester_statechart = import_from_yaml(f)

    # Create the interpreter and the watcher
    interpreter = Interpreter(elevator_statechart)
    watcher = ExecutionWatcher(interpreter)

    # Add the tester and start watching
    tester = watcher.watch_with(tester_statechart)
    watcher.start()

    # Send the elevator to 4th
    interpreter.queue(Event('floorSelected', floor=4)).execute(max_steps=2)
    assert tester.context['destinations'] == [4]

    interpreter.execute()
    assert tester.context['destinations'] == []

    # Stop watching. The statechart ends in a final state only if a failure occured
    watcher.stop()

    assert not tester.final
