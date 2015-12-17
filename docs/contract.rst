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
    - the invariants are checked at the end of each macro step. The state must be in the active configuration.
 - For transitions:
    - the preconditions are checked before the process of the transition (and before executing transition action).
    - the postconditions are checked after the process of the transition (and after executing transition action).
    - the invariants are checked before and after the process of the transition.
 - For statecharts:
    - the preconditions are checked before any stabilization step (**but** after executing ``on entry``).
    - the postconditions are checked when the statechart enters a final configuration.
    - the invariants are checked at the end of each macro step.


Defining contracts in YAML
--------------------------

A YAML definition of a statechart (see :ref:`yaml_statecharts`) can embed the contract definitions.
Preconditions, postconditions and invariants are defined as nested items of a ``contract`` property.
The name of these items is either ``before`` (precondition), ``after`` (postcondition) or ``always`` (invariant),
as follows:

.. code:: yaml

    contract:
     - before: ...
     - after: ...
     - always: ...

Obviously, more than one condition of each type can be specified:

.. code:: yaml

    contract:
     - before: ...
     - before: ...
     - before: ...
     - after: ...

A condition is an expression that will be evaluated by an :py:class:`~sismic.evaluator.Evaluator`
instance (see :doc:`evaluation`).

.. code:: yaml

    contract:
     - before: x > 0
     - before: y > 0
     - after: x + y == 0
     - always: x + y >= 0

Contracts can be defined for statecharts too:

.. code:: yaml

    statechart:
      name: example
      contract:
       - always: x >= 0
       - always: not active('initial') or x > 0

If you make use of the default :py:class:`~sismic.evaluator.PythonEvaluator`, the old value of a variable
is also available in ``__old__`` for postconditions and invariants:

.. code:: yaml

    contract:
      always: d > __old__.d
      after: (x - __old__.x) < d

See the documentation of :py:class:`~sismic.evaluator.PythonEvaluator` for more information.

Example
*******

The following example shows some invariants, preconditions and postconditions added
to the `Elevator example <https://github.com/AlexandreDecan/sismic/blob/master/examples/concrete/elevator.yaml>`__.

.. literalinclude:: ../examples/contract/elevator.yaml
   :language: yaml


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
The exception displays several information to help debug::

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

If you do not want the execution to be interrupted by such exceptions, you can set the ``silent_contract``
parameter to ``True`` when constructing an ``Interpreter``.
The exceptions will be stored and will be made available in

.. autoattribute:: sismic.interpreter.Interpreter.failed_conditions

Notice that nested objects in :py:exc:`~sismic.model.ConditionFailed` are copied using a shallow copy, not a deep copy.
As a consequence, there is no guarantee that the value of their attributes did not change between the time at
which the exception was initialized, and the time at which it is accessed.

Here is how the copy is done:

.. literalinclude:: ../sismic/model.py
    :pyobject: ConditionFailed.__init__


