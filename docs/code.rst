.. _code_evaluation:

Include code in statecharts
===========================

Python code evaluator
---------------------

A statechart can specify code that needs to be executed under some circumstances.
For example, the *preamble* of a statechart, the *guard* or *action* of a transition or the
*on entry* and *on exit* of a state may all contain code.

In Sismic, these pieces of code can be evaluated and executed by :py:class:`~sismic.code.Evaluator` instances.
By default, when an interpreter is created, a :py:class:`~sismic.code.PythonEvaluator` is created and allows
the interpreter to evaluate and execute Python code contained in a statechart.

Alternatively, a :py:class:`~sismic.code.DummyEvaluator` that always evaluates conditions to ``True`` and
silently ignores actions can be used, but is clearly of less interest.

In the following, we will implicitly assume that the code evaluator is an instance of :py:class:`~sismic.code.PythonEvaluator`.


Context of the Python code evaluator
------------------------------------

When a code evaluator is created or provided to an interpreter, its ``context`` is exposed through the ``context``
attribute of the interpreter. The context of an evaluator is a mapping between variable names and their values.
When a piece of code contained in a statechart has to be evaluated or executed, the context of the evaluator is used to
populate the local and global variables that are available for this piece of code.

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

When an interpreter is created for this statechart, its preamble is executed and the context of the code evaluator is
populated with ``{'x': 1, 'y': 0}``. When the statechart is further executed (initialized), and its root state
*s1* is entered, the code ``x += 1`` contained in the ``on entry`` field of *s1* is then executed in this context.
After execution, the context is ``{'x': 2, 'y': 0}``.

The default code evaluator has a global context that is always exposed when a piece of code has to be evaluated
or executed, and also defines local contexts for each state. Local contexts allow one to create variables whose
scope is limited to the state and its descendants. In other word, the context of a state is composed of its local
context and the ones of its ancestors. The context of a transition is the same than the one of its source state.

More precisely, every state and every transition has a specific evaluation context.
The code associated with a state is executed in a local context which is composed of local variables and every
variable that is defined in the context of the parent state. The context of a transition is built upon the context
of its source state.

Dealing with local contexts should not be an issue when writing code in the statechart, as it's very close to the
way scopes are handled by Python.
It could however look tricky when manipulating the ``context`` attribute of an interpreter or of a
:py:class:`~sismic.code.PythonEvaluator` instance directly.
For convenience, the context that is exposed by those objects prepend the name of the state to the name of the
variables that were defined in that state. For instance, if ``x`` has been defined independently in both *s1* and *s2*,
and assuming that *s1* is not a descendant nor an ancestor of *s2*, then the value of ``x`` in *s1* and *s2* can be
accessed respectively using ``interpreter.context['s1.x']`` and ``interpreter.context['s2.x']``.


When a :py:class:`~sismic.code.PythonEvaluator` instance is initialized, an initial context can be specified.
For convenience, the initial context can be directly provided to the constructor of an :py:class:`~sismic.interpreter.Interpreter`.

It should be noticed that the initial context is set *before* executing the preamble of a statechart.
While this should be expected, it has the direct consequence that if a variable defined in the initial context is
also defined by the preamble, the latter will override its value, as illustrated by the following example:

.. testcode:: variable_override

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter
    import math as my_favorite_module

    yaml = """statechart:
      name: example
      preamble:
        x = 1
      root state:
        name: s
    """

    statechart = import_from_yaml(yaml)
    context = {
        'x': 2,
        'math': my_favorite_module
    }

    interpreter = Interpreter(statechart, initial_context=context)

    print(interpreter.context['x'])

.. testoutput:: variable_override

    1

In this example, the value of ``x`` is eventually set to ``1``.
While the initial context provided to the interpreter defined the value of ``x`` to ``2``, the code contained in the
preamble overrode its value.
If you want to make use of the initial context to somehow *parametrize* the execution of the statechart, while still
providing *default* values for these parameters, you should check the existence of the variables before setting
their values. This can be done as follows:

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


Predefined variables and functions
----------------------------------

When a piece of code is evaluated or executed, the default Python code evaluator enriches its local context with
several predefined variables and functions. These predefined objects depend on the situation triggering a code
evaluation or a code execution (entry or exit actions, guard evaluation, transition action, ...).

These entries are covered in the docstring of a :py:class:`~sismic.code.PythonEvaluator`:

.. autoclass:: sismic.code.PythonEvaluator
    :noindex:



Anatomy of a code evaluator
---------------------------

.. note:: The documentation below explains how an evaluator is organized and what does the default built-in Python evaluator.
    Readers that are not interested in tuning existing evaluators or creating new ones can skip this part of the documentation.

An :py:class:`~sismic.code.Evaluator` subclass must at lest implement the following methods and attributes:

.. automethod:: sismic.code.Evaluator._evaluate_code
    :noindex:

.. automethod:: sismic.code.Evaluator._execute_code
    :noindex:

.. autoattribute:: sismic.code.Evaluator.context
    :noindex:


.. note::
    None of those two methods are actually called by the interpreter during the execution of a statechart.
    These methods are *fallback methods* that are used by other methods that are implicitly called depending on what is
    currently being processed in the statechart. The documentation of :py:class:`~sismic.code.Evaluator` covers this:

.. autoclass:: sismic.code.Evaluator
    :members:
    :exclude-members: _evaluate_code, _execute_code, context
    :member-order: bysource
    :noindex:

