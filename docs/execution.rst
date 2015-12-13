Executing statecharts
=====================

Statechart semantic
-------------------

The module :py:mod:`~sismic.simulator` contains a :py:class:`~sismic.simulator.Simulator` class that interprets a statechart
mainly following `SCXML <http://www.w3.org/TR/scxml/>`__ semantic.
In particular, eventless transitions are processed before evented transitions, internal events are consumed
before external events, and the simulation follows a inner-first/source-state and run-to-completion semantic.

The main difference between SCXML and Sismic's default simulator comes when considering parallel states.
The UML specification defines that several transitions in parallel regions can be triggered by a same event:

    "Due to the presence of orthogonal Regions, it is possible that multiple Transitions (in different Regions) can be
    triggered by the same Event occurrence. The **order in which these Transitions are executed is left undefined**."
    --- `UML 2.5 Specification <http://www.omg.org/cgi-bin/doc?formal/15-03-01.pdf>`__

This sometimes implies a non-deterministic choice in the order in which transitions must be processed, and
in the order in which states must be exited and/or entered. This problem is addressed in SCXML specification:

    "enabledTransitions will contain multiple transitions only if a parallel state is active.
    In that case, we may have one transition selected for each of its children. [...]
    If multiple states are active (i.e., we are in a parallel region), then there may be multiple transitions,
    one per active atomic state (though some states may not select a transition.) In this case, the
    transitions are taken **in the document order of the atomic states** that selected them."
    --- `SCXML Specification <http://www.w3.org/TR/scxml/#AlgorithmforSCXMLInterpretation>`__

However, from our point of view, this solution is not satisfactory.
The execution should not depend on the order in which items are defined in some document.
Sismiccircumvents this by raising a ``Warning`` and stopping the execution if
multiple transitions can be triggered at the same time. To some extent, this is the same approach
than in Rhapsody:

    "Rhapsody detects such cases of nondeterminism during code generation
    and does not allow them. The motivation for this is that the generated code
    is intended to serve as a final implementation and for most embedded software
    systems such nondeterminism is not acceptable."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

However, their approach only concerns conflicting transitions that are not fired in an orthogonal state.
In orthogonal states, the order in which transitions are triggered in still non-determinist:

    "The order of firing transitions of orthogonal components is not defined, and
    depends on an arbitrary traversal in the implementation. Also, the actions on
    the transitions of the orthogonal components are interleaved in an arbitrary
    way."
    --- `The Rhapsody Semantics of Statecharts <http://research.microsoft.com/pubs/148785/charts04.pdf>`__

.. _parallel_semantic:

To avoid such situations and to avoid defining arbitrary order on the execution, we decided to
allow event to trigger **at most** one transition at a time. As a consequence, this means that parallel
states execution should be "event-independant", ie. a same event cannot trigger two (or more) transitions
in distinct parallel state's substates.

There exist several workarounds to this.
For instance, one can define a shared object in the context of an evaluator that
allows parallel states to communicate and to synchronize. Or, at statechart level, one can define an additional
parallel state that *resends* events for each other parallel state (ie. if the received event is *e1*, it raises
an internal event *e1_i* for each other parallel region *i*).
Finally, the restriction we implemented can also be overridden by subclassing the simulator, as our implementation
already considers that multiple transitions could be fired at once (see :ref:`other_semantics`).

While it seems radical, our approach respects the UML specification which requires that "*the designer
does not rely on any particular order for event instances to be dispatched to the relevant orthogonal regions*".


Using *Simulator*
-----------------

A :py:class:`~sismic.simulator.Simulator` instance is constructed upon a :py:class:`~sismic.model.StateChart` instance and
an optional callable that returns an :py:class:`~sismic.evaluator.Evaluator` (see :ref:`code_evaluation`).
If no evaluator is specified, :py:class:`~sismic.evaluator.PythonEvaluator` class will be used.

Consider the following example.

.. code:: python

    from sismic.simulator import Simulator
    from sismic.model import Event

    simulator = Simulator(my_statechart)
    # We are now in a stable initial state
    simulator.send(Event('click'))  # Send event to the simulator
    simulator.execute_once()  # Will process the event if no eventless transitions are found at first


For convenience, :py:meth:`~sismic.simulator.Simulator.send` returns ``self`` and thus can be chained:

.. code:: python

    simulator.send(Event('click')).send(Event('click')).execute_once()

Notice that :py:meth:`~sismic.simulator.Simulator.execute_once` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call :py:meth:`~sismic.simulator.Simulator.execute_once` until it returns a ``None`` value.
For instance:

.. code:: python

    while simulator.execute_once():
      pass


As a shortcut, the :py:meth:`~sismic.simulator.Simulator.execute` method will return a list of :py:class:`~sismic.simulator.MacroStep` instances
obtained by repeatedly calling :py:meth:`~sismic.simulator.Simulator.execute_once`:

.. code:: python

    from sismic.simulator import MacroStep

    steps = simulator.execute()
    for step in steps:
      assert isinstance(step, MacroStep)

Notice that a call to :py:meth:`~sismic.simulator.Simulator.execute` first computes the list and **then** returns
it, meaning that all the steps are already processed when the call returns.

As a call to :py:meth:`~sismic.simulator.Simulator.execute` could lead to an infinite execution
(see for example `simple/infinite.yaml <https://github.com/AlexandreDecan/sismic/blob/master/examples/simple/infinite.yaml>`__),
an additional parameter ``max_steps`` can be specified to limit the number of steps that are computed
and executed by the method.

.. code:: python

    assert len(simulator.execute(max_steps=10)) <= 10

At any time, you can reset the simulator by calling :py:meth:`~sismic.simulator.Simulator.reset`.

For convenience, a :py:class:`~sismic.model.StateChart` has an :py:meth:`~sismic.model.StateChart.events` method
that returns the list of all possible events that can be interpreted by this statechart (other events will
be consumed and ignored).

This method also accepts a state name or a list of state names to restrict the list of returned events,
and is thus commonly used to get a list of the "interesting" events:

.. code:: python

    print(my_statechart.events(simulator.configuration))



The main methods and attributes of a simulator instance are:

.. autoclass:: sismic.simulator.Simulator
    :members: send, execute_once, execute, configuration, running, reset



Macro and micro steps
---------------------

The simulator is fully observable: its :py:meth:`~sismic.simulator.Simulator.execute_once`
(resp. :py:meth:`~sismic.simulator.Simulator.execute`) method returns
an instance of (resp. a list of) :py:class:`~sismic.simulator.MacroStep`.
A macro step corresponds to the process of consuming an event, regardless of the number and the type (eventless or not)
of transitions triggered. A macro step also includes every consecutive stabilization step
(ie. the steps that are needed to enter nested states, or to switch into the configuration of an history state).

A :py:class:`~sismic.simulator.MacroStep` exposes the consumed ``event`` (:py:class:`~sismic.model.Event`)
if any, a (possibly empty) list of ``transitions`` (:py:class:`~sismic.model.Transition` and two sequences of state
names: ``entered_states`` and ``exited_states``.
States order in those list indicates the order in which their *on entry* and *on exit* actions were processed.

.. autoclass:: sismic.simulator.MacroStep
    :members:

The main step and the stabilization steps of a macro step are exposed through ``main_step`` and ``micro_steps``.
The first is a :py:class:`~sismic.simulator.MicroStep` instance, and the second is an ordered list of
:py:class:`~sismic.simulator.MicroStep` instances.
A micro step is the smallest, atomic step that a statechart can execute.
A :py:class:`~sismic.simulator.MacroStep` instance thus can be viewed (and is!) an aggregate of
:py:class:`~sismic.simulator.MicroStep` instances.

.. autoclass:: sismic.simulator.MicroStep
    :members:

This way, a complete run of a state machine can be summarized as an ordered list of
:py:class:`~sismic.simulator.MacroStep` instances,
and details of such a run can be obtained using the :py:class:`~sismic.simulator.MicroStep` list of a
:py:class:`~sismic.simulator.MacroStep`.



Advanced uses
-------------

A :py:class:`~pyss.simulator.Simulator` makes use of several protected methods for its initialization or to compute
which transition should be processed next, which are the next steps, etc.

These methods can be easily overriden or combined to define other semantics.


Additional (protected) methods
******************************

.. automethod:: pyss.simulator.Simulator._start
.. automethod:: pyss.simulator.Simulator._execute_step
.. automethod:: pyss.simulator.Simulator._actionable_transitions
.. automethod:: pyss.simulator.Simulator._transition_step
.. automethod:: pyss.simulator.Simulator._stabilize_step
.. automethod:: pyss.simulator.Simulator._stabilize


.. _other_semantics:

Implementing other semantics
****************************

It is also quite easy to extend (or adapt) parts of a simulator to implement other semantics.

Outer-first/source-state semantic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For example, if you are interested in a outer-first/source-state semantic (instead of the
inner-first/source-state one that is currently provided), you can subclass :py:class:`~pyss.simulator.Simulator` as follows:

.. code:: python

    class OuterFirstSimulator(Simulator):
        def __init__(self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)

        def _actionable_transitions(*args, **kwargs):
            transitions = super()._actionable_transitions(*args, **kwargs)
            transitions.reverse()
            return transitions

Internal events have no priority
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As another example, if you are interested in considering that internal event should not have
priority over external event, it is sufficient to override the :py:meth:`~pyss.simulator.Simulator.send` method:

.. code:: python

     def send(self, event:model.Event, internal=False):
        self.append(event)  # No distinction between internal and external events
        return self


Custom way to deal with non-determinism
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you find that the way we deal with non-determinism is too radical or not enough permissive
(remember :ref:`this <parallel_semantic>`), you can implement your own approach to deal with non-determinism.
The method :py:meth:`~pyss.simulator.Simulator._actionable_transitions` already returns all the transitions that
can be triggered by an event. This method is actually called by :py:meth:`~pyss.simulator.Simulator._transition_step`
which currently checks that at most one transition can be triggered.

You can override :py:meth:`~pyss.simulator.Simulator._transition_step` and define how situations in which several
transitions are triggered are dealt. The remaining of the implementation is already conceived in a way to deal with
multiple transitions fired at once.
In particular, your implementation should return an appropriate ``MicroStep`` instances where selected transitions,
entered states and exited states are ordered according to your arbitrary choice to deal with non-determinism.

