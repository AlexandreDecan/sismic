.. _code_evaluation:

Code contained in statecharts
=============================

A statechart can write code to be executed under some circumstances.
For example, the ``on entry`` property on a ``statechart``, ``guard`` or ``action`` on a transition or the
``on entry`` and ``on exit`` property for a state.

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

    evaluator = PythonEvaluator({'x': 1, 'math': my_favorite_module})


By default, the context exposes an :py:class:`~sismic.model.Event` and a ``send`` function.
They can be used to send internal event to the simulator, eg., ``on entry: send(Event('Hello World!'))``.

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