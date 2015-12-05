Evaluate and execute code contained in statecharts
==================================================


A statechart can write code to be executed under some circumstances.
For example, the `on entry` property on a `statechart`, `guard` or `action` on a transition or the
`on entry` and `on exit` property for a state.

In PySS, these pieces of code can be evaluated and executed by `Evaluator` instances.
An `Evaluator` must provide two methods:

 - A `evaluate_condition(condition, event)` method that takes a condition (a one-line string containing some code)
 and an `Event` instance (which is essentially a `name` and a dictionary `data`). This methods should return either `True` or `False`.
 - A `execute_action(action, event)` method that takes an action (a string containing some code) and an `Event`
 instance. This method should return a list of `Event` instances that will be treated as internal events
 (and thus that have priority).

By default, PySS provides two built-in `Evaluator` subclasses:

 - A `DummyEvaluator` that always evaluate a guard to `True` and silently ignores `action`, `on entry` and `on exit`.
 - A `PythonEvaluator` that brings Python into our statecharts.

An instance of `PythonEvaluator` can evaluate and execute Python code expressed in the statechart.
Such an instance relies on the concept of `context`, which is a dictionary-like structure that contains the data
that are exposed to the pieces of code of the statechart (ie. override `__locals__`).

As an example, consider the following partial statechart definition.

.. code:: yaml

    statechart:
    # ...
    on entry: x = 1
    states:
      - name: s1
        on entry: x += 1

When the statechart is initialized, the `context` of a `PythonEvaluator` will contain `{'x': 1}`.
When *s1* is entered, the code will be evaluated with this context.
After the execution of `x += 1`, the context will contain `{'x': 1}`.

When a `PythonEvaluator` instance is initialized, a prepopulated context can be specified:

.. code:: python

    import math as my_favorite_module
    # ...
    evaluator = PythonEvaluator({'x': 1, 'math': my_favorite_module})


By default, the context will expose an `Event` class (from `model.Event`) and a `send` function, that can be used
to send internal event to the simulator (eg.: `on entry: send(Event('Hello World!'))`).

Additionally, the `__builtins__` of Python are also exposed, implying that you can use nearly everything provided
by the standard library of Python.

