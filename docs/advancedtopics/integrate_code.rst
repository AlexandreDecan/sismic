.. _integrate_code:

Integrate statecharts into your code
====================================

Sismic provides several ways to integrate executable statecharts into your Python source code.
The simplest way is to directly *embed* the entire code in the statechart’s description. This was illustrated with the
Elevator example in :ref:`code_evaluation`. Its code is part of the YAML file of the statechart, and interpreted by
Sismic during the statechart's execution.

In order to make a statechart communicate with the source code contained in the environment in which it is executed,
there are basically two approaches:

1. The statechart sends events to, or receives external events from the environment.
2. The environment stores shared objects in the statechart’s initial context, and the statechart calls operations on
   these objects and/or accesses the variables contained in it.

Of course, one could also use a hybrid approach, combining ideas from the three approches above.

Running example
---------------

In this document, we will present the main differences between the two approaches, on the basis of a simple example of a Graphical User Interface (GUI)
whose behaviour is defined by a statechart. All the source code and YAML files  for this example, discussed in more
detail below, is available in the *docs/examples* directory of Sismic’s repository.

The example represents a simple stopwatch, i.e., a timer than can be started, stopped and reset. It also provides a
split time feature and a display of the elapsed time. A button-controlled GUI of such a stopwatch looks as follows
(inactive buttons are greyed out):

.. image:: /examples/stopwatch/stopwatch_gui.png
    :align: center

Essentially, the stopwatch simply displays a value, representing the elapsed time (expressed in seconds), which is
initially 0. By clicking on the *start* button the stopwatch starts running. When clicking on *stop*, the stopwatch stops running.
By using *split*, the time being displayed is temporarily frozen, although the stopwatch continues to run.
Clicking on *unsplit* while continue to display the actual elapsed time. *reset* will restart from 0, and *quit* will quit the stopwatch application.

The idea is that the buttons will trigger state changes and actions carried out by an underlying statechart.
Taking abstraction of the concrete implementation, the statechart would essentially look as follows, with one main *active* state containing two parallel substates *timer* and *display*.

.. image:: /examples/stopwatch/stopwatch_overview.png
    :align: center

Controlling a statechart from within the environment
----------------------------------------------------

Let us illustrate how to control a statechart through source code that executes in the environment containing the statechart.
The statechart's behaviour is triggered by external events sent to it by the source code each time one of the buttons in the GUI is pressed.
Conversely, the statechart itself can send events back to the source code to update its display.

This statechart looks as follows:

.. image:: /examples/stopwatch/stopwatch_with_logic.png
    :align: center

Here is the YAML file containing the  textual description of this statechart:

.. literalinclude:: /examples/stopwatch/stopwatch.yaml
    :language: yaml

We observe that the statechart contains an ``elapsed_time`` variable, that is updated every second while the stopwatch is in the *running* state.
The statechart will modify its behaviour by receiving *start*, *stop*, *reset* and *split* events from its external environment.
In parallel to this, every 100 milliseconds, the *display* state of the statechart sends a *refresh* event (parameterised by the ``time`` variable containing the ``elapsed_time`` value) back to its external environment.
In the *lap time* state (reached through a *split* event) , this regular refreshing is stopped until a new *split* event is received.

The source code (shown below) that defines the GUI of the stopwatch, and that controls the statechart by sending it events, is implemented using the :py:mod:`Tkinter` library.
Each button of the GUI is bound to a Python method in which the corresponding event is created and sent to the statechart.
The statechart is *bound* to the source code by defining a new :py:class:`~sismic.interpreter.Interpreter` that contains the parsed YAML specification, and using the :py:meth:`~sismic.interpreter.Interpreter.bind` 
method. The  ``event_handler`` passed to it allows the Python source code to receive events back from the statechart.
In particular, the ``w_timer`` field of the GUI will be updated with a new value of the time whenever the statechart sends a *refresh* event.
The ``run`` method, which is put in Tk's mainloop, updates the internal clock of the interpreter and executes the interpreter.

.. literalinclude:: /examples/stopwatch/stopwatch_gui.py
    :language: python


Controlling the environment from within the statechart
------------------------------------------------------

In this second example, we basically reverse the idea: now the Python code that resides in the environment contains the
logic (e.g., the ``elapsed_time`` variable), and this code is exposed to, and controlled by, a statechart that represents
the main loop of the program and calls the necessary methods in the source code.
These method calls are associated to actions on the statechart's transitions.
With this solution, the statechart is no longer a *black box*, since it needs to be aware of the source code, in particular
the methods it needs to call in this code.

An example of the Python code that is controlled by the statechart is given below:

.. literalinclude:: /examples/stopwatch/stopwatch.py
    :pyobject: Stopwatch

The statechart expects such a ``Stopwatch`` instance to be created and provided in its initial context.
Recall that an :py:class:`~sismic.interpreter.Interpreter` accepts an optional ``initial_context`` parameter.
In this example, ``initial_context={'stopwatch': Stopwatch()}``.

The statechart is simpler than in the previous example: one parallel region handles the
running status of the stopwatch, and a second one handles its split features.

.. image:: /examples/stopwatch/stopwatch_with_object.png
    :align: center

.. literalinclude:: /examples/stopwatch/stopwatch_external.yaml
    :language: yaml

The Python code of the GUI no longer needs to *listen* to the events sent by the interpreter. It should, of course, continue to send events (corresponding to button presses) to the statechart using ``send``.
The *binding* between the statechart and the GUI is now achieved differently, by simply passing the ``stopwatch`` object to the :py:class:`~sismic.interpreter.Interpreter` as its ``initial_context``.

.. literalinclude:: /examples/stopwatch/stopwatch_gui_external.py
    :language: python
