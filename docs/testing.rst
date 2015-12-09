Testing statecharts with statecharts
====================================

Like software, statecharts can be tested too.

It is always possible to test the execution of a statechart *by hand*.
The simulator stores and returns several values that can be inspected during the execution, including
the active configuration, the list of entered or exited states, etc.
The functional tests in *tests/test_simulator.py* on the GitHub repository are several examples
of this kind of tests.

However, this approach is not really pleasant to test statecharts, and even less to specify invariants or
behavioral expectations.

PySS provides a module, namely :py:mod:`pyss.testing`, to ease statecharts testing.
In particular, this module brings a way to test statecharts using... statecharts!


How to write tests?
-------------------

In the following, we will make a clear distinction between the *tested statechart* (the one that we are
interested to test) and *statechart testers* (or simply *testers*), which are the ones that express the conditions or
invariants that should be satisfied by the tested statechart.

Testers are classical statechart, in the sense that the syntax nor the semantic differ
from tested statecharts.

These statecharts differ in the events they receive, and from the variables and functions available in
their execution context (see :ref:`python_evaluator`).


Specific events received
************************

In addition to (optional) internal events, a tester is expected to automatically
receive a deterministic sequence of the three following events:

 - ``start``: this event is sent when a stable initial state is reached by the tested statechart.
 - ``stop``: this event is sent when the execution of the tested statechart ends (either because it reaches a final
   configuration, or no more transition can be processed, or because its execution was interrupted by
   :py:meth:`~pyss.testing.StateChartTester.stop`, see below).
 - ``step``: this event is sent after the computation and the execution of a :py:class:`~pyss.simulator.MacroStep` in
   the tested statechart.


Specific contextual data
************************

Each tester is executed using a :py:class:`~pyss.evaluator.PythonEvaluator` and as such, contextual data
(the *context*) are available during execution. In the case of a tester, this context is always populated and
updated with the following items:

.. :function:: entered(state_name: str) -> bool

   Return *True* if given state name was entered in the last executed step.

.. :function:: exited(state_name: str) -> bool

   Return *True* if given state name was exited in the last executed step.

.. :function:: active(state_name: str) -> bool

   Return *True* if given state name was active in the last executed step.

.. :function:: processed(event_name: str) -> bool

   Return *True* if given event was part of the last executed transition.

.. :function:: consumed(event_name: str) -> bool

   Return *True* if given event was consumed in the last executed step, no matter if
   it lead to the execution of a transition.


Moreover, the context also expose the context of the tested statechart through the key ``context``.
For example, the following YAML definition of a transition accesses the ''destination`` value
of a tested statechart:

.. code:: yaml

    statemachine:
        # ...
        transitions:
         - guard: context['destination'] > 0
           # ...


Expected behavior
*****************

Importantly, and this is why this point deserves a subsection, you **must** ensure that valid execution
of your testers end in a final configuration.

At the end of the execution of a test, an assertion will be raised if there is a tester which is not in a
final configuration.


Examples
********

The following examples are relative to :ref:`yaml_example`.

Destination is finally reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tester is an example of a test that needs to end in a final configuration.

This tester ensures that a destination is always reached before the end
of the execution of the ``elevator`` statechart.

The state ``waiting`` awaits that a ``floorSelected`` event is processed.
When the floor is selected, it waits until ``current == destination`` to go
in ``destinationReached`` state.

If the execution ends (``stop`` event) before the destination is reached (ie. in
another state than ``destinationReached``), the tester execution does not end
in a final state, meaning that the test fails.

.. literalinclude:: examples/tester/elevator/destination_reached.yaml
   :language: yaml


Doors are closed while moving
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tester is an example of a test that raises an ``AssertionError``.

This tester checks that the elevator can not move (ie. be in ``moving`` state)
while the doors are opened.
If this happens, a transition to ``error`` occurs.
The ``on entry`` of ``error`` then raises an ``AssertionError``.

.. literalinclude:: examples/tester/elevator/closed_doors_while_moving.yaml
   :language: yaml

7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^

This dummy example could fail if the current floor is ``7``.
This example shows that assertion can be made on transition action too.

.. literalinclude:: examples/tester/elevator/never_go_7th_floor.yaml
   :language: yaml


The *testing* module
--------------------

The :py:mod:`pyss.testing` module essentially defines the following classes:

 - :py:class:`~pyss.testing.TesterConfiguration` defines the configuration of a test
 - :py:class:`~pyss.testing.StateChartTester` initializes a test.

.. autoclass:: pyss.testing.TesterConfiguration

.. autoclass:: pyss.testing.StateChartTester
    :members:

In order to test a statechart, you need to get:

1. A statechart you want to test.
2. At least one tester, ie. a statechart that checks some invariant or condition.
3. A test scenario, which is in fact a list of :py:class:`~pyss.model.event` instances.


Executing tests
---------------

Assume we previously defined and imported a tested statechart ``tested_sc`` and a tester ``tester``, two
instances of :py:class:`~pyss.model.StateChart`.

We first define a test configuration.

.. code:: python

    config = TesterConfiguration(tested_sc)

This configuration is mainly used to set a test environment (the ``setUp()`` of a unit test).
We can specify which code evaluator will be used, by specifying a :py:class:`~pyss.evaluator.Evaluator` instance:

.. code:: python

    config = TesterConfiguration(tested_sc, evaluator=DummyEvaluator)

It is also possible to specify a different semantic for the execution of the tested statechart (see :ref:`other_semantics`).
This can be done using the ``simulator_class`` parameter. Importantly, as the name suggests,
you should not provide an instance of a simulator, but a class (or any callable that takes a
:py:class:`~pyss.model.StateChart` and a :py:class:`~pyss.evaluator.Evaluator` and that returns a simulator).

.. code:: python

    config = TesterConfiguration(tested_sc, simulator_class=MyOtherSimulatorClass)

This way, you can for example test that your initial statechart is invariant under several distinct simulator.

It is now time to specify which are the testers we want to use.
Not surprisingly, :py:meth:`~pyss.testing.TesterConfiguration.add_test` method does the job.
This method takes a :py:class:`~pyss.model.StateChart` instance that is a statechart tester.

.. code:: python

    config.add_test(tester_sc)

You could add as many testers as you want.

It is also possible to provide specific code evaluator and specific simulator for each tester, as it was
the case for the tested statechart. The syntax is the same:

.. code:: python

    config.add_test(other_tester_sc, evaluator=DummyEvaluator, simulator_class=MyOtherSimulatorClass)


Our test configuration is now ready, and we can go one step further.
We now need to create a test. This can be done using :py:meth:`~pyss.testing.TesterConfiguration.build_tester`.
This method takes a list of :py:class:`~pyss.model.Event` which will be sent to the tested statechart.
This list can be viewed as a *scenario* for the test.
The method returns an instance of :py:class:`~pyss.testing.StateChartTester`.

.. code:: python

   events = [Event('event1'), Event('event2'), Event('event3')]
   test = config.build_tester(events)

Using a ``test``, you can execute the test by calling :py:meth:`~pyss.testing.StateChartTester.execute_once` or
:py:meth:`~pyss.testing.StateChartTester.execute` (which repeatedly calls the first one).

A test mainly executes the tested statechart, step by step, and sends specific events to the tester.
The tester are then executed (using the :py:meth:`~pyss.simulator.Simulator.execute` method of the simulator).

Success of a test
*****************

A test is successful if a call :py:meth:`~pyss.testing.StateChartTester.execute` ends with no
``AssertionError`` raised.

As such an execution can lead to an infinite loop, you may be tempted to define a ``max_steps`` limit for the execution.
In this case, you should also manually call :py:meth:`~pyss.testing.StateChartTester.stop` at the end of the
execution to ensure that testers are aware of the end of the execution.

This method mainly sends a ``stop`` event, and checks that every tester is in a final configuration.

Failure of a test
*****************

A test failed when one of the following occurs:

 - An AssertionError was raised by one of the tester.
 - There is at least one tester that is not in a final configuration after the execution (or when
   :py:meth:`~pyss.testing.StateChartTester.stop` is called).
 - Any other exception occurred in the execution of the tested statechart or the statechart testers.
