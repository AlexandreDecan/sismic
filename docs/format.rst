Defining statecharts
====================

Defining statecharts in YAML
----------------------------

Statecharts can be defined using a YAML format.

A YAML definition of a statechart can be easily imported to a :py:class:`~pyss.model.StateChart` instance.
The module :py:mod:`pyss.io` provides a convenient loader :py:func:`~pyss.io.import_from_yaml` which takes a textual YAML definition
of a statechart. It also provides ways to export statechart to YAML.

.. automodule:: pyss.io
    :members: import_from_yaml, export_to_yaml

Although the parser is quite robut and should warn about most syntaxic problems, a :py:class:`~pyss.model.StateChart` instance has a
:py:meth:`~pyss.model.StateChart.validate` method performs numerous other checks. This method either return ``True`` if the statechart *seems* to
be valid, or raise an ``AssertionError`` exception with a meaningful message.


Statechart elements
*******************

Statechart
^^^^^^^^^^

The root of the YAML file should declare a statechart:

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
Each state consist of at least a ``name``. Depending on the state type, several fields can be declared.

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

Final and History states
^^^^^^^^^^^^^^^^^^^^^^^^

Final state simply declares a ``type: final`` property.
History state simply declares a ``type: history`` property. Default semantic is shallow history.
For a deep history semantic, add a ``deep: True`` property. Example:

.. code:: yaml

    - name: s1
    - name: history state
      type: history
      deep: True
    - name: s2
      type: final

An history state can optionally define an initial state using ``initial``, for e.g.:

.. code:: yaml

  - name: history state
    type: history
    initial: s1

The ``initial`` value (for history state or, later, for compound state) should refer to a parent's
substate and will be used the first time the history state is reached if it has not yet a memorized configuration.


Compound states
^^^^^^^^^^^^^^^

Except final states and history states, states can contain nested states.
Such a state is a *compound state*.

.. code:: yaml

  - name: compound state
    states:
      - name: nested state 1
      - name: nested state 2
        states:
          - name: nested state 2a

**note:** PySS does not expose the *region* concept of a statechart.
A *region* is an aggregate of several state, and can be expressed using a compound state.

Orthogonal states
^^^^^^^^^^^^^^^^^

Orthogonal states (sometimes referred as parallel states) must be with ``parallel states`` instead of ``states``.
For example, the following statechart declares two concurrent processes:

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

Simple states, compound states and parallel states can declare transitions using ``transitions``:

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


An internal transition is a transition that does not declare a ``target``, implicitly meaning that its ``target`` is
the state in which the transition is defined. When such a transition is processed, the parent state is not exited nor
entered.

Finally, to prevent trivial infinite loops on execution, an internal transition must either define an event or a guard.


.. _yaml_example:


Example
*******

Full example of a statechart definition using YAML.

.. literalinclude:: ../examples/concrete/elevator.yaml
   :language: yaml


Defining statecharts in Python
------------------------------

While it is possible to directly define the statechart using Python objects,
this is not very convenient.

Events, transitions and states
******************************

The module :py:mod:`pyss.model` contains several classes and mixins to define
states, transitions and events. Apart from
:py:class:`~pyss.model.StateMixin`, :py:class:`~pyss.model.ActionStateMixin`,
:py:class:`~pyss.model.TransitionStateMixin`, and :py:class:`~pyss.model.CompositeStateMixin`, it defines:

.. automodule:: pyss.model
    :members: Event, Transition, BasicState, CompoundState, OrthogonalState, HistoryState, FinalState
    :member-order: bysource

Statecharts
***********

The :py:class:`~pyss.model.StateChart` class is probably more interesting in the sense that
your are more subject to deal with instances of this class.

.. autoclass:: pyss.model.StateChart
    :members:

Consider the source of :py:mod:`pyss.io` as an how-to to construct a statechart using :py:mod:`pyss.model`.
