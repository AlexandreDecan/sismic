.. _communication:

Communication between statecharts
=================================

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


Binding statecharts
-------------------

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

    interpreter_1 = Interpreter(import_from_yaml(open('examples/elevator/elevator.yaml')))
    interpreter_2 = Interpreter(import_from_yaml(open('examples/elevator/elevator_buttons.yaml')))
    interpreter_3 = Interpreter(import_from_yaml(open('examples/elevator/elevator_buttons.yaml')))

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
    internal and external events are the priority order in which they are processed by the interpreter.


.. testcode:: bind

    from sismic.interpreter import InternalEvent, Event

    # Manually create and raise an internal event
    interpreter_3._raise_event(InternalEvent('test'))

    print('Events for interpreter_1:', interpreter_1._external_events.pop())
    print('Events for interpreter_2:', interpreter_2._external_events.pop())
    print('Events for interpreter_3:', interpreter_3._internal_events.pop())

.. testoutput:: bind

    Events for interpreter_1: Event('test')
    Events for interpreter_2: Event('test')
    Events for interpreter_3: InternalEvent('test')


Example of communicating statecharts
------------------------------------

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
    from sismic.interpreter import Interpreter, Event, InternalEvent

    elevator = Interpreter(import_from_yaml(open('examples/elevator/elevator.yaml')))
    buttons = Interpreter(import_from_yaml(open('examples/elevator/elevator_buttons.yaml')))

    # Elevator will receive events from buttons
    buttons.bind(elevator)

Events that are sent **to** ``buttons`` are not propagated, but events that are sent **by** ``buttons``
are automatically propagated to ``elevator``:

.. testcode:: buttons

    print('Awaiting events in buttons:', list(buttons._external_events))  # Empty
    buttons.queue(Event('button_2_pushed'))

    print('Awaiting events in buttons:', list(buttons._external_events))  # External event

    buttons.execute(max_steps=2)  # (1) initialize buttons, and (2) consume button_2_pushed
    print('Awaiting events in buttons:', list(buttons._internal_events))
    print('Awaiting events in elevator:', list(elevator._external_events))

.. testoutput:: buttons

    Awaiting events in buttons: []
    Awaiting events in buttons: [Event('button_2_pushed')]
    Awaiting events in buttons: [InternalEvent('floorSelected', floor=2)]
    Awaiting events in elevator: [Event('floorSelected', floor=2)]

The execution of bound statecharts does not differ from the execution of unbound statecharts:

.. testcode:: buttons

    elevator.execute()
    print('Current floor:', elevator.context.get('current'))

.. testoutput:: buttons

    Current floor: 2