
Dealing with time
=================

It is quite usual in a statechart to rely on some notion of time.
To cope with this, the built-in evaluator (see :py:class:`~sismic.code.PythonEvaluator`) has support for
time events ``after(x)`` and ``idle(x)``, meaning that a transition can be triggered after a certain amount of time.

When it comes to interpreting statecharts, Sismic deals with time using an internal clock whose value is exposed
by the :py:attr:`~sismic.interpreter.Interpreter.time` property of an :py:class:`~sismic.interpreter.Interpreter`.
Basically, this clock does nothing by itself except for being available for an
:py:class:`~sismic.code.Evaluator` instance.
If your statechart needs to rely on a time value, you have to set it by yourself.

Below are some examples to illustrate the use of time events.


Simulated time
--------------

Sismic provides a discrete step-by-step interpreter for statecharts.
It seems natural in a discrete simulation to rely on simulated time.

The following example illustrates a statechart modeling the behavior of a simple *elevator*.
If the elevator is sent to the 4th floor, according to the YAML definition of this statechart,
the elevator should automatically go back to the ground floor after 10 seconds.

.. code:: yaml

    - target: doorsClosed
      guard: after(10) and current > 0
      action: destination = 0

Rather than waiting for 10 seconds, one can simulate this.
First, one should load the statechart and initialize the interpreter:

.. testcode:: clock

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    with open('examples/elevator/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)

The internal clock of our interpreter is ``0``.
This is, ``interpreter.time == 0`` holds.
We now ask our elevator to go to the 4th floor.

.. testcode:: clock

    interpreter.queue(Event('floorSelected', floor=4))
    interpreter.execute()

The elevator should now be on the 4th floor.
We inform the interpreter that 2 seconds have elapsed:

.. testcode:: clock

    interpreter.time += 2
    print(interpreter.execute())

.. testoutput:: clock
    :hide:

    []

The output should be an empty list ``[]``.
Of course, nothing happened since the condition ``after(10)`` is not
satisfied yet.
We now inform the interpreter that 8 additional seconds have elapsed.

.. testcode:: clock

    interpreter.time += 8
    print(interpreter.execute())

.. testoutput:: clock
    :hide:

    [MacroStep@10(None, [Transition(doorsOpen, doorsClosed, None)], >['doorsClosed'], <['doorsOpen']), MacroStep@10(None, [Transition(doorsClosed, movingDown, None)], >['moving', 'movingDown'], <['doorsClosed']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(movingDown, movingDown, None)], >['movingDown'], <['movingDown']), MacroStep@10(None, [Transition(moving, doorsOpen, None)], >['doorsOpen'], <['movingDown', 'moving'])]

The output now contains a list of steps, from which we can see that the elevator has moved down to the ground floor.
We can check the current floor:

.. testcode:: clock

    print(interpreter.context.get('current'))

.. testoutput:: clock
    :hide:

    0

This displays ``0``.

Real time
---------

If a statechart needs to be aware of a real clock, the simplest way to achieve this is by using
the :py:func:`time.time` function of Python.
In a nutshell, the idea is to synchronize ``interpreter.time`` with a real clock.
Let us first initialize an interpreter using one of our statechart example, the *elevator*:

.. testcode:: realclock

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    with open('examples/elevator/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    interpreter = Interpreter(statechart)

The interpreter initially sets its clock to 0.
As we are interested in a real-time simulation of the statechart,
we need to set the internal clock of our interpreter.
We import from :py:mod:`time` a real clock,
and store its value into a ``starttime`` variable.

.. testcode:: realclock

    import time
    starttime = time.time()

We can now execute the statechart by sending a ``floorSelected`` event, and wait for the output.
For our example, we first ask the statechart to send to elevator to the 4th floor.

.. testcode:: realclock

    interpreter.queue(Event('floorSelected', floor=4))
    interpreter.execute()
    print('Current floor:', interpreter.context.get('current'))
    print('Current time:', interpreter.time)

At this point, the elevator is on the 4th floor and is waiting for another input event.
The internal clock value is still 0.

.. testoutput:: realclock

    Current floor: 4
    Current time: 0

We should inform our interpreter of the new current time.
Of course, as our interpreter follows a discrete simulation, nothing really happens until we call
:py:meth:`~sismic.interpreter.Interpreter.execute` or :py:meth:`~sismic.interpreter.Interpreter.execute_once`.

.. testcode:: realclock

    interpreter.time = time.time() - starttime
    # Does nothing if (time.time() - starttime) is less than 10!
    interpreter.execute()

Assuming you quickly wrote these lines of code, nothing happened.
But if you wait a little bit, and update the clock again, it should move the elevator to the ground floor.

.. testcode:: realclock

    interpreter.time = time.time() - starttime
    interpreter.execute()

And *voilà*!

As it is not very convenient to manually set the clock each time you want to execute something, it is best to
put it in a loop. To avoid the use of a ``starttime`` variable, you can set the initial time of an interpreter
using the ``initial_time`` parameter of its constructor.
This is illustrated in the following example.

.. code:: python

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    from sismic.model import Event

    import time

    # Load statechart and create an interpreter
    with open('examples/elevator.yaml') as f:
        statechart = import_from_yaml(f)

    # Set the initial time
    interpreter = Interpreter(statechart)
    interpreter.time = time.time()

    # Send an initial event
    interpreter.queue(Event('floorSelected', floor=4))

    while not interpreter.final:
        interpreter.time = time.time()
        if interpreter.execute():
            print('something happened at time {}'.format(interpreter.time))

        time.sleep(0.5)  # 500ms

Here, we called the :py:func:`~time.sleep` function to slow down the loop (optional).
The output should look like::

    something happened at time 1450383083.9943285
    something happened at time 1450383093.9920669

As our statechart does not define any way to reach a final configuration,
the ``not interpreter.final`` condition always holds,
and the execution needs to be interrupted manually.


Asynchronous execution
----------------------

Notice from previous example that using a loop makes it impossible to send events to the interpreter.
For convenience, sismic provides a :py:func:`sismic.interpreter.helpers.run_in_background`
function that run an interpreter in a thread, and does the job of synchronizing the clock for you.



.. note:: An optional argument ``callback`` can be passed to :py:func:`~sismic.interpreter.helpers.run_in_background`.
    It must be a callable that accepts the (possibly empty) list of :py:class:`~sismic.model.MacroStep` returned by 
    the underlying call to :py:meth:`~sismic.interpreter.Interpreter.execute`. 
