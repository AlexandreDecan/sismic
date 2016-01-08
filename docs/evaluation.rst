.. _code_evaluation:

Code contained in statecharts
=============================

A statechart can specify code that needs to be executed under some circumstances.
For example, the ``on entry`` property on a statechart, the ``guard`` or ``action`` on a transition or the
``on entry`` and ``on exit`` properties for a state may all contain code.

In Sismic, these pieces of code can be evaluated and executed by :py:class:`~sismic.evaluator.Evaluator` instances.

.. _python_evaluator:

Built-in Python code evaluator
------------------------------

By default, Sismic provides two built-in :py:class:`~sismic.evaluator.Evaluator` subclasses:

 - A default :py:class:`~sismic.evaluator.PythonEvaluator` that allows the statecharts to execute Python code directly.
 - A :py:class:`~sismic.evaluator.DummyEvaluator` that always evaluates to ``True`` and silently ignores
   ``action``, ``on entry`` and ``on exit``. Its context is an empty dictionary.


The *context* of an evaluator
*****************************

An instance of :py:class:`~sismic.evaluator.PythonEvaluator` can evaluate and execute Python code specified in the statechart.
The key point to understand how it works is the concept of ``context``, which is a dictionary-like structure that contains the data
that is exposed to the code fragments contained in the statechart (ie. override ``__locals__``).

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

.. testcode::

    from sismic.evaluator import PythonEvaluator
    import math as my_favorite_module

    evaluator = PythonEvaluator(initial_context={'x': 1, 'math': my_favorite_module})

For convenience, the initial context can be directly provided to an :py:class:`~sismic.interpreter.Interpreter`
constructor.

Notice that the initial context is evaluated *before* any code contained in the statechart.
As a consequence, this implies that if a same variable name is used both in the initial context and
in the YAML, the value set in the initial context will be overridden by the value set in the YAML definition.

.. testsetup:: variable_override

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

.. testcode:: variable_override

    yaml = """statechart:
      name: example
      on entry:
        x = 1
      initial: s
      states:
        - name: s
    """

    statechart = import_from_yaml(yaml)
    interpreter = Interpreter(statechart, initial_context={'x': 2})
    print(interpreter.context['x'])

In this example, the value of ``x`` in the statechart is set to ``1`` while the initial context sets its
value to ``2``. However, as the initial context is evaluated before the statechart, the value of
``x`` is ``1``:

.. testoutput:: variable_override

    1

This is a perfectly normal, expected behavior.
If you want to define variables in your statechart that can be overridden by an initial context, you should
check this variable does not exist in ``locals()``. For example, using

.. testcode::

    if not 'x' in locals():
        x = 1

or equivalently,

.. testcode::

    x = locals().get('x', 1)


Features of the built-in Python evaluator
*****************************************

Depending on the situation (state entered, guard evaluation, etc.), the context is populated with additional
entries. These entries are covered in the next section.


.. autoclass:: sismic.evaluator.PythonEvaluator
    :noindex:

Anatomy of a code evaluator
---------------------------

The documentation below explains how an evaluator is organized and what does the default built-in Python evaluator.
Readers that are not interested in tuning existing evaluators or creating new ones can skip this part of the documentation.

An :py:class:`~sismic.evaluator.Evaluator` must provide two main methods and an attribute:

.. automethod:: sismic.evaluator.Evaluator._evaluate_code
    :noindex:

.. automethod:: sismic.evaluator.Evaluator._execute_code
    :noindex:

.. autoattribute:: sismic.evaluator.Evaluator.context
    :noindex:

Notice that none of the two methods is actually called by the interpreter during the execution of a
statechart. These methods are fallback methods, meaning they are implicitly called when one of the
following methods is not defined in a concrete evaluator instance:

.. autoclass:: sismic.evaluator.Evaluator
    :members:
    :exclude-members: _evaluate_code, _execute_code, context
    :noindex:

In order to understand how the evaluator works, the documentation of the :py:class:`~sismic.evaluator.Evaluator` mentions the following important statements:

 - Methods :py:meth:`~sismic.evaluator.Evaluator.execute_onentry` and :py:meth:`~sismic.evaluator.Evaluator.execute_onexit`
   are called respectively when a state is entered or exited, even if this state does not define a ``on_entry`` or
   ``on_exit`` attribute.
 - Method :py:meth:`~sismic.evaluator.Evaluator.execute_action` is called when a transition is processed, even if
   the transition does not define any ``action``.

This allows the evaluator to keep track of the states that are entered or exited, and of the transitions that are
processed.


Examples
--------

Consider the following statechart that performs simple arithmetic operations.

.. literalinclude:: ../tests/yaml/actions.yaml
   :language: yaml


The statechart :ref:`here <yaml_example>` shows a more intricate example.
