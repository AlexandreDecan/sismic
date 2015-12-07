Executing statecharts
=====================

A statechart can be executed from the command-line interface or, for a finer-grained
execution, programmatically.


From the command line
---------------------

In a nutshell::

    (shell) pyss execute -vvv  examples/concrete/history.yaml --events next pause


Please consult :ref:`cli_execute` for more information.


Module `simulator`
------------------

The module ``simulator`` contains a ``Simulator`` class that interprets a statechart following SCXML semantic.
In particular, eventless transitions are processed before evented transitions, internal events are consumed
before external events, and the simulation follows a inner-first/source-state semantic.

A ``Simulator`` instance is constructed upon a ``StateChart`` instance and an optional ``Evaluator`` (see :ref:`code_evaluation`).
If no ``Evaluator`` instance is specified, a ``DummyEvaluator`` instance will be used by default.

The main methods of a simulator instance are:

.. automethod:: pyss.simulator.Simulator.configuration

.. automethod:: pyss.simulator.Simulator.running

.. automethod:: pyss.simulator.Simulator.send

.. automethod:: pyss.simulator.Simulator.execute_once

.. automethod:: pyss.simulator.Simulator.execute


Consider the following example.

.. code:: python

    simulator = Simulator(my_statechart)
    # We are now in a stable initial state
    simulator.send(Event('click'))  # Send event to the simulator
    simulator.execute_once()  # Will process the event if no eventless transitions are found at first


For convenience, ``send`` returns ``self`` and thus can be chained:

.. code:: python

    simulator.send(Event('click')).send(Event('click')).execute_once()


Notice that ``execute_once()`` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call ``execute_once()`` until it returns a ``None`` value.
For instance:

.. code:: python

    while simulator.execute_once():
      pass


As a shortcut, a ``Simulator`` instance provides an iterator:

.. code:: python

    for step in simulator:
      assert isinstance(step, MacroStep)
    assert simulator.execute_once() == None


And as a better shortcut, the ``execute()`` method will return a list of ``MacroStep`` instances
obtained by repeatedly calling ``execute_once()``:

.. code:: python

    steps = simulator.execute()
    for step in steps:
      assert isinstance(step, MacroStep)


The simulator is fully observable: its ``execute_once()`` method returns an instance of ``MacroStep``.
A macro step corresponds to the process of either an eventless transition, or an evented transition,
or no transition (but consume the event), including the stabilization steps (ie. the steps that are needed
to enter nested states, or to switch into the configuration of an history state).


Macro and micro steps
---------------------

A ``MacroStep`` exposes an ``Event`` (``None`` in case of eventless transition), a ``Transition`` (``None`` if the
event was consumed without triggering a transition) and two sequences of state names: ``entered_states`` and
``exited_states``. States order in those list indicates the order in which their ``on entry`` and ``on exit`` actions
were processed.

The main step and the stabilization steps of a macro step are exposed through ``main_step`` and ``micro_steps``.
The first is a ``MicroStep`` instance, and the second is an ordered list of ``MicroStep`` instances.
A micro step is the smallest, atomic step that a statechart can execute.
A ``MacroStep`` instance can be viewed (and is!) an aggregate of ``MicroStep`` instances.

This way, a complete run of a state machine can be summarized as an ordered list of ``MacroStep`` instances,
and details of such a run can be obtained using the ``MicroStep``'s of a ``MacroStep``.


Advanced usages
---------------

A ``Simulator`` instance provides several other methods than can give useful information about
the execution of a statechart.

``Simulator`` private methods
*****************************

.. automethod:: pyss.simulator.Simulator._start
.. automethod:: pyss.simulator.Simulator._execute_step
.. automethod:: pyss.simulator.Simulator._actionable_transitions
.. automethod:: pyss.simulator.Simulator._transition_step
.. automethod:: pyss.simulator.Simulator._stabilize_step
.. automethod:: pyss.simulator.Simulator._stabilize

Implemeting other semantics
***************************

It is also quite easy to extend (or adapt) parts of a simulator to implement other semantics.
For example, if you are interested in a outer-first/source-state semantic (instead of the
inner-first/source-state one that is currently provided), you can subclass ``Simulator`` as follows:

.. code:: python

    class OuterFirstSimulator(Simulator):
        def __init__(self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)

        def _actionable_transitions(*args, **kwargs):
            transitions = super()._actionable_transitions(*args, **kwargs)
            transitions.reverse()
            return transitions


