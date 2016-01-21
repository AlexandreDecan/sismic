Changelog
=========

0.17.0 (unreleased)
-------------------

Many backward incompatible changes in this update, especially if you used to work with ``model``.
The YAML format of a statechart also changed, look carefully at the changelog and the documentation.

- (Added) YAML: an history state can declare *on entry* and *on exit*.
- (Added) Statechart: new methods to manipulate transitions: ``transitions_from``, ``transitions_to``,
  ``transitions_with``, ``remove_transition`` and ``rotate_transition``.
- (Added) Statechart: new methods to manipulate states: ``remove_state``, ``rename_state``, ``move_state``,
  ``state_for``, ``parent_for``, ``children_for``.
- (Added) Steps: ``__eq__`` for ``MacroStep`` and ``MicroStep``.
- (Added) Stories: ``tell_by_step`` method for a ``Story``.
- (Added) Testing: ``teststory_from_trace`` generates a *step* event at the beginning of each step.
- (Added) Module: a new exceptions hierarchy (see ``exceptions`` module).
  The new exceptions are used in place of the old ones (``Warning``, ``AssertionError`` and ``ValueError``).
- (Changed) YAML: uppermost *states:* should be replaced by *initial state:* and can contain at most one state.
- (Changed) YAML: uppermost *on entry:* should be replaced by *preamble:*.
- (Changed) YAML: initial memory of an history state should be specified using *memory* instead of *initial*.
- (Changed) YAML: contracts for a statechart must be declared on its root state.
- (Changed) Statechart: rename ``StateChart`` to ``Statechart``.
- (Changed) Statechart: rename ``events`` to ``events_for``.
- (Changed) Statechart: ``states`` attribute is now ``Statechart.state_for`` method.
- (Changed) Statechart: ``register_state`` is now ``add_state``.
- (Changed) Statechart: ``register_transition`` is now ``add_transition``.
- (Changed) Statechart: now defines a root state.
- (Changed) Statechart: checks done in ``validate``.
- (Changed) Transition: ``.event`` is a string instead of an ``Event`` instance.
- (Changed) Transition: attributes ``from_state`` and ``to_state`` are renamed into ``source`` and ``target``.
- (Changed) Event: ``__eq__`` takes ``data`` attribute into account.
- (Changed) Event: ``event.foo`` raises an ``AttributeError`` instead of a ``KeyError`` if ``foo`` is not defined.
- (Changed) State: ``StateMixin.name`` is now read-only (use ``Statechart.rename_state``).
- (Changed) State: split ``HistoryState`` into a mixin ``HistoryStateMixin`` and two concrete subclasses,
  namely ``ShallowHistoryState`` and ``DeepHistoryState``.
- (Changed) IO: Complete rewrite of ``io.import_from_yaml`` to load states before transitions. Parameter names have changed.
- (Changed) Module: adapt module hierarchy (no visible API change).
- (Changed) Module: expose module content through ``__all__``.
- (Removed) Transition: ``transitions`` attribute on ``TransitionStateMixin``, use ``Statechart.transitions_for`` instead.
- (Removed) State: ``CompositeStateMixin.children``, use ``Statechart.children_for`` instead.


0.16.0 (2015-01-15)
-------------------

- (Added) An ``InternalEvent`` subclass for ``model.Event``.
- (Added) ``Interpreter`` now exposes its ``statechart``.
- (Added) ``Statechart.validate`` checks that a targeted compound state declares an initial state.
- (Changed) ``Interpreter.queue`` does not accept anymore an ``internal`` parameter.
  Use an instance of ``InternalEvent`` instead (#20).
- (Fixed) ``Story.story_from_trace`` now ignores internal events (#19).
- (Fixed) Condition C3 in ``Statechart.validate``.

0.15.0 (2015-01-12)
-------------------

- (Changed) Rename ``Interpreter.send`` to ``Interpreter.queue`` (#18).
- (Changed) Rename ``evaluator`` module to ``code``.

0.14.3 (2015-01-12)
-------------------

- (Added) Changelog.
- (Fixed) Missing files in MANIFEST.in
