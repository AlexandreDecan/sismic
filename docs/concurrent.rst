.. _communication:

Running multiple statecharts
============================

It is not unusual to have to deal with multiple distinct components in which the behavior of a component is driven
by things that happen in the other components.
One can model such a situation using a single statechart with parallel states, or by plugging several statecharts
into one main statechart (see :py:meth:`sismic.model.Statechart.copy_from_statechart`).
The communication and synchronization between the components can be done either by using ``active(state_name)`` in
guards, or by sending internal events that address other components.

However, we believe that this approach is not very convenient:

    - all the components must be defined in a single statechart;
    - state name collision could occur;
    - components must share a single execution context;
    - component composition is not easy to achieve
    - ...

Sismic allows to define multiple components in multiple statecharts, and brings a way for those statecharts to
communicate and synchronize via events.


Communicating statecharts
-------------------------

Every instance of :py:class:`~sismic.interpreter.Interpreter` exposes a :py:meth:`~sismic.interpreter.Interpreter.bind`
method which allows to bind statecharts.

.. automethod:: sismic.interpreter.Interpreter.bind
    :noindex:

When an interpreter ``interpreter_1`` is bound to an interpreter ``interpreter_2`` using
``interpreter_1.bind(interpreter_2)``, the **internal** events that are sent by ``interpreter_1`` are automatically
propagated as **external** events to ``interpreter_2``.
The binding is not restricted to only two statecharts.
For example, assume we have three instances of :py:class:`~sismic.interpreter.Interpreter`:

.. testsetup:: bind

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    interpreter_1 = Interpreter(import_from_yaml(filepath='examples/elevator/elevator.yaml'))
    interpreter_2 = Interpreter(import_from_yaml(filepath='examples/elevator/elevator_buttons.yaml'))
    interpreter_3 = Interpreter(import_from_yaml(filepath='examples/elevator/elevator_buttons.yaml'))

.. testcode:: bind

    assert isinstance(interpreter_1, Interpreter)
    assert isinstance(interpreter_2, Interpreter)
    assert isinstance(interpreter_3, Interpreter)

We define a bidirectional communication between the two first interpreters:

.. testcode:: bind

    interpreter_1.bind(interpreter_2)
    interpreter_2.bind(interpreter_1)

We also bind the third interpreters with the two first ones.

.. testcode:: bind

    interpreter_3.bind(interpreter_1)
    interpreter_3.bind(interpreter_2)

When an internal event is sent by an interpreter, the bound interpreters also receive this event as an external
event.
In the last example, when an internal event is sent by ``interpreter_3``, then a corresponding external event
is sent both to ``interpreter_1`` and ``interpreter_2``.

.. note:: Practically, unless you subclassed :py:class:`~sismic.interpreter.Interpreter`, the only difference between
    internal and external events is the priority order in which they are processed by the interpreter.


.. testcode:: bind

    from sismic.interpreter import InternalEvent

    # Manually create and raise an internal event
    interpreter_3._raise_event(InternalEvent('test'))

    print('Events for interpreter_1:', interpreter_1._select_event(consume=False))
    print('Events for interpreter_2:', interpreter_2._select_event(consume=False))
    print('Events for interpreter_3:', interpreter_3._select_event(consume=False))

.. testoutput:: bind

    Events for interpreter_1: Event('test')
    Events for interpreter_2: Event('test')
    Events for interpreter_3: InternalEvent('test')

.. note::

    The :py:meth:`~sismic.interpreter.Interpreter.bind` method is a high-level interface for 
    :py:meth:`~sismic.interpreter.Interpreter.attach`. Internally, the former wraps given
    interpreter or callable with an appropriate listener before calling 
    :py:meth:`~sismic.interpreter.Interpreter.attach`. You can unbound a previously
    bound interpreter with :py:meth:`~sismic.interpreter.Interpreter.detach` method.
    This method accepts a previously attached listener, so you'll need to keep track of the listener returned
    by the initial call to :py:meth:`~sismic.interpreter.Interpreter.bind`.
    

Example of communicating statecharts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider our running example, the elevator statechart.
This statechart expects to receive *floorSelected* events (with a *floor* parameter representing the selected floor).
The statechart operates autonomously, provided that we send such events.

Let us define a new statechart that models a panel of buttons for our elevator.
For example, we consider that our panel has 4 buttons numbered 0 to 3.

.. literalinclude:: /examples/elevator/elevator_buttons.yaml
   :language: yaml

As you can see in the YAML version of this statechart, the panel expects an event for each button:
*button_0_pushed*, *button_1_pushed*, *button_2_pushed* and *button_3_pushed*.
Each of those event causes the execution of a transition which, in turn, creates and sends a *floorSelected* event.
The *floor* parameter of this event corresponds to the button number.

We bind our panel with our elevator, such that the panel can control the elevator:

.. testcode:: buttons

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    elevator = Interpreter(import_from_yaml(filepath='examples/elevator/elevator.yaml'))
    buttons = Interpreter(import_from_yaml(filepath='examples/elevator/elevator_buttons.yaml'))

    # Elevator will receive events from buttons
    buttons.bind(elevator)

Events that are sent **to** ``buttons`` are not propagated, but events that are sent **by** ``buttons``
are automatically propagated to ``elevator``:

.. testcode:: buttons

    print('Awaiting event in buttons:', buttons._select_event())  # None
    buttons.queue('button_2_pushed')

    print('Awaiting event in buttons:', buttons._select_event())  # External event
    print('Awaiting event in elevator:', elevator._select_event())  # None

    buttons.execute(max_steps=2)  # (1) initialize buttons, and (2) consume button_2_pushed
    print('Awaiting event in buttons:', buttons._select_event())  # Internal event 
    print('Awaiting event in elevator:', elevator._select_event())  # External event

.. testoutput:: buttons

    Awaiting event in buttons: None
    Awaiting event in buttons: Event('button_2_pushed')
    Awaiting event in elevator: None
    Awaiting event in buttons: InternalEvent('floorSelected', floor=2)
    Awaiting event in elevator: Event('floorSelected', floor=2)

The execution of bound statecharts does not differ from the execution of unbound statecharts:

.. testcode:: buttons

    elevator.execute()
    print('Current floor:', elevator.context.get('current'))

.. testoutput:: buttons

    Current floor: 2


Synchronizing the clock 
-----------------------

Each interpreter in Sismic has its own clock to deal with time (see :ref:`dealing_time`). 
When creating an interpreter, it is possible to specify which clock should be used to compute the 
``time`` attribute of the interpreter. 
When multiple statecharts have to be run concurrently, it is often convenient to have their 
time synchronized. This can be achieved (to some extent) by providing a shared instance
of a clock to their interpreter.

.. testcode:: time_sync

    from sismic.io import import_from_yaml

    elevator_sc = import_from_yaml(filepath='examples/elevator/elevator.yaml')
    buttons_sc = import_from_yaml(filepath='examples/elevator/elevator_buttons.yaml')


    from sismic.clock import SimulatedClock
    from sismic.interpreter import Interpreter

    # Create the clock and share its instance with all interpreters
    clock = SimulatedClock()
    elevator = Interpreter(elevator_sc, clock=clock)
    buttons = Interpreter(buttons_sc, clock=clock)

.. note::

    As :py:class:`~sismic.clock.SimulatedClock` is the default clock used in Sismic, we could have written the three
    last lines of this example as follow:

    .. code-block:: python

        elevator = Interpreter(elevator_sc)
        buttons = Interpreter(buttons_sc, clock=elevator.clock)

We can now execute the statecharts and check their time value.

.. testcode:: time_sync

    clock.start()
     
    elevator_step = elevator.execute_once()
    buttons_step = buttons.execute_once()

    clock.stop()

As a single instance of a clock is used by both interpreter, the values exposed by their clocks 
are obviously the same: 

.. testcode:: time_sync

    assert elevator.clock.time == buttons.clock.time

However, even if the clock is the same for all interpreters, this does not always mean that the calls
to :py:meth:`~sismic.interpreter.Interpreter.execute_once` are all performed at the same time. 
Depending on the time required to process the first ``execute_once``, the second one will be called
with a delay of (at least) a few milliseconds.

We can check this by looking at the :py:attr:`~sismic.model.MacroStep.time` attribute of the returned
steps, or by looking at the :py:attr:`~sismic.interpreter.Interpreter.time` attribute of the interpreter
that corresponds to the time of the last executed step:

.. testcode:: time_sync

    assert elevator_step.time != buttons_step.time
    assert elevator.time != buttons.time

To avoid these slight variations between different calls to :py:meth:`~sismic.interpreter.Interpreter.execute_once`, 
Sismic offers a :py:class:`~sismic.clock.SynchronizedClock` 
whose value is based on another interpreter's time.

.. testcode:: time_sync

    from sismic.clock import SynchronizedClock

    elevator = Interpreter(elevator_sc)
    buttons = Interpreter(buttons_sc, clock=SynchronizedClock(elevator))

With the help of this :py:class:`~sismic.clock.SynchronizedClock`, it is possible to perfectly "align" the time of several
interpreters. Obviously, in this context, we first need to execute the interpreter that "drives" the time:

.. testcode:: time_sync

    elevator.clock.start()
     
    elevator_step = elevator.execute_once()
    buttons_step = buttons.execute_once()

    elevator.clock.stop()
    
Now we can check that the time of the last executed steps are the same:

.. testcode:: time_sync

    assert elevator_step.time == buttons_step.time
    assert elevator.time == buttons.time
    
.. note::

    While the two interpreters were virtually executed at the same time value, 
    their clocks still have different values as a :py:class:`~sismic.clock.SynchronizedClock` is based 
    on the ``time`` attribute of given interpreter and not on its internal clock.

    .. testcode:: time_sync

        assert elevator.clock.time != buttons.clock.time
    
.. warning:: 

    Because the time of an interpreter is set by the clock each time :py:meth:`~sismic.interpreter.Interpreter.execute_once` is called, you should avoid using :py:meth:`~sismic.interpreter.Interpreter.execute` (that repeatedly calls :py:meth:`~sismic.interpreter.Interpreter.execute_once`) if you want a perfect synchronization between two or more interpreters. 
    In our example, a call to :py:meth:`~sismic.interpreter.Interpreter.execute` instead of :py:meth:`~sismic.interpreter.Interpreter.execute_once` for the first interpreter implies that the time value of the second interpreter will equal the time value of the first interpreter after having executed all its macro steps. 
    In other words, the execution of the second interpreter will be synchronized with the execution of the last macro step of the first interpreter in that case. 
