.. _code_evaluation:

Code contained in statecharts
=============================

A statechart can write code to be executed under some circumstances.
For example, the ``on entry`` property on a statechart, the ``guard`` or ``action`` on a transition or the
``on entry`` and ``on exit`` properties for a state.

In Sismic, these pieces of code can be evaluated and executed by :py:class:`~sismic.evaluator.Evaluator` instances.


Code evaluator
--------------

An :py:class:`~sismic.evaluator.Evaluator` must provide two methods and an attribute:

.. autoclass:: sismic.evaluator.Evaluator
    :members:


By default, Sismic provides two built-in :py:class:`~sismic.evaluator.Evaluator` subclasses:

 - A :py:class:`~sismic.evaluator.DummyEvaluator` that always evaluate a guard to ``True`` and silently ignores
   ``action``, ``on entry`` and ``on exit``. Its context is an empty dictionary.
 - A :py:class:`~sismic.evaluator.PythonEvaluator` that brings Python into our statecharts and which is used by default.

.. _python_evaluator:

Built-in Python code evaluator
------------------------------

An instance of :py:class:`~sismic.evaluator.PythonEvaluator` can evaluate and execute Python code expressed in the statechart.
The key point to understand how it works is the concept of ``context``, which is a dictionary-like structure that contains the data
that are exposed to the pieces of code of the statechart (ie. override ``__locals__``).

As an example, consider the following partial statechart definition.

.. code:: yaml

    statechart:
    # ...
    on entry: x = 1
    states:
      - name: s1
        on entry: x += 1

When the statechart is initialized, the ``context`` of a :py:class:`~sismic.evaluator.PythonEvaluator` is ``{'x': 1}``.
When *s1* is entered, the code will be evaluated with this context.
After the execution of ``x += 1``, the context associates ``2`` to ``x``.

When a :py:class:`~sismic.evaluator.PythonEvaluator` instance is initialized, a prepopulated context can be specified:

.. code:: python

    from sismic.evaluator import PythonEvaluator
    import math as my_favorite_module

    evaluator = PythonEvaluator(initial_context={'x': 1, 'math': my_favorite_module})

By default, the context already exposes several values:

 - The :py:class:`~sismic.model.Event` class to allow the creation of internal events.
 - A ``send`` function that takes an :py:class:`~sismic.model.Event` instance and fires an internal event with.
 - An ``active(name) -> bool`` Boolean function that takes a state name and return ``True`` if and only if this state is currently
   active, ie. it is in the active configuration of the :py:class:`~sismic.interpreter.Interpreter` instance
   that makes use of this evaluator.
 - An ``event`` variable that (possibly) contains the :py:class:`~sismic.model.Event` instance associated to
   the transitions (either when :py:meth:`~sismic.evaluator.Evaluator.evaluate_condition` is called or when
   :py:meth:`~sismic.evaluator.Evaluator.execute_action` is called for a transition action).

Unless you override its entry in the context, the ``__builtins__`` of Python are automatically exposed.
This implies you can use nearly everything from Python in your code.

.. autoclass:: sismic.evaluator.PythonEvaluator


If an exception occurred while executing or evaluating a piece of code, it is propagated by the
evaluator.

Examples
--------

Consider the following statechart that performs simple arithmetic operations.

.. literalinclude:: ../examples/simple/actions.yaml
   :language: yaml


The statechart :ref:`here <yaml_example>` shows a more intricate example.