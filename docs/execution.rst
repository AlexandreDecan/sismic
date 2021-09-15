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
can be triggered simultaneously. This may occur for transitions in orthogonal/parallel states, or when transitions 
declaring the same event have guards that are not mutually exclusive.

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
in particular when there may be many different ways to construct or to import a statechart.

Another statechart tool does not even define any order on the transitions in such situations:

    "Rhapsody detects such cases of nondeterminism during code generation
    and **does not allow them**. The motivation for this is that the generated code
    is intended to serve as a final implementation and for most embedded software
    systems such nondeterminism is not acceptable."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

We decide to follow Rhapsody and to raise an error (in fact, a :py:exc:`~sismic.exceptions.NonDeterminismError`) if such cases of
nondeterminism occur during the execution. Notice that this only concerns multiple transitions in the same
composite state, not in parallel states.

.. note:: 

    Sismic allows to define priorities on transitions. This can be used to address some cases of 
    nondeterminism. During execution, if a transition can be triggered, then transitions originating 
    from the same state and whose priority is strictly lower than the selected one won't be considered. 
    Note that, as usual, transitions with no event are considered before transitions with event, 
    regardless of the associated priorities.

When multiple transitions are triggered from within distinct parallel states, the situation is even more intricate.
According to the Rhapsody implementation:

    "The order of firing transitions of orthogonal components is not defined, and
    depends on an arbitrary traversal in the implementation. Also, the actions on
    the transitions of the orthogonal components are **interleaved in an arbitrary
    way**."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

SCXML circumvents this problem by relying again on the *document order*.

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


.. seealso::
    Other semantics can be quite easily implemented. For example, the extension *sismic-semantics* already
    provides support for outer-first/source-state semantics and priority to transitions with event.
    More information on :ref:`extensions`.


Using *Interpreter*
-------------------

An :py:class:`~sismic.interpreter.Interpreter` instance is constructed upon a :py:class:`~sismic.model.Statechart`
instance and an optional callable that returns an :py:class:`~sismic.code.Evaluator`.
This callable must accept an interpreter and an initial execution context as input (see :ref:`code_evaluation`).
If not specified, a :py:class:`~sismic.code.PythonEvaluator` will be used.
This default evaluator can parse and interpret Python code in statecharts.

Consider the following example:

.. testcode:: interpreter

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    # Load statechart from yaml file
    elevator = import_from_yaml(filepath='examples/elevator/elevator.yaml')

    # Create an interpreter for this statechart
    interpreter = Interpreter(elevator)

When an interpreter is built, the statechart is not yet in an initial configuration.
To put the statechart in its initial configuration (and to further execute the statechart),
call :py:meth:`~sismic.interpreter.Interpreter.execute_once`.

.. testcode:: interpreter

    print('Before:', interpreter.configuration)

    step = interpreter.execute_once()

    print('After:', interpreter.configuration)

.. testoutput:: interpreter

    Before: []
    After: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']

The method :py:meth:`~sismic.interpreter.Interpreter.execute_once` returns information about what happened
during the execution, including the transitions that were processed, the event that was consumed and the
sequences of entered and exited states (see :ref:`steps` and :py:class:`sismic.model.MacroStep`).

.. testcode:: interpreter

    for attribute in ['event', 'transitions', 'entered_states', 'exited_states', 'sent_events']:
        print('{}: {}'.format(attribute, getattr(step, attribute)))

.. testoutput:: interpreter

    event: None
    transitions: []
    entered_states: ['active', ...]
    exited_states: []
    sent_events: []


One can send events to the statechart using its :py:meth:`sismic.interpreter.Interpreter.queue` method.
This method accepts either an :py:class:`~sismic.interpreter.Event` instance, or the name of an event.
Multiple events (or names) can be provided at once.

.. testcode:: interpreter

    interpreter.queue('click')
    interpreter.execute_once()  # Process the "click" event

    interpreter.queue('clack')  # An event name can be provided as well
    interpreter.execute_once()  # Process the "clack" event

    interpreter.queue('click', 'clack')
    interpreter.execute_once()  # Process "click"
    interpreter.execute_once()  # Process "clack"

For convenience, :py:meth:`~sismic.interpreter.Interpreter.queue` returns the interpreter and thus can be chained:

.. testcode:: interpreter

    interpreter.queue('click', 'clack', 'clock').execute_once()

Notice that :py:meth:`~sismic.interpreter.Interpreter.execute_once` consumes at most one event at a time.
In the above example, the *clack* event is not yet processed.
This can be checked by looking at the external event queue of the interpreter.

.. testcode:: interpreter

    for time, event in interpreter._external_queue:
        print(event.name)

.. testoutput:: interpreter

    clack
    clock

.. note::

    An interpreter has two event queues, one for external events (the ones that are added using 
    :py:meth:`~sismic.interpreter.Interpreter.queue`), and one for internal events (the ones that 
    are sent from within the statechart). External events are stored in ``_external_queue`` while 
    internal events are stored in ``_internal_queue``. Internal events are always processed before
    external ones. To access the next event that will be processed by the interpreter, use the 
    :py:meth:`~sismic.interpreter.Interpreter._select_event` method. 

To process all events **at once**, one can repeatedly call :py:meth:`~sismic.interpreter.Interpreter.execute_once` until
it returns a ``None`` value, meaning that nothing happened during the last call. For instance:

.. testcode:: interpreter

    while interpreter.execute_once():
      pass

For convenience, an interpreter has an :py:meth:`~sismic.interpreter.Interpreter.execute` method that repeatedly
call :py:meth:`~sismic.interpreter.Interpreter.execute_once` and that returns a list of its output (a list of
:py:class:`sismic.model.MacroStep`).

.. testcode:: interpreter

    from sismic.model import MacroStep

    interpreter.queue('click', 'clack')

    for step in interpreter.execute():
      assert isinstance(step, MacroStep)

Notice that a call to :py:meth:`~sismic.interpreter.Interpreter.execute` first computes the list and **then** returns
it, meaning that all the steps are already processed when the call returns.
As a call to :py:meth:`~sismic.interpreter.Interpreter.execute` could lead to an infinite execution
(see for example `simple/infinite.yaml <https://github.com/AlexandreDecan/sismic/blob/master/tests/yaml/infinite.yaml>`__),
an additional parameter ``max_steps`` can be specified to limit the number of steps that are computed
and executed by the method. By default, this parameter is set to ``-1``, meaning there is no limit on the number
of underlying calls to :py:meth:`~sismic.interpreter.Interpreter.execute_once`.

.. testcode:: interpreter

    interpreter.queue('click', 'clack', 'clock')
    assert len(interpreter.execute(max_steps=2)) <= 2

    # 'clock' is not yet processed
    assert len(interpreter.execute()) == 1

The statechart used for these examples did not react to *click*, *clack* and *clock* because none of 
these events are expected to be received by the statechart (or, in other words, the statechart was
not written to react to these events). 

For convenience, a :py:class:`~sismic.model.Statechart` has an :py:meth:`~sismic.model.Statechart.events_for` method
that returns the list of all possible events that are expected by this statechart.

.. testcode:: interpreter

    print(elevator.events_for(interpreter.configuration))

.. testoutput:: interpreter

    ['floorSelected']

The *elevator* statechart, the one used for this example, only reacts to *floorSelected* events.
Moreover, it assumes that *floorSelected* events have an additional parameter named ``floor``.
These events are *parametrized* events, and their parameters be accessed by action code and guards 
in the statechart during execution. 

For example, the *floorSelecting* state of the *elevator* example has a transition
``floorSelected / destination = event.floor`` that stores the value of the *floor* parameter
into the *destination* variable.

To add parameters to an event, simply pass these parameters as named arguments to the 
:py:meth:`~sismic.interpreter.Interpreter.queue` method of the interpreter.


.. testcode:: interpreter

    print('Current floor is', interpreter.context['current'])

    interpreter.queue('floorSelected', floor=1)
    interpreter.execute()

    print('Current floor is', interpreter.context['current'])

.. testoutput:: interpreter

    Current floor is 0
    Current floor is 1

Notice how we can access the current values of *internal variables* by use of ``interpreter.context``.
This attribute is a mapping between internal variable names and their current value.


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
empty) list :py:attr:`~sismic.model.MacroStep.transition` of :py:class:`~sismic.interpreter.Transition` instances,
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
and details can be obtained using the :py:class:`~sismic.model.MicroStep` list of a
:py:class:`~sismic.model.MacroStep`.


Observing the execution
-----------------------

The interpreter is fully observable during its execution. It provides many methods and attributes
that can be used to see what happens. In particular:

* The :py:meth:`~sismic.interpreter.Interpreter.execute_once` (resp. :py:meth:`~sismic.interpreter.Interpreter.execute`)
   method returns an instance of (resp. a list of) :py:class:`sismic.model.MacroStep`.
* The :py:func:`~sismic.helpers.log_trace` function can be used to log all the steps that were processed during the
   execution of an interpreter. This methods takes an interpreter and returns a (dynamic) list of macro steps.
* The list of active states can be retrieved using :py:attr:`~sismic.interpreter.Interpreter.configuration`.
* The context of the execution is available using :py:attr:`~sismic.interpreter.Interpreter.context`
   (see :ref:`code_evaluation`).
* It is possible to bind a callable that will be called each time an event is sent by the statechart using
   the :py:meth:`~sismic.interpreter.Interpreter.bind` method of an interpreter (see :ref:`communication`).
* Meta-events are raised by the interpreter for specific events (e.g. a state is entered, a state is exited, etc.). 
   Listeners can subscribe to these meta-events with :py:attr:`~sismic.interpreter.Interpreter.attach`.


Asynchronous execution
----------------------

The calls to :py:meth:`~sismic.interpreter.Interpreter.execute` or :py:meth:`~sismic.interpreter.Interpreter.execute_once`
are blocking calls, i.e. they are performed synchronously. To allow asynchronous execution of a statechart, one 
has, e.g., to run the interpreter in a separate thread or to continuously loop over these calls. 

Module :py:mod:`~sismic.runner` contains an :py:class:`~sismic.runner.AsyncRunner` that provides basic
support for continuous asynchronous execution of statecharts:

.. autoclass:: sismic.runner.AsyncRunner
    :noindex:


    

Anatomy of the interpreter
--------------------------

.. note::

    This section explains which are the methods that are called during the execution of a statechart, and is 
    mainly useful if you plan to extend or alter the semantics of the execution.
    

An :py:class:`~sismic.interpreter.Interpreter` makes use of several *private* methods for its initialization and computations.
These methods computes the transition(s) that should be processed, the resulting steps, etc.
These methods can be overridden or combined to define variants of statechart semantics.

.. automethod:: sismic.interpreter.Interpreter._compute_steps

.. automethod:: sismic.interpreter.Interpreter._select_event

.. automethod:: sismic.interpreter.Interpreter._select_transitions

.. automethod:: sismic.interpreter.Interpreter._sort_transitions

.. automethod:: sismic.interpreter.Interpreter._create_steps

.. automethod:: sismic.interpreter.Interpreter._create_stabilization_step

.. automethod:: sismic.interpreter.Interpreter._apply_step


These methods are all used (even indirectly) by :py:class:`~sismic.interpreter.Interpreter.execute_once`.

.. seealso:: 

    Consider looking at the source of :py:class:`~sismic.interpreter.Interpreter.execute_once` to understand
    how these methods are related and organized.
