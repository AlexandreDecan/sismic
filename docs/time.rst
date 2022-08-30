.. _dealing_time:

Dealing with time
#################

It is quite usual in statecharts to find notations such as "*after 30 seconds*", often expressed as specific events
on a transition. Sismic does not support the use of these *special events*, and proposes instead to deal with time
by making use of some specifics provided by its interpreter and the default Python code evaluator.

Every interpreter has an internal clock that is exposed through its :py:attr:`~sismic.interpreter.Interpreter.clock` 
attribute and that can be used to manipulate the time of the simulation. 

The built-in Python code evaluator allows one to make use of ``after(...)``, ``idle(...)`` in guards or contracts.
These two Boolean predicates can be used to automatically compare the current time (as exposed by interpreter clock)
with a predefined value that depends on the state in which the predicate is used. For instance, ``after(x)`` will
evaluate to ``True`` if the current time of the interpreter is at least ``x`` seconds greater than the time when the
state using this predicate (or source state in the case of a transition) was entered.
Similarly, ``idle(x)`` evaluates to ``True`` if no transition was triggered during the last ``x`` seconds.

These two predicates rely on the :py:attr:`~sismic.interpreter.Interpreter.time` attribute of an interpreter.
The value of that attribute is computed at the beginning of each executed step based on a clock. 

.. note:: 

    The interpreter's time is set by the clock each time :py:meth:`~sismic.interpreter.Interpreter.execute_once` is called. 
    Consequently, a call to :py:meth:`~sismic.interpreter.Interpreter.execute` (that repeatedly calls :py:meth:`~sismic.interpreter.Interpreter.execute_once`) could lead to macro steps with different time values, depending on the duration required to process the underlying calls to :py:meth:`~sismic.interpreter.Interpreter.execute_once`.


Interpreter clock
=================

Sismic provides three implementations of :py:class:`~sismic.clock.Clock` in its :py:mod:`sismic.clock` module.
The first one is a :py:class:`~sismic.clock.SimulatedClock` that can be manually or automatically incremented. In the latter case, 
the speed of the clock can be easily changed. The second implementation is a classical :py:class:`~sismic.clock.UtcClock` that corresponds
to a wall-clock in UTC with no flourish. The third implemention is a :py:class:`~sismic.clock.SynchronizedClock` that synchronizes its time value 
based on the one of an interpreter. Its main use case is to support the co-execution of property statecharts.

By default, the interpreter uses a :py:class:`~sismic.clock.SimulatedClock`. If you want the 
interpreter to rely on another kind of clock, pass an instance of :py:class:`~sismic.clock.Clock`
as the ``clock`` parameter of an interpreter constructor. 


Simulated clock
---------------

The default clock is a :py:class:`~sismic.clock.SimulatedClock` instance.
Its current time value can be read from the :py:attr:`~sismic.clock.SimulatedClock.time` attribute. 
The clock starts at 0 and can either be manually changed by setting its time value, or 
automatically (after having called its :py:meth:`~sismic.clock.SimulatedClock.start` method). 


.. testcode:: clock

    from sismic.clock import SimulatedClock

    clock = SimulatedClock()
    print('initial time:', clock.time)

    clock.time += 10
    print('new time:', clock.time)

.. testoutput:: clock

    initial time: 0
    new time: 10

.. note::

    Notice that time is expected to be monotonic: it is not allowed to set a new value that is strictly lower than
    the previous one. 


To support pseudo real time, a :py:class:`~sismic.clock.SimulatedClock` instance exposes two methods, namely 
:py:meth:`~sismic.clock.SimulatedClock.start` and :py:meth:`~sismic.clock.SimulatedClock.stop`. 
When the :py:meth:`~sismic.clock.SimulatedClock.start` method is called, the clock measures the elapsed time
using Python's ``time.time()`` function.

.. testcode:: clock

    from time import sleep

    clock = SimulatedClock()

    clock.start()
    sleep(0.1)
    print('after 0.1: {:.1f}'.format(clock.time))


.. testoutput:: clock

    after 0.1: 0.1

You can still change the current time value even if the clock is started:

.. testcode:: clock

    clock.time = 10
    print('after having been set to 10: {:.1f}'.format(clock.time))
    
    sleep(0.1)
    print('after 0.1: {:.1f}'.format(clock.time))

.. testoutput:: clock

    after having been set to 10: 10.0
    after 0.1: 10.1

Finally, a simulated clock can be accelerated or slowed down by changing the value 
of its :py:attr:`~sismic.clock.SimulatedClock.speed` attribute. By default, the value of this 
attribute is set to ``1``. A higher value (e.g., ``2``) means that the clock will be faster
than real time (e.g., 2 times faster), while a lower value slows down the clock. 

.. testcode:: clock

    clock = SimulatedClock()
    clock.speed = 100

    clock.start()
    sleep(0.1)
    clock.stop()

    print('new time: {:.0f}'.format(clock.time))

.. testoutput:: clock

    new time: 10


Example: manual time
~~~~~~~~~~~~~~~~~~~~

The following example illustrates a statechart modelling the behavior of a simple *elevator*.
If the elevator is sent to the 4th floor then, according to the YAML definition of this statechart,
the elevator should automatically go back to the ground floor after 10 seconds.

.. code:: yaml

    - target: doorsClosed
      guard: after(10) and current > 0
      action: destination = 0

Rather than waiting for 10 seconds, one can simulate this.
First, one should load the statechart and initialize the interpreter:

.. testcode::

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter, Event

    statechart = import_from_yaml(filepath='examples/elevator/elevator.yaml')

    interpreter = Interpreter(statechart)

The time of the internal clock of our interpreter is set to ``0`` by default.
We now ask our elevator to go to the 4th floor.

.. testcode::

    interpreter.queue(Event('floorSelected', floor=4))
    interpreter.execute()

The elevator should now be on the 4th floor.
We inform the interpreter that 2 seconds have elapsed:

.. testcode::

    interpreter.clock.time += 2
    print(interpreter.execute())

.. testoutput::
    :hide:

    []

The output should be an empty list ``[]``.
Of course, nothing happened since the condition ``after(10)`` is not
satisfied yet.
We now inform the interpreter that 8 additional seconds have elapsed.

.. testcode::

    interpreter.clock.time += 8
    interpreter.execute()

The elevator must has moved down to the ground floor.
Let's check the current floor:

.. testcode::

    print(interpreter.context.get('current'))

.. testoutput::

    0


Example: automatic time
~~~~~~~~~~~~~~~~~~~~~~~

If the execution of a statechart needs to rely on a real clock, the simplest way to achieve this
is by using the :py:meth:`~sismic.clock.SimulatedClock.start` method of an interpreter clock. 

Let us first initialize an interpreter using one of our statechart example, the *elevator*:

.. testcode:: realclock

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter, Event

    statechart = import_from_yaml(filepath='examples/elevator/elevator.yaml')

    interpreter = Interpreter(statechart)

Initially, the internal clock is set to 0. 
As we want to simulate the statechart based on real-time, we need to start the clock. 
For this example, as we don't want to have to wait 10 seconds for the elevator to 
move to the ground floor, we speed up the internal clock by a factor of 100:

.. testcode:: realclock

    interpreter.clock.speed = 100
    interpreter.clock.start()

We can now execute the statechart by sending a ``floorSelected`` event, and wait for the output.
For our example, we first ask the statechart to send to elevator to the 4th floor.

.. testcode:: realclock

    interpreter.queue(Event('floorSelected', floor=4))
    interpreter.execute()
    print('Current floor:', interpreter.context.get('current'))
    print('Current time:', int(interpreter.clock.time))

At this point, the elevator is on the 4th floor and is waiting for another input event.
The internal clock value is still close to 0.

.. testoutput:: realclock

    Current floor: 4
    Current time: 0

Let's wait 0.1 second (remember that we speed up the internal clock, so 0.1 second means 10 seconds
for our elevator):

.. testcode:: realclock

    from time import sleep

    sleep(0.1)
    interpreter.execute()

We can now check that our elevator is on the ground floor:

.. testcode:: realclock

    print(interpreter.context.get('current'))

.. testoutput:: realclock

    0


Wall-clock 
----------

The second clock provided by Sismic is a :py:class:`~sismic.clock.UtcClock` whose time 
is synchronized with system time (it relies on the ``time.time()`` function of Python).


.. testcode::

    from sismic.clock import UtcClock
    from time import time

    clock = UtcClock()
    assert (time() - clock.time) <= 1


Synchronized clock
------------------

The third clock is a :py:class:`~sismic.clock.SynchronizedClock` that expects an 
:py:class:`~sismic.interpreter.Interpreter` instance, and synchronizes its time
value based on the value of the ``time`` attribute of the interpreter.

The main use cases are when statechart executions have to be synchronized to the 
point where a shared clock instance is not sufficient because executions should 
occur at exactly the same time, up to the milliseconds. Internally, this clock 
is used when property statecharts are bound to an interpreter, as they need to be
executed at the exact same time. 


Implementing other clocks
-------------------------

You can quite easily write your own clock implementation, for example if you need to
synchronize different distributed interpreters. 
Simply subclass the :py:class:`~sismic.clock.Clock` base class.

.. autoclass:: sismic.clock.Clock
    :members:
    :member-order: bysource
    :noindex:



Delayed events
==============

Sismic also has support for delayed events, i.e. events that will be triggered in the future.

When a delayed event is queued in an interpreter at time ``T`` with delay ``D``, 
it is not processed by a call to :py:meth:`~sismic.interpreter.Interpreter.execute` 
or to :py:meth:`~sismic.interpreter.Interpreter.execute_once` unless the current clock 
time value exceeds ``T + D``. 

Delayed events can be created simply by providing a ``delay`` parameter when an 
:py:class:`~sismic.model.Event` instance is created, or when calling 
an interpreter's :py:meth:`~sismic.interpreter.Interpreter.queue` method. 


.. testcode:: delayed

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    statechart = import_from_yaml(filepath='examples/elevator/elevator.yaml')
    interpreter = Interpreter(statechart)

    interpreter.queue('floorSelected', floor=4, delay=5)


Delayed events are not processed by the interpreter, as long as the current clock
has not reached given delay. 

.. testcode:: delayed

    print('Current time:', interpreter.clock.time)  # 0
    interpreter.execute()  
    print('Current floor:', interpreter.context['current'])  # Still on ground floor

.. testoutput:: delayed

    Current time: 0
    Current floor: 0

They are processed as soon as the clock time value exceeds the expected delay:

.. testcode:: delayed

    interpreter.clock.time = 5
    interpreter.execute()
    print('Current floor:', interpreter.context['current'])  # Still on ground floor

.. testoutput:: delayed

    Current floor: 4


Notice that the time when a delayed event will be processed is based on the time value of 
the clock when the :py:meth:`~sismic.interpreter.Interpreter.queue` method is called, not 
the :py:attr:`~sismic.interpreter.Interpreter.time` attribute that corresponds to the time of 
the last executed step.

.. testcode:: delayed

    interpreter.clock.time = 6
    print('Interpreter time:', interpreter.time)
    print('Clock time:', interpreter.clock.time)
    
    interpreter.queue('floorSelected', floor=2, delay=1)
    
.. testoutput:: delayed

    Interpreter time: 5
    Clock time: 6
    
.. testcode:: delayed

    interpreter.clock.time = 7
    interpreter.execute()  # Event is processed, because 6 + 1 >= 7

    print('Current floor:', interpreter.context['current'])    

.. testoutput:: delayed

    Current floor: 2
