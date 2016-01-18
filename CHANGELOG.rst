Changelog
=========

Unreleased
----------

Many backward incompatible changes in this update, especially if you used to work with ``model``.
The YAML format of a statechart also changed, look carefully at the changelog and the documentation.

- (Added) An *initial code* property (YAML) for statecharts.
- (Added) A new exceptions hierarchy (see ``exceptions`` module).
  The new exceptions are used in place of the old ones (``Warning``, ``AssertionError`` and ``ValueError``).
- (Added) Statechart has ``transitions_from``, ``transitions_to`` and ``transitions_with`` methods and
  exposes a ``transitions`` property.
- (Added) Statechart has ``parent_for`` and ``children_for`` methods and exposes a ``states`` property.
- (Added) Statechart has ``remove_state`` and ``remove_transition`` methods.
- (Added) Statechart has a ``rename_state`` method.
- (Changed) Rename ``model.StateChart`` to ``model.Statechart``.
- (Changed) Rename ``Statechart.events`` to ``Statechart.events_for``.
- (Changed) Rename ``Statechart.register_state`` to ``Statechart.add_state`` and ``Statechart.register_transition``.
- (Changed) ``Transition.event`` is a string instead of an ``Event`` instance.
- (Changed) ``Event.__eq__`` includes a comparison of its ``data`` attribute.
- (Changed) ``StateMixin.name`` is now read-only (use ``Statechart.rename_state``).
- (Changed) ``Statechart.states`` becomes ``Statechart.state_for`` method.
- (Changed) A ``Statechart`` has a ``root`` state.
- (Changed) Rewrite ``io.import_from_yaml`` to load states before transitions. This function does not anymore
  accept a ``validate_statechart`` parameter. Its ``validate_schema`` parameter is now ``not ignore_schema``.
- (Changed) Split ``model.HistoryState`` into a mixin ``model.HistoryStateMixin`` and two concrete subclasses,
  namely ``ShallowHistoryState`` and ``DeepHistoryState``.
- (Changed) Adapt module hierarchy (no API change, but see ``code`` module).
- (Changed) Define ``__all__`` in each module, to restrict usage of imported stuff.
- (Removed) Contracts and codes for statecharts (define them on root state instead).
- (Removed) Cache for several ``model.Statechart`` methods.
- (Removed) ``Statechart.validate`` (C1, C2 and C4 are now included in the construction process).
- (Removed) ``CompositeStateMixin.children``, use ``Statechart.children_for`` instead.
- (Removed) ``io.export_to_yaml``.
- (Removed) ``transitions`` attribute on ``TransitionStateMixin``, use ``Statechart.transitions_for`` instead.

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
