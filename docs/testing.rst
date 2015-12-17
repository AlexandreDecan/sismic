Testing statecharts with statecharts
====================================

Like software, statecharts can be tested too.

It is always possible to test the execution of a statechart *by hand*.
The interpreter stores and returns several values that can be inspected during the execution, including
the active configuration, the list of entered or exited states, etc.
The functional tests in *tests/test_interpreter.py* on the GitHub repository are several examples
of this kind of tests.

However, this approach is not really pleasant to test statecharts, and even less when it comes to specify
invariants or behavioral conditions.

Thanks to Sismic, module :py:mod:`sismic.checker` makes it easy to test statecharts.
In particular, this module brings a way to test statecharts using... statecharts!


Writing tests
-------------

**Remark**: in the following, the term *tested statechart* refers to the statechart that will be tested,
while the term *statechart testers* (or simply *testers*) refers to the ones that express conditions or
invariants that should be satisfied by the tested statechart.


Statechart testers are classical statechart, in the sense that their syntax nor their semantic differ
from tested statecharts. The main difference comes from the events they receive, and from the variables
and functions exposed in their execution context (see :ref:`python_evaluator`).


Specific received events
************************

In addition to (optional) internal events, a statechart tester is expected to automatically
receive a deterministic sequence of the three following events:

 - ``start`` -- this event is sent when a stable initial state is reached by the tested statechart.
 - ``stop`` -- this event is sent when the execution of the tested statechart ends (either because it reaches a final
   configuration, or no more transition can be processed, or because its execution was interrupted by
   :py:meth:`~sismic.checker.StateChartTester.stop`, see below).
 - ``step`` -- this event is sent after the computation and the execution of a :py:class:`~sismic.checker.MacroStep` in
   the tested statechart.


Specific contextual data
************************

Each tester is executed using by default a :py:class:`~sismic.evaluator.PythonEvaluator` and as such, contextual data
(the *context*) are available during execution. The context is exposed through a ``step`` variable to the tester,
and contains the following items:

.. py:function:: entered(state_name: str) -> bool

   Return *True* if given state name was entered in the last executed step.


.. py:function:: step.exited(state_name: str) -> bool

   Return *True* if given state name was exited in the last executed step.


.. py:function:: step.active(state_name: str) -> bool

   Return *True* if given state name was active in the last executed step.


.. py:function:: step.processed(event_name: str) -> bool

   Return *True* if given event was part of the last executed transition.


.. py:function:: step.consumed(event_name: str) -> bool

   Return *True* if given event was consumed in the last executed step, no matter if
   it lead to the execution of a transition.


Moreover, the context of a tester also expose the context of the tested statechart through ``step.context``.
This way, you can define guards (or actions) that rely on the data available in the tested statechart.

For example, the guard in the following transition (in a statechart tester) checks that ``moving`` is an active state
in tested statechart's current step, and checks the value of tested statechart's ``destination``:

.. code:: yaml

    statemachine:
        # ...
        transitions:
         - guard: step.active('moving') and step.context['destination'] > 0
           # ...

Examples
********

The following examples are relative to :ref:`this statechart <yaml_example>`.

Destination is finally reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tester is an example of a test that needs to end in a final configuration.
It ensures that a destination is always reached before the end
of the execution of the ``elevator`` statechart.

The state ``accepting`` awaits that a ``floorSelected`` event is processed.
When the floor is selected, the configuration is ``awaiting destination`` until
``current == destination``, when it goes to ``accepting`` again.
If the execution ends (``stop`` event) before the destination is reached (ie. in
another state than ``accepting``), the state ``assertion failed`` is reached where
the ``on entry`` raises an ``AssertionError``, meaning that the test failed.

.. literalinclude:: ../examples/tester/elevator/destination_reached.yaml
   :language: yaml


7th floor is never reached
^^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows that assertion can be made on transition action too.
This dummy example could fail if the current floor is ``7``.

.. literalinclude:: ../examples/tester/elevator/never_go_7th_floor.yaml
   :language: yaml


Doors are closed while moving
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tester checks that the elevator can not move (ie. be in ``moving`` state)
while the doors are opened.
If this happens, a transition to ``error`` occurs.
The ``on entry`` of ``error`` then raises an ``AssertionError``.

.. literalinclude:: ../examples/tester/elevator/closed_doors_while_moving.yaml
   :language: yaml


The *testing* module
--------------------

The :py:mod:`sismic.checker` module essentially defines the following classes:

 - :py:class:`~sismic.checker.TesterConfiguration` defines the configuration of a test
 - :py:class:`~sismic.checker.StateChartTester` initializes a test.

.. autoclass:: sismic.checker.TesterConfiguration
    :members:

.. autoclass:: sismic.checker.StateChartTester
    :members:


Executing tests
---------------

In order to test a statechart, you need to get:

    1. A statechart you want to test.
    2. At least one tester, ie. a statechart that checks some invariant or condition.
    3. A test scenario, which is in fact a list of :py:class:`~sismic.model.event` instances.

Assume we previously defined and imported a tested statechart ``tested_sc`` and a tester ``tester``, two
instances of :py:class:`~sismic.model.StateChart`.

We first define a test configuration.

.. code:: python

    from sismic.checker import TesterConfiguration, StateChartTester

    config = TesterConfiguration(tested_sc)

This configuration is mainly used to set a test environment (the ``setUp()`` of a unit test).
We can specify which code evaluator will be used, by specifying a callable that return an
:py:class:`~sismic.evaluator.Evaluator` instance. Remember that in Python, a class is a callable, so
it is perfectly legit to write this:

.. code:: python

    from sismic.evaluator import DummyEvaluator

    config = TesterConfiguration(tested_sc, evaluator_klass=DummyEvaluator)

It is also possible to specify a different semantic for the execution of the tested statechart (see :ref:`other_semantics`).
This can be done using the ``interpreter_klass`` parameter.

.. code:: python

    config = TesterConfiguration(tested_sc, interpreter_klass=MyOtherInterpreterClass)

This way, you can for example test that your initial statechart is invariant under several distinct interpreter.
It is now time to specify which are the testers we want to use.
Not surprisingly, :py:meth:`~sismic.checker.TesterConfiguration.add_test` method does the job.
This method takes a :py:class:`~sismic.model.StateChart` instance that is a statechart tester.

.. code:: python

    config.add_test(tester_sc)

You could add as many testers as you want.
It is also possible to provide specific code evaluator and specific interpreter for each tester, as it was
the case for the tested statechart. The syntax is the same:

.. code:: python

    config.add_test(other_tester_sc, evaluator_klass=DummyEvaluator, interpreter_klass=MyOtherInterpreterClass)


Our test configuration is now ready, and we can go one step further.
We now need to create a test. This can be done using :py:meth:`~sismic.checker.TesterConfiguration.build_tester`.
This method takes a list of :py:class:`~sismic.model.Event` which will be sent to the tested statechart.
This list can be viewed as a *scenario* for the test.
The method returns an instance of :py:class:`~sismic.checker.StateChartTester`.

.. code:: python

   from sismic.model import Event

   events = [Event('event1'), Event('event2'), Event('event3')]
   test = config.build_tester(events)

Using a ``test``, you can execute the test by calling :py:meth:`~sismic.checker.StateChartTester.execute_once` or
:py:meth:`~sismic.checker.StateChartTester.execute` (which repeatedly calls the first one).
A test mainly executes the tested statechart, step by step, and sends specific events to the tester.
The tester are then executed (using the :py:meth:`~sismic.interpreter.Interpreter.execute` method of the interpreter).

A test is considered as a success if the call to :py:meth:`~sismic.checker.StateChartTester.execute` ends, and
no :py:exc:`~sismic.model.ConditionFailed` (subclasses ``AssertionError``) was raised.

Depending on the underlying interpreter (but this at least concerns the default one!), the execution of a statechart
can be infinite. As for interpreter's :py:meth:`~sismic.interpreter.Interpreter.execute`, you can specify a
``max_steps`` parameter to limit the number of steps that are executed.

.. code:: python

    test.execute(max_steps=10)

At the end of the execution, you must call the :py:meth:`~sismic.checker.StateChartTester.stop` method.
This method sends a ``stop`` event to the statechart testers.
This permits testers to check that some condition still holds at the end of the execution.

As a shortcut, :py:class:`~sismic.testing.StateChartTester` exposes a context manager that does the job
for you. This context manager can be used as follows:

.. code:: python

    with config.build_tester(events) as test:
        test.execute()


A test fails when one of ``execute`` or ``stop`` (called implicitly by the context manager) raises
a :py:exc:`~sismic.model.ConditionFailed`.

Integrating with *unittest*
---------------------------

It is very easy to use the :py:mod:`~sismic.checker` module with Python :py:mod:`unittest`.

Consider the source of `tests/test_testing.py <https://github.com/AlexandreDecan/sismic/blob/master/tests/test_checker.py>`__:

.. literalinclude:: ../tests/test_checker.py
    :language: python