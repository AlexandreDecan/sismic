Changelog
=========

Unreleased
----------

Many backward incompatible changes in this update, look carefully at the changelog and the documentation.

 - (Added) A new exceptions hierarchy (see ``exceptions`` module).
   The new exceptions are used in place of the old ones (``Warning``, ``AssertionError`` and ``ValueError``).
 - (Added) An *initial code* property (YAML) for statecharts.
 - (Added) Statechart has ``transitions_from``, ``transitions_to`` and ``transitions_with`` methods and
   exposes a ``transitions`` property.
 - (Added) Statechart has ``parent_for`` and ``children_for`` methods and exposes a ``states`` property.
 - (Changed) ``Transition.event`` is a string instead of an ``Event`` instance.
 - (Changed) ``Transition.from_state``, ``Transition.to_state`` and ``StateMixin.name`` are protected.
 - (Changed) Rename ``model.StateChart`` to ``model.Statechart``.
 - (Changed) ``Statechart.states`` becomes ``Statechart.state_for`` method.
 - (Changed) A statechart defines a root state (*initial state* in YAML).
 - (Changed) Rename ``Statechart.events`` to ``Statechart.events_for``.
 - (Changed) Rename ``Statechart.register_state`` to ``Statechart.add_state`` and ``Statechart.register_transition``
   to ``Statechart.add_transition``.
 - (Changed) Rewrite ``io.import_from_yaml`` to load states before transitions. This function does not anymore
   accept a ``validate_statechart`` parameter. Its ``validate_schema`` parameter is now ``not ignore_schema``.
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
