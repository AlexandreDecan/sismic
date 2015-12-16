Executing statecharts
=====================

.. _semantic:

Statechart semantic
-------------------

The module :py:mod:`~sismic.interpreter` contains an :py:class:`~sismic.interpreter.Interpreter` class that
interprets a statechart mainly following `SCXML <http://www.w3.org/TR/scxml/>`__ semantic.
In particular, eventless transitions are processed before evented transitions, internal events are consumed
before external events, and the simulation follows a inner-first/source-state and run-to-completion semantic.

The main difference between SCXML and Sismic's default interpreter comes when considering that multiple transitions
can be triggered at once. This may occurs when transitions sharing a same event have guards that are not mutually
exclusive or for transitions in parallel states.

Triggering multiple transitions at once implies a non-deterministic choice in the order in which transitions must be
processed, and in the order in which states must be exited and/or entered.
This is problematic as even the UML specification does not enforce an order:

    "Due to the presence of orthogonal Regions, it is possible that multiple Transitions (in different Regions) can be
    triggered by the same Event occurrence. The **order in which these Transitions are executed is left undefined**."
    --- `UML 2.5 Specification <http://www.omg.org/cgi-bin/doc?formal/15-03-01.pdf>`__

The problem is currently addressed by the SCXML specification which defines document order as the order
in which (non-parallel) transitions should be processed.

    "If multiple matching transitions are present, take the **first in document order**."
    --- `SCXML Specification <http://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation>`__

However, from our point of view, this solution is not satisfactory.
The execution should not depend on the order in which items are defined in some document, in particular when
there are many different ways to construct or to import a statechart.
Some other tools do not even define any order on the transitions in such situations:

    "Rhapsody detects such cases of nondeterminism during code generation
    and **does not allow them**. The motivation for this is that the generated code
    is intended to serve as a final implementation and for most embedded software
    systems such nondeterminism is not acceptable."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

We decide to follow Rhapsody and to raise an error (in fact, a ``Warning``) if such cases of
nondeterminism occur during the execution. Notice that this only concerns multiple transitions in the same
component, not in parallel component.
When multiple transitions are triggered from distinct parallel components, the situation is even more intricate.

    "The order of firing transitions of orthogonal components is not defined, and
    depends on an arbitrary traversal in the implementation. Also, the actions on
    the transitions of the orthogonal components are **interleaved in an arbitrary
    way**."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

SCXML circumvents this problem using again document definition order.

    "enabledTransitions will contain multiple transitions only if a parallel state is active.
    In that case, we may have one transition selected for each of its children. [...]
    If multiple states are active (i.e., we are in a parallel region), then there may be multiple transitions,
    one per active atomic state (though some states may not select a transition.) In this case, the
    transitions are taken **in the document order of the atomic states** that selected them."
    --- `SCXML Specification <http://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation>`__

Sismic does not agree with SCXML on the chosen order, and defines that multiple orthogonal transitions
should be processed in a decreasing source state depth order.
This is perfectly coherent with the inner-first/source-state semantic, as "deeper" transitions are processed
before "less nested" ones. Ties are broken by lexicographic order of the source states names.

Notice that orthogonal regions should ideally be independent, implying that such situations should not
arise ("*the designer does not rely on any particular order for event instances to be dispatched
to the relevant orthogonal regions*", UML specification).


Using *Interpreter*
-------------------

A :py:class:`~sismic.interpreter.Interpreter` instance is constructed upon a :py:class:`~sismic.model.StateChart`
instance and an optional callable that returns an :py:class:`~sismic.evaluator.Evaluator` (see :ref:`code_evaluation`).
If no evaluator is specified, :py:class:`~sismic.evaluator.PythonEvaluator` class will be used.

Consider the following example.

.. code:: python

    from sismic.interpreter import Interpreter
    from sismic.model import Event

    interpreter = Interpreter(my_statechart)
    # We are now in a stable initial state
    interpreter.send(Event('click'))  # Send event to the interpreter
    interpreter.execute_once()  # Will process the event if no eventless transitions are found at first

The method :py:meth:`~sismic.interpreter.Interpreter.execute_once` returns information about what happened
during the execution, including the transitions that were processed, the event that was consumed and the
sequences of entered and exited states (see :ref:`steps`).

For convenience, :py:meth:`~sismic.interpreter.Interpreter.send` returns ``self`` and thus can be chained:

.. code:: python

    interpreter.send(Event('click')).send(Event('click')).execute_once()

Notice that :py:meth:`~sismic.interpreter.Interpreter.execute_once` consumes at most one event at a time.
In this example, the second *click* event is not processed.
..
To process all events *at once*, repeatedly call :py:meth:`~sismic.interpreter.Interpreter.execute_once` until
it returns a ``None`` value. For instance:

.. code:: python

    while interpreter.execute_once():
      pass


As a shortcut, the :py:meth:`~sismic.interpreter.Interpreter.execute` method will return a list of
:py:class:`~sismic.interpreter.MacroStep` instances obtained by repeatedly calling
:py:meth:`~sismic.interpreter.Interpreter.execute_once`:

.. code:: python

    from sismic.interpreter import MacroStep

    steps = interpreter.execute()
    for step in steps:
      assert isinstance(step, MacroStep)

Notice that a call to :py:meth:`~sismic.interpreter.Interpreter.execute` first computes the list and **then** returns
it, meaning that all the steps are already processed when the call returns.
..
As a call to :py:meth:`~sismic.interpreter.Interpreter.execute` could lead to an infinite execution
(see for example `simple/infinite.yaml <https://github.com/AlexandreDecan/sismic/blob/master/examples/simple/infinite.yaml>`__),
an additional parameter ``max_steps`` can be specified to limit the number of steps that are computed
and executed by the method.

.. code:: python

    assert len(interpreter.execute(max_steps=10)) <= 10

At any time, you can reset the simulator by calling :py:meth:`~sismic.interpreter.Interpreter.reset`.
..
For convenience, a :py:class:`~sismic.model.StateChart` has an :py:meth:`~sismic.model.StateChart.events` method
that returns the list of all possible events that can be interpreted by this statechart (other events will
be consumed and ignored).
..
This method also accepts a state name or a list of state names to restrict the list of returned events,
and is thus commonly used to get a list of the "interesting" events:

.. code:: python

    print(my_statechart.events(interpreter.configuration))



Putting all together, the main methods and attributes of a simulator instance are:

.. autoclass:: sismic.interpreter.Interpreter
    :members: send, execute_once, execute, configuration, running, reset


.. _steps:

Macro and micro steps
---------------------

The interpreter is fully observable: its :py:meth:`~sismic.interpreter.Interpreter.execute_once`
(resp. :py:meth:`~sismic.interpreter.Interpreter.execute`) method returns
an instance of (resp. a list of) :py:class:`~sismic.interpreter.MacroStep`.
A macro step corresponds to the process of consuming an event, regardless of the number and the type (eventless or not)
of triggered transitions. A macro step also includes every consecutive stabilization step
(ie. the steps that are needed to enter nested states, or to switch into the configuration of an history state).

A :py:class:`~sismic.interpreter.MacroStep` exposes the consumed ``event`` (an :py:class:`~sismic.model.Event` instance)
if any, a (possibly empty) list ``transitions`` of :py:class:`~sismic.model.Transition` instances, and two
aggregated ordered sequences of state names, ``entered_states`` and ``exited_states``.
States order in those list indicates the order in which their *on entry* and *on exit* actions were processed.
..
As transitions are atomically processed, this means that they could exist a state in ``entered_states`` that is
entered before some state in ``exited_states`` is exited.
The exact order in which states are exited and entered is indirectly available through the ``steps`` attribute that
is a list of all the :py:class:`~sismic.interpreter.MicroStep`` that were executed. Each of them contains the states
that were exited and entered during its execution.


.. autoclass:: sismic.interpreter.MacroStep
    :members:

A micro step is the smallest, atomic step that a statechart can execute.
A :py:class:`~sismic.interpreter.MacroStep` instance thus can be viewed (and is!) an aggregate of
:py:class:`~sismic.interpreter.MicroStep` instances.

.. autoclass:: sismic.interpreter.MicroStep
    :members:

This way, a complete run of a state machine can be summarized as an ordered list of
:py:class:`~sismic.interpreter.MacroStep` instances,
and details of such a run can be obtained using the :py:class:`~sismic.interpreter.MicroStep` list of a
:py:class:`~sismic.interpreter.MacroStep`.



.. _other_semantics:

Implementing other semantics
----------------------------

A :py:class:`~sismic.interpreter.Interpreter` makes use of several protected methods for its initialization or to compute
which transition should be processed next, which are the next steps, etc.

These methods can be easily overridden or combined to define other semantics.

.. automethod:: sismic.interpreter.Interpreter._select_eventless_transitions
.. automethod:: sismic.interpreter.Interpreter._select_transitions
.. automethod:: sismic.interpreter.Interpreter._sort_transitions
.. automethod:: sismic.interpreter.Interpreter._compute_transitions_steps
.. automethod:: sismic.interpreter.Interpreter._execute_step
.. automethod:: sismic.interpreter.Interpreter._compute_stabilization_step


These methods are called directly (or not) by :py:class:`~sismic.interpreter.Interpreter.execute_once`.
Consider looking at the source of :py:class:`~sismic.interpreter.Interpreter.execute_once` to understand
how these methods are related and organized.



Example: Outer-first/source-state semantic
******************************************

For example, if you are interested in a outer-first/source-state semantic (instead of the
inner-first/source-state one that is currently provided), you can subclass :py:class:`~sismic.interpreter.Interpreter`
and override :py:class:`~sismic.interpreter.Interpreted._select_eventless_transitions` and
:py:class:`~sismic.interpreter.Interpreted._select_transitions`.
Actually, as the former relies on the second, your changes will only concern the traversal order in
:py:class:`~sismic.interpreter.Interpreted._select_transitions` method.


Example: Internal events have no priority
*****************************************

As another example, if you are interested in considering that internal event should not have
priority over external event, it is sufficient to override the :py:meth:`~sismic.interpreter.Interpreter.send` method:

.. code:: python

     def send(self, event:model.Event, internal=False):
        self.append(event)  # No distinction between internal and external events
        return self


Example: Custom way to deal with non-determinism
************************************************

If you find that the way we deal with non-determinism is too far from other semantics like SCXML or Rhapsody,
(remember :ref:`semantic`), you can implement your own approach to deal with non-determinism.
The method :py:meth:`~sismic.interpreter.Interpreter._sort_transitions` is where the whole job is done:

1. It looks for non-determinism in (non-parallel) transitions,
2. It looks for conflicting transitions in parallel transitions,
3. It sorts the kept transitions based on our semantic.

According to your needs, adapt the content of this method.

