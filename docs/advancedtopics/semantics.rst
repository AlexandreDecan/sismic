
.. _other_semantics:

Implementing other statechart semantics
=======================================

An :py:class:`~sismic.interpreter.Interpreter` makes use of several *private* methods for its initialization and computations.
These methods computes the transition(s) that should be processed, the resulting steps, etc.
These methods can be overridden or combined easily to define other variants of the statechart semantics.

.. automethod:: sismic.interpreter.Interpreter._select_eventless_transitions

.. automethod:: sismic.interpreter.Interpreter._select_transitions

.. automethod:: sismic.interpreter.Interpreter._sort_transitions

.. automethod:: sismic.interpreter.Interpreter._compute_transitions_steps

.. automethod:: sismic.interpreter.Interpreter._execute_step

.. automethod:: sismic.interpreter.Interpreter._compute_stabilization_step


These methods are called directly (or not) by :py:class:`~sismic.interpreter.Interpreter.execute_once`.

.. seealso:: Consider looking at the source of :py:class:`~sismic.interpreter.Interpreter.execute_once` to understand
    how these methods are related and organized.



Example: Outer-first/source-state semantics
-------------------------------------------

For example, in order to obtain an outer-first/source-state semantics (instead of the
inner-first/source-state one that Sismic provides by default),
one should subclass :py:class:`~sismic.interpreter.Interpreter`
and override :py:class:`~sismic.interpreter.Interpreter._select_eventless_transitions` and
:py:class:`~sismic.interpreter.Interpreter._select_transitions`.

.. note:: Actually, as the former relies on the later, the changes will only concern the traversal order in the
    :py:class:`~sismic.interpreter.Interpreter._select_transitions` method.


Example: Semantics where internal events have no priority
---------------------------------------------------------

If you want to change the semantics of Sismic so that internal events no longer have
priority over external events, it suffices to override the :py:meth:`~sismic.interpreter.Interpreter.queue` method
and to replace ``self._events.appendleft(event)`` by ``self._events.append(event)`` in the
``if isinstance(event, InternalEvent):`` part.


Example: Custom way to deal with non-determinism
------------------------------------------------

If you want to change the way the Sismic semantics deals with non-determinism,
for example because it deviates from the semantics given by SCXML or Rhapsody
(remember :ref:`semantic`), you can implement your own variant for dealing with non-determinism.
The method :py:meth:`~sismic.interpreter.Interpreter._sort_transitions` is where the whole job is done:

1. It looks for non-determinism in (non-parallel) transitions,
2. It looks for conflicting transitions in parallel transitions,
3. It sorts the kept transitions based on our semantic.

According to your needs, adapt the content of this method.

