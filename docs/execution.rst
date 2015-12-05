Execute statecharts
===================


The module `simulator` contains a `Simulator` class that interprets a statechart following SCXML semantic.
A `Simulator` instance is constructed upon a `StateChart` instance and an optional `Evaluator`.
If no `Evaluator` instance is specified, a `DummyEvaluator` instance will be used by default.

The main methods of a simulator instance are:

 - `send(event)` takes an `Event` instance that will be added to a FIFO queue of external events.
 - `execute_once()` processes a transition based on the oldest queued event (or no event if an eventless transition can be processed), and stabilizes
  the simulator in a stable situation (ie. processes initial states, history states, etc.). This method returns an instance of `MacroStep` (see
  below) or `None` if (1) no eventless transition can be processed, (2) there is no event in the event queue.
  This method returns an instance of `MacroStep` or `None` if nothing was done.
 - `execute()` that repeatedly calls `execute_once()` and return a list returned values.
 - Property `configuration`: contains an (unordered) list of active states.
 - Property `running`: return `True` if and only if the statechart is running AND is not in a final configuration.

Example:

.. code:: python

    simulator = Simulator(my_statechart)
    # We are now in a stable initial state
    simulator.send(Event('click'))  # Send event to the simulator
    simulator.execute_once()  # Will process the event if no eventless transitions are found at first


For convenience, `send` returns `self` and thus can be chained:

.. code:: python

    simulator.send(Event('click')).send(Event('click')).execute_once()


Notice that `execute_once()` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call `execute_once()` until it returns a `None` value.
For instance:

.. code:: python

    while simulator.execute_once():
      pass


As a shortcut, a `Simulator` instance provides an iterator:

.. code:: python

    for step in simulator:
      assert isinstance(step, MacroStep)
    assert simulator.execute_once() == None


And as a better shortcut, the `execute()` method will return a list of `MacroStep` instances
obtained by repeatedly calling `execute_once()`:

.. code:: python

    steps = simulator.execute()
    for step in steps:
      assert isinstance(step, MacroStep)


The simulator is fully observable: its `execute_once()` method returns an instance of `MacroStep`.
A macro step corresponds to the process of either an eventless transition, or an evented transition,
or no transition (but consume the event), including the stabilization steps (ie. the steps that are needed
to enter nested states, or to switch into the configuration of an history state).

A `MacroStep` exposes an `Event` (`None` in case of eventless transition), a `Transition` (`None` if the
event was consumed without triggering a transition) and two sequences of state names: `entered_states` and
`exited_states`. States order in those list indicates the order in which their `on entry` and `on exit` actions
were processed.

The main step and the stabilization steps of a macro step are exposed through `main_step` and `micro_steps`.
The first is a `MicroStep` instance, and the second is an ordered list of `MicroStep` instances.
A micro step is the smallest, atomic step that a statechart can execute.
A `MacroStep` instance can be viewed (and is!) an aggregate of `MicroStep` instances.

This way, a complete run of a state machine can be summarized as an ordered list of `MacroStep` instances,
and details of such a run can be obtained using the `MicroStep`'s of a `MacroStep`.
