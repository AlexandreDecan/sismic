Statecharts definition
======================

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

Because Sismic is supposed to be independent of a particular visual modeling tool, and easy to integrate in other programs
without requiring the implementation of a visual notation, statecharts are expressed using YAML, a human-friendly textual
notation (the alternative of using something like SCXML was discarded because its notation is too verbose and not
really "human-readable".)

.. seealso:: This section explains how the elements that compose a valid statechart in Sismic can be defined using YAML.
    If you are not familiar with YAML, have a look at `YAML official documentation <http://yaml.org/spec/1.1/>`__.

Statechart
**********

The root of the YAML file **must** declare a statechart:

.. code:: yaml

    statechart:
      name: Name of the statechart
      description: Description of the statechart
      root state:
        [...]


The *name* and the *root state* keys are mandatory, the *description* is optional.
The *root state* key contains a state definition (see below).
If specific code needs to be executed during initialization of the statechart, this can be specified
using *preamble*. In this example, the code is written in Python.

.. code:: yaml

    statechart:
      name: statechart containing initialization code
      preamble: x = 1


Code can be written on multiple lines as follows:

.. code:: yaml

    preamble: |
      x = 1
      y = 2


States
******

A statechart must declare a root state.
Each state consist of at least a mandatory *name*. Depending on the state type, other optional fields can be declared.

.. code:: yaml

    statechart:
      name: with state
      root state:
        name: root


Entry and exit actions
**********************

For each declared state, the optional *on entry* and *on exit* fields can be used to specify the code that has to be executed when entering and leaving the state:

.. code:: yaml

    - name: s1
      on entry: x += 1
      on exit: |
        x -= 1
        y = 2


Final states
************

A *final state* can be declared by specifying *type: final*:

.. code:: yaml

    - name: s1
      type: final


Shallow and deep history states
*******************************

*History states* can be declared as follows:

- *type: shallow history* to declare a *shallow history* state;
- *type: deep history* to declare a *deep history* state.

.. code:: yaml

    - name: history state
      type: shallow history

A history state can optionally declare a default initial memory using *memory*.
Importantly, the *memory* value **must** refer to a parent's substate.

.. code:: yaml

  - name: history state
    type: deep history
    memory: s1

.. seealso:: We refer to the semantics of UML for the difference between both types of histories.


Composite states
****************

A state that is neither a final state nor a history state can contain nested states.
Such a state is commonly called a *composite state*.

.. code:: yaml

  - name: composite state
    states:
      - name: nested state 1
      - name: nested state 2
        states:
          - name: nested state 2a

A composite state can define its initial state using *initial*.

.. code:: yaml

  - name: composite state
    initial: nested state 1
    states:
      - name: nested state 1
      - name: nested state 2
        initial: nested state a2
        states:
          - name: nested state 2a


.. note:: Unlike UML, but similarly to SCXML, Sismic does not explicitly represent the concept of *region*.
    A region is essentially a logical set of nested states, and thus can be viewed as a specialization of a composite state.


Orthogonal states
*****************

*Orthogonal states* (sometimes referred as *parallel states*) allow to specify multiple nested statecharts running in parallel.
They must declare their nested states using *parallel states* instead of *states*.

.. code:: yaml

  statechart:
    name: statechart containing multiple orthogonal states
    initial state:
      name: processes
      parallel states:
        - name: process 1
        - name: process 2


Transitions
***********

*Transitions* between states, compound states and parallel states can be declared with the *transitions* field.
Transitions typically specify a target state using the *target* field:

.. code:: yaml

  - name: state with transitions
    transitions:
      - target: other state

Other optional fields can be specified for a transition:
a *guard* (a Boolean expression that will be evaluated to determine if the transition can be followed),
an *event* (name of the event that will trigger the transition),
an *action* (code that will be executed if the transition is processed).
Here is a full example of a transition specification:

.. code:: yaml

  - name: state with an outgoing transition
    transitions:
      - target: some other state
        event: click
        guard: x > 1
        action: print('Hello World!')

One type of transition, called an *internal transition*, does not require to declare a *target*.
Instead, it **must** either define an event or define a guard to determine when it should become active
(otherwise, infinite loops would occur during simulation or execution).

Notice that such a transition does not trigger the *on entry* and *on exit* of its state, and can thus be used
to model an *internal action*.


Statechart examples
*******************

.. _elevator_example:

Elevator
~~~~~~~~

The Elevator statechart is one of the running examples in this documentation. Its visual description (currently not supported by Sismic) could look as follows:

.. image:: /examples/elevator/elevator.png
    :align: center

The corresponding YAML description is given below. To make the statechart self-contained, a Python class ``Doors``
is included containing two methods ``open()`` and ``close()`` and a boolean variable ``opened``. Upon entering in the *active* state, a ``doors`` object of this class will be created and initialised by setting the value of ``opened`` to ``True``.

.. literalinclude:: /examples/elevator/elevator.yaml
   :language: yaml

Microwave
~~~~~~~~~

The microwave statechart defines and relies on a set of supported events (events that are expected to be received during its execution)
and on a set of sendable events (events that will be fired by this statechart during execution).
Those events are defined in the ``description`` field of the YAML file, for documentation purpose only.

Typically, this statechart will be executed jointly with other components (keyboard, doors, lamp, heating, ...).

.. literalinclude:: /examples/microwave/microwave.yaml
    :language: yaml


Importing and validating statecharts
------------------------------------

The :py:class:`~sismic.model.Statechart` class provides several methods to construct, to query and to manipulate a statechart.
A YAML definition of a statechart can be easily imported to a :py:class:`~sismic.model.Statechart` instance.
The module :py:mod:`sismic.io` provides a convenient loader :py:func:`~sismic.io.import_from_yaml`
which takes a textual YAML definition of a statechart and returns a :py:class:`~sismic.model.Statechart` instance.

.. automodule:: sismic.io
    :members: import_from_yaml
    :noindex:

For example:

.. testcode:: python

    from sismic import io, model

    with open('examples/elevator/elevator.yaml') as f:
        statechart = io.import_from_yaml(f)
        assert isinstance(statechart, model.Statechart)

The parser performs an automatic validation against the YAML schema of the next subsection.
It also does several other checks using its :py:class:`~sismic.model.Statechart.validate` method.

.. seealso:: While statecharts can be defined in YAML, they can be defined in pure
    Python too. Moreover, :py:class:`~sismic.model.Statechart` instances exhibit several methods to query and
    manipulate statecharts (e.g.: :py:meth:`~sismic.model.Statechart.rename_state`,
    :py:meth:`~sismic.model.Statechart.rotate_transition`, :py:meth:`~sismic.model.Statechart.copy_from_statechart`, etc.).
    Consider looking at :py:class:`~sismic.model.Statechart` API for more information.


YAML validation schema
**********************

See `pykwalify <https://github.com/Grokzen/pykwalify/>`__ for more information about the semantic.

.. literalinclude:: ../sismic/io/schema.yaml
    :language: yaml

