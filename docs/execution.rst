Executing statecharts
=====================

A statechart can be executed from the command-line interface or, for a finer-grained
execution, programmatically.


The *simulator* module
----------------------

The module :py:mod:`~pyss.simulator` contains a :py:class:`~pyss.simulator.Simulator` class that interprets a statechart following SCXML semantic.
In particular, eventless transitions are processed before evented transitions, internal events are consumed
before external events, and the simulation follows a inner-first/source-state semantic.

A :py:class:`~pyss.simulator.Simulator` instance is constructed upon a :py:class:`~pyss.model.StateChart` instance and
an optional callable that returns an :py:class:`~pyss.evaluator.Evaluator` (see :ref:`code_evaluation`).
If no evaluator is specified, :py:class:`~pyss.evaluator.PythonEvaluator` class will be set.

The main methods of a simulator instance are:

.. autoclass:: pyss.simulator.Simulator
    :members: configuration, running, send, execute_once, execute


Macro and micro steps
*********************

The simulator is fully observable: its :py:meth:`~pyss.simulator.Simulator.execute_once` (resp. :py:meth:`~pyss.simulator.Simulator.execute`) method returns
an instance of (resp. a list of) :py:class:`~pyss.simulator.MacroStep`.
A macro step corresponds to the process of either an eventless transition, or an evented transition,
or no transition (but consume the event), including the stabilization steps (ie. the steps that are needed
to enter nested states, or to switch into the configuration of an history state).

A :py:class:`~pyss.simulator.MacroStep` exposes an :py:class:`~pyss.model.Event`
(``None`` in case of eventless transition), a :py:class:`~pyss.model.Transition` (``None`` if the
event was consumed without triggering a transition) and two sequences of state names: ``entered_states`` and
``exited_states``. States order in those list indicates the order in which their ``on entry`` and ``on exit`` actions
were processed.

.. autoclass:: pyss.simulator.MacroStep
    :members:

The main step and the stabilization steps of a macro step are exposed through ``main_step`` and ``micro_steps``.
The first is a :py:class:`~pyss.simulator.MicroStep` instance, and the second is an ordered list of
:py:class:`~pyss.simulator.MicroStep` instances.
A micro step is the smallest, atomic step that a statechart can execute.
A :py:class:`~pyss.simulator.MacroStep` instance thus can be viewed (and is!) an aggregate of
:py:class:`~pyss.simulator.MicroStep` instances.

.. autoclass:: pyss.simulator.MicroStep
    :members:

This way, a complete run of a state machine can be summarized as an ordered list of
:py:class:`~pyss.simulator.MacroStep` instances,
and details of such a run can be obtained using the :py:class:`~pyss.simulator.MicroStep`'s of a
:py:class:`~pyss.simulator.MacroStep`.


Example
*******

Consider the following example.

.. code:: python

    simulator = Simulator(my_statechart)
    # We are now in a stable initial state
    simulator.send(Event('click'))  # Send event to the simulator
    simulator.execute_once()  # Will process the event if no eventless transitions are found at first


For convenience, :py:meth:`~pyss.simulator.Simulator.send` returns ``self`` and thus can be chained:

.. code:: python

    simulator.send(Event('click')).send(Event('click')).execute_once()


Notice that :py:meth:`~pyss.simulator.Simulator.execute_once` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call :py:meth:`~pyss.simulator.Simulator.execute_once` until it returns a ``None`` value.
For instance:

.. code:: python

    while simulator.execute_once():
      pass


As a shortcut, the :py:meth:`~pyss.simulator.Simulator.execute` method will return a list of :py:class:`~pyss.simulator.Simulator.MacroStep` instances
obtained by repeatedly calling :py:meth:`~pyss.simulator.Simulator.execute_once`:

.. code:: python

    steps = simulator.execute()
    for step in steps:
      assert isinstance(step, MacroStep)

As a call to :py:meth:`~pyss.simulator.Simulator.execute` could lead to an infinite execution (see for example */examples/simple/infinite.yaml*),
an additional parameter ``max_steps: int`` can be specified to limit the number of steps that are computed
and executed by the method.

.. code:: python

    assert len(simulator.execute(max_steps=10)) <= 10


Advanced uses
-------------

A :py:class:`~pyss.simulator.Simulator` instance provides several other methods than can give useful information about
the execution of a statechart.


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

As another example, if you are interested in considering that internal event should not have
priority over external event, it is sufficient to override the :py:meth:`~pyss.simulator.Simulator.send` method:

.. code:: python

     def send(self, event:model.Event, internal=False):
        self.append(event)  # No distinction between internal and external events
        return self