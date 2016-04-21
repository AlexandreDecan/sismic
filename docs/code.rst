.. _code_evaluation:

Include code in statecharts
===========================

A statechart can specify code that needs to be executed under some circumstances.
For example, the *preamble* property on a statechart, the *guard* or *action* on a transition or the
*on entry* and *on exit* properties for a state may all contain code.

In Sismic, these pieces of code can be evaluated and executed by :py:class:`~sismic.code.Evaluator` instances.

.. _python_evaluator:

Built-in Python code evaluator
------------------------------

By default, Sismic provides two built-in :py:class:`~sismic.code.Evaluator` subclasses:

 - A default :py:class:`~sismic.code.PythonEvaluator` that allows the statecharts to execute Python code directly.
 - A :py:class:`~sismic.code.DummyEvaluator` that always evaluates to ``True`` and silently executes nothing when
   it is called. Its context is an empty dictionary.

The key point to understand how an evaluator works is the concept of ``context``, which is a dictionary-like structure that contains the data
that is exposed to the code fragments contained in the statechart (ie. override ``__locals__``).

As an example, consider the following partial statechart definition.

.. code:: yaml

    statechart:
      # ...
      preamble: |
        x = 1
        y = 0
      root state:
        name: s1
        on entry: x += 1

When the statechart is initialized, the ``context`` of the :py:class:`~sismic.code.PythonEvaluator` is ``{'x': 1, 'y': 0}``.
When *s1* is entered, the code will be evaluated with this context.
After the execution of ``x += 1``, the context associates ``2`` to ``x``.

More precisely, every state and every transition has a specific evaluation context.
The code associated with a state is executed in a local context which is composed of local variables and every
variable that is defined in the context of the parent state. The context of a transition is built upon the context
of its source state.

.. note:: While you have full access to an ancestor's context, the converse is not true: every variable that
    is defined in a context is NOT visible by any other context, except the ones that are nested.

When a :py:class:`~sismic.code.PythonEvaluator` instance is initialized, an initial context can be specified:

.. testcode::

    from sismic.code import PythonEvaluator
    import math as my_favorite_module

    evaluator = PythonEvaluator(initial_context={'x': 1, 'math': my_favorite_module})

For convenience, the initial context can be directly provided to the constructor of an :py:class:`~sismic.interpreter.Interpreter`.

.. note:: The initial context is evaluated *before* any code contained in the statechart.
    As a consequence, this implies that if a same variable name is used both in the initial context and
    in the YAML, the value set in the initial context will be overridden by the value set in the YAML definition.

.. testsetup:: variable_override

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

.. testcode:: variable_override

    yaml = """statechart:
      name: example
      preamble:
        x = 1
      root state:
        name: s
    """

    statechart = import_from_yaml(yaml)
    interpreter = Interpreter(statechart, initial_context={'x': 2})
    print(interpreter.context['x'])

In this example, the value of ``x`` in the statechart is set to ``1`` while the initial context sets its
value to ``2``. However, as the initial context is evaluated before the statechart, the value of
``x`` is ``1``.

.. testoutput:: variable_override
    :hide:

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


.. warning::

    Under the hood, a Python evaluator makes use of ``eval()`` and ``exec()`` with global and local contexts.
    This can lead to some *weird* issues with variable scope (as in list comprehensions or lambda's).
    See `this question on Stackoverflow <http://stackoverflow.com/questions/32894942/listcomp-unable-to-access-locals-defined-in-code-called-by-exec-if-nested-in-fun>`__ for more information.


Features of the built-in Python evaluator
-----------------------------------------

Depending on the situation (state entered, guard evaluation, etc.), the context is populated with additional
entries. These entries are covered in the docstring of a :py:class:`~sismic.code.PythonEvaluator`:


.. autoclass:: sismic.code.PythonEvaluator
    :noindex:

.. note:: The documentation below explains how an evaluator is organized and what does the default built-in Python evaluator.
    Readers that are not interested in tuning existing evaluators or creating new ones can skip this part of the documentation.


Anatomy of a code evaluator
---------------------------

An :py:class:`~sismic.code.Evaluator` must provide two main methods and an attribute:

.. automethod:: sismic.code.Evaluator._evaluate_code
    :noindex:

.. automethod:: sismic.code.Evaluator._execute_code
    :noindex:

.. autoattribute:: sismic.code.Evaluator.context
    :noindex:

None of the two methods is actually called by the interpreter during the execution of a statechart.
These methods are fallback methods, meaning they are implicitly called when one of the following methods is not defined in a concrete evaluator instance:

.. autoclass:: sismic.code.Evaluator
    :members:
    :exclude-members: _evaluate_code, _execute_code, context
    :member-order: bysource
    :noindex:

In order to understand how the evaluator works, the documentation of the :py:class:`~sismic.code.Evaluator` mentions the following important statements:

 - Methods :py:meth:`~sismic.code.Evaluator.execute_onentry` and :py:meth:`~sismic.code.Evaluator.execute_onexit`
   are called respectively when a state is entered or exited, even if this state does not define a *on_entry* or
   *on_exit* attribute.
 - Method :py:meth:`~sismic.code.Evaluator.execute_action` is called when a transition is processed, even if
   the transition does not define any *action*.

This allows the evaluator to keep track of the states that are entered or exited, and of the transitions that are
processed.

