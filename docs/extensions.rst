.. _extensions:

Extensions for Sismic
---------------------

Sismic can be quite easily extended to support other semantics, other code evaluators or even other features.
The `sismic-extensions <https://github.com/AlexandreDecan/sismic-extensions>`__ already provides some extensions.

Feel free to contact us if you developed an extension you would want to be listed here.


sismic-amola
============

This extension provides support to import and export statechart written using AMOLA. This allows statecharts to be
created, edited and displayed with the `ASEME IDE <http://aseme.tuc.gr/>`__.

The extension and its documentation can be found `here <https://github.com/AlexandreDecan/sismic-extensions/sismic_amola>`__.


sismic-semantics
================

This extension provides two variations around the default interpreter: one supporting outer-first/source-state semantics,
and a second giving priority to transitions with event (instead of eventless transitions).

The extension and its documentation can be found `here <https://github.com/AlexandreDecan/sismic-extensions/sismic_semantics>`__.




Implementing other statechart semantics and evaluators
------------------------------------------------------

.. _other_semantics:

Anatomy of the interpreter
==========================

An :py:class:`~sismic.interpreter.Interpreter` makes use of several *private* methods for its initialization and computations.
These methods computes the transition(s) that should be processed, the resulting steps, etc.
These methods can be overridden or combined to define variants of statechart semantics.

.. automethod:: sismic.interpreter.Interpreter._select_event

.. automethod:: sismic.interpreter.Interpreter._select_transitions

.. automethod:: sismic.interpreter.Interpreter._filter_transitions

.. automethod:: sismic.interpreter.Interpreter._sort_transitions

.. automethod:: sismic.interpreter.Interpreter._create_steps

.. automethod:: sismic.interpreter.Interpreter._create_stabilization_step

.. automethod:: sismic.interpreter.Interpreter._apply_step


These methods are all used (even indirectly) by :py:class:`~sismic.interpreter.Interpreter.execute_once`.

.. seealso:: Consider looking at the source of :py:class:`~sismic.interpreter.Interpreter.execute_once` to understand
    how these methods are related and organized.



.. _other_code:


Anatomy of a code evaluator
===========================

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

