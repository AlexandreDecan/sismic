
Dealing with time
=================

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


Interpreter clock
-----------------

The clock of an interpreter is an instance of :py:class:`~sismic.interpreter.Clock` and is 
exposed through its :py:attr:`~sismic.interpreter.Interpreter.clock` attribute. 

The clock always starts at ``0`` and accumulates the elapsed time. 
Its current time value can be read from the :py:attr:`~sismic.interpreter.Clock.time` attribute. 
By default, the value of this attribute does not change, unless manually modified (simulated time) or
by starting the clock (using :py:meth:`~sismic.interpreter.Clock.start`, wall-clock time).


To change the current time of a clock, simply set a new value to the :py:attr:`~sismic.interpreter.Clock.time` attribute.
Notice that time is expected to be monotonic: it is not allowed to set a new value that is strictly lower than
the previous one. 

As expected, simulated time can be easily achieved by manually modifying this value:

.. testcode:: clock

    from sismic.interpreter import Clock

    clock = Clock()
    print('initial time:', clock.time)

    clock.time += 10
    print('new time:', clock.time)

.. testoutput:: clock

    initial time: 0
    new time: 10


To support real time, a :py:class:`~sismic.interpreter.Clock` object has two methods, namely 
:py:meth:`~sismic.interpreter.Clock.start` and :py:meth:`~sismic.interpreter.Clock.stop`. 
These methods can be used respectively to start and stop the synchronization with real time. 
Internally, the clock relies on Python's ``time.time()`` function. 

.. testcode:: clock

    from time import sleep

    clock = Clock()

    clock.start()
    sleep(0.1)
    print('after 0.1: {:.1f}'.format(clock.time))


.. testoutput:: clock

    after 0.1: 0.1


A clock based on real time can also be manually changed during the execution by setting a 
new value for its :py:attr:`~sismic.interpreter.Clock.time` attribute:


.. testcode:: clock

    clock.time = 10
    print('after having been set to 10: {:.1f}'.format(clock.time))
    
    sleep(0.1)
    print('after 0.1: {:.1f}'.format(clock.time))

.. testoutput:: clock

    after having been set to 10: 10.0
    after 0.1: 10.1


Finally, a clock based on real time can be accelerated or slowed down by changing the value 
of its :py:attr:`~sismic.interpreter.Clock.speed` attribute. By default, the value of this 
attribute is set to ``1``. A higher value (e.g. ``2``) means that the clock will be faster
than real time (e.g. 2 times faster), while a lower value slows down the clock. 

.. testcode:: clock

    clock = Clock()
    clock.speed = 100

    clock.start()
    sleep(0.1)
    clock.stop()

    print('new time: {:.0f}'.format(clock.time))

.. testoutput:: clock

    new time: 10

    

Simulated time
--------------

The following example illustrates a statechart modeling the behavior of a simple *elevator*.
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



Real or wall-clock time
-----------------------

If the execution of a statechart needs to rely on a real clock, the simplest way to achieve this
is by using the :py:meth:`~sismic.interpreter.Clock.start` method of an interpreter clock. 

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