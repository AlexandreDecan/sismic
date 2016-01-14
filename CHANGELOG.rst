Changelog
=========

Unreleased
----------

- Add an ``InternalEvent`` subclass for ``model.Event``.
- ``Interpreter.queue`` does not accept anymore an ``internal`` parameter.
   Use an instance of ``InternalEvent`` instead (#20).
- ``Story.story_from_trace`` now ignores internal events (#19).
- ``Interpreter`` now exposes its ``statechart``.

0.15.0 (2015-01-12)
-------------------

- Rename ``Interpreter.send`` to ``Interpreter.queue`` (#18).
- Rename ``evaluator`` module to ``code``.

0.14.3 (2015-01-12)
-------------------

- Add a changelog.
- Include many additional files in package manifest.
