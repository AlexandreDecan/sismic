Executing statecharts
=====================

.. _semantic:

Statechart semantics
--------------------

The module :py:mod:`~sismic.interpreter` contains an :py:class:`~sismic.interpreter.Interpreter` class that
interprets a statechart mainly following the `SCXML 1.0 <http://www.w3.org/TR/scxml/>`__ semantics.
In particular, eventless transitions are processed *before* transitions containing events, internal events are consumed
*before* external events, and the simulation follows a inner-first/source-state and run-to-completion semantics.

The main difference between SCXML and Sismic's default interpreter resides in how multiple transitions
can be triggered simultaneously. This may occur for transitions in orthogonal/parallel states, or when transitions declaring the same event have guards that are not mutually exclusive.

Simulating the simultaneious triggering of multiple transitions is problematic,
since it implies to make a non-deterministic choice on the order in which the transitions must be processed,
and on the order in which the source states must the exited and the target states must be entered.
The UML 2.5 specification explicitly leaves this issue unresolved, thereby delegating the decision to tool developers:

    "Due to the presence of orthogonal Regions, it is possible that multiple Transitions (in different Regions) can be
    triggered by the same Event occurrence. The **order in which these Transitions are executed is left undefined**."
    --- `UML 2.5 Specification <http://www.omg.org/cgi-bin/doc?formal/15-03-01.pdf>`__

The SCXML specification addresses the issue by using the *document order* (i.e., the order in which the transitions
appear in the SCXML file) as the order in which (non-parallel) transitions should be processed.

    "If multiple matching transitions are present, take the **first in document order**."
    --- `SCXML Specification <http://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation>`__

From our point of view, this solution is not satisfactory.
The execution should not depend on the (often arbitrary) order in which items happen to be declared in some document,
in particular when there many be many different ways to construct or import a statechart.

Other statechart tools do not even define any order on the transitions in such situations:

    "Rhapsody detects such cases of nondeterminism during code generation
    and **does not allow them**. The motivation for this is that the generated code
    is intended to serve as a final implementation and for most embedded software
    systems such nondeterminism is not acceptable."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

We decide to follow Rhapsody and to raise an error (in fact, a ``Warning``) if such cases of
nondeterminism occur during the execution. Notice that this only concerns multiple transitions in the same
composite state, not in parallel states.

When multiple transitions are triggered from within distinct parallel states, the situation is even more intricate.
According to the Rhapsody implementation:

    "The order of firing transitions of orthogonal components is not defined, and
    depends on an arbitrary traversal in the implementation. Also, the actions on
    the transitions of the orthogonal components are **interleaved in an arbitrary
    way**."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

SCXML again circumvents this problem by using the *document order*.

    "enabledTransitions will contain multiple transitions only if a parallel state is active.
    In that case, we may have one transition selected for each of its children. [...]
    If multiple states are active (i.e., we are in a parallel region), then there may be multiple transitions,
    one per active atomic state (though some states may not select a transition.) In this case, the
    transitions are taken **in the document order of the atomic states** that selected them."
    --- `SCXML Specification <http://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation>`__

Again, Sismic does not agree with SCXML on this, and instead defines that multiple orthogonal/parallel transitions
should be processed in a decreasing source state depth order.
This is perfectly coherent with our aforementioned inner-first/source-state semantics, as "deeper" transitions are processed
before "less nested" ones. In case of ties, the lexicographic order of the source state names will prevail.

Note that in an ideal world, orthogonal/parallel regions should be independent, implying that *in principle* such situations should not
arise ("*the designer does not rely on any particular order for event instances to be dispatched
to the relevant orthogonal regions*", UML specification). In practice, however, it is often desirable to allow such situations.


Using *Interpreter*
-------------------

A :py:class:`~sismic.interpreter.Interpreter` instance is constructed upon a :py:class:`~sismic.model.StateChart`
instance and an optional callable that returns an :py:class:`~sismic.evaluator.Evaluator` (see :ref:`code_evaluation`).
If no evaluator is specified, the :py:class:`~sismic.evaluator.PythonEvaluator` class will be used.

Consider the following example.

.. testsetup:: interpreter

    from sismic.io import import_from_yaml
    my_statechart = import_from_yaml(open('../examples/elevator.yaml'))

.. testcode:: interpreter

    from sismic.interpreter import Interpreter
    from sismic.model import Event

    interpreter = Interpreter(my_statechart)

    # We are now in a stable initial state

    interpreter.send(Event('click'))  # Send event to the interpreter
    interpreter.execute_once()  # Will process the event if no eventless transitions are found at first

The method :py:meth:`~sismic.interpreter.Interpreter.execute_once` returns information about what happened
during the execution, including the transitions that were processed, the event that was consumed and the
sequences of entered and exited states (see :ref:`steps`).

For convenience, :py:meth:`~sismic.interpreter.Interpreter.send` returns ``self`` and thus can be chained.
We will see later that Sismic also provides a way to express scenarios, in order to avoid repeated calls to ``send``.

.. testcode:: interpreter

    interpreter.send(Event('click')).send(Event('click')).execute_once()

Notice that :py:meth:`~sismic.interpreter.Interpreter.execute_once` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call :py:meth:`~sismic.interpreter.Interpreter.execute_once` until
it returns a ``None`` value. For instance:

.. testcode:: interpreter

    while interpreter.execute_once():
      pass


As a shortcut, the :py:meth:`~sismic.interpreter.Interpreter.execute` method will return a list of
:py:class:`~sismic.interpreter.MacroStep` instances obtained by repeatedly calling
:py:meth:`~sismic.interpreter.Interpreter.execute_once`:


.. testcode:: interpreter

    from sismic.interpreter import MacroStep

    steps = interpreter.execute()
    for step in steps:
      assert isinstance(step, MacroStep)

Notice that a call to :py:meth:`~sismic.interpreter.Interpreter.execute` first computes the list and **then** returns
it, meaning that all the steps are already processed when the call returns.

As a call to :py:meth:`~sismic.interpreter.Interpreter.execute` could lead to an infinite execution
(see for example `simple/infinite.yaml <https://github.com/AlexandreDecan/sismic/blob/master/tests/yaml/infinite.yaml>`__),
an additional parameter ``max_steps`` can be specified to limit the number of steps that are computed
and executed by the method.

.. testcode:: interpreter

    assert len(interpreter.execute(max_steps=10)) <= 10

At any time, you can reset the simulator by calling :py:meth:`~sismic.interpreter.Interpreter.reset`.
For convenience, a :py:class:`~sismic.model.StateChart` has an :py:meth:`~sismic.model.StateChart.events` method
that returns the list of all possible events that can be interpreted by this statechart (other events will
be consumed and ignored).
This method also accepts a state name or a list of state names to restrict the list of returned events,
and is thus commonly used to get a list of the "interesting" events:

.. testcode:: interpreter

    print(my_statechart.events(interpreter.configuration))

.. testoutput:: interpreter
    :hide:

    ['floorSelected']


Putting all together, the main methods and attributes of a simulator instance are:

.. autoclass:: sismic.interpreter.Interpreter
    :members: send, execute_once, execute, time, configuration, final, trace, reset


.. _steps:

Macro and micro steps
---------------------

The Sismic interpreter is fully observable.
Its :py:meth:`~sismic.interpreter.Interpreter.execute_once`
(resp. :py:meth:`~sismic.interpreter.Interpreter.execute`) method returns
an instance of (resp. a list of) :py:class:`~sismic.interpreter.MacroStep`.
A *macro step* corresponds to the process of consuming an event, regardless of the number and the type (eventless or not)
of triggered transitions. A macro step also includes every consecutive *stabilization step*
(i.e., the steps that are needed to enter nested states, or to switch into the configuration of a history state).

A :py:class:`~sismic.interpreter.MacroStep` exposes the consumed ``event`` (an :py:class:`~sismic.model.Event` instance)
if any, a (possibly empty) list ``transitions`` of :py:class:`~sismic.model.Transition` instances,
and two aggregated ordered sequences of state names, ``entered_states`` and ``exited_states``.
The order of states in those lists determines the order in which their *on entry* and *on exit* actions were processed.
As transitions are atomically processed, this means that they could exit a state in ``entered_states`` that is
entered before some state in ``exited_states`` is exited.
The exact order in which states are exited and entered is indirectly available through the ``steps`` attribute that
is a list of all the :py:class:`~sismic.interpreter.MicroStep` that were executed. Each of them contains the states
that were exited and entered during its execution.


.. autoclass:: sismic.interpreter.MacroStep
    :members:

A *micro step* is the smallest, atomic step that a statechart can execute.
A :py:class:`~sismic.interpreter.MacroStep` instance thus can be viewed (and is!) an aggregate of
:py:class:`~sismic.interpreter.MicroStep` instances.

.. autoclass:: sismic.interpreter.MicroStep
    :members:

This way, a complete *run* of a statechart can be summarized as an ordered list of
:py:class:`~sismic.interpreter.MacroStep` instances,
and details of such a run can be obtained using the :py:class:`~sismic.interpreter.MicroStep` list of a
:py:class:`~sismic.interpreter.MacroStep`.
For convenience, an interpreter has a :py:attr:`~sismic.interpreter.trace` attribute that returns the list
of executed macro steps (including the initial stabilization step).


Dealing with time
-----------------

It is quite usual in a statechart to rely on some notion of time.
To cope with this, the built-in evaluator (see :py:class:`~sismic.evaluator.PythonEvaluator`) has support for
time events ``after(x)`` and ``idle(x)``, meaning that a transition can be triggered after a certain amount of time.

When it comes to interpreting statecharts, Sismic deals with time using an internal clock whose value is exposed
by the :py:attr:`~sismic.interpreter.Interpreter.time` property of an :py:class:`~sismic.interpreter.Interpreter`.
Basically, this clock does nothing by itself except for being available for an
:py:class:`~sismic.evaluator.Evaluator` instance.
If your statechart needs to rely on a time value, you have to set it by yourself.

Below are some examples to illustrate the use of time events.


Example with simulated time
***************************

Sismic provides a discrete step-by-step interpreter for statecharts.
It seems natural in a discrete simulation to rely on simulated time.

The following example illustrates a statechart modeling the behavior of a simple *elevator*.
If the elevator is sent to the 4th floor, according to the YAML definition of this statechart,
the elevator should automatically go back to the ground floor after 10 seconds.

.. code:: yaml

    - target: doorsClosed
      guard: after(10) and current > 0
      action: destination = 0

Rather than waiting for 10 seconds, one can simulate this.
First, one should load the statechart and initialize the interpreter:

.. testcode:: clock

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    with open('../examples/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)

The internal clock of our interpreter is ``0``.
This is, ``interpreter.time == 0`` holds.
We now ask our elevator to go to the 4th floor.

.. testcode:: clock

    interpreter.send(Event('floorSelected', data={'floor': 4}))
    interpreter.execute()

The elevator should now be on the 4th floor.
We inform the interpreter that 2 seconds have elapsed:

.. testcode:: clock

    interpreter.time += 2
    print(interpreter.execute())

.. testoutput:: clock
    :hide:

    []

The output should be an empty list ``[]``.
Of course, nothing happened since the condition ``after(10)`` is not
satisfied yet.
We now inform the interpreter that 8 additional seconds have elapsed.

.. testcode:: clock

    interpreter.time += 8
    print(interpreter.execute())

.. testoutput:: clock
    :hide:

    [MacroStep@10(None, [Transition(doorsOpen, doorsClosed, None)], >['doorsClosed'], <['doorsOpen']), MacroStep@10(None, [Transition(doorsClosed, movingDown, None)], >['moving', 'movingDown'], <['doorsClosed']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(moving, doorsOpen, None)], >['doorsOpen'], <['movingDown', 'moving'])]

The output now contains a list of steps, from which we can see that the elevator has moved down to the ground floor.
We can check the current floor:

.. testcode:: clock

    print(interpreter._evaluator.context['current'])

.. testoutput:: clock
    :hide:

    0

This displays ``0``.

Example with real time
**********************

If a statechart needs to be aware of a real clock, the simplest way to achieve this is by using
the :py:func:`time.time` function of Python.
In a nutshell, the idea is to synchronize ``interpreter.time`` with a real clock.
Let us first initialize an interpreter using one of our statechart example, the *elevator*:

.. testcode:: realclock

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    with open('../examples/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)

The interpreter initially sets its clock to 0.
As we are interested in a real-time simulation of the statechart,
we need to set the internal clock of our interpreter.
We import from :py:mod:`time` a real clock,
and store its value into a ``starttime`` variable.

.. testcode:: realclock

    import time
    starttime = time.time()

We can now execute the statechart by sending a ``floorSelected`` event, and wait for the output.
For our example, we first ask the statechart to send to elevator to the 4th floor.

.. testcode:: realclock

    interpreter.send(Event('floorSelected', data={'floor': 4}))
    interpreter.execute()
    print('Current floor:', interpreter._evaluator.context['current'])
    print('Current time:', interpreter.time)

At this point, the elevator is on the 4th floor and is waiting for another input event.
The internal clock value is still 0.

.. testoutput:: realclock

    Current floor: 4
    Current time: 0

We should inform our interpreter of the new current time.
Of course, as our interpreter follows a discrete simulation,
nothing really happens until we call
:py:meth:`~sismic.interpreter.Interpreter.execute` or :py:meth:`~sismic.interpreter.Interpreter.execute_once`.

.. testcode:: realclock

    interpreter.time = time.time() - starttime
    # Does nothing if (time.time() - starttime) is less than 10!
    interpreter.execute()

Assuming you quickly wrote these lines of code, nothing happened.
But if you wait a little bit, and update the clock again, it should move the elevator to the ground floor.

.. testcode:: realclock

    interpreter.time = time.time() - starttime
    interpreter.execute()

And *voilà*!

As it is not very convenient to manually set the clock each time you want to execute something, it is best to
put it in a loop.

.. code:: python

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    with open('../examples/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)

    # Initial scenario
    interpreter.send(Event('floorSelected', data={'floor': 4}))

    import time
    starttime = time.time()

    while not interpreter.final:
        interpreter.time = time.time() - starttime
        if interpreter.execute():
            print('something happened at time {}'.format(time.time()))

        time.sleep(0.5)  # 500ms

Here, we called the :py:func:`~time.sleep` function to slow down the loop (optional).
The output should look like::

    something happened at time 1450383083.9943285
    something happened at time 1450383093.9920669

As our statechart does not define any way to reach a final configuration,
the ``not interpreter.final`` condition always holds,
and the executiong needs to be interrupted manually.


Using *threading*
*****************

Notice from previous example that using a loop, it is not possible to send events to the interpreter.
For convenience, sismic provides a :py:func:`~sismic.interpreter.run_in_background`
function that run an interpreter in a thread, and does the job of synchronizing the clock for you.

.. autofunction:: sismic.interpreter.run_in_background


.. testcode:: thread

    import time
    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter, run_in_background
    from sismic.model import Event

    with open('../examples/microwave.yaml') as f:
        interpreter = Interpreter(import_from_yaml(f))

    run_in_background(interpreter, delay=0.01)

    print('Initial:', interpreter.configuration)

    # Open door
    interpreter.send(Event('toggledoor'))

    time.sleep(0.05)
    print('Toggledoor:', interpreter.configuration)


    # Wait 200ms and close the door
    time.sleep(0.200)
    interpreter.send(Event('toggledoor'))

    time.sleep(0.05)
    print('Toggledoor:', interpreter.configuration)


    # Wait 200ms and unplug
    time.sleep(0.200)
    interpreter.send(Event('unplug'))

    time.sleep(0.05)
    print('Final:', interpreter.configuration)

.. testoutput:: thread

    Initial: ['plugged', 'door', 'heating', 'lamp', 'turntable', 'door.close', 'heating.off', 'lamp.off', 'turntable.off']
    Toggledoor: ['plugged', 'door', 'heating', 'lamp', 'turntable', 'door.open', 'heating.off', 'lamp.on', 'turntable.off']
    Toggledoor: ['plugged', 'door', 'heating', 'lamp', 'turntable', 'door.close', 'heating.off', 'lamp.off', 'turntable.off']
    Final: []


.. _other_semantics:

Implementing other statechart semantics
---------------------------------------

A :py:class:`~sismic.interpreter.Interpreter` makes use of several protected methods for its initialization or to compute
which transition should be processed next, which are the next steps, etc.

These methods can be overridden or combined easily to define other variants of the statechart semantics.

.. automethod:: sismic.interpreter.Interpreter._select_eventless_transitions
.. automethod:: sismic.interpreter.Interpreter._select_transitions
.. automethod:: sismic.interpreter.Interpreter._sort_transitions
.. automethod:: sismic.interpreter.Interpreter._compute_transitions_steps
.. automethod:: sismic.interpreter.Interpreter._execute_step
.. automethod:: sismic.interpreter.Interpreter._compute_stabilization_step


These methods are called directly (or not) by :py:class:`~sismic.interpreter.Interpreter.execute_once`.
Consider looking at the source of :py:class:`~sismic.interpreter.Interpreter.execute_once` to understand
how these methods are related and organized.



Example: Outer-first/source-state semantics
*******************************************

For example, in order to obtain an outer-first/source-state semantics (instead of the
inner-first/source-state one that Sismic provides by default),
one should subclass :py:class:`~sismic.interpreter.Interpreter`
and override :py:class:`~sismic.interpreter.Interpreted._select_eventless_transitions` and
:py:class:`~sismic.interpreter.Interpreted._select_transitions`.
Actually, as the former relies on the second, the changes will only concern the traversal order in the
:py:class:`~sismic.interpreter.Interpreted._select_transitions` method.


Example: Semantics where internal events have no priority
*********************************************************

If you want to change the semantics of Sismic so that internal events no longer have
priority over external events, it suffices to override the :py:meth:`~sismic.interpreter.Interpreter.send` method:

.. code:: python

     def send(self, event:model.Event, internal=False):
        self.append(event)  # No distinction between internal and external events
        return self


Example: Custom way to deal with non-determinism
************************************************

If you want to change the way the Sismic semantics deals with non-determinism,
for example because it deviates from the semantics given by SCXML or Rhapsody
(remember :ref:`semantic`), you can implement your own variant for dealing with non-determinism.
The method :py:meth:`~sismic.interpreter.Interpreter._sort_transitions` is where the whole job is done:

1. It looks for non-determinism in (non-parallel) transitions,
2. It looks for conflicting transitions in parallel transitions,
3. It sorts the kept transitions based on our semantic.

According to your needs, adapt the content of this method.

