Defining statecharts
====================

About statecharts
-----------------

Statecharts are a well-known visual language for modeling the executable behavior of complex reactive event-based systems.
They were invented in the 1980s by David Harel, and have gained a more widespread adoption since they became part of
the UML modeling standard.

Statecharts offer more sophisticated modeling concepts than the more classical state diagrams of finite state machines.
For example, they support hierarchical composition of states, orthogonal regions
to express parallel execution, guarded transitions, and actions on transitions or states. Different flavours of
executable semantics for statecharts have been proposed in the literature and in existing tools.

.. _yaml_statecharts:

Defining statecharts in YAML
----------------------------

Statecharts can be defined using a YAML format.

A YAML definition of a statechart can be easily imported to a :py:class:`~sismic.model.StateChart` instance.
The module :py:mod:`sismic.io` provides a convenient loader :py:func:`~sismic.io.import_from_yaml`
which takes a textual YAML definition of a statechart. It also provides ways to export statechart to YAML.

.. automodule:: sismic.io
    :members: import_from_yaml, export_to_yaml

For example:

.. code:: python

    from sismic import io, model

    with open('examples/concrete/elevator.yaml') as f:
        statechart = io.import_from_yaml(f)
        assert isinstance(statechart, model.StateChart)


Although the parser is quite robut and should warn about most syntaxic problems, a :py:class:`~sismic.model.StateChart` instance has a
:py:meth:`~sismic.model.StateChart.validate` method that can perform numerous other checks.
This method either returns ``True`` if the statechart *seems* to
be valid, or raises an ``AssertionError`` exception with a meaningful message.


Statechart elements
*******************

This section explains how the elements that compose a statechart can be defined using YAML.
If you are not familiar with YAML, have a look at `YAML official documentation <http://yaml.org/spec/1.1/>`__.


Statechart
^^^^^^^^^^

The root of the YAML file **must** declare a statechart:

.. code:: yaml

    statechart:
      name: Name of this statechart
      initial: name of the initial state


The ``name`` and the ``initial`` state are mandatory.
You can declare code to execute on the initialization of the statechart using ``on entry``, as follows:

.. code:: yaml

    statechart:
      name: with code
      initial: s1
      on entry: x = 1


Code can be written on multiple lines:

.. code:: yaml

    on entry: |
      x = 1
      y = 2


States
^^^^^^

A statechart has to declare a (nonempty) list of states using ``states``.
Each state consist of at least a ``name``. Depending on the state type, several other fields can be declared.

.. code:: yaml

    statemachine:
      name: with state
      initial: s1
      states:
        - name: s1


Entry and exit actions
^^^^^^^^^^^^^^^^^^^^^^

For each state, it is possible to specify the code that has to be executed when entering and leaving the
state using ``on entry`` and ``on exit`` as follows:

.. code:: yaml

    - name: s1
      on entry: x += 1
      on exit: |
        x -= 1
        y = 2

Final states
^^^^^^^^^^^^

A state that declares a ``type: final`` property is a *final state*:

.. code:: yaml

    - name: s1
      type: final

Shallow and deep history sates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A state that declares a ``type: shallow history`` property is an *shallow history state*.
If you want an history state to follow the deep semantic, set ``type`` to ``deep history``.

.. code:: yaml

    - name: history state
      type: shallow history
      deep: True

An history state can optionally define an initial memory using ``initial``.

.. code:: yaml

  - name: history state
    type: deep history
    initial: s1

Importantly, the ``initial`` memory value **must** refer to a parent's substate.

Compound states
^^^^^^^^^^^^^^^

A state that is neither a final state nor an history state can contain nested states.
Such a state is a *compound state*.

.. code:: yaml

  - name: compound state
    states:
      - name: nested state 1
      - name: nested state 2
        states:
          - name: nested state 2a

Notice that PySS does not explicit the concept of *region*.
As a region is mainly a logical set of nested states, it can be emulated using a compound state.

Orthogonal states
^^^^^^^^^^^^^^^^^

*Orthogonal states* (sometimes referred as *parallel states*) must declare their nested states using ``parallel states``
instead of ``states``.

.. code:: yaml

  statechart:
    name: Concurrent processes state machine
    initial: processes
    states:
      - name: processes
        parallel states:
          - name: process 1
          - name: process 2

A compound orthogonal state can not be declared at top level, and should be nested in a compound state, as
illustrated in the previous example. In other words, it is not allowed to define ``parallel states``
instead of ``states`` in this previous example.

Transitions
^^^^^^^^^^^

States, compound states and parallel states can declare *transitions* with ``transitions``:

.. code:: yaml

  - name: state with transitions
    transitions:
      - target: other state


A transition can define a ``target`` (name of the target state), a ``guard`` (a Boolean expression
that will be evaluated), an ``event`` (name of the event) and an ``action`` (code that will be executed if the
transition is processed). All those fields are optional. A full example of a transition:

.. code:: yaml

  - name: state with a transition
    transitions:
      - target: other state
        event: click
        guard: x > 1
        action: print('Hello World!')


An *internal transition* is a transition that does not declare a ``target``.
To prevent trivial infinite loops on execution, an internal transition **must** either define an event
or define a guard.

.. _yaml_example:


Example
*******

Full example of a statechart definition using YAML.

.. literalinclude:: ../examples/concrete/elevator.yaml
   :language: yaml


Defining statecharts in Python
------------------------------

While it is not very convenient, it is still possible to define the statechart using Python objects.
The following sections detail the Python structure of a statechart.


The module :py:mod:`sismic.model` contains several classes and mixins to define
states, transitions and events. Apart from the mixin classes, it defines:

.. automodule:: sismic.model
    :members: Event, Transition, BasicState, CompoundState, OrthogonalState, HistoryState, FinalState, StateChart
    :member-order: bysource

Consider the source of :py:mod:`sismic.io` as an example of how to construct a statechart using :py:mod:`sismic.model`.

