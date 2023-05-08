Changelog
=========

1.6.5 (2023-05-08)
------------------

 - (Fixed) Dropped support for Python 3.5 and 3.6 since they are no longer supported by ``ruamel.yaml`` used internally.


1.6.4 (2023-03-03)
------------------

 - (Fixed) Invalid output of ``export_to_plantuml`` if ``statechart_preamble`` is enabled, with plantuml-1.2022.12 (`#119 <https://github.com/AlexandreDecan/sismic/issues/119>`__).


1.6.3 (2021-08-05)
------------------

 - (Fixed) ``Statechart.remove_state`` no longer resets all initial states and all history states (`#110 <https://github.com/AlexandreDecan/sismic/pull/110>`__, Rigó Ernő).


1.6.2 (2020-12-29)
------------------

 - (Added) Support for Python 3.9.
 - (Fixed) Remove deprecated import from ``collections`` (`#101 <https://github.com/AlexandreDecan/sismic/pull/101>`__).
 - (Fixed) Remove deprecated ``threading.isAlive`` used in ``sismic.runner.AsyncRunner``.


1.6.1 (2020-07-10)
------------------

 - (Fixed) Remove dependency to ``typing`` since it is no longer required for Python 3.5 and prevents the installation of Sismic.


1.6.0 (2020-03-28)
------------------

 - (Added) Arrows to represent initial memory of an history state for ``sismic.io.export_to_plantuml`` (`#96 <https://github.com/AlexandreDecan/sismic/pull/96>`__).
 - (Fixed) Issue preventing initial memory to be defined for history states (`#95 <https://github.com/AlexandreDecan/sismic/pull/95>`__).


1.5.0 (2020-03-09)
------------------

 - (Added) A ``sismic-plantuml`` command-line utility to access ``sismic.io.export_to_plantuml``.


1.4.2 (2019-07-19)
------------------

 - (Fixed) Transitions are no longer duplicated when calling ``copy_from_statechart``  (`#91 <https://github.com/AlexandreDecan/sismic/issues/91>`__).


1.4.1 (2019-01-15)
------------------

The internals required to expose time and event-related predicates in a ``PythonEvaluator`` are moved
to the ``Interpreter`` instead of being handled by context providers. This eases the implementation by other
code evaluators of uniform semantics for these predicates. This change does not affect Sismic public API.

 - (Deprecated) Internal module ``sismic.code.context``.


1.4.0 (2018-10-21)
------------------

This new release contains many internal changes. While the public API is stable and/or backwards
compatible, expect some breaking changes if you relied on Sismic internal API.

A new binding/monitoring system has been deployed on ``Interpreter``, allowing listeners to be notified about
meta-events. Listeners are simply callables that accept meta-events instances.

 - (Added) An ``Interpreter.attach`` method that accepts any callable. Meta-events raised by the interpreter
   are propagated to attached listeners.
 - (Added) An ``Interpreter.detach`` method to detach a previously attached listener.
 - (Added) Module ``sismic.interpreter.listener`` with two convenient listeners for the newly introduced ``Interpreter.attach`` method.
   The ``InternalEventListener`` identifies sent events and propagates them as external events. The ``PropertyStatechartListener``
   propagates meta-events, executes and checks property statecharts.
 - (Changed) ``Interpreter.bind`` is built on top of ``attach`` and ``InternalEventListener``.
 - (Changed) ``Interpreter.bind_property_statechart`` is built on top of ``attach`` and ``PropertyStatechartListener``.
 - (Changed) Meta-Event *step started* has a ``time`` attribute.
 - (Changed) Property statecharts are checked for each meta-events, not only at the end of the step.
 - (Changed) Meta-events *step started* and *step ended* are sent even if no step can be processed.
 - (Deprecated) Passing an interpreter to ``bind_property_statechart`` is deprecated, use ``interpreter_klass`` instead.

Time and event related predicates were extracted from ``PythonEvaluator`` to ease their reuse.
They can be found in ``TimeContextProvider`` and ``EventContextProvider`` of ``sismic.code.context`` and
rely on the new monitoring system:

 - (Added) ``TimeContextProvider`` and ``EventContextProvider`` in ``sismic.code.context`` that
   exposes most of the predicates that are used in ``PythonEvaluator``.
 - (Added) A ``setdefault`` function that can be used in the preamble and actions of a
   statechart to assign a default value to a variable.
 - (Changed) Most predicates exposed by ``PythonEvaluator`` are implemented by context providers.
 - (Deprecated) ``on_step_starts`` method of an ``Evaluator``.

We also refactored how events are passed and processed by the interpreter.
The main visible consequences are:

 - (Added) Event parameters can be directly passed to ``Interpreter.queue``.
 - (Fixed) Internal events are processed before external ones (regression introduced in 1.3.0).
 - (Fixed) Optional transition for ``testing.transition_is_processed``, as promised by its documentation but not implemented.
 - (Removed) Internal module ``sismic.interpreter.queue``.
 - (Deprecated) ``DelayedEvent``, use ``Event`` with a ``delay`` parameter instead.
 - (Deprecated) BDD step *delayed event sent*, use *event sent* instead.

And some other small changes:

 - (Added) Documentation about concurrently running multiple statecharts.
 - (Changed) State invariants are checked even if no step can be processed.
 - (Fixed) Hook-errors reported by ``sismic-bdd`` CLI are a little bit more verbose (`#81 <https://github.com/AlexandreDecan/sismic/issues/81>`__).


1.3.0 (2018-07-06)
------------------

Priority can be defined on transitions, allowing to simulate default transitions and to break non-deterministic
situations when many transitions are triggered for a single source state:

 - (Added) Priority can be set for transitions (using *low*, *high* or any integer in yaml). Transitions
   are selected according to their priorities (still following eventless and inner-first/source state semantics).
 - (Added) Interpreter's ``_select_transitions`` gets two new parameters, ``eventless_first`` and ``inner_first``.
   Both default to ``True`` and can be used in subclasses to change the default semantics of the interpreter.

The current time of an interpreter is now clock-based driven, thanks to the ``Clock`` base class and its implementations.

 - (Added) A ``sismic.clock`` module with a ``Clock`` base class and three direct implementations,
   namely ``SimulatedClock``, ``UtcClock`` and ``SynchronizedClock``. A ``SimulatedClock`` allows to manually or automatically
   change the time, while a ``UtcClock`` as the expected behaviour of a wall-clock and a ``SynchronizedClock`` is a clock that
   synchronizes with another interpreter. ``Clock`` instances are used by the interpreter to get the current time during execution.
   See documentation for more information.
 - (Added) An ``Interpreter.clock`` attribute that stores an instance of the newly added ``Clock`` class.
 - (Changed) ``interpreter.time`` represents the time of the last executed step, not the current
   time. Use ``interpreter.clock.time`` instead.
 - (Deprecated) Setting ``Interpreter.time`` is deprecated, set time with ``Interpreter.clock.time`` instead.

Queued events can be delayed when they are added to the interpreter event queue.

 - (Added) Delayed events are supported through ``DelayedEvent`` and ``DelayedInternalEvent``. If
   a delayed event with delay *d* is queued or sent by an interpreter at time *t*, it will not be processed
   unless `execute` or `execute_once` is called after the current clock exceeds *t + d*.
 - (Added) Property statecharts receive a *delayed event sent* meta-event when a delayed event is sent by a statechart.
 - (Added) Delayed events can be sent from within a statechart by specifying a ``delay`` parameter to the ``sent`` function.
 - (Added) An ``EventQueue`` class (in ``sismic.interpreter.queue``) that controls how (delayed) events are handled by an interpreter.

A new interpreter runner that benefit from the clock-based handling of time and delayed events:

 - (Added) An ``AsyncRunner`` in the newly added ``runner`` module to asynchronously run an interpreter at regular interval.
 - (Changed) ``helpers.run_in_background`` no longer synchronizes the interpreter clock.
   Use the ``start()`` method of ``interpreter.clock`` or an ``UtcClock`` instance instead.
 - (Deprecated) ``helpers.run_in_background`` is deprecated, use ``runner.AsyncRunner`` instead.

And other small changes:

 - (Added) A ``sismic.testing`` module containing some testing primitives to ease the writing of unit tests.
 - (Changed) ``Interpreter.queue`` does not longer accept ``InternalEvent``.
 - (Fixed) State *on entry* time (used for ``idle`` and ``after``) is set after the *on entry*
   action is executed, making the two predicates more accurate when long-running actions are
   executed when a state is entered. Similarly, ``idle`` is reset after the action of a transition
   is performed, not before.
 - (Changed) Drop official support for Python 3.4.


1.2.2 (2018-06-21)
------------------

- (Fixed) Event shouldn't be exposed when guards of eventless transitions are evaluated (regression
  introduced in version 1.2.1).
- (Changed) Improve performances when selecting transitions that could/will be triggered.


1.2.1 (2018-06-19)
------------------

- (Fixed) Transitions are evaluated according to their event (eventless ones first) and
  inner-first/source state semantics, allowing to bypass many useless guard evaluations.


1.2.0 (2018-06-11)
------------------

- (Added) A ``notify`` function that can be used in the action code fragments of a statechart to send user-defined
  meta-events to the bound property statecharts (`#67 <https://github.com/AlexandreDecan/sismic/issues/67>`__).


1.1.2 (2018-05-09)
------------------

- (Fixed) Interpreter instances can be serialized using ``pickle`` (`#66 <https://github.com/AlexandreDecan/sismic/issues/66>`__).


1.1.1 (2018-04-26)
------------------

- (Fixed) Whitespaces in event parameters used in BDD steps are stripped before they are evaluated.


1.1.0 (2018-04-23)
------------------

- (Added) ``Interpreter._select_event`` accepts an additional parameter ``consume`` that can be used
  to select an event without consuming it.
- (Added) Documentation for extensions, and two (not included in Sismic!) extensions providing import/export
  with AMOLA, and new semantics for the interpreter.
- (Fixed) Final states remain in the active configuration unless they are all children of the root state. In this
  case, statechart execution is stopped. Previously, if all leaf states of the active configuration were final states,
  the execution stopped even if these final states were nested in an orthogonal or compound state. The corrected
  behavior strictly adheres to SCXML 1.0 semantics. This could be a backward incompatible change if you explicitly
  relied on the previously wrong behaviour.


1.0.1 (2018-04-18)
------------------

- (Fixed) BDD steps that involve a state raise a ``StatechartError`` if state does not exist.
  This prevents *state X is active* (and its variants) to fail, e.g., because *X* is misspelled.


1.0.0 (2018-04-11)
------------------

After more than two years of development, Sismic is stable enough to be released in version 1.0.0.
Consequently, Sismic will adhere to semantic versioning (see `semver.org <https://semver.org/>`__), meaning that
breaking changes will only occur in major releases, backward compatible changes in minor releases, and bug fixes in
patches.


0.26.9 (2018-04-03)
-------------------

- (Fixed) ``based_on`` for ``export_to_plantuml`` correctly takes into account states whose name contains whitespaces.
- (Fixed) ``export_to_plantuml`` properly exports transition with no event, no guard and no action.
- (Changed) ``export_to_yaml`` does not add quotes by default.


0.26.8 (2018-03-23)
-------------------

- (Added) ``import_from_yaml`` accepts a ``filepath`` argument.
- (Added) ``based_on`` and ``based_on_filepath`` parameters for ``export_to_plantuml`` so a previously generated
  PlantUML file can be used as a basis for a new one (including its modifications related to the direction and length
  of transitions).


0.26.7 (2018-03-21)
-------------------

- (Removed) Nested context (ie. nested variable scopes) for the Python code evaluator.
- (Fixed) BDD step *expression {expression} holds*.


0.26.6 (2018-03-17)
-------------------

- (Changed) Export to PlantUML uses short arrows by default.
- (Changed) Many improvements related to the transitions when using ``export_to_plantuml``.


0.26.4 (2018-03-16)
-------------------

- (Added) ``sismic.bdd.execute_bdd`` can be used to execute BDD tests programmatically.
- (Added) ``sismic.bdd.__main__`` is the CLI interface for ``sismic-behave`` and can now be executed using
  ``python -m sismic.bdd`` too if sismic is available but not installed.
- (Added) Many tests for BDD steps.
- (Changed) ``Statechart.copy_from_statechart`` has only its first argument that can be provided by position.
  The remaining ones (esp. ``source`` and ``replace``) should be provided by name.
- (Fixed) Sismic requires behave >= 1.6.0.
- (Fixed) Older versions of typing do not contain ``Deque``.
- (Removed) ``sismic.bdd.cli.execute_behave``, subsumed by ``sismic.bdd.execute_bdd``.


0.26.3 (2018-03-15)
-------------------

- (Added) ``sismic.bdd`` exposes ``sismic.bdd.cli.execute_behave`` function to programmatically use ``sismic-bdd``.
- (Changed) ``execute_behave`` function has only two required parameters, and the remaining ones (that have default
  values) can only be set by name, not by position.
- (Changed) ``action_alias`` and ``assertion_alias`` of module ``sismic.bdd.steps`` are renamed to ``map_action``
  and ``map_assertion`` and are directly available from ``sismic.bdd``.


0.26.2 (2018-03-15)
-------------------

- (Fixed) Step *Given/when I repeat "{step}" {repeat} times* requires *step* to be provided with no Gherkin
  keyword. The current keyword (either *given* or *when*) is automatically used.
- (Fixed) Escape expression in *then expression "{expression}" holds* and its negative counterpart.


0.26.0 (2018-03-15)
-------------------

Sismic support for BDD was completely rewritten. The CLI is now ``sismic-bdd``, pointing to the ``cli`` submodule of
the newly created ``sismic.bdd`` module. All steps that are related to Sismic internals were removed, and only
steps that manipulate the statechart are kept. Check the documentation and ``sismic.bdd.steps`` for more information.
Execution semantics have slightly changed but shouldn't have any impact when running BDD tests.
Predefined steps can be easily extended thanks to the ``action_alias`` and ``assertion_alias`` helpers.
See documentation for more details.

- (Changed) ``sismic-behave`` CLI is now ``sismic-bdd``.
- (Removed) ``--coverage`` option from ``sismic-behave`` CLI.
- (Changed) Rename ``sismic.testing`` to ``sismic.bdd``, and ``sismic.testing.behave`` to ``sismic.bdd.cli``.
- (Changed) A new list of predefined steps, available in ``sismic.bdd.steps``, see documentation.
- (Changed) A "when" step is now required before any "then" step. The "then" steps assert on what happens during
  the "when" steps, and not on the whole execution or the last step as before.
- (Added) ``sismic.bdd.steps`` provides ``action_alias`` and ``assertion_alias`` to make defining new steps easy.
- (Changed) BDD tests are directly executed by ``pytest`` (instead of being triggered by Travis-CI).

Other changes:

- (Changed) ``Interpreter.bind_property`` becomes ``Interpreter.bind_property_statechart``.
- (Changed) ``helpers.coverage_from_trace`` returns a dict with "entered states", "exited states" and
  "processed transitions".
- (Removed) Unused ``io.text``.


0.25.3 (2018-03-13)
-------------------

- (Fixed) ``export_to_dict`` (and by extension, ``export_to_yaml``) didn't export transition contracts.
- (Changed) All the tests are now written using ``pytest`` instead of ``unittest``.


0.25.2 (2018-03-11)
-------------------

- (Added) Make ``Event``, ``InternalEvent`` and ``MetaEvent`` available from ``interpreter`` as well.
- (Changed) Move ``helpers`` from ``sismic.interpreter.helpers`` to ``sismic.helpers``.
- (Removed) Remove module ``stories``, not really required anymore.


0.25.1 (2018-03-09)
-------------------

- (Added) Full equality comparison (``__eq__``) for states and transitions (including all relevant attributes).
- (Added) ``Interpreter.queue`` also accepts an event name in addition to an ``Event`` instance.
- (Added) ``Interpreter.queue`` accepts more than one event (or name) at once.
- (Changed) ``Evaluator.execute_onentry`` and ``execute_onexit`` become ``execute_on_entry`` and ``execute_on_exit``.
- (Changed) Many type annotations were added or fixed.
- (Changed) ``Interpreter.bind`` can no longer be chained.


0.25.0 (2018-03-09)
-------------------

Property statecharts do not require anymore the use of an ``ExecutionWatcher`` and are now directly supported
by the interpreter. The documentation contains a new page, *Monitoring properties*, that explains how to monitor
properties at runtime and provides some examples of property statecharts.

- (Added) Property statechart can be bound to an interpreter with ``interpreter.bound_property`` method, that accepts
  either a ``Statechart`` or an ``Interpreter`` instance.
- (Added) A ``PropertyStatechartError`` that is raised when a property statechart reaches a final state.
- (Added) A ``MetaEvent`` class to represent meta-events sent by the interpreter for property statechart checking.
- (Added) ``Interpreter._notify_property(event_name, **kwargs)`` and ``Interpreter._check_properties(macro_step)`` that
  are used internally to respectively send meta-events to bound properties, and to check these properties.
- (Changed) ``Interpreter.raise_event`` is now ``Interpreter._raise_event`` as it's not supposed to be part of the public API.
- (Removed) ``sismic.testing`` module was removed (including the ``ExecutionWatcher`` and ``TestStoryFromTrace``).
- (Removed) BDD steps related to the execution watcher, in ``sismic.testing.steps``.
- (Fixed) ``Interpreter.time`` cannot be set to a lower value than the current one (ie. time is monotonic).
- (Fixed) A statechart preamble cannot be used to send events.


0.24.3 (2018-03-08)
-------------------

- (Fixed) ``ExecutionWatcher.stop()`` was not called at the end of the execution when ``sismic-behave`` was
  called with ``--properties``.
- (Removed) Unused dependency on ``pyparsing``.


0.24.2 (2018-02-27)
-------------------

- (Added) ``sismic.io`` contains an ``export_to_plantuml`` function to export a statechart to PlantUML.
- (Added) ``sismic-behave`` accepts a ``--properties`` argument, pointing to a list of YAML files containing
  property statecharts that will be checked during execution (in a fail fast mode).
- (Changed) ``sismic.io.export_to_yaml`` accepts an additional ``filepath`` argument.
- (Fixed) Whitespaces in strings are trimmed when using ``import_from_dict`` (and hence, using ``import_from_yaml``).


0.23.1 (2018-02-20)
-------------------

- (Fixed) An exited state is removed from the current configuration before its postconditions are checked.
- (Removed) Sequential conditions that were introduced in 0.22.0.


0.22.11 (2017-01-12)
--------------------

- (Fixed) Path error when using ``sismic-behave`` on Windows.


0.22.10 (2016-11-25)
--------------------

- (Added) A ``--debug-on-error`` parameter for ``sismic-behave``.


0.22.9 (2016-11-25)
-------------------

- (Fixed) Behave step "Event x should be fired" now checks that the event was fired during the last execution.


0.22.8 (2016-10-19)
-------------------

- (Fixed) YAML values like "1", "1.0", "yes", "True" are converted to strings, not to int, float and bool respectively.
- (Changed) ``ruamel.yaml`` replaces ``pyyaml`` as supported YAML parser.
- (Changed) Use ``schema`` instead of ``pykwalify`` (which unfortunately freezes its dependencies versions)
  to validate (the structure of) YAML files.
- (Changed) ``import_from_yaml`` raises ``StatechartError`` instead of ``SchemaError`` if it cannot validate given
  YAML against the predefined schema.


0.22.7 (2016-08-19)
-------------------

- (Added) A new helper ``coverage_from_trace`` that returns coverage information (in absolute numbers) from a trace.
- (Added) Parameter ``fails_fast`` (default is ``False``, behavior preserved) for ``ExecutionWatcher.watch_with``
  methods. This parameter allows the watcher to raise an ``AssertionError`` as soon as the added watcher reaches a
  final configuration.
- (Changed) ``StateMixin``, ``Transition`` and ``Event``'s ``__eq__`` method returns a ``NotImplemented`` object
  if the other object involved in the comparison is not an instance of the same class, meaning that ``Event('a') == 1``
  now raises a ``NotImplementedError`` instead of being ``False``.


0.22.6 (2016-08-03)
-------------------

- (Changed) ``Event``, ``MacroStep``, ``MicroStep``, ``StateMixin``, ``Transition``, ``Statechart`` and
  ``Interpreter``'s ``__repr__`` returns a valid Python expression.
- (Changed) The context returned by a ``PythonEvaluator`` (and thus by the default ``Interpreter``) exhibits
  nested variables (the ones that are not defined in the preamble of a statechart). Those variables are prefixed by
  the name of the state in which they are declared, to avoid name clashing.
- (Changed) Context variables are sorted in exceptions'``.__str__`` methods.


0.22.4 (2016-07-08)
-------------------

- (Added) ``sismic-behave`` CLI now accepts a ``--steps`` parameter, which is a list of file paths containing the steps
  implementation.
- (Added) ``sismic-behave`` CLI now accepts a ``--show-steps`` parameter, which list the steps (equivalent to
  Behave's overriden ``--steps`` parameter).
- (Added) ``sismic-behave`` now returns an appropriate exit code.
- (Changed) Reorganisation of ``docs/examples``.
- (Fixed) Coverage data for ``sismic-behave`` takes the initialization step into account (regression
  introduced in 0.21.0).


0.22.3 (2016-07-06)
-------------------

- (Added) ``sent`` and ``received`` are also available in preconditions and postconditions.


0.22.2 (2016-07-01)
-------------------

- (Added) ``model.Event`` is now correctly pickled, meaning that Sismic can be used in a multiprocessing environment.


0.22.1 (2016-06-29)
-------------------

- (Added) A *event {event_name} should not be fired* steps for BDD.
- (Added) Both ``MicroStep`` and ``MacroStep`` have a list ``sent_events`` of events that were sent during the step.
- (Added) Property statecharts receive a ``event sent`` event when an event is sent by the statechart under test.
- (Changed) Events fired from within the statechart are now collected and sent at the end of the current micro step,
  instead of being immediately sent.
- (Changed) Invariants and sequential contracts are now evaluated ordered by their state's depth


0.22.0 (2016-06-13)
-------------------

- (Added) Support for sequential conditions in contracts (see documentation for more information).
- (Added) Python code evaluator: *after* and *idle* are now available in postconditions and invariants.
- (Added) Python code evaluator: *received* and *sent* are available in invariants.
- (Added) An ``Evaluator`` has now a ``on_step_starts`` method which is called at the beginning of each step, with
  the current event (if any) being processed.
- (Added) ``Interpreter.raise_event`` to send events from within the statechart.
- (Added) A ``copy_from_statechart`` method for a ``Statechart`` instance that allows to copy (part of) a statechart
  into a state.
- (Added) Microwave controller example (see *docs/examples/microwave.[yaml|py]*).
- (Changed) Events sent by a code evaluator are now returned by the ``execute_*`` methods instead of being
  automatically added to the interpreter's queue.
- (Changed) Moved ``run_in_background`` and ``log_trace`` from ``sismic.interpreter`` to the newly added
  ``sismic.interpreter.helpers``.
- (Changed) Internal API changes: rename ``self.__x`` to ``self._x`` to avoid (mostly) useless name mangling.


0.21.0 (2016-04-22)
-------------------

Changes for ``interpreter.Interpreter`` class:

- (Removed) ``_select_eventless_transition`` which is a special case of ``_select_transition``.
- (Added) ``_select_event``, extracted from ``execute_once``.
- (Added) ``_filter_transitions``, extracted from ``_select_transition``.
- (Changed) ``_execute_step`` is now ``_apply_step``.
- (Changed) ``_compute_stabilization_step`` is now ``_create_stabilization_step`` and accepts a list of state names
- (Changed) ``_compute_transitions_step`` is now ``_create_steps``.
- (Changed) Except for the ``statechart`` parameter, all the parameters for ``Interpreter``'s constructor can now be
  only provided by name.
- (Fixed) Contracts on a transition are checked (if not explicitly disabled) even if the transition has no *action*.
- (Fixed) ``Evaluator.execute_action`` is called even if the transition has no *action*.
- (Fixed) States are added/removed from the active configuration as soon as they are entered/exited.
  Previously, the configuration was only updated at the end of the step (and could possibly lead to inaccurate results
  when using ``active(name)`` in a ``PythonEvaluator``).

The default ``PythonEvaluator`` class has been completely rewritten:

- (Changed) Code contained in states and/or transitions is now executed with a local context instead of a
  global one. The local context of a state is built upon the local context of its parent, and so one until the local
  context of the statechart is reached. This should facilitate the use of dummy variables in nested states
  and transitions.
- (Changed) The code is now compiled (once) before is evaluation/execution. This should increase performance.
- (Changed) The frozen context of a state (ie. ``__old__``) is now computed only if contracts are checked, and only
  if at least one invariant or one postcondition exists.
- (Changed) The ``initial_context`` parameter of ``Evaluator``'s constructor can now only be provided by name.
- (Changed) The ``additional_context`` parameter of ``Evaluator._evaluate_code`` and ``Evaluator._execute_code`` can
  now only be provided by name.

Miscellaneous:

- (Fixed) Step *I load the statechart* now executes (once) the statechart in order to put it into a stable
  initial configuration (regression introduced in 0.20.0).

0.20.5 (2016-04-14)
-------------------

- (Added) Type hinting (see PEP484 and mypy-lang project)

0.20.4 (2016-03-25)
-------------------

- (Changed) Statechart testers are now called property statechart.
- (Changed) Property statechart can describe *desirable* and *undesirable* properties.

0.20.3 (2016-03-22)
-------------------

- (Changed) Step *Event x should be fired* now checks sent events from the beginning of the test, not only for the last
  executed step.
- (Fixed) Internal events that are sequentially sent are now sequentially consumed (and not anymore in reverse order).

0.20.2 (2016-02-24)
-------------------

- (Fixed) ``interpreter.log_trace`` does not anymore log empty macro step.

0.20.1 (2016-02-19)
-------------------

- (Added) A *step ended* event at the end of each step in a tester story.
- (Changed) The name of the events and attributes that are exposed in a tester story has changed.
  Consult the documentation for more information.

0.20.0 (2016-02-17)
-------------------

- (Added) Module ``interpreter`` provides a ``log_trace`` function that takes an interpreter instance and returns
  a (dynamic) list of executed macro steps.
- (Added) Module ``testing`` exposes an ``ExecutionWatcher`` class that can be used to check statechart properties
  with tester statecharts at runtime.
- (Changed) ``Interpreter.__init__`` does not anymore stabilize the statechart. Stabilization is done during the
  first call of ``execute_once``.
- (Changed) ``Story.tell`` returns a list of ``MacroStep`` (the *trace*) instead of an ``Interpreter`` instance.
- (Changed) The name of some attributes of an event in a tester story changes (e.g. *event* becomes *consumed_event*,
  *state* becomes *entered_state* or *exited_state* or *source_state* or *target_state*).
- (Removed) ``Interpreter.trace``, as it can be easily obtained from ``execute_once`` or using ``log_trace``.
- (Removed) ``Interpreter.__init__`` does not accept an ``initial_time`` parameter.
- (Fixed) Parallel state without children does not any more result into an infinite loop.

0.19.0 (2016-02-10)
-------------------

- (Added) BDD can now output coverage data using ``--coverage`` command-line argument.
- (Changed) The YAML definition of a statechart must use *root state:* instead of *initial state:*.
- (Changed) When a contract is evaluated by a ``PythonEvaluator``, ``__old__.x`` raises an ``AttributeError`` instead
  of a ``KeyError`` if ``x`` does not exist.
- (Changed) Behave is now called from Python instead of using a subprocess and thus allows debugging.

0.18.1 (2016-02-03)
-------------------

- (Added) Support for behavior-driven-development using Behave.

0.17.3 (2016-01-29)
-------------------

- (Added) An ``io.text.export_to_tree`` that returns a textual representation of the states.
- (Changed) ``Statechart.rename_to`` does not anymore raise ``KeyError`` but ``exceptions.StatechartError``.
- (Changed) Wheel build should work on Windows

0.17.1 (2016-01-25)
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


0.16.0 (2016-01-15)
-------------------

- (Added) An ``InternalEvent`` subclass for ``model.Event``.
- (Added) ``Interpreter`` now exposes its ``statechart``.
- (Added) ``Statechart.validate`` checks that a targeted compound state declares an initial state.
- (Changed) ``Interpreter.queue`` does not accept anymore an ``internal`` parameter.
  Use an instance of ``InternalEvent`` instead (#20).
- (Fixed) ``Story.story_from_trace`` now ignores internal events (#19).
- (Fixed) Condition C3 in ``Statechart.validate``.

0.15.0 (2016-01-12)
-------------------

- (Changed) Rename ``Interpreter.send`` to ``Interpreter.queue`` (#18).
- (Changed) Rename ``evaluator`` module to ``code``.

0.14.3 (2016-01-12)
-------------------

- (Added) Changelog.
- (Fixed) Missing files in MANIFEST.in
