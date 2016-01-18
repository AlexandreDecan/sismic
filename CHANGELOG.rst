Changelog
=========

Unreleased
----------

 - (Added) A new exceptions hierarchy (see ``exceptions`` module).
   The new exceptions are used in place of the old ones (``Warning``, ``AssertionError`` and ``ValueError``).
 - (Added) A *initial code* property (YAML) for statecharts.
 - (Changed) Rename ``model.StateChart`` to ``model.Statechart``.
 - (Changed) ``Statechart.states`` becomes ``Statechart.state_for`` method.
 - (Changed) A statechart defines a root state (*initial state* in YAML).
 - (Changed) ``Transition.event`` is a string instead of an ``Event`` instance.
 - (Removed) Contracts and codes for statecharts (define them on root state instead).
 - (Removed) ``io.export_to_yaml``.
 - (Removed) Cache for several ``model.Statechart`` methods.

0.16.0 (2015-01-15)
-------------------

- (Added) Add an ``InternalEvent`` subclass for ``model.Event``.
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
