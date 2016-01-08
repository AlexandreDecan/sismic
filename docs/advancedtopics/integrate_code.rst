.. _integrate_code:

Integrating Sismic into code
============================

One can easily integrate code into a statechart (see :ref:`code_evaluation`).
By providing an initial context to a :py:class:`~sismic.evaluator.Evaluator` instance, it is also easy
to inject external objects into a statechart.

We now illustrate how one can integrate a statechart into code.
Consider the following stopwatch statechart, which is also available in the *examples* directory.
In a nutshell, this example shows how to control a stopwatch timer from a graphical user interface.

Stopwatch statechart
--------------------

We first consider the statechart describing the behavior of our stopwatch timer.
Basically, it is a stopwatch that supports *start*, *stop*, *split*, and *reset* features.
These features are triggered by external events.
The stopwatch sends an *updated* event when its display is updated, and stores its display
in *display_timer*.

.. literalinclude:: ../../examples/stopwatch.yaml
    :language: yaml

Stopwatch user interface
------------------------

.. image:: ../images/stopwatch.png

The statechart is executed and synchronized with a GUI defined using :py:mod:`Tkinter`.
The key points for this code are:

- the use of :py:meth:`sismic.interpreter.Interpreter.bind` to trigger a refresh of the
  timer label when a *updated* event is sent by the statechart,
- the use of :py:meth:`sismic.interpreter.Interpreter.send` to send events to the statechart
  when a button is pressed, and
- the ``run`` method that handles the time and the execution of the interpreter.

.. literalinclude:: ../../examples/stopwatch.py
    :language: python
