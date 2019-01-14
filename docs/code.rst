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

When a code evaluator is created or provided to an interpreter, all the variables that are defined or used by the 
statechart are stored in an *execution context*. This context is exposed through the ``context``
attribute of the interpreter and can be seen as a mapping between variable names and their values.
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

The default code evaluator uses a global context, meaning that all variables that are defined in the statechart are
exposed by the evaluator when a piece of code has to be evaluated or executed. The main limitation of this approach
is that you cannot have distinct variables with a same name in different states or, in other words, there is
only one scope for all your variables. 

The preamble of a statechart can be used to provide default values for some variables. However, the preamble is part of 
the statechart and as such, cannot be used to *parametrize* the statechart. To circumvent this, an initial context
can be specified when a :py:class:`~sismic.code.PythonEvaluator` is created. For convenience, this initial context
can also be passed to the constructor of an :py:class:`~sismic.interpreter.Interpreter`.

Considered the following toy example:

.. testcode:: initial_context

    from sismic.io import import_from_yaml
    from sismic.interpreter import Interpreter

    yaml = """statechart:
      name: example
      preamble:
        x = DEFAULT_X
      root state:
        name: s
    """

    statechart = import_from_yaml(yaml)

Notice that variable ``DEFAULT_X`` is used in the preamble but not defined. The statechart expects this 
variable to be provided in the initial context, as illustrated next:

.. testcode:: initial_context

    interpreter = Interpreter(statechart, initial_context={'DEFAULT_X': 1})

We can check that the value of ``x`` is ``1`` by accessing the ``context`` attribute of the interpreter:

.. testcode:: initial_context

    assert interpreter.context['x'] == 1

Omitting to provide the ``DEFAULT_X`` variable in the initial context leads to an error, as an unknown
variable is accessed by the preamble: 

.. testcode:: initial_context

    try:
        Interpreter(statechart)
    except Exception as e: 
        print(e)

.. testoutput:: initial_context

    "name 'DEFAULT_X' is not defined" occurred while executing "x = DEFAULT_X"

It could be tempting to define a default value for ``x`` in the preamble **and** overriding this 
value by providing an initial context where ``x`` is defined. However, the initial context of an 
interpreter is set **before** executing the preamble of a statechart. As a consequence, if a variable
is defined both in the initial context and the preamble, its value will be overridden by the preamble.

Consider the following example where ``x`` is both defined in the initial context and the preamble:

.. testcode:: initial_context

    yaml = """statechart:
      name: example
      preamble:
        x = 1
      root state:
        name: s
    """

    statechart = import_from_yaml(yaml)
    interpreter = Interpreter(statechart, initial_context={'x': 2})

    assert interpreter.context['x'] == 1

The value of ``x`` is eventually set to ``1``. 

While the initial context provided to the interpreter defined the value of ``x`` to ``2``, the code 
contained in the preamble overrode its value. If you want to make use of the initial context to 
somehow *parametrize* the execution of the statechart while still providing *default* values for 
these parameters, you should either check the existence of the variables before setting their values 
or rely on the ``setdefault`` function that is exposed by the Python code evaluator when a piece of
code is executed (not only in the preamble). 

This function can be used to define (and return) a variable, very similarly to the 
``setdefault`` method of a dictionary. Using this function, we can easily rewrite the preamble 
of our statechart to deal with the optional default values of ``x`` (and ``y`` and ``z`` in this 
example):

.. testcode:: initial_context

    yaml = """statechart:
      name: example
      preamble: |
        x = setdefault('x', 1)
        setdefault('y', 1)  # Value is affected to y implicitly
        setdefault('z', 1)  # Value is affected to z implicitly
      root state:
        name: s
        on entry: print(x, y, z)
    """

    statechart = import_from_yaml(yaml)
    interpreter = Interpreter(statechart, initial_context={'x': 2, 'z': 3})
    interpreter.execute()

.. testoutput:: initial_context

    2 1 3


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


.. note::

    This section explains which are the methods that are called during the execution or evaluation of 
    a piece of code, and is mainly useful if you plan to write your own statechart code interpreter. 
    

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
