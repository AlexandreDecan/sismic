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

Depending on the situation (state entered, guard evaluation, etc.), the context is populated with additional
entries. These entries are covered in the next section.


Features of the built-in Python evaluator
*****************************************

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
