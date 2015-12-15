Contract programming for statecharts
====================================

Sismic has a built-in support for contract programming for statecharts.

    Design by contract (DbC), also known as contract programming, programming by contract and
    design-by-contract programming, is an approach for designing software. It prescribes that
    software designers should define formal, precise and verifiable interface specifications for
    software components, which extend the ordinary definition of abstract data types with
    **preconditions, postconditions and invariants**. These specifications are referred to as
    "contracts", in accordance with a conceptual metaphor with the conditions and obligations
    of business contracts.
    --- `Wikipedia <https://en.wikipedia.org/wiki/Design_by_contract>`__


Preconditions, postconditions and invariants
--------------------------------------------

Preconditions, postconditions and invariants can be defined for statecharts, and Sismic
will check these conditions at runtime. If a condition is not satisfied, an ``AssertionError``
will be raised. More specifically, one of the three following subclasses will be raised:

.. autoexception:: sismic.model.PreconditionFailed

.. autoexception:: sismic.model.PostconditionFailed

.. autoexception:: sismic.model.InvariantFailed


The three exceptions inherit from the following subclass of ``AssertionError``:

.. autoexception:: sismic.model.ConditionFailed
    :members:


The semantic of pre/postconditions and invariants is not surprising:

 - For states:
    - the preconditions are checked before the state is entered (and before executing ``on entry``).
    - the postconditions are checked after the state is exited (and after executing ``on exit``).
    - the invariants are checked at the end of each micro step. The state must be in the active configuration.
 - For transitions:
    - the preconditions are checked before the process of the transition (and before executing transition action).
    - the postconditions are checked after the process of the transition (and after executing transition action).



Defining contracts in YAML
--------------------------

A YAML definition of a statechart (see :ref:`yaml_statecharts`) can embed the contract definitions.
Preconditions, postconditions and invariants are defined as nested items of a ``contract`` property,
as follows:

.. code:: yaml

    contract:
     - pre: ...
     - post: ...
     - inv: ...

Obviously, more than one condition of each type can be specified:

.. code:: yaml

    contract:
     - pre: ...
     - pre: ...
     - pre: ...
     - post: ...

A condition is an expression that will be evaluated by method :py:meth:`~sismic.evaluator.Evaluator.evaluate_condition`
of an :py:class:`~sismic.evaluator.Evaluator` instance (see :doc:`evaluation`).
..
The following example expects a :py:class:`~sismic.evaluator.PythonEvaluator`, which is the default one.

.. code:: yaml

    contract:
     - pre: x > 0
     - pre: y > 0
     - post: x + y == 0
     - inv: x + y >= 0

While a ``contract`` can be defined both for states and transitions, a contract for a transition can only contain
preconditions (``pre``) and postconditions (``post``) but no invariant (``inv``).

.. code:: yaml

    states:
     - name: s1
       on entry: x = x - 1
       contract:
         - pre: x > 0
       transitions:
         - event: tick
           target: s2
           contract:
            - pre: x >= 0


Example
*******

The following example shows some invariants, preconditions and postconditions added
to the `Elevator example <https://github.com/AlexandreDecan/sismic/blob/master/examples/concrete/elevator.yaml>`__.

.. literalinclude:: ../examples/contract/elevator.yaml
   :language: yaml
   :diff: ../examples/concrete/elevator.yaml


Defining contracts in Python
----------------------------

The class :py:class:`~sismic.model.Transition` inherits from :py:class:`~sismic.model.ConditionsMixin`
which makes available two lists of strings, namely ``preconditions`` and ``postconditions``.
Similarly, every subclass of :py:class:`~sismic.model.StateMixin` inherits from :py:class:`~sismic.model.ConditionsMixin`
and from :py:class:`~sismic.model.InvariantsMixin`.
The later adds a ``invariants`` list of strings representing the conditions.

.. autoclass:: sismic.model.ConditionsMixin
    :members:
    :inherited-members:
    :undoc-members:

.. autoclass:: sismic.model.InvariantsMixin
    :members:
    :inherited-members:
    :undoc-members:


Executing statecharts with contract
-----------------------------------

The execution of a statechart that contains preconditions, postconditions and invariants does not differ
from the execution of a statechart that does not. The only difference is that conditions are checked
at runtime and may raise a subclass of :py:exc:`~sismic.model.ConditionFailed`.

.. code:: python

    from sismic.model import Event
    from sismic.interpreter import Interpreter
    from sismic.io import import_from_yaml

    with open('examples/contract/elevator.yaml') as f:
        statechart = import_from_yaml(f)
        interpreter = Interpreter(statechart)
        interpreter.send(Event('floorSelected', {'floor': 4}))
        interpreter.execute()

Here we manually changed one of the precondition such that it failed at runtime.
The exception displays several information to help debug.

    PreconditionFailed: Assertion not satisfied!
    Object: BasicState(movingUp)
    Assertion: current > destination
    Configuration: ['active', 'floorListener', 'movingElevator', 'floorSelecting']
    Step: MicroStep(None, doorsClosed -> movingUp, ['moving', 'movingUp'], ['doorsClosed'])
    Evaluation context:
     - send = <function PythonEvaluator.__init__.<locals>.<lambda> at 0x7ff07fd1d620>
     - active = <function PythonEvaluator.__init__.<locals>.<lambda> at 0x7ff0709ce950>
     - doors = <Doors object at 0x7ff070942da0>
     - event = None
     - current = 0
     - Doors = <class 'Doors'>
     - Event = <class 'sismic.model.Event'>
     - destination = 4
