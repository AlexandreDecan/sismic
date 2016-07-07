Statecharts execution
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

Simulating the simultaneous triggering of multiple transitions is problematic,
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

We decide to follow Rhapsody and to raise an error (in fact, a :py:exc:`~sismic.exceptions.NonDeterminismError`) if such cases of
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

An :py:class:`~sismic.interpreter.Interpreter` instance is constructed upon a :py:class:`~sismic.model.Statechart`
instance and an optional callable that returns an :py:class:`~sismic.code.Evaluator`.
This callable must accept an interpreter and an initial execution context as input (see :ref:`code_evaluation`).
If not specified, a :py:class:`~sismic.code.PythonEvaluator` will be used.
This default evaluator can parse and interpret Python code in statecharts.

Consider the following example.

.. testsetup:: interpreter

    from sismic.io import import_from_yaml
    my_statechart = import_from_yaml(open('examples/elevator/elevator.yaml'))

.. testcode:: interpreter

    from sismic.interpreter import Interpreter
    from sismic.model import Event

    interpreter = Interpreter(my_statechart)

The method :py:meth:`~sismic.interpreter.Interpreter.execute_once` returns information about what happened
during the execution, including the transitions that were processed, the event that was consumed and the
sequences of entered and exited states (see :ref:`steps`).

The first call to :py:meth:`~sismic.interpreter.Interpreter.execute_once` puts the statechart in its initial
configuration:

.. testcode:: interpreter

    print('Before:', interpreter.configuration)

    step = interpreter.execute_once()

    print('After:', interpreter.configuration)

.. testoutput:: interpreter

    Before: []
    After: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']

One can send events to the statechart using its :py:meth:`sismic.interpreter.Interpreter.queue` methods.

.. testcode:: interpreter

    interpreter.queue(Event('click'))
    interpreter.execute_once()  # Process the event

For convenience, :py:meth:`~sismic.interpreter.Interpreter.queue` returns ``self`` and thus can be chained.
We will see later that Sismic also provides a way to express scenarios, in order to avoid repeated calls to ``queue``.

.. testcode:: interpreter

    interpreter.queue(Event('click')).queue(Event('click')).execute_once()

Notice that :py:meth:`~sismic.interpreter.Interpreter.execute_once` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call :py:meth:`~sismic.interpreter.Interpreter.execute_once` until
it returns a ``None`` value. For instance:

.. testcode:: interpreter

    while interpreter.execute_once():
      pass


As a shortcut, the :py:meth:`~sismic.interpreter.Interpreter.execute` method will return a list of
:py:class:`sismic.model.MacroStep` instances obtained by repeatedly calling
:py:meth:`~sismic.interpreter.Interpreter.execute_once`:


.. testcode:: interpreter

    from sismic.model import MacroStep

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

For convenience, a :py:class:`~sismic.model.Statechart` has an :py:meth:`~sismic.model.Statechart.events_for` method
that returns the list of all possible events that can be interpreted by this statechart (other events will
be consumed and ignored).
This method also accepts a state name or a list of state names to restrict the list of returned events,
and is thus commonly used to get a list of the "interesting" events:

.. testcode:: interpreter

    print(my_statechart.events_for(interpreter.configuration))

.. testoutput:: interpreter
    :hide:

    ['floorSelected']



.. _steps:

Macro and micro steps
---------------------

An interpreter :py:meth:`~sismic.interpreter.Interpreter.execute_once`
(resp. :py:meth:`~sismic.interpreter.Interpreter.execute`) method returns
an instance of (resp. a list of) :py:class:`sismic.model.MacroStep`.
A *macro step* corresponds to the process of consuming an event, regardless of the number and the type (eventless or not)
of triggered transitions. A macro step also includes every consecutive *stabilization step*
(i.e., the steps that are needed to enter nested states, or to switch into the configuration of a history state).

A :py:class:`~sismic.model.MacroStep` exposes the consumed :py:attr:`~sismic.model.MacroStep.event` if any, a (possibly
empty) list :py:attr:`~sismic.model.MacroStep.transitions` of :py:class:`~sismic.model.Transition` instances,
and two aggregated ordered sequences of state names, :py:attr:`~sismic.model.MacroStep.entered_states` and
:py:attr:`~sismic.model.MacroStep.exited_states`.
In addition, a :py:class:`~sismic.model.MacroStep` exposes a list :py:attr:`~sismic.model.MacroStep.sent_events` of
events that were fired by the statechart during the considered step.
The order of states in those lists determines the order in which their *on entry* and *on exit* actions were processed.
As transitions are atomically processed, this means that they could exit a state in
:py:attr:`~sismic.model.MacroStep.entered_states` that is entered before some state in
:py:attr:`~sismic.model.MacroStep.exited_states` is exited.
The exact order in which states are exited and entered is indirectly available through the
:py:attr:`~sismic.model.MacroStep.steps` attribute that is a list of all the :py:class:`~sismic.model.MicroStep`
that were executed. Each of them contains the states that were exited and entered during its execution, and the a list
of events that were sent during the step.

A *micro step* is the smallest, atomic step that a statechart can execute.
A :py:class:`~sismic.model.MacroStep` instance thus can be viewed (and is!) an aggregate of
:py:class:`~sismic.model.MicroStep` instances.

This way, a complete *run* of a statechart can be summarized as an ordered list of
:py:class:`~sismic.model.MacroStep` instances,
and details of such a run can be obtained using the :py:class:`~sismic.model.MicroStep` list of a
:py:class:`~sismic.model.MacroStep`.


Observing the execution
-----------------------

The interpreter is fully observable during its execution. It provides many public and private attributes
that can be used to see what happens. In particular:

 - The :py:meth:`~sismic.interpreter.Interpreter.execute_once` (resp. :py:meth:`~sismic.interpreter.Interpreter.execute`)
   method returns an instance of (resp. a list of) :py:class:`sismic.model.MacroStep`.
 - The :py:func:`~sismic.interpreter.helpers.log_trace` function can be used to log all the steps that were processed during the
   execution of an interpreter. This methods takes an interpreter and returns a (dynamic) list of macro steps.
 - The list of active states can be retrieved using :py:attr:`~sismic.interpreter.Interpreter.configuration`.
 - The context of the execution is available using :py:attr:`~sismic.interpreter.Interpreter.context`
   (see :ref:`code_evaluation`).
 - It is possible to bind a callable that will be called each time an event is sent by the statechart using
   the :py:attr:`~sismic.interpreter.Interpreter.bind` method of an interpreter (see :ref:`communication`).